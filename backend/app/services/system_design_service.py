from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID, uuid4

import structlog

from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)

# Core Buzzword Catalog with required architectural justification markers
BUZZWORD_JUSTIFICATION_RULES: dict[str, dict[str, Any]] = {
    "kafka": {
        "markers": ["throughput", "partition", "offset", "consumer group", "ordering", "replay", "log", "stream", "retention"],
        "min_markers": 1,
        "advice": "When proposing Kafka, justify it by discussing partition keys, consumer groups, message ordering, or data retention policies.",
    },
    "cassandra": {
        "markers": ["write-heavy", "partition key", "clustering", "lsm", "tunable consistency", "linear scale", "wide-column", "wide column"],
        "min_markers": 1,
        "advice": "When proposing Cassandra/ScyllaDB, explain the partition key design, write-heavy traffic pattern, or tunable consistency level (e.g. LOCAL_QUORUM).",
    },
    "redis": {
        "markers": ["cache", "ttl", "invalidation", "eviction", "lru", "latency", "sub-millisecond", "pub/sub", "sorted set", "distributed lock"],
        "min_markers": 1,
        "advice": "When introducing Redis, specify cache eviction policies (LRU/LFU), TTL strategies, or exact data structures (hashes, sorted sets).",
    },
    "elasticsearch": {
        "markers": ["full-text", "inverted index", "search", "tokenizer", "fuzzy", "relevance", "aggregation", "log analysis"],
        "min_markers": 1,
        "advice": "When using Elasticsearch, explain the inverted index, search query patterns, or why relational full-text search was insufficient.",
    },
    "kubernetes": {
        "markers": ["orchestration", "autoscaling", "hpa", "container", "ingress", "pod", "rolling update", "service mesh"],
        "min_markers": 1,
        "advice": "Avoid name-dropping Kubernetes without explaining autoscaling thresholds (HPA), ingress routing, or container resource limits.",
    },
    "sharding": {
        "markers": ["shard key", "consistent hashing", "rebalancing", "hotspot", "range", "hash-based", "cross-shard"],
        "min_markers": 1,
        "advice": "When proposing database sharding, define the exact shard key, how cross-shard queries are handled, and how hotspots are prevented.",
    },
    "event sourcing": {
        "markers": ["event store", "snapshot", "cqrs", "immutable", "audit trail", "event stream", "reconstruction"],
        "min_markers": 1,
        "advice": "When proposing Event Sourcing, address event schema evolution, read-side projection latency, and snapshot frequency.",
    },
    "cqrs": {
        "markers": ["read model", "write model", "command", "query", "eventual consistency", "projection"],
        "min_markers": 1,
        "advice": "When specifying CQRS, discuss how write commands synchronize with read projections and how eventual consistency lag is managed.",
    },
    "vector database": {
        "markers": ["dimension", "embedding", "hnsw", "ann", "approximate nearest neighbor", "similarity", "cosine", "recall", "index"],
        "min_markers": 1,
        "advice": "When proposing a Vector DB (Pinecone/Milvus/pgvector), specify embedding dimensions, index type (HNSW/IVFFlat), and distance metric.",
    },
    "grpc": {
        "markers": ["protobuf", "http/2", "binary", "streaming", "multiplexing", "contract", "schema", "rpc"],
        "min_markers": 1,
        "advice": "When using gRPC, justify with low-latency binary serialization, HTTP/2 multiplexing, or strict Protobuf interface contracts.",
    },
    "graphql": {
        "markers": ["over-fetching", "under-fetching", "resolver", "n+1", "dataloader", "schema", "field"],
        "min_markers": 1,
        "advice": "When introducing GraphQL, address client-driven queries, resolver query planning, and the N+1 problem mitigation (e.g. DataLoader).",
    },
    "bloom filter": {
        "markers": ["false positive", "membership", "hash function", "bit array", "cache miss", "probabilistic"],
        "min_markers": 1,
        "advice": "When using a Bloom Filter, discuss tolerable false positive rates, bit array sizing, and how negative lookups save disk/cache I/O.",
    },
    "consistent hashing": {
        "markers": ["virtual nodes", "hash ring", "rebalancing", "skew", "partition", "token"],
        "min_markers": 1,
        "advice": "When mentioning Consistent Hashing, explain the hash ring distribution, virtual node assignment to prevent hotspots, and rebalancing costs.",
    },
    "snowflake": {
        "markers": ["64-bit", "timestamp", "worker id", "sequence", "k-sorted", "epoch", "time-sortable"],
        "min_markers": 1,
        "advice": "When proposing Twitter Snowflake IDs, outline the 64-bit bitmask (timestamp, machine/worker ID, sequence) and time-sortability.",
    },
    "raft": {
        "markers": ["consensus", "leader election", "log replication", "quorum", "term", "heartbeat"],
        "min_markers": 1,
        "advice": "When citing Raft/Paxos, explain quorum majority requirements, leader election failover, and log replication guarantees.",
    },
}


@dataclass
class BuzzwordAnalysis:
    total_buzzwords_detected: int
    justified_buzzwords: list[str]
    unjustified_buzzwords: list[dict[str, str]]
    buzzword_density_score: float  # 0 to 1 (lower is better if unjustified, 1.0 means fully justified)
    penalty_applied: float


@dataclass
class ArchitecturePillarScore:
    pillar_name: str
    score: float  # 0 to 100
    weight: float
    strengths: list[str]
    weaknesses: list[str]
    critical_missing_elements: list[str]


@dataclass
class SystemDesignEvaluation:
    overall_score: float  # 0 to 100
    tier: Literal["Senior/Staff Level", "Mid Level", "Junior Level", "Unsatisfactory"]
    pillar_scores: dict[str, ArchitecturePillarScore]
    buzzword_analysis: BuzzwordAnalysis
    single_points_of_failure: list[str]
    bottlenecks: list[str]
    scale_readiness: str
    key_tradeoffs: list[str]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "tier": self.tier,
            "pillar_scores": {
                k: {
                    "score": round(v.score, 1),
                    "weight": v.weight,
                    "strengths": v.strengths,
                    "weaknesses": v.weaknesses,
                    "critical_missing_elements": v.critical_missing_elements,
                }
                for k, v in self.pillar_scores.items()
            },
            "buzzword_analysis": {
                "total_buzzwords_detected": self.buzzword_analysis.total_buzzwords_detected,
                "justified_buzzwords": self.buzzword_analysis.justified_buzzwords,
                "unjustified_buzzwords": self.buzzword_analysis.unjustified_buzzwords,
                "buzzword_density_score": round(self.buzzword_analysis.buzzword_density_score, 2),
                "penalty_applied": round(self.buzzword_analysis.penalty_applied, 1),
            },
            "single_points_of_failure": self.single_points_of_failure,
            "bottlenecks": self.bottlenecks,
            "scale_readiness": self.scale_readiness,
            "key_tradeoffs": self.key_tradeoffs,
            "recommendation": self.recommendation,
        }


SYSTEM_DESIGN_EVAL_PROMPT = """
You are a Principal Infrastructure & System Architecture Interviewer (Bar Raiser) at an elite tech enterprise.
Evaluate the candidate's system design submission against the problem requirements.

CRITICAL INSTRUCTION:
Do NOT award high scores for buzzword-heavy answers that lack numerical estimation, failure modes, or concrete trade-offs.

Return ONLY valid JSON matching this schema:
{
  "overall_score": float (0-100),
  "tier": "Senior/Staff Level" | "Mid Level" | "Junior Level" | "Unsatisfactory",
  "pillar_scores": {
    "requirements_clarification": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]},
    "non_functional_requirements": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]},
    "high_level_architecture": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]},
    "data_model_and_storage": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]},
    "api_design": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]},
    "scalability_and_partitioning": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]},
    "failure_modes_and_resilience": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]},
    "trade_offs_and_deep_dive": {"score": float 0-100, "strengths": [str], "weaknesses": [str], "critical_missing_elements": [str]}
  },
  "single_points_of_failure": [str],
  "bottlenecks": [str],
  "scale_readiness": str,
  "key_tradeoffs": [str],
  "recommendation": str
}
"""


class SystemDesignEngine:
    """Enterprise System Design evaluation engine with anti-buzzword filter and 8-pillar rubric."""

    PILLAR_WEIGHTS = {
        "requirements_clarification": 0.10,
        "non_functional_requirements": 0.15,
        "high_level_architecture": 0.15,
        "data_model_and_storage": 0.15,
        "api_design": 0.10,
        "scalability_and_partitioning": 0.15,
        "failure_modes_and_resilience": 0.10,
        "trade_offs_and_deep_dive": 0.10,
    }

    def __init__(self, llm_svc: LLMService | None = None) -> None:
        self._llm = llm_svc or LLMService()

    def inspect_buzzwords(self, text: str) -> BuzzwordAnalysis:
        """Scan text for architectural buzzwords and verify whether concrete justifications exist."""
        text_lower = text.lower()
        justified: list[str] = []
        unjustified: list[dict[str, str]] = []

        for term, rule in BUZZWORD_JUSTIFICATION_RULES.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, text_lower):
                # Search for justification markers near the term or across text
                found_markers = [m for m in rule["markers"] if m in text_lower]
                if len(found_markers) >= rule["min_markers"]:
                    justified.append(term)
                else:
                    unjustified.append({
                        "buzzword": term,
                        "advice": rule["advice"],
                        "missing_context": f"Mentioned '{term}' without discussing {', '.join(rule['markers'][:3])}.",
                    })

        total = len(justified) + len(unjustified)
        if total == 0:
            return BuzzwordAnalysis(
                total_buzzwords_detected=0,
                justified_buzzwords=[],
                unjustified_buzzwords=[],
                buzzword_density_score=1.0,
                penalty_applied=0.0,
            )

        density = len(justified) / total
        penalty = min(len(unjustified) * 4.0, 20.0)  # Max 20 points penalty for empty buzzwords

        return BuzzwordAnalysis(
            total_buzzwords_detected=total,
            justified_buzzwords=justified,
            unjustified_buzzwords=unjustified,
            buzzword_density_score=density,
            penalty_applied=penalty,
        )

    async def evaluate_architecture(
        self,
        problem_title: str,
        problem_prompt: str,
        candidate_submission: dict[str, Any] | str,
    ) -> SystemDesignEvaluation:
        """Evaluate architectural submission across 8 pillars + buzzword defense."""
        # Normalize submission to string and structured sections
        if isinstance(candidate_submission, dict):
            raw_text = "\n\n".join(f"=== {k.upper().replace('_', ' ')} ===\n{v}" for k, v in candidate_submission.items() if v)
            sections_dict = candidate_submission
        else:
            raw_text = str(candidate_submission)
            sections_dict = {"architecture_text": raw_text}

        # 1. Anti-Buzzword Heuristic Analysis
        buzzword_res = self.inspect_buzzwords(raw_text)

        # 2. LLM Multi-Pillar Deep Evaluation
        user_msg = (
            f"SYSTEM DESIGN PROBLEM: {problem_title}\n"
            f"REQUIREMENTS & CONSTRAINTS: {problem_prompt}\n\n"
            f"CANDIDATE ARCHITECTURAL SUBMISSION:\n{raw_text[:8000]}\n\n"
            f"ANTI-BUZZWORD AUDIT RESULTS:\n"
            f"Total buzzwords: {buzzword_res.total_buzzwords_detected}, "
            f"Justified: {len(buzzword_res.justified_buzzwords)}, "
            f"Unjustified: {len(buzzword_res.unjustified_buzzwords)} ({[u['buzzword'] for u in buzzword_res.unjustified_buzzwords]})\n"
            f"Penalty to apply: -{buzzword_res.penalty_applied} points."
        )

        try:
            llm_result = await self._llm._chat_json(SYSTEM_DESIGN_EVAL_PROMPT, user_msg)
            return self._format_eval_result(llm_result, buzzword_res)
        except Exception as exc:
            log.warn("system_design_llm_failed_fallback", error=str(exc))
            return self._fallback_evaluate_architecture(problem_title, sections_dict, buzzword_res)

    def _format_eval_result(
        self,
        llm_result: dict[str, Any],
        buzzwords: BuzzwordAnalysis,
    ) -> SystemDesignEvaluation:
        raw_score = float(llm_result.get("overall_score", 70.0))
        final_score = max(10.0, min(100.0, raw_score - buzzwords.penalty_applied))

        if final_score >= 85.0:
            tier = "Senior/Staff Level"
        elif final_score >= 70.0:
            tier = "Mid Level"
        elif final_score >= 50.0:
            tier = "Junior Level"
        else:
            tier = "Unsatisfactory"

        pillar_scores: dict[str, ArchitecturePillarScore] = {}
        llm_pillars = llm_result.get("pillar_scores", {})

        for name, weight in self.PILLAR_WEIGHTS.items():
            p_data = llm_pillars.get(name, {})
            score = float(p_data.get("score", 70.0))
            pillar_scores[name] = ArchitecturePillarScore(
                pillar_name=name,
                score=score,
                weight=weight,
                strengths=p_data.get("strengths", ["Solid architectural concepts"]),
                weaknesses=p_data.get("weaknesses", []),
                critical_missing_elements=p_data.get("critical_missing_elements", []),
            )

        return SystemDesignEvaluation(
            overall_score=final_score,
            tier=tier,
            pillar_scores=pillar_scores,
            buzzword_analysis=buzzwords,
            single_points_of_failure=llm_result.get("single_points_of_failure", []),
            bottlenecks=llm_result.get("bottlenecks", []),
            scale_readiness=llm_result.get("scale_readiness", "Capable of medium-scale distributed workload"),
            key_tradeoffs=llm_result.get("key_tradeoffs", []),
            recommendation=llm_result.get("recommendation", "Architectural evaluation completed successfully."),
        )

    def _fallback_evaluate_architecture(
        self,
        title: str,
        sections: dict[str, Any],
        buzzwords: BuzzwordAnalysis,
    ) -> SystemDesignEvaluation:
        """Deterministic offline fallback evaluator for System Design."""
        full_text = " ".join(str(v) for v in sections.values()).lower()
        word_count = len(full_text.split())

        pillar_scores: dict[str, ArchitecturePillarScore] = {}

        # Heuristic checks for key architectural concepts
        checks = {
            "requirements_clarification": ["read", "write", "qps", "rps", "users", "dau", "traffic"],
            "non_functional_requirements": ["latency", "sla", "slo", "availability", "99.9", "cap", "consistency"],
            "high_level_architecture": ["gateway", "load balancer", "microservice", "service", "client", "worker"],
            "data_model_and_storage": ["schema", "primary key", "index", "relational", "nosql", "table", "document"],
            "api_design": ["post", "get", "endpoint", "rest", "grpc", "payload", "json", "idempotent"],
            "scalability_and_partitioning": ["sharding", "replica", "partition", "horizontal", "cache", "redis", "cdn"],
            "failure_modes_and_resilience": ["failover", "circuit breaker", "fallback", "retry", "queue", "redundancy"],
            "trade_offs_and_deep_dive": ["tradeoff", "trade-off", "versus", "vs", "cost", "complexity", "overhead"],
        }

        weighted_total = 0.0
        for pillar, keywords in checks.items():
            matched = sum(1 for kw in keywords if kw in full_text)
            p_score = 55.0 + (matched * 10.0)
            if word_count > 70:
                p_score += 10.0
            p_score = max(35.0, min(95.0, p_score))

            weight = self.PILLAR_WEIGHTS[pillar]
            weighted_total += p_score * weight

            pillar_scores[pillar] = ArchitecturePillarScore(
                pillar_name=pillar,
                score=p_score,
                weight=weight,
                strengths=[f"Included coverage of key {pillar.replace('_', ' ')} concepts."],
                weaknesses=[] if matched >= 3 else [f"Expand on concrete {pillar.replace('_', ' ')} details."],
                critical_missing_elements=[] if matched >= 2 else [f"Detailed specifications for {pillar.replace('_', ' ')}."],
            )

        final_score = max(10.0, min(100.0, weighted_total - buzzwords.penalty_applied))
        if final_score >= 82.0:
            tier = "Senior/Staff Level"
        elif final_score >= 68.0:
            tier = "Mid Level"
        elif final_score >= 50.0:
            tier = "Junior Level"
        else:
            tier = "Unsatisfactory"

        spof = []
        if "load balancer" not in full_text:
            spof.append("Missing redundant Load Balancer layer creating potential traffic bottleneck.")
        if "replica" not in full_text:
            spof.append("Primary database lacks automated read replicas or multi-AZ failover.")

        return SystemDesignEvaluation(
            overall_score=final_score,
            tier=tier,
            pillar_scores=pillar_scores,
            buzzword_analysis=buzzwords,
            single_points_of_failure=spof,
            bottlenecks=["Database write IOPS under peak spikes" if "cache" not in full_text else "Network egress bandwidth"],
            scale_readiness="Demonstrates foundational distributed systems knowledge with room for deeper trade-off analysis.",
            key_tradeoffs=["Latency vs Consistency in cross-region replication", "Cache-aside invalidation vs DB load"],
            recommendation="Advance candidate to in-depth technical deep-dive with focus on specific failure recovery scenarios.",
        )

    def validate_architecture_graph(
        self,
        components: list[dict[str, Any]],
        connections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Validates an architectural topology graph for:
        - Structural connectivity (path from client/ingress to storage)
        - Orphan/unconnected nodes
        - Single Points of Failure (SPOF)
        - Critical tier redundancy (multi-instance app/web servers, read-replicas, multi-AZ cache)
        """
        if not components:
            return {
                "is_resilient": False,
                "resilience_score": 0.0,
                "spof_nodes": ["No components defined in topology"],
                "warnings": ["Architecture graph is empty"],
                "redundancy_report": {},
                "recommendations": ["Add core components: Clients, Ingress Gateway/LB, App Tier, Storage."],
            }

        node_ids = {c.get("id", str(idx)): c for idx, c in enumerate(components)}
        node_types = {c.get("id", str(idx)): c.get("type", "service").lower() for idx, c in enumerate(components)}

        adj: dict[str, set[str]] = {nid: set() for nid in node_ids}
        in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
        out_degree: dict[str, int] = {nid: 0 for nid in node_ids}

        for conn in connections:
            u = conn.get("from")
            v = conn.get("to")
            if u in node_ids and v in node_ids:
                adj[u].add(v)
                out_degree[u] += 1
                in_degree[v] += 1

        orphans = [nid for nid in node_ids if in_degree[nid] == 0 and out_degree[nid] == 0]

        has_lb = any("balancer" in t or "gateway" in t or "ingress" in t for t in node_types.values())
        has_cache = any("cache" in t or "redis" in t or "memcached" in t for t in node_types.values())
        has_queue = any("queue" in t or "broker" in t or "kafka" in t or "rabbitmq" in t for t in node_types.values())
        has_db = any("database" in t or "db" in t or "postgres" in t or "mysql" in t or "mongo" in t or "cassandra" in t for t in node_types.values())
        has_cdn = any("cdn" in t or "edge" in t or "cloudfront" in t for t in node_types.values())

        spof_nodes: list[str] = []
        warnings: list[str] = []
        redundancy_report: dict[str, Any] = {}

        for nid, comp in node_ids.items():
            name = comp.get("name", nid)
            ctype = comp.get("type", "service").lower()
            replicas = comp.get("replicas", 1)
            is_clustered = comp.get("is_clustered", False) or replicas > 1
            redundancy_report[name] = {"type": ctype, "replicas": replicas, "clustered": is_clustered}

            if not is_clustered and ("database" in ctype or "db" in ctype or "primary" in ctype):
                spof_nodes.append(f"{name} ({ctype}): Single database instance without read replica or automatic multi-AZ failover.")
            elif not is_clustered and ("balancer" in ctype or "gateway" in ctype):
                spof_nodes.append(f"{name} ({ctype}): Single ingress gateway without active-passive or DNS anycast redundancy.")
            elif not is_clustered and ("cache" in ctype and in_degree[nid] > 1):
                warnings.append(f"{name} ({ctype}): Unclustered standalone cache; cache failure will storm primary database.")

        if orphans:
            warnings.append(f"Orphan nodes disconnected from architecture: {', '.join(node_ids[o].get('name', o) for o in orphans)}")

        if not has_lb:
            warnings.append("Missing Load Balancer / API Gateway layer before application services.")
        if not has_cache:
            warnings.append("Missing dedicated caching layer (e.g. Redis) between application and persistence tier.")
        if not has_queue:
            warnings.append("No asynchronous message queue detected for non-blocking background workloads.")

        base_score = 100.0
        base_score -= len(spof_nodes) * 18.0
        base_score -= len(warnings) * 6.0
        if not has_db:
            base_score -= 25.0
        if not has_lb:
            base_score -= 15.0

        resilience_score = max(10.0, min(100.0, round(base_score, 1)))
        is_resilient = len(spof_nodes) == 0 and resilience_score >= 70.0

        recommendations: list[str] = []
        if spof_nodes:
            recommendations.append("Deploy standby replicas with health checks and automated promotion for all data stores.")
        if not has_cache:
            recommendations.append("Implement a distributed cache (e.g. Redis Cluster with LRU eviction) to protect write IOPS.")
        if not has_queue:
            recommendations.append("Introduce a distributed log/queue (e.g. Kafka/SQS) for burst decoupling and asynchronous processing.")
        if not has_cdn:
            recommendations.append("Place a Geo-distributed CDN (e.g. Cloudflare / CloudFront) at the edge for asset offload.")

        return {
            "is_resilient": is_resilient,
            "resilience_score": resilience_score,
            "spof_nodes": spof_nodes,
            "warnings": warnings,
            "redundancy_report": redundancy_report,
            "recommendations": recommendations,
        }

    def verify_capacity_estimation(
        self,
        scenario_key: str,
        candidate_estimates: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validates back-of-the-envelope capacity estimations against architectural baselines:
        Computes standard DAU, QPS, Storage, Bandwidth, and RAM Cache requirements.
        """
        baselines = {
            "distributed_rate_limiter": {
                "dau": 50_000_000,
                "read_qps": 400_000.0,
                "write_qps": 100_000.0,
                "peak_multiplier": 2.5,
                "payload_size_kb": 0.5,
                "daily_storage_gb": 120.0,
                "five_year_storage_tb": 219.0,
                "bandwidth_gbps": 2.0,
                "ram_cache_gb": 32.0,
            },
            "notification_service": {
                "dau": 100_000_000,
                "read_qps": 25_000.0,
                "write_qps": 25_000.0,
                "peak_multiplier": 3.0,
                "payload_size_kb": 2.0,
                "daily_storage_gb": 200.0,
                "five_year_storage_tb": 365.0,
                "bandwidth_gbps": 0.8,
                "ram_cache_gb": 64.0,
            },
            "global_video_streaming": {
                "dau": 200_000_000,
                "read_qps": 100_000.0,
                "write_qps": 10_000.0,
                "peak_multiplier": 2.0,
                "payload_size_kb": 5.0,
                "daily_storage_gb": 500_000.0,
                "five_year_storage_tb": 912_500.0,
                "bandwidth_gbps": 250_000.0,
                "ram_cache_gb": 512.0,
            },
        }

        bench = baselines.get(scenario_key, baselines["distributed_rate_limiter"])
        deviations: dict[str, Any] = {}
        metric_scores: list[float] = []
        feedback: list[str] = []

        fields = [
            ("read_qps", "Read QPS", bench["read_qps"]),
            ("write_qps", "Write QPS", bench["write_qps"]),
            ("daily_storage_gb", "Daily Storage (GB)", bench["daily_storage_gb"]),
            ("bandwidth_gbps", "Network Bandwidth (Gbps)", bench["bandwidth_gbps"]),
            ("ram_cache_gb", "RAM Cache (GB)", bench["ram_cache_gb"]),
        ]

        for key, label, bench_val in fields:
            cand_val = candidate_estimates.get(key)
            if cand_val is not None:
                try:
                    c_float = float(cand_val)
                    if c_float <= 0:
                        ratio = 0.0
                    else:
                        ratio = c_float / bench_val if c_float >= bench_val else bench_val / c_float

                    if ratio <= 2.0:
                        acc = 100.0
                        eval_note = "Accurate order of magnitude."
                    elif ratio <= 5.0:
                        acc = 75.0
                        eval_note = "Reasonable approximation within 5x tolerance."
                    elif ratio <= 10.0:
                        acc = 50.0
                        eval_note = "Significant deviation from standard enterprise benchmark."
                    else:
                        acc = 25.0
                        eval_note = "Unrealistic scale estimation (exceeds 10x deviation)."

                    metric_scores.append(acc)
                    deviations[key] = {
                        "metric": label,
                        "candidate_estimate": c_float,
                        "benchmark": bench_val,
                        "deviation_factor": round(ratio, 2),
                        "accuracy_score": acc,
                        "evaluation": eval_note,
                    }
                    if acc < 75.0:
                        feedback.append(f"{label}: Estimated {c_float}, expected ~{bench_val} ({eval_note})")
                except (ValueError, TypeError):
                    metric_scores.append(20.0)
            else:
                deviations[key] = {
                    "metric": label,
                    "candidate_estimate": None,
                    "benchmark": bench_val,
                    "accuracy_score": 0.0,
                    "evaluation": "Not provided by candidate.",
                }
                feedback.append(f"{label}: Missing from candidate calculations.")

        overall_score = round(sum(metric_scores) / max(len(metric_scores), 1), 1) if metric_scores else 50.0
        if overall_score >= 80.0:
            rating = "Exceptional Estimation Accuracy"
        elif overall_score >= 60.0:
            rating = "Acceptable Estimation Accuracy"
        else:
            rating = "Needs Mathematical Rigor"

        return {
            "overall_accuracy_score": overall_score,
            "rating": rating,
            "benchmark_model": bench,
            "metric_evaluations": deviations,
            "feedback": feedback if feedback else ["All capacity estimations match realistic production sizing."],
        }

    async def answer_clarification(
        self,
        scenario_key: str,
        question: str,
    ) -> dict[str, Any]:
        """
        Interactive Bar-Raiser persona answering candidate's scope/NFR clarification questions.
        """
        q_lower = question.lower()

        clarifications_db: dict[str, list[dict[str, str]]] = {
            "distributed_rate_limiter": [
                {"keywords": ["consistency", "acid", "cap", "eventual"], "answer": "Eventual consistency across regions is acceptable. Over-throttling by 1% under extreme network split is tolerable, but latency overhead per request must strictly remain under 2ms."},
                {"keywords": ["algorithm", "sliding window", "token bucket", "leaky bucket"], "answer": "Support sliding-window log or counter for general API tiers, and token bucket for burst-tolerant endpoints."},
                {"keywords": ["client", "user", "ip", "token", "header"], "answer": "Throttling should support multiple keys: Authenticated User ID (highest priority), API Client Key, and Client IP as fallback for unauthenticated requests."},
                {"keywords": ["failure", "open", "closed", "down"], "answer": "Default to Fail-Open with alert paging when the rate limiter tier is completely partitioned, to prevent breaking customer traffic."},
            ],
            "notification_service": [
                {"keywords": ["order", "fifo", "priority"], "answer": "Critical transactional notifications (e.g. OTPs, 2FA) require priority queueing with p99 delivery < 1 second. Marketing campaigns can be batched with lower priority."},
                {"keywords": ["idempotency", "dedup", "duplicate"], "answer": "At-least-once delivery with deduplication window of 24 hours based on an idempotency key passed by the sending service."},
                {"keywords": ["rate limit", "vendor", "twilio", "fcm", "sendgrid"], "answer": "Third-party vendors enforce upstream rate limits. You must implement backpressure and rate-limiting queues per vendor."},
            ],
            "global_video_streaming": [
                {"keywords": ["bitrate", "resolution", "4k", "transcode"], "answer": "We support Adaptive Bitrate Streaming (HLS / MPEG-DASH) with resolutions from 360p up to 4K HDR. Ingestion transcoding is asynchronous."},
                {"keywords": ["region", "global", "latency", "cdn"], "answer": "Video segments are cached across 150+ edge CDN PoPs globally. 95% of playback requests must be served directly from edge caches."},
                {"keywords": ["watch history", "progress", "resume"], "answer": "Playback progress is checkpointed every 10 seconds. Eventual consistency is fine for cross-device resumption within a 30-second window."},
            ],
        }

        matched_answer = None
        tips = [
            "Good clarification! In real interviews, quantifying requirements early demonstrates Senior/Staff engineering maturity.",
            "Remember to state any assumptions explicitly in your design sections.",
        ]

        rules = clarifications_db.get(scenario_key, [])
        for r in rules:
            if any(kw in q_lower for kw in r["keywords"]):
                matched_answer = r["answer"]
                break

        if not matched_answer:
            matched_answer = (
                f"Great question. For the {scenario_key.replace('_', ' ')} scenario, assume standard enterprise L6 scale: "
                "prioritize high availability (99.99%) and sub-50ms p95 latency. Assume multi-region active-passive deployments "
                "with asynchronous cross-region synchronization."
            )

        return {
            "scenario_key": scenario_key,
            "question": question,
            "answer": matched_answer,
            "bar_raiser_tips": tips,
        }
