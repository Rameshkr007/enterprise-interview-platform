from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_graph import CandidateSkillMastery
from app.models.sm2_card import SpacedRepetitionCard
from app.services.skill_graph_service import CANONICAL_SKILL_NODES

log = structlog.get_logger(__name__)


# ── CANONICAL INTERVIEW FLASHCARD CATALOG (LINKED TO SKILL DAG) ───────────────
CANONICAL_FLASHCARDS: list[dict[str, Any]] = [
    # Tier 1
    {
        "skill_id": "cs_fundamentals",
        "concept_key": "big_o_amortized_analysis",
        "title": "Amortized Complexity vs Worst-Case",
        "question_prompt": "What is the amortized time complexity of dynamic array append, and why does geometric resizing guarantee this bound?",
        "answer_explanation": "Dynamic arrays double capacity when full (geometric resizing factor 2). While resizing copies N elements taking O(N) worst-case time, this copy is amortized across N preceding O(1) appends. Summing the geometric series yields 2N operations across N appends, proving strictly O(1) amortized cost.",
        "key_takeaway": "Geometric resizing yields O(1) amortized; arithmetic (+K) resizing degrades to O(N) amortized.",
        "category": "Foundations",
        "tier": 1,
    },
    {
        "skill_id": "git_version_control",
        "concept_key": "git_dag_rebase_vs_merge",
        "title": "Git Rebase vs Merge Commit Topologies",
        "question_prompt": "How do Git Rebase and Git Merge alter the Directed Acyclic Graph (DAG) of commit objects?",
        "answer_explanation": "Merge creates a 2-parent merge commit preserving true chronological history without rewriting commit SHAs. Rebase rewrites commit history by transplanting branch commits one-by-one onto the tip of the target branch with new commit SHAs, producing a strictly linear commit history without diamond branches.",
        "key_takeaway": "Merge preserves original commit SHAs and topology; Rebase rewrites commit SHAs for linear history.",
        "category": "Tools & Collaboration",
        "tier": 1,
    },
    # Tier 2
    {
        "skill_id": "data_structures_core",
        "concept_key": "hash_collision_probing_strategies",
        "title": "Separate Chaining vs Open Addressing",
        "question_prompt": "Compare cache locality and degradation behavior between Open Addressing (Linear/Quadratic Probing) and Separate Chaining.",
        "answer_explanation": "Open Addressing stores all key-values in contiguous table memory, maximizing CPU L1/L2 cache locality, but suffers from primary clustering and degrades sharply past load factor 0.7. Separate Chaining uses linked node buckets, tolerating load factors > 1.0, but incurs pointer overhead and cache misses.",
        "key_takeaway": "Open addressing optimizes cache locality up to α=0.7; Chaining tolerates high load factors with pointer overhead.",
        "category": "Algorithms & Data Structures",
        "tier": 2,
    },
    {
        "skill_id": "networking_tcp_ip",
        "concept_key": "tcp_time_wait_state_lifecycle",
        "title": "TCP TIME_WAIT State Purpose & 2MSL",
        "question_prompt": "Why does the active-closer socket stay in TIME_WAIT for 2MSL (Maximum Segment Lifetime)?",
        "answer_explanation": "TIME_WAIT lasts 2MSL (typically 60-120 seconds) to: (1) reliably retransmit the final ACK if the passive closer retransmits FIN, ensuring clean connection teardown, and (2) allow delayed duplicate packets from the connection to dissipate before their 4-tuple (srcIP, srcPort, dstIP, dstPort) can be reused.",
        "key_takeaway": "TIME_WAIT ensures delivery of the final ACK and prevents old duplicate segments from corrupting new connections.",
        "category": "Networking & Protocols",
        "tier": 2,
    },
    {
        "skill_id": "os_fundamentals",
        "concept_key": "virtual_memory_tlb_page_fault",
        "title": "TLB Miss vs Page Fault Execution Mechanics",
        "question_prompt": "What is the hardware and OS difference between a TLB Miss and a Page Fault?",
        "answer_explanation": "A TLB miss occurs in hardware (MMU) when the page table cache lacks the virtual-to-physical translation, requiring a hardware page-table walk. A Page Fault occurs when the valid bit in the page table entry is 0 (page not in physical RAM), triggering an OS hardware interrupt to load the page from disk/swap into RAM.",
        "key_takeaway": "TLB miss is hardware memory walk (nanoseconds); Page fault is OS kernel disk I/O interrupt (milliseconds).",
        "category": "Operating Systems & Concurrency",
        "tier": 2,
    },
    # Tier 3
    {
        "skill_id": "indexing_b_trees",
        "concept_key": "b_plus_tree_leaf_linked_list",
        "title": "B+ Tree vs B-Tree for Relational Indexes",
        "question_prompt": "Why do relational database engines (PostgreSQL, InnoDB) use B+ Trees rather than standard B-Trees?",
        "answer_explanation": "In B+ Trees, internal nodes store only routing keys, allowing much higher fan-out (larger branching factor per 8KB page) and shallower tree depth (3-4 levels for billions of rows). All payload data is stored exclusively in leaf nodes linked via doubly linked lists, enabling sequential O(log N + K) range scans without tree re-traversals.",
        "key_takeaway": "B+ Tree guarantees high fan-out (shallow tree) and bidirectional linked leaf nodes for range scans.",
        "category": "Storage & Databases",
        "tier": 3,
    },
    {
        "skill_id": "multithreading_concurrency",
        "concept_key": "deadlock_coffman_conditions",
        "title": "The 4 Coffman Deadlock Conditions",
        "question_prompt": "List the four Coffman conditions necessary for deadlock to occur and how lock ordering breaks them.",
        "answer_explanation": "The 4 conditions are: (1) Mutual Exclusion, (2) Hold and Wait, (3) No Preemption, and (4) Circular Wait. Enforcing a global lock acquisition order breaks Circular Wait, guaranteeing cycles cannot form in the resource allocation graph.",
        "key_takeaway": "Deadlock requires Mutual Exclusion, Hold & Wait, No Preemption, and Circular Wait. Strict ordering eliminates Circular Wait.",
        "category": "Operating Systems & Concurrency",
        "tier": 3,
    },
    {
        "skill_id": "http_rest_protocols",
        "concept_key": "http2_multiplexing_hol_blocking",
        "title": "HTTP/2 Multiplexing vs TCP Head-of-Line Blocking",
        "question_prompt": "How does HTTP/2 solve application Head-of-Line (HoL) blocking, and why does TCP HoL blocking still persist?",
        "answer_explanation": "HTTP/2 introduces binary framing and multiplexed bidirectional streams over a single TCP connection, eliminating application-level request serialization. However, because TCP enforces strict byte-stream delivery, a single dropped packet in the IP layer stalls all multiplexed HTTP/2 streams until retransmitted (solved by HTTP/3 / QUIC over UDP).",
        "key_takeaway": "HTTP/2 solves stream interleaving over one connection; QUIC / HTTP/3 over UDP solves transport-level TCP HoL blocking.",
        "category": "Networking & Protocols",
        "tier": 3,
    },
    # Tier 4
    {
        "skill_id": "locks_and_atomics",
        "concept_key": "cas_aba_problem_resolution",
        "title": "Compare-And-Swap (CAS) & The ABA Problem",
        "question_prompt": "Describe the ABA problem in lock-free concurrent data structures and how version stamping prevents it.",
        "answer_explanation": "A thread reads memory value A. Before it performs CAS(A, new), another thread modifies A to B and back to A. The first thread's CAS succeeds thinking nothing changed, though intermediate state was modified. Solution: Version tags or generation counters (e.g., AtomicStampedReference in Java or double-word CAS) incrementing a monotonic counter on each mutation.",
        "key_takeaway": "ABA is solved by pairing values with monotonic generation counters (Tagged Pointers / DCAS).",
        "category": "Operating Systems & Concurrency",
        "tier": 4,
    },
    {
        "skill_id": "transaction_isolation_acid",
        "concept_key": "write_skew_serializable_snapshot",
        "title": "Write Skew Anomaly Under Snapshot Isolation",
        "question_prompt": "Explain Write Skew under Snapshot Isolation using the On-Call Doctor example.",
        "answer_explanation": "Two on-call doctors simultaneously submit requests to take off. Constraint: At least one doctor must remain on call. Each transaction reads that 2 doctors are on call. Each transaction modifies a different row (Doctor A marks status=off; Doctor B marks status=off). Both commit because their write sets do not overlap, leaving 0 doctors on call. Prevented only by Serializable isolation or explicit SELECT FOR UPDATE locking.",
        "key_takeaway": "Write skew occurs when overlapping read constraints are violated by non-overlapping concurrent writes.",
        "category": "Storage & Databases",
        "tier": 4,
    },
    {
        "skill_id": "consistent_hashing",
        "concept_key": "consistent_hashing_virtual_nodes",
        "title": "Consistent Hashing Virtual Nodes & Churn",
        "question_prompt": "Why are virtual nodes (vnodes) essential in consistent hashing ring partitioning?",
        "answer_explanation": "Standard consistent hashing maps physical servers to a single point on a 0 to 2^32-1 ring, resulting in severe load variance (non-uniform key distribution). Virtual nodes map each physical server to 100-256 tokens uniformly across the ring, reducing coefficient of variation in shard load to < 5% and spreading churn evenly across all peers during node failure.",
        "key_takeaway": "Virtual nodes achieve uniform key distribution across the ring and distribute rebalance load evenly upon node churn.",
        "category": "Distributed Systems",
        "tier": 4,
    },
    {
        "skill_id": "event_driven_messaging",
        "concept_key": "kafka_consumer_rebalance_protocol",
        "title": "Kafka Consumer Group Rebalance Protocols",
        "question_prompt": "What is the difference between Eager Rebalance and Incremental Cooperative Rebalancing in Apache Kafka?",
        "answer_explanation": "Eager Rebalance forces all consumers in a group to revoke all assigned partitions simultaneously, halting message processing ('stop-the-world') during coordinator partition reassignment. Cooperative Rebalancing (Kafka 2.4+) revokes only the specific partitions migrating between consumers, allowing unaffected partitions to stream continuously with zero downtime.",
        "key_takeaway": "Cooperative rebalancing avoids stop-the-world pauses by migrating partitions incrementally in two phases.",
        "category": "Distributed Systems",
        "tier": 4,
    },
    {
        "skill_id": "vector_databases_hnsw",
        "concept_key": "hnsw_graph_skip_list_recall",
        "title": "HNSW Graph Indexing & ANN Trade-offs",
        "question_prompt": "How does Hierarchical Navigable Small World (HNSW) combine multi-layer skip lists with proximity graphs?",
        "answer_explanation": "HNSW builds a multi-layer geometric graph where top layers have sparse nodes and long-range edges (for logarithmic-time coarse spatial routing), while bottom layers have dense nodes and short-range clustering. Search navigates greedily from the top entry point down to layer 0, achieving O(log N) approximate nearest neighbor recall without exhaustive brute-force vector scans.",
        "key_takeaway": "HNSW achieves O(log N) search by descending through multi-layer Voronoi graphs with greedy routing.",
        "category": "AI & Data Infrastructure",
        "tier": 4,
    },
    # Tier 5
    {
        "skill_id": "raft_paxos_consensus",
        "concept_key": "raft_log_matching_invariant",
        "title": "Raft Log Matching & Leader Append Invariant",
        "question_prompt": "State the Raft Log Matching Property and how the leader enforces it during AppendEntries RPC.",
        "answer_explanation": "If two logs contain an entry with the same index and term, they store the identical command and their logs are identical in all preceding entries up to that index. The leader enforces this by including (prevLogIndex, prevLogTerm) in every AppendEntries RPC; if the follower's log does not match, it rejects the RPC, causing the leader to decrement nextIndex and back up until logs converge.",
        "key_takeaway": "Log Matching Property guarantees uncommitted conflicting follower entries are overwritten by the authoritative leader.",
        "category": "Distributed Systems",
        "tier": 5,
    },
    {
        "skill_id": "distributed_transactions_2pc",
        "concept_key": "two_phase_commit_blocking_coordinator",
        "title": "Two-Phase Commit (2PC) Blocking Coordinator Failure",
        "question_prompt": "Why is standard Two-Phase Commit considered an inherently blocking protocol?",
        "answer_explanation": "In 2PC Phase 1 (Prepare), participants vote YES and acquire exclusive row locks. If the coordinator crashes after all participants vote YES but before sending COMMIT/ABORT, participants cannot autonomously commit (coordinator might have aborted) nor abort (coordinator might have committed). Participants remain blocked holding locks indefinitely until coordinator recovery.",
        "key_takeaway": "2PC blocks indefinitely if the coordinator fails during the decision commit window, holding participant resource locks.",
        "category": "Distributed Systems",
        "tier": 5,
    },
    {
        "skill_id": "lsm_trees_storage",
        "concept_key": "lsm_compaction_write_amplification",
        "title": "LSM-Tree Compaction: Leveled vs Size-Tiered",
        "question_prompt": "Compare Size-Tiered vs Leveled Compaction in terms of Write Amplification, Read Amplification, and Space Amplification.",
        "answer_explanation": "Size-Tiered (STCS) compacts SSTables of similar sizes together; it has low Write Amplification and high write throughput, but high Space Amplification (~50% free disk needed) and high Read Amplification. Leveled Compaction (LCS) divides data into exponential size tiers (L0, L1, L2...); it bounds Space Amplification (~10%) and Read Amplification, but has high Write Amplification (rewriting full levels).",
        "key_takeaway": "Size-Tiered optimizes write throughput at the cost of space; Leveled bounds space and read latency at higher write cost.",
        "category": "Storage & Databases",
        "tier": 5,
    },
    {
        "skill_id": "event_sourcing_cqrs",
        "concept_key": "cqrs_eventual_consistency_read_skew",
        "title": "CQRS Read Model Projections & Eventual Consistency",
        "question_prompt": "How does a CQRS architecture handle Read-Your-Own-Writes consistency for clients after command execution?",
        "answer_explanation": "Because write commands append to an event log and asynchronous projections update the query read store, immediate read queries may return stale state. Solutions: (1) Returning the projected entity state directly in the command response, (2) Client passes the event commit version/sequence, and query service polls until projection lag catches up, or (3) Session consistency caching at the edge.",
        "key_takeaway": "Mitigate CQRS eventual consistency via command result hydration or sequence-version client tokens.",
        "category": "Distributed Systems",
        "tier": 5,
    },
    {
        "skill_id": "service_mesh_envoy",
        "concept_key": "envoy_circuit_breaker_outlier_detection",
        "title": "Envoy Outlier Detection vs Application Circuit Breakers",
        "question_prompt": "How does Envoy Proxy perform passive outlier detection and ejection across an upstream cluster?",
        "answer_explanation": "Envoy monitors live request traffic without synthetic health probes. When an upstream host returns consecutive 5xx errors (e.g. 5 failures within 10s), Envoy automatically ejects it from the load balancing pool for an initial base ejection duration (e.g. 30s). The ejection duration increases exponentially with repeated failures, insulating client traffic transparently at the network L4/L7 boundary.",
        "key_takeaway": "Outlier detection passively ejects unhealthy cluster endpoints using live consecutive error telemetry.",
        "category": "Cloud & Infrastructure",
        "tier": 5,
    },
]


@dataclass
class SM2CalculationResult:
    repetition_count: int
    interval_days: int
    easiness_factor: float
    retention_score: float
    next_review_due: datetime


class SM2LearningService:
    """
    SuperMemo-2 (SM-2) Spaced Repetition Engine.
    Implements:
    - Mathematical SM-2 interval & easiness factor calculations
    - Ebbinghaus forgetting curve retention decay
    - Canonical interview card deck management
    - User review queue scheduling and due-item prioritization
    - Mastery boost sync with CandidateSkillMastery
    """

    def __init__(self, db: AsyncSession | None = None) -> None:
        self._db = db

    # ── 1. MATHEMATICAL SM-2 CORE ─────────────────────────────────────────────
    @staticmethod
    def calculate_sm2_update(
        quality: int,
        repetition_count: int,
        interval_days: int,
        easiness_factor: float,
        reference_time: datetime | None = None,
    ) -> SM2CalculationResult:
        """
        Mathematical implementation of SuperMemo-2 (SM-2).
        quality: 0 (Blackout) to 5 (Perfect instant recall).
        - Quality < 3: Failure -> reset repetitions to 0, interval to 1 day.
        - Quality >= 3: Success -> increase interval geometrically:
            n=0 -> I=1
            n=1 -> I=6
            n>=2 -> I = ceil(I * EF)
        - Update Easiness Factor:
            EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            EF = max(1.3, EF')
        """
        if quality < 0 or quality > 5:
            raise ValueError(f"Quality rating must be between 0 and 5, received {quality}")

        ref_time = reference_time or datetime.now(UTC)

        # 1. Update Easiness Factor
        ef_delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ef = round(max(1.3, easiness_factor + ef_delta), 2)

        # 2. Update Repetitions & Interval
        if quality < 3:
            # Failed recall: reset to beginning
            new_reps = 0
            new_interval = 1
        else:
            # Successful recall
            if repetition_count == 0:
                new_interval = 1
            elif repetition_count == 1:
                new_interval = 6
            else:
                new_interval = math.ceil(interval_days * new_ef)
            new_reps = repetition_count + 1

        # 3. Calculate Retention Score via Ebbinghaus curve model
        # Base retention score derived from immediate quality: q=5 -> 1.0, q=3 -> 0.76, q=0 -> 0.40
        retention = round(min(1.0, max(0.2, 0.40 + (quality * 0.12))), 2)

        next_due = ref_time + timedelta(days=new_interval)

        return SM2CalculationResult(
            repetition_count=new_reps,
            interval_days=new_interval,
            easiness_factor=new_ef,
            retention_score=retention,
            next_review_due=next_due,
        )

    @staticmethod
    def calculate_current_retention_probability(
        elapsed_days: float,
        interval_days: int,
    ) -> float:
        """
        Computes the current retention probability R using the Ebbinghaus forgetting curve:
        R = exp(-elapsed / stability), where stability S is proportional to interval_days.
        """
        if interval_days <= 0:
            return 0.5
        stability = max(1.0, float(interval_days))
        retention = math.exp(-elapsed_days / stability)
        return round(min(1.0, max(0.05, retention)), 3)

    # ── 2. DECK POPULATION & SEEDING ──────────────────────────────────────────
    async def seed_user_deck(
        self,
        user_id: UUID,
        skill_ids: list[str] | None = None,
    ) -> list[SpacedRepetitionCard]:
        """Seeds canonical flashcards for the user idempotently."""
        if self._db is None:
            raise RuntimeError("Database session required for seed_user_deck")

        # Check existing cards for user
        existing_result = await self._db.execute(
            select(SpacedRepetitionCard.concept_key).where(SpacedRepetitionCard.user_id == user_id)
        )
        existing_keys = set(existing_result.scalars().all())

        new_cards: list[SpacedRepetitionCard] = []
        target_skills_set = set(skill_ids) if skill_ids else None

        for item in CANONICAL_FLASHCARDS:
            if target_skills_set and item["skill_id"] not in target_skills_set:
                continue
            if item["concept_key"] in existing_keys:
                continue

            card = SpacedRepetitionCard(
                user_id=user_id,
                skill_id=item["skill_id"],
                concept_key=item["concept_key"],
                title=item["title"],
                question_prompt=item["question_prompt"],
                answer_explanation=item["answer_explanation"],
                key_takeaway=item["key_takeaway"],
                category=item["category"],
                tier=item["tier"],
                repetition_count=0,
                easiness_factor=2.5,
                interval_days=1,
                retention_score=1.0,
                next_review_due=datetime.now(UTC),
                review_history=[],
            )
            self._db.add(card)
            new_cards.append(card)

        if new_cards:
            await self._db.flush()
            log.info("sm2_cards_seeded", user_id=str(user_id), count=len(new_cards))

        return new_cards

    # ── 3. QUEUE FETCHING & DUE CARDS ─────────────────────────────────────────
    async def get_due_cards(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> list[SpacedRepetitionCard]:
        """
        Retrieves cards due for review (next_review_due <= now or never reviewed),
        prioritizing:
        1. Overdue cards (earliest due first)
        2. Higher difficulty tiers (Tier 5 down to Tier 1)
        """
        if self._db is None:
            raise RuntimeError("Database session required for get_due_cards")

        now = datetime.now(UTC)
        query = (
            select(SpacedRepetitionCard)
            .where(
                SpacedRepetitionCard.user_id == user_id,
                SpacedRepetitionCard.next_review_due <= now,
            )
            .order_by(
                SpacedRepetitionCard.next_review_due.asc(),
                SpacedRepetitionCard.tier.desc(),
            )
            .limit(limit)
        )
        result = await self._db.execute(query)
        cards = list(result.scalars().all())

        # If user has no overdue cards, include unreviewed cards (repetition_count == 0)
        if len(cards) < limit:
            remaining_limit = limit - len(cards)
            existing_ids = [c.id for c in cards]
            unreviewed_query = (
                select(SpacedRepetitionCard)
                .where(
                    SpacedRepetitionCard.user_id == user_id,
                    SpacedRepetitionCard.repetition_count == 0,
                    SpacedRepetitionCard.id.notin_(existing_ids) if existing_ids else True,
                )
                .order_by(SpacedRepetitionCard.tier.desc())
                .limit(remaining_limit)
            )
            unreviewed_result = await self._db.execute(unreviewed_query)
            cards.extend(list(unreviewed_result.scalars().all()))

        return cards

    # ── 4. REVIEW SUBMISSION & MASTERY SYNC ───────────────────────────────────
    async def submit_card_review(
        self,
        user_id: UUID,
        card_id: UUID,
        quality: int,
    ) -> dict[str, Any]:
        """
        Processes a candidate's SM-2 review rating (0 to 5), updates card schedule,
        and awards mastery points in CandidateSkillMastery.
        """
        if self._db is None:
            raise RuntimeError("Database session required for submit_card_review")

        card = await self._db.get(SpacedRepetitionCard, card_id)
        if not card or card.user_id != user_id:
            raise ValueError(f"Card {card_id} not found for user {user_id}")

        now = datetime.now(UTC)
        calc = self.calculate_sm2_update(
            quality=quality,
            repetition_count=card.repetition_count,
            interval_days=card.interval_days,
            easiness_factor=card.easiness_factor,
            reference_time=now,
        )

        # Record review history entry
        history_entry = {
            "reviewed_at": now.isoformat(),
            "quality": quality,
            "prev_interval": card.interval_days,
            "new_interval": calc.interval_days,
            "prev_ef": card.easiness_factor,
            "new_ef": calc.easiness_factor,
            "reps": calc.repetition_count,
        }

        card.repetition_count = calc.repetition_count
        card.interval_days = calc.interval_days
        card.easiness_factor = calc.easiness_factor
        card.retention_score = calc.retention_score
        card.last_quality = quality
        card.last_reviewed_at = now
        card.next_review_due = calc.next_review_due
        card.review_history = (card.review_history or []) + [history_entry]

        self._db.add(card)

        # Sync with CandidateSkillMastery if quality >= 3
        mastery_boost = 0.0
        if quality >= 3:
            mastery_query = select(CandidateSkillMastery).where(
                CandidateSkillMastery.user_id == user_id,
                CandidateSkillMastery.skill_id == card.skill_id,
            )
            m_res = await self._db.execute(mastery_query)
            mastery = m_res.scalar_one_or_none()

            boost_amount = 3.5 if quality == 5 else (2.0 if quality == 4 else 1.0)
            if mastery:
                mastery.mastery_score = min(100.0, mastery.mastery_score + boost_amount)
                mastery.last_assessed_at = now
                self._db.add(mastery)
                mastery_boost = boost_amount
            else:
                new_mastery = CandidateSkillMastery(
                    user_id=user_id,
                    skill_id=card.skill_id,
                    mastery_score=min(100.0, 50.0 + boost_amount),
                    confidence=0.85,
                    is_inferred=False,
                    verified_via="sm2_spaced_repetition",
                )
                self._db.add(new_mastery)
                mastery_boost = boost_amount

        await self._db.flush()
        await self._db.refresh(card)

        log.info(
            "sm2_review_completed",
            card_id=str(card.id),
            quality=quality,
            new_interval=calc.interval_days,
            new_ef=calc.easiness_factor,
        )

        return {
            "card_id": str(card.id),
            "concept_key": card.concept_key,
            "title": card.title,
            "quality": quality,
            "repetition_count": card.repetition_count,
            "interval_days": card.interval_days,
            "easiness_factor": card.easiness_factor,
            "retention_score": card.retention_score,
            "next_review_due": card.next_review_due.isoformat(),
            "mastery_boost_applied": mastery_boost,
        }

    # ── 5. DECK ANALYTICS & STATS ─────────────────────────────────────────────
    async def get_deck_stats(self, user_id: UUID) -> dict[str, Any]:
        """Calculates candidate memory stability, mature vs young card counts, and streaks."""
        if self._db is None:
            raise RuntimeError("Database session required for get_deck_stats")

        cards_res = await self._db.execute(
            select(SpacedRepetitionCard).where(SpacedRepetitionCard.user_id == user_id)
        )
        cards = list(cards_res.scalars().all())

        now = datetime.now(UTC)
        total_cards = len(cards)
        due_today = 0
        mature_count = 0  # Interval >= 21 days
        young_count = 0   # Interval < 21 days and reps > 0
        new_count = 0     # Reps == 0
        retention_sum = 0.0
        total_reviews = 0

        for c in cards:
            if c.next_review_due <= now:
                due_today += 1

            if c.repetition_count == 0:
                new_count += 1
            elif c.interval_days >= 21:
                mature_count += 1
            else:
                young_count += 1

            retention_sum += c.retention_score
            total_reviews += len(c.review_history or [])

        avg_retention = round((retention_sum / max(total_cards, 1)) * 100, 1) if total_cards else 0.0

        # Calculate review streak based on review_history timestamps
        all_review_dates = set()
        for c in cards:
            for r in (c.review_history or []):
                rev_date_str = r.get("reviewed_at", "")[:10]
                if rev_date_str:
                    all_review_dates.add(rev_date_str)

        streak = 0
        check_date = now.date()
        while check_date.isoformat() in all_review_dates:
            streak += 1
            check_date -= timedelta(days=1)

        return {
            "total_cards": total_cards,
            "due_today_count": due_today,
            "mature_cards_count": mature_count,
            "young_cards_count": young_count,
            "new_cards_count": new_count,
            "average_retention_pct": avg_retention,
            "total_reviews_completed": total_reviews,
            "current_streak_days": streak,
        }
