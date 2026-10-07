from __future__ import annotations

import collections
from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_graph import CandidateSkillMastery, CustomSkillNode, SkillRelationType

log = structlog.get_logger(__name__)


@dataclass
class SkillNodeData:
    id: str
    name: str
    category: str
    tier: int  # 1 (Fundamentals) to 5 (Staff/Principal Mastery)
    description: str
    prerequisites: list[str] = field(default_factory=list)
    specializations: list[str] = field(default_factory=list)
    complements: list[str] = field(default_factory=list)
    equivalents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "tier": self.tier,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "specializations": self.specializations,
            "complements": self.complements,
            "equivalents": self.equivalents,
        }


# Canonical Enterprise Software Engineering & Architecture Skill DAG
CANONICAL_SKILL_NODES: dict[str, SkillNodeData] = {
    # ── Tier 1: Foundations ───────────────────────────────────────────────────
    "cs_fundamentals": SkillNodeData(
        id="cs_fundamentals",
        name="Computer Science Fundamentals",
        category="Foundations",
        tier=1,
        description="Boolean logic, memory representation, binary arithmetic, and algorithmic complexity (Big-O).",
    ),
    "programming_basics": SkillNodeData(
        id="programming_basics",
        name="Structured Programming & Control Flow",
        category="Foundations",
        tier=1,
        description="Variables, scoping, loops, recursion, functions, and error handling paradigms.",
        prerequisites=["cs_fundamentals"],
    ),
    "git_version_control": SkillNodeData(
        id="git_version_control",
        name="Git & Version Control Systems",
        category="Tools & Collaboration",
        tier=1,
        description="Branching strategies, rebase, merge conflicts, Git internals (DAG of commits, tree/blob objects).",
        prerequisites=["programming_basics"],
    ),

    # ── Tier 2: Core Data Structures & Systems ────────────────────────────────
    "data_structures_core": SkillNodeData(
        id="data_structures_core",
        name="Core Data Structures",
        category="Algorithms & Data Structures",
        tier=2,
        description="Arrays, Linked Lists, Stacks, Queues, Hash Tables, and Collision Resolution strategies.",
        prerequisites=["programming_basics"],
    ),
    "networking_tcp_ip": SkillNodeData(
        id="networking_tcp_ip",
        name="Networking (TCP/IP & Sockets)",
        category="Networking & Protocols",
        tier=2,
        description="TCP 3-way handshake, flow control, congestion window, UDP vs TCP, and OSI socket programming.",
        prerequisites=["cs_fundamentals"],
    ),
    "relational_sql": SkillNodeData(
        id="relational_sql",
        name="Relational Databases & SQL",
        category="Storage & Databases",
        tier=2,
        description="Schema modeling, normalization, foreign keys, SQL joins, aggregations, and query plans.",
        prerequisites=["programming_basics"],
    ),
    "os_fundamentals": SkillNodeData(
        id="os_fundamentals",
        name="Operating Systems & Processes",
        category="Operating Systems & Concurrency",
        tier=2,
        description="Virtual memory, paging, CPU scheduling, processes, threads, context switching, and system calls.",
        prerequisites=["cs_fundamentals"],
    ),

    # ── Tier 3: Intermediate Architecture & Applied Systems ───────────────────
    "trees_and_graphs": SkillNodeData(
        id="trees_and_graphs",
        name="Trees, Heaps & Graph Traversal",
        category="Algorithms & Data Structures",
        tier=3,
        description="Binary Search Trees, Tries, Priority Queues, BFS, DFS, Dijkstra, and Topological Sort.",
        prerequisites=["data_structures_core"],
    ),
    "multithreading_concurrency": SkillNodeData(
        id="multithreading_concurrency",
        name="Multithreading & Concurrency",
        category="Operating Systems & Concurrency",
        tier=3,
        description="Thread pools, race conditions, deadlocks, critical sections, and event loops.",
        prerequisites=["os_fundamentals"],
        complements=["networking_tcp_ip"],
    ),
    "http_rest_protocols": SkillNodeData(
        id="http_rest_protocols",
        name="HTTP/2, REST & Web Protocols",
        category="Networking & Protocols",
        tier=3,
        description="RESTful contracts, status codes, HTTP/1.1 keep-alive vs HTTP/2 multiplexing, CORS, and TLS.",
        prerequisites=["networking_tcp_ip"],
        complements=["relational_sql"],
    ),
    "indexing_b_trees": SkillNodeData(
        id="indexing_b_trees",
        name="Database Indexing (B+ Trees)",
        category="Storage & Databases",
        tier=3,
        description="B+ Tree structure, clustered vs non-clustered indexes, composite indexes, and index selectivity.",
        prerequisites=["relational_sql", "data_structures_core"],
    ),
    "containerization_docker": SkillNodeData(
        id="containerization_docker",
        name="Containerization (Docker & OCI)",
        category="Cloud & Infrastructure",
        tier=3,
        description="Linux cgroups, namespaces, image layering, multi-stage builds, and container networking.",
        prerequisites=["os_fundamentals"],
    ),
    "distributed_systems_basics": SkillNodeData(
        id="distributed_systems_basics",
        name="Distributed Systems Fundamentals",
        category="Distributed Systems",
        tier=3,
        description="RPC paradigms, clock drift, failure models, network partitions, and fallacies of distributed computing.",
        prerequisites=["networking_tcp_ip", "multithreading_concurrency"],
    ),

    # ── Tier 4: Advanced Distributed Systems & Infrastructure ────────────────
    "locks_and_atomics": SkillNodeData(
        id="locks_and_atomics",
        name="Lock-Free & Atomic Primitives",
        category="Operating Systems & Concurrency",
        tier=4,
        description="Compare-And-Swap (CAS), memory barriers, volatile memory semantics, spinlocks, and reentrant locks.",
        prerequisites=["multithreading_concurrency"],
    ),
    "transaction_isolation_acid": SkillNodeData(
        id="transaction_isolation_acid",
        name="ACID & Transaction Isolation Levels",
        category="Storage & Databases",
        tier=4,
        description="Read Committed, Repeatable Read, Serializable, MVCC, write skew, and phantom reads.",
        prerequisites=["indexing_b_trees"],
    ),
    "consistent_hashing": SkillNodeData(
        id="consistent_hashing",
        name="Consistent Hashing & Ring Partitioning",
        category="Distributed Systems",
        tier=4,
        description="Virtual nodes, hash rings, load skew prevention, and partition rebalancing during node churn.",
        prerequisites=["distributed_systems_basics", "data_structures_core"],
    ),
    "cap_pacelc_theorems": SkillNodeData(
        id="cap_pacelc_theorems",
        name="CAP & PACELC Trade-offs",
        category="Distributed Systems",
        tier=4,
        description="Consistency vs Availability under partitions, and Latency vs Consistency in normal operation.",
        prerequisites=["distributed_systems_basics"],
    ),
    "event_driven_messaging": SkillNodeData(
        id="event_driven_messaging",
        name="Event-Driven Messaging & Streaming (Kafka)",
        category="Distributed Systems",
        tier=4,
        description="Append-only commit logs, partition keys, consumer groups, offset management, and backpressure.",
        prerequisites=["distributed_systems_basics", "http_rest_protocols"],
        complements=["consistent_hashing"],
    ),
    "grpc_protobuf": SkillNodeData(
        id="grpc_protobuf",
        name="gRPC & Binary Protocol Buffers",
        category="Networking & Protocols",
        tier=4,
        description="IDL schema contracts, binary wire format, client/server streaming, and HTTP/2 transport.",
        prerequisites=["http_rest_protocols"],
    ),
    "kubernetes_orchestration": SkillNodeData(
        id="kubernetes_orchestration",
        name="Kubernetes & Container Orchestration",
        category="Cloud & Infrastructure",
        tier=4,
        description="Pods, Deployments, ReplicaSets, Services, Ingress, HPA autoscaling, and stateful sets.",
        prerequisites=["containerization_docker", "networking_tcp_ip"],
    ),
    "vector_databases_hnsw": SkillNodeData(
        id="vector_databases_hnsw",
        name="Vector Databases & HNSW Indexing",
        category="AI & Data Infrastructure",
        tier=4,
        description="High-dimensional embeddings, Cosine/Euclidean distance, HNSW graphs, and ANN recall tuning.",
        prerequisites=["trees_and_graphs", "indexing_b_trees"],
    ),

    # ── Tier 5: Staff & Principal Architecture ────────────────────────────────
    "raft_paxos_consensus": SkillNodeData(
        id="raft_paxos_consensus",
        name="Distributed Consensus (Raft / Paxos)",
        category="Distributed Systems",
        tier=5,
        description="Leader election, quorum majorities, log replication, split-brain resolution, and term transitions.",
        prerequisites=["cap_pacelc_theorems", "locks_and_atomics"],
    ),
    "distributed_transactions_2pc": SkillNodeData(
        id="distributed_transactions_2pc",
        name="Distributed Transactions (2PC & Saga)",
        category="Distributed Systems",
        tier=5,
        description="Two-Phase Commit coordinator failures, blocking nature, Saga orchestration vs choreography, and compensating transactions.",
        prerequisites=["transaction_isolation_acid", "cap_pacelc_theorems"],
    ),
    "lsm_trees_storage": SkillNodeData(
        id="lsm_trees_storage",
        name="LSM-Trees & Write-Heavy Storage Engines",
        category="Storage & Databases",
        tier=5,
        description="MemTable, Write-Ahead Log (WAL), SSTables, Compaction algorithms (Size-Tiered/Leveled), and Bloom filters.",
        prerequisites=["indexing_b_trees", "os_fundamentals"],
    ),
    "event_sourcing_cqrs": SkillNodeData(
        id="event_sourcing_cqrs",
        name="Event Sourcing & CQRS Architecture",
        category="Distributed Systems",
        tier=5,
        description="Command Query Responsibility Segregation, read projections, event streams, schema evolution, and snapshots.",
        prerequisites=["event_driven_messaging", "distributed_transactions_2pc"],
    ),
    "service_mesh_envoy": SkillNodeData(
        id="service_mesh_envoy",
        name="Service Mesh & Zero-Trust Traffic (Envoy)",
        category="Cloud & Infrastructure",
        tier=5,
        description="Sidecar proxy injection, mTLS, circuit breaking at edge, distributed tracing, and traffic shadowing.",
        prerequisites=["kubernetes_orchestration", "grpc_protobuf"],
    ),
}

# Standard Role Archetype Subgraphs
ROLE_ARCHETYPES: dict[str, dict[str, Any]] = {
    "senior_backend_l5": {
        "title": "Senior Backend Engineer (L5)",
        "department": "Core Engineering",
        "description": "Expert in API design, database modeling, concurrency, caching, and resilient service communication.",
        "target_skills": [
            "data_structures_core",
            "relational_sql",
            "indexing_b_trees",
            "transaction_isolation_acid",
            "multithreading_concurrency",
            "http_rest_protocols",
            "grpc_protobuf",
            "distributed_systems_basics",
            "consistent_hashing",
            "containerization_docker",
        ],
        "passing_threshold": 75.0,
    },
    "staff_distributed_architect_l6": {
        "title": "Principal Distributed Systems Architect (L6)",
        "department": "Platform & Infrastructure",
        "description": "Mastery of distributed consensus, fault-tolerant persistence, cross-region replication, and microservice decoupling.",
        "target_skills": [
            "distributed_systems_basics",
            "cap_pacelc_theorems",
            "consistent_hashing",
            "event_driven_messaging",
            "transaction_isolation_acid",
            "distributed_transactions_2pc",
            "raft_paxos_consensus",
            "lsm_trees_storage",
            "event_sourcing_cqrs",
            "service_mesh_envoy",
        ],
        "passing_threshold": 80.0,
    },
    "data_ai_platform_engineer": {
        "title": "AI & Data Platform Engineer (L5)",
        "department": "AI Foundations",
        "description": "Architects high-throughput event streaming, vector retrieval infrastructure, and distributed data pipelines.",
        "target_skills": [
            "data_structures_core",
            "trees_and_graphs",
            "relational_sql",
            "indexing_b_trees",
            "event_driven_messaging",
            "vector_databases_hnsw",
            "containerization_docker",
            "kubernetes_orchestration",
        ],
        "passing_threshold": 75.0,
    },
}


class SkillGraphService:
    """
    High-Performance Directed Acyclic Graph (DAG) Engine for:
    - Topological prerequisite sorting
    - Cycle detection & DAG invariant enforcement
    - Root-cause prerequisite gap traversal
    - Transitive skill mastery credit propagation
    - Role archetype alignment & graph distance calculations
    """

    def __init__(self, db: AsyncSession | None = None) -> None:
        self._db = db
        self._nodes = dict(CANONICAL_SKILL_NODES)
        self.verify_acyclic()

    def get_all_nodes(self) -> list[SkillNodeData]:
        """Returns all skill nodes in the canonical DAG."""
        return list(self._nodes.values())

    def get_node(self, skill_id: str) -> SkillNodeData | None:
        """Returns specific skill node details."""
        return self._nodes.get(skill_id)

    def verify_acyclic(self) -> None:
        """
        Validates the DAG invariant using 3-color cycle detection (0: White, 1: Gray, 2: Black).
        Raises ValueError if a cyclic prerequisite dependency exists.
        """
        visited: dict[str, int] = {k: 0 for k in self._nodes}

        def dfs(node_id: str, path: list[str]) -> None:
            visited[node_id] = 1  # In progress (Gray)
            node = self._nodes.get(node_id)
            if node:
                for prereq in node.prerequisites:
                    if prereq not in self._nodes:
                        continue
                    if visited[prereq] == 1:
                        cycle_path = " -> ".join(path + [prereq])
                        raise ValueError(f"Cycle detected in Skill DAG: {cycle_path}")
                    if visited[prereq] == 0:
                        dfs(prereq, path + [prereq])
            visited[node_id] = 2  # Completed (Black)

        for node_id in self._nodes:
            if visited[node_id] == 0:
                dfs(node_id, [node_id])

    def topological_sort(self, skill_subset: list[str] | None = None) -> list[str]:
        """
        Kahn's algorithm: Produces a strictly valid linear ordering of skills such that
        for every directed prerequisite edge (u -> v), u appears before v.
        """
        target_set = set(skill_subset) if skill_subset else set(self._nodes.keys())
        
        # Build in-degree map for target set
        in_degree: dict[str, int] = {s: 0 for s in target_set}
        adj: dict[str, list[str]] = collections.defaultdict(list)

        for sid in target_set:
            node = self._nodes.get(sid)
            if not node:
                continue
            for prereq in node.prerequisites:
                if prereq in target_set:
                    adj[prereq].append(sid)
                    in_degree[sid] += 1

        queue = collections.deque([s for s in target_set if in_degree[s] == 0])
        ordered: list[str] = []

        while queue:
            curr = queue.popleft()
            ordered.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(target_set):
            raise ValueError("Topological sort failed due to unreachable or cyclic nodes.")

        return ordered

    def get_prerequisite_closure(self, skill_id: str) -> set[str]:
        """Computes all transitive ancestors (prerequisites) required for a skill."""
        ancestors: set[str] = set()
        queue = collections.deque([skill_id])

        while queue:
            curr = queue.popleft()
            node = self._nodes.get(curr)
            if node:
                for prereq in node.prerequisites:
                    if prereq not in ancestors:
                        ancestors.add(prereq)
                        queue.append(prereq)

        return ancestors

    def analyze_root_cause_gaps(
        self,
        candidate_mastery: dict[str, float],
        failed_skills: list[str],
        passing_threshold: float = 65.0,
    ) -> dict[str, Any]:
        """
        When a candidate fails questions on complex skills (e.g. Raft Consensus),
        this algorithm traverses backwards along prerequisite edges to identify the
        earliest/lowest-tier unmastered root ancestor that caused the downstream failure.
        """
        root_causes: list[dict[str, Any]] = []
        full_gap_set: set[str] = set()

        for failed in failed_skills:
            if failed not in self._nodes:
                continue

            prereqs = self.get_prerequisite_closure(failed)
            # Find all prerequisites where candidate score is below threshold or absent
            unmastered_prereqs = [
                p for p in prereqs
                if candidate_mastery.get(p, 0.0) < passing_threshold
            ]

            full_gap_set.update(unmastered_prereqs)
            full_gap_set.add(failed)

            if unmastered_prereqs:
                # Topologically sort unmastered prerequisites to identify the root foundational gap
                sorted_unmastered = self.topological_sort(unmastered_prereqs)
                root_node_id = sorted_unmastered[0]
                root_node = self._nodes[root_node_id]
                root_causes.append({
                    "failed_skill": failed,
                    "failed_skill_name": self._nodes[failed].name,
                    "root_cause_skill_id": root_node_id,
                    "root_cause_skill_name": root_node.name,
                    "root_cause_tier": root_node.tier,
                    "candidate_score": candidate_mastery.get(root_node_id, 0.0),
                    "diagnosis": (
                        f"Candidate failed '{self._nodes[failed].name}' primarily because foundational prerequisite "
                        f"'{root_node.name}' (Tier {root_node.tier}) is unmastered ({candidate_mastery.get(root_node_id, 0.0):.1f}%)."
                    ),
                    "remedy_sequence": [self._nodes[s].name for s in sorted_unmastered],
                })
            else:
                root_causes.append({
                    "failed_skill": failed,
                    "failed_skill_name": self._nodes[failed].name,
                    "root_cause_skill_id": failed,
                    "root_cause_skill_name": self._nodes[failed].name,
                    "root_cause_tier": self._nodes[failed].tier,
                    "candidate_score": candidate_mastery.get(failed, 0.0),
                    "diagnosis": f"Foundational prerequisites are intact. Failure is isolated directly to '{self._nodes[failed].name}'.",
                    "remedy_sequence": [self._nodes[failed].name],
                })

        return {
            "total_failed_skills": len(failed_skills),
            "root_causes": root_causes,
            "all_unmastered_skills": list(full_gap_set),
            "remediation_roadmap": self.topological_sort(list(full_gap_set)) if full_gap_set else [],
        }

    def propagate_transitive_credit(
        self,
        demonstrated_skills: dict[str, float],
        decay_factor: float = 0.85,
    ) -> dict[str, dict[str, Any]]:
        """
        Transitive Credit Propagation:
        If a candidate proves mastery of an advanced Tier-4 or Tier-5 skill (e.g. Raft Consensus = 90%),
        the DAG automatically infers and awards baseline credit to its prerequisite ancestors,
        decayed by distance: Score_infer = Demonstrated_Score * (decay_factor ^ distance).
        """
        mastery_results: dict[str, dict[str, Any]] = {}

        # 1. Seed direct scores
        for sid, score in demonstrated_skills.items():
            if sid in self._nodes:
                mastery_results[sid] = {
                    "score": round(score, 1),
                    "confidence": 1.0,
                    "is_inferred": False,
                    "source": "direct_assessment",
                    "tier": self._nodes[sid].tier,
                }

        # 2. Traverse backwards from highest tier to lowest tier
        sorted_by_tier = sorted(
            demonstrated_skills.keys(),
            key=lambda k: self._nodes[k].tier if k in self._nodes else 0,
            reverse=True,
        )

        for high_skill in sorted_by_tier:
            if high_skill not in self._nodes:
                continue
            base_score = demonstrated_skills[high_skill]

            # Breadth-first search along prerequisite edges with distance tracking
            queue: collections.deque[tuple[str, int]] = collections.deque([(high_skill, 0)])
            visited_bfs: set[str] = {high_skill}

            while queue:
                curr_sid, dist = queue.popleft()
                node = self._nodes.get(curr_sid)
                if not node:
                    continue

                for prereq in node.prerequisites:
                    if prereq not in self._nodes:
                        continue
                    new_dist = dist + 1
                    inferred_score = round(base_score * (decay_factor ** new_dist), 1)
                    inferred_conf = round(max(0.5, 0.95 - (new_dist * 0.1)), 2)

                    # Update if not present or if newly inferred score is higher
                    if prereq not in mastery_results:
                        mastery_results[prereq] = {
                            "score": inferred_score,
                            "confidence": inferred_conf,
                            "is_inferred": True,
                            "source": f"inferred_from_{high_skill}",
                            "tier": self._nodes[prereq].tier,
                        }
                    elif mastery_results[prereq]["is_inferred"]:
                        if inferred_score > mastery_results[prereq]["score"]:
                            mastery_results[prereq]["score"] = inferred_score
                            mastery_results[prereq]["source"] = f"inferred_from_{high_skill}"

                    if prereq not in visited_bfs:
                        visited_bfs.add(prereq)
                        queue.append((prereq, new_dist))

        return mastery_results

    def evaluate_role_alignment(
        self,
        candidate_mastery: dict[str, float],
        role_key: str = "senior_backend_l5",
    ) -> dict[str, Any]:
        """
        Evaluates candidate's skill DAG profile against standard enterprise role archetypes.
        Calculates graph coverage, readiness score, and critical path gaps.
        """
        role = ROLE_ARCHETYPES.get(role_key, ROLE_ARCHETYPES["senior_backend_l5"])
        target_skills: list[str] = role["target_skills"]
        pass_threshold: float = role["passing_threshold"]

        verified_skills: list[dict[str, Any]] = []
        missing_skills: list[dict[str, Any]] = []
        total_score_sum = 0.0

        for sid in target_skills:
            node = self._nodes.get(sid)
            if not node:
                continue
            cand_score = candidate_mastery.get(sid, 0.0)
            total_score_sum += cand_score

            if cand_score >= pass_threshold:
                verified_skills.append({
                    "skill_id": sid,
                    "name": node.name,
                    "tier": node.tier,
                    "score": cand_score,
                })
            else:
                missing_skills.append({
                    "skill_id": sid,
                    "name": node.name,
                    "tier": node.tier,
                    "score": cand_score,
                    "delta_needed": round(pass_threshold - cand_score, 1),
                })

        coverage_pct = round((len(verified_skills) / max(len(target_skills), 1)) * 100, 1)
        composite_readiness = round(total_score_sum / max(len(target_skills), 1), 1)

        # Build prioritized learning sequence to bridge gaps
        missing_ids = [m["skill_id"] for m in missing_skills]
        remediation_path = self.topological_sort(missing_ids) if missing_ids else []

        verdict = (
            "Ready for Role" if coverage_pct >= 85.0 and composite_readiness >= pass_threshold
            else "Progressing Toward Role" if coverage_pct >= 50.0
            else "Foundational Gaps Identified"
        )

        return {
            "role_key": role_key,
            "role_title": role["title"],
            "department": role["department"],
            "coverage_percentage": coverage_pct,
            "composite_readiness": composite_readiness,
            "role_passing_threshold": pass_threshold,
            "verdict": verdict,
            "verified_skills_count": len(verified_skills),
            "missing_skills_count": len(missing_skills),
            "verified_skills": verified_skills,
            "missing_skills": missing_skills,
            "prioritized_learning_sequence": [self._nodes[s].name for s in remediation_path],
        }

    def generate_learning_pathway(
        self,
        candidate_mastery: dict[str, float],
        target_skill_id: str,
    ) -> dict[str, Any]:
        """
        Generates a topological milestone curriculum to take candidate from their current state
        to verified mastery of the target skill.
        """
        if target_skill_id not in self._nodes:
            raise ValueError(f"Skill '{target_skill_id}' not found in taxonomy.")

        all_prereqs = self.get_prerequisite_closure(target_skill_id)
        all_prereqs.add(target_skill_id)

        # Filter to only skills the candidate has not yet mastered
        unmastered = [s for s in all_prereqs if candidate_mastery.get(s, 0.0) < 70.0]
        ordered_steps = self.topological_sort(unmastered)

        milestones = []
        for idx, sid in enumerate(ordered_steps, 1):
            node = self._nodes[sid]
            milestones.append({
                "step": idx,
                "skill_id": sid,
                "name": node.name,
                "tier": node.tier,
                "category": node.category,
                "current_score": candidate_mastery.get(sid, 0.0),
                "target_score": 85.0,
                "estimated_study_hours": node.tier * 4,
                "concept_summary": node.description,
            })

        return {
            "target_skill_id": target_skill_id,
            "target_skill_name": self._nodes[target_skill_id].name,
            "total_milestones": len(milestones),
            "estimated_total_hours": sum(m["estimated_study_hours"] for m in milestones),
            "curriculum": milestones,
        }
