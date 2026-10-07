from __future__ import annotations

import collections
import re
import time
from typing import Any

import structlog
from sqlalchemy import event
from sqlalchemy.engine import Connection, CursorResult, ExecutionContext

log = structlog.get_logger(__name__)


def _fingerprint_sql(statement: str) -> str:
    """Normalizes SQL statement by stripping extra whitespace, params, and newlines."""
    stmt = re.sub(r"\s+", " ", statement).strip()
    # Mask string literals and numbers
    stmt = re.sub(r"'[^']*'", "'?'", stmt)
    stmt = re.sub(r"\b\d+\b", "?", stmt)
    # Mask UUIDs
    stmt = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "?", stmt, flags=re.IGNORECASE)
    return stmt[:200]


class QueryProfiler:
    """
    SQLAlchemy Database Query Profiler.
    Monitors all SQL statement executions, measures timing, detects slow queries (> 30ms),
    and flags N+1 query antipatterns.
    """

    _instance: QueryProfiler | None = None

    SLOW_THRESHOLD_MS = 30.0  # ms
    N_PLUS_ONE_THRESHOLD = 3  # repetitions in sliding window

    def __init__(self) -> None:
        self._is_hooked = False
        self._total_queries = 0
        self._total_duration_ms = 0.0
        self._slow_queries: collections.deque[dict[str, Any]] = collections.deque(maxlen=100)
        self._recent_queries: collections.deque[dict[str, Any]] = collections.deque(maxlen=100)
        self._fingerprint_stats: dict[str, dict[str, Any]] = {}
        # Sliding window for N+1 detection: fingerprint -> deque of timestamps
        self._fingerprint_window: dict[str, collections.deque[float]] = collections.defaultdict(
            lambda: collections.deque(maxlen=20)
        )
        self._n_plus_one_alerts: list[dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> QueryProfiler:
        if cls._instance is None:
            cls._instance = QueryProfiler()
        return cls._instance

    def attach_to_engine(self, async_engine: Any) -> None:
        """Attaches execution listeners to SQLAlchemy async engine's underlying sync engine."""
        if self._is_hooked:
            return
        try:
            sync_engine = getattr(async_engine, "sync_engine", async_engine)

            @event.listens_for(sync_engine, "before_cursor_execute")
            def before_cursor_execute(
                conn: Connection,
                cursor: Any,
                statement: str,
                parameters: Any,
                context: ExecutionContext | None,
                executemany: bool,
            ) -> None:
                if context:
                    context._query_start_time = time.perf_counter()  # type: ignore[attr-defined]

            @event.listens_for(sync_engine, "after_cursor_execute")
            def after_cursor_execute(
                conn: Connection,
                cursor: Any,
                statement: str,
                parameters: Any,
                context: ExecutionContext | None,
                executemany: bool,
            ) -> None:
                start_time = getattr(context, "_query_start_time", None) if context else None
                if start_time is not None:
                    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                else:
                    duration_ms = 1.0

                self.record_query(statement, duration_ms)

            self._is_hooked = True
            log.info("query_profiler_hooked", slow_threshold_ms=self.SLOW_THRESHOLD_MS)
        except Exception as exc:
            log.warning("query_profiler_hook_failed", error=str(exc))

    def record_query(self, statement: str, duration_ms: float) -> dict[str, Any]:
        """Manually or automatically records a query execution and evaluates thresholds."""
        now = time.time()
        self._total_queries += 1
        self._total_duration_ms += duration_ms

        fp = _fingerprint_sql(statement)
        is_slow = duration_ms >= self.SLOW_THRESHOLD_MS

        # Update stats per fingerprint
        if fp not in self._fingerprint_stats:
            self._fingerprint_stats[fp] = {
                "fingerprint": fp,
                "statement_sample": statement[:180],
                "call_count": 0,
                "total_duration_ms": 0.0,
                "min_duration_ms": duration_ms,
                "max_duration_ms": duration_ms,
                "avg_duration_ms": duration_ms,
                "is_slow": is_slow,
                "is_n_plus_one": False,
            }

        st = self._fingerprint_stats[fp]
        st["call_count"] += 1
        st["total_duration_ms"] = round(st["total_duration_ms"] + duration_ms, 2)
        st["min_duration_ms"] = min(st["min_duration_ms"], duration_ms)
        st["max_duration_ms"] = max(st["max_duration_ms"], duration_ms)
        st["avg_duration_ms"] = round(st["total_duration_ms"] / st["call_count"], 2)
        if is_slow:
            st["is_slow"] = True

        # N+1 Sliding Window Evaluation (queries within 3.0s window)
        ts_queue = self._fingerprint_window[fp]
        # Clean older than 3 seconds
        while ts_queue and (now - ts_queue[0]) > 3.0:
            ts_queue.popleft()
        ts_queue.append(now)

        is_n1 = False
        if len(ts_queue) >= self.N_PLUS_ONE_THRESHOLD:
            is_n1 = True
            st["is_n_plus_one"] = True
            # Check if not recently alerted
            if not any(a["fingerprint"] == fp and (now - a["timestamp"]) < 10.0 for a in self._n_plus_one_alerts):
                self._n_plus_one_alerts.append({
                    "fingerprint": fp,
                    "frequency": len(ts_queue),
                    "statement": statement[:160],
                    "recommendation": "Potential N+1 query loop detected. Use joinedload() or selectinload() on related collections.",
                    "timestamp": now,
                })
                log.warning("n_plus_one_query_detected", fingerprint=fp, frequency=len(ts_queue))

        record = {
            "statement": statement[:200],
            "fingerprint": fp,
            "duration_ms": duration_ms,
            "is_slow": is_slow,
            "is_n_plus_one": is_n1,
            "timestamp": now,
        }

        self._recent_queries.append(record)
        if is_slow:
            self._slow_queries.append(record)

        return record

    def get_summary(self) -> dict[str, Any]:
        avg_query_time = round(self._total_duration_ms / max(self._total_queries, 1), 2)
        sorted_fps = sorted(
            self._fingerprint_stats.values(),
            key=lambda x: x["max_duration_ms"],
            reverse=True,
        )

        return {
            "total_queries_executed": self._total_queries,
            "total_duration_ms": round(self._total_duration_ms, 2),
            "average_duration_ms": avg_query_time,
            "slow_query_count": len(self._slow_queries),
            "n_plus_one_alerts_count": len(self._n_plus_one_alerts),
            "slow_threshold_ms": self.SLOW_THRESHOLD_MS,
            "top_slow_queries": list(self._slow_queries)[-15:],
            "top_fingerprints": sorted_fps[:10],
            "n_plus_one_warnings": self._n_plus_one_alerts[-5:],
        }

    def reset(self) -> None:
        self._total_queries = 0
        self._total_duration_ms = 0.0
        self._slow_queries.clear()
        self._recent_queries.clear()
        self._fingerprint_stats.clear()
        self._fingerprint_window.clear()
        self._n_plus_one_alerts.clear()
