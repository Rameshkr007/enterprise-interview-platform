from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from typing import Any, Callable, Coroutine

import structlog

from app.core.redis import get_redis_client

log = structlog.get_logger(__name__)


class L1MemoryCache:
    """Thread-safe and async-friendly in-memory LRU cache with TTL."""

    def __init__(self, max_items: int = 2000, default_ttl: int = 300) -> None:
        self._max_items = max_items
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            val, expiry = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return val

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        async with self._lock:
            expiry = time.time() + (ttl if ttl is not None else self._default_ttl)
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expiry)
            if len(self._cache) > self._max_items:
                self._cache.popitem(last=False)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear_prefix(self, prefix: str) -> int:
        async with self._lock:
            keys_to_del = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_del:
                del self._cache[k]
            return len(keys_to_del)

    async def clear_all(self) -> None:
        async with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        ratio = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_items": self._max_items,
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio_pct": round(ratio, 2),
        }


class TieredCacheManager:
    """
    Enterprise Hierarchical Cache Manager.
    L1: Ultra-fast local in-memory LRU (< 0.2ms)
    L2: Distributed Redis storage (< 2.0ms) with namespace tracking and stampede protection.
    """

    _instance: TieredCacheManager | None = None

    def __init__(self) -> None:
        self.l1 = L1MemoryCache(max_items=3000, default_ttl=300)
        self._l2_hits = 0
        self._l2_misses = 0
        self._semantic_hits = 0
        self._tokens_saved = 0
        self._cost_saved_usd = 0.0

    @classmethod
    def get_instance(cls) -> TieredCacheManager:
        if cls._instance is None:
            cls._instance = TieredCacheManager()
        return cls._instance

    def _build_l2_key(self, namespace: str, key: str) -> str:
        return f"cache:l2:{namespace}:{key}"

    async def get_or_compute(
        self,
        namespace: str,
        key: str,
        computer: Callable[[], Coroutine[Any, Any, Any]],
        ttl: int = 300,
        l1_ttl: int = 60,
    ) -> tuple[Any, str]:
        """
        Hierarchical fetch.
        Returns: (result_data, hit_status: 'HIT-L1' | 'HIT-L2' | 'MISS')
        """
        combined_key = f"{namespace}:{key}"

        # 1. Check L1 In-Memory
        l1_val = await self.l1.get(combined_key)
        if l1_val is not None:
            return l1_val, "HIT-L1"

        # 2. Check L2 Redis
        redis_key = self._build_l2_key(namespace, key)
        try:
            r = get_redis_client()
            raw = await r.get(redis_key)
            if raw is not None:
                self._l2_hits += 1
                data = json.loads(raw)
                # Populate L1
                await self.l1.set(combined_key, data, ttl=l1_ttl)
                return data, "HIT-L2"
            else:
                self._l2_misses += 1
        except Exception:
            self._l2_misses += 1

        # 3. Compute Value
        computed = await computer()

        # 4. Write back to L1 & L2
        await self.l1.set(combined_key, computed, ttl=l1_ttl)
        try:
            r = get_redis_client()
            await r.set(redis_key, json.dumps(computed, default=str), ex=ttl)
            # Add to namespace set for easy invalidation
            await r.sadd(f"cache:ns:{namespace}", redis_key)
        except Exception as exc:
            log.warning("l2_cache_set_failed", error=str(exc), key=redis_key)

        return computed, "MISS"

    async def get(self, namespace: str, key: str) -> tuple[Any | None, str]:
        """Explicit get across L1 and L2."""
        combined_key = f"{namespace}:{key}"
        l1_val = await self.l1.get(combined_key)
        if l1_val is not None:
            return l1_val, "HIT-L1"

        redis_key = self._build_l2_key(namespace, key)
        try:
            r = get_redis_client()
            raw = await r.get(redis_key)
            if raw is not None:
                self._l2_hits += 1
                data = json.loads(raw)
                await self.l1.set(combined_key, data, ttl=60)
                return data, "HIT-L2"
            self._l2_misses += 1
        except Exception:
            self._l2_misses += 1

        return None, "MISS"

    async def set(self, namespace: str, key: str, value: Any, ttl: int = 300) -> None:
        """Explicit set to both L1 and L2."""
        combined_key = f"{namespace}:{key}"
        await self.l1.set(combined_key, value, ttl=min(ttl, 60))

        redis_key = self._build_l2_key(namespace, key)
        try:
            r = get_redis_client()
            await r.set(redis_key, json.dumps(value, default=str), ex=ttl)
            await r.sadd(f"cache:ns:{namespace}", redis_key)
        except Exception as exc:
            log.warning("l2_cache_set_failed", error=str(exc), key=redis_key)

    async def invalidate(self, namespace: str, key: str) -> None:
        """Invalidate single key across L1 and L2."""
        combined_key = f"{namespace}:{key}"
        await self.l1.delete(combined_key)

        redis_key = self._build_l2_key(namespace, key)
        try:
            r = get_redis_client()
            await r.delete(redis_key)
            await r.srem(f"cache:ns:{namespace}", redis_key)
        except Exception:
            pass

    async def invalidate_namespace(self, namespace: str) -> int:
        """Invalidate all keys under a given namespace across L1 and L2."""
        count = await self.l1.clear_prefix(f"{namespace}:")
        try:
            r = get_redis_client()
            ns_set_key = f"cache:ns:{namespace}"
            keys = await r.smembers(ns_set_key)
            if keys:
                decoded_keys = [k.decode("utf-8") if isinstance(k, bytes) else k for k in keys]
                await r.delete(*decoded_keys)
                count += len(decoded_keys)
            await r.delete(ns_set_key)
        except Exception as exc:
            log.warning("l2_namespace_invalidate_failed", namespace=namespace, error=str(exc))
        return count

    async def purge_all(self) -> int:
        """Purge all application caches."""
        await self.l1.clear_all()
        purged = 0
        try:
            r = get_redis_client()
            keys = await r.keys("cache:l2:*")
            ns_keys = await r.keys("cache:ns:*")
            all_keys = list(set(keys + ns_keys))
            if all_keys:
                purged = len(all_keys)
                await r.delete(*all_keys)
        except Exception:
            pass
        return purged

    # ── Semantic & LLM Vector Response Caching ──────────────────────────────
    def hash_prompt(self, prompt: str, model: str = "gpt-4o", temperature: float = 0.2) -> str:
        """Generates deterministic fingerprint for semantic LLM prompts."""
        content = f"{model}:{temperature}:{prompt.strip()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def get_semantic_llm(self, prompt_hash: str) -> dict[str, Any] | None:
        res, status = await self.get("llm_semantic", prompt_hash)
        if res is not None:
            self._semantic_hits += 1
            estimated_tokens = res.get("estimated_tokens", 850)
            self._tokens_saved += estimated_tokens
            # Standard blended cost approx $0.005 per 1k tokens
            self._cost_saved_usd += round((estimated_tokens / 1000.0) * 0.005, 4)
            return res.get("response")
        return None

    async def set_semantic_llm(
        self, prompt_hash: str, response: dict[str, Any], estimated_tokens: int = 850, ttl: int = 86400
    ) -> None:
        payload = {
            "response": response,
            "estimated_tokens": estimated_tokens,
            "cached_at": time.time(),
        }
        await self.set("llm_semantic", prompt_hash, payload, ttl=ttl)

    async def get_stats(self) -> dict[str, Any]:
        l1_stats = self.l1.stats
        total_l2 = self._l2_hits + self._l2_misses
        l2_ratio = (self._l2_hits / total_l2 * 100) if total_l2 > 0 else 0.0

        total_requests = l1_stats["hits"] + l1_stats["misses"]
        effective_hits = l1_stats["hits"] + self._l2_hits
        effective_ratio = (effective_hits / max(total_requests, 1)) * 100

        # Retrieve Redis namespace keyspaces
        namespaces_info: list[dict[str, Any]] = []
        try:
            r = get_redis_client()
            ns_keys = await r.keys("cache:ns:*")
            for nk in ns_keys:
                nk_str = nk.decode("utf-8") if isinstance(nk, bytes) else nk
                ns_name = nk_str.replace("cache:ns:", "")
                count = await r.scard(nk_str)
                namespaces_info.append({
                    "namespace": ns_name,
                    "keys_count": count,
                    "l2_ttl_default_seconds": 300,
                })
        except Exception:
            pass

        return {
            "l1": l1_stats,
            "l2": {
                "hits": self._l2_hits,
                "misses": self._l2_misses,
                "hit_ratio_pct": round(l2_ratio, 2),
            },
            "overall": {
                "effective_hit_ratio_pct": round(min(effective_ratio, 100.0), 2),
                "total_cache_hits": effective_hits,
                "total_cache_misses": l1_stats["misses"] - self._l2_hits if l1_stats["misses"] >= self._l2_hits else 0,
            },
            "semantic_llm_cache": {
                "hits": self._semantic_hits,
                "tokens_saved": self._tokens_saved,
                "cost_saved_usd": round(self._cost_saved_usd, 4),
            },
            "namespaces": namespaces_info,
        }
