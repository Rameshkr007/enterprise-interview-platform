"""
Phase 12: Skill Graph & DAG Taxonomy Test Suite
Validates:
1. Directed Acyclic Graph (DAG) Invariant Enforcement & 3-Color Cycle Detection
2. Kahn's Topological Sorting Algorithm for Valid Prerequisite-Ordered Curricula
3. Prerequisite Transitive Closure Traversal
4. Root-Cause Foundational Prerequisite Gap Analysis
5. Transitive Skill Mastery Credit Propagation with Distance Decay
6. Enterprise Role Archetype Alignment & Readiness Scoring
7. Dynamic Milestone Learning Pathway Generator
8. Full HTTP REST Endpoints Coverage for Skill Graph API
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.skill_graph_service import (
    CANONICAL_SKILL_NODES,
    ROLE_ARCHETYPES,
    SkillGraphService,
    SkillNodeData,
)


async def test_phase12_skill_graph_dag() -> None:
    print("\n========================================================")
    print("=== STARTING PHASE 12: SKILL GRAPH & DAG TAXONOMY TEST ===")
    print("========================================================\n")

    svc = SkillGraphService()

    # ── 1. DAG INVARIANT & CYCLE DETECTION ────────────────────────────────────
    print("--- 1. Testing DAG Invariants & Cycle Detection ---")
    # Verify canonical graph has no cycles
    svc.verify_acyclic()
    print("  [PASS] Canonical Skill DAG is strictly acyclic (0 cycles found).")

    # Artificially inject a cycle into a mock graph copy to verify 3-color DFS detection
    cyclic_nodes = {
        "node_a": SkillNodeData(id="node_a", name="A", category="Test", tier=1, description="", prerequisites=["node_c"]),
        "node_b": SkillNodeData(id="node_b", name="B", category="Test", tier=1, description="", prerequisites=["node_a"]),
        "node_c": SkillNodeData(id="node_c", name="C", category="Test", tier=1, description="", prerequisites=["node_b"]),
    }
    cyclic_svc = SkillGraphService.__new__(SkillGraphService)
    cyclic_svc._nodes = cyclic_nodes

    cycle_caught = False
    try:
        cyclic_svc.verify_acyclic()
    except ValueError as e:
        cycle_caught = True
        print(f"  [PASS] Artificially injected cycle caught successfully: {e}")
    assert cycle_caught, "Cycle detection failed to trigger on cyclic dependency!"

    # ── 2. KAHN'S TOPOLOGICAL SORTING ─────────────────────────────────────────
    print("\n--- 2. Testing Kahn's Topological Sorting ---")
    sorted_all = svc.topological_sort()
    assert len(sorted_all) == len(CANONICAL_SKILL_NODES)

    # Invariant: Every prerequisite MUST appear before the dependent skill
    position_map = {sid: idx for idx, sid in enumerate(sorted_all)}
    for sid, node in CANONICAL_SKILL_NODES.items():
        for prereq in node.prerequisites:
            assert position_map[prereq] < position_map[sid], (
                f"Topological violation: Prerequisite {prereq} (pos {position_map[prereq]}) "
                f"must appear before dependent {sid} (pos {position_map[sid]})"
            )
    print(f"  [PASS] All {len(sorted_all)} canonical skills sorted topologically with 100% prerequisite integrity.")

    # ── 3. PREREQUISITE CLOSURE TRAVERSAL ─────────────────────────────────────
    print("\n--- 3. Testing Transitive Prerequisite Closure ---")
    raft_ancestors = svc.get_prerequisite_closure("raft_paxos_consensus")
    assert "cap_pacelc_theorems" in raft_ancestors
    assert "distributed_systems_basics" in raft_ancestors
    assert "networking_tcp_ip" in raft_ancestors
    assert "cs_fundamentals" in raft_ancestors
    assert "locks_and_atomics" in raft_ancestors
    assert "multithreading_concurrency" in raft_ancestors
    assert "os_fundamentals" in raft_ancestors
    print(f"  [PASS] Raft consensus transitive ancestors resolved: {len(raft_ancestors)} ancestral skills verified.")

    # ── 4. ROOT-CAUSE PREREQUISITE GAP ANALYSIS ───────────────────────────────
    print("\n--- 4. Testing Root-Cause Prerequisite Gap Backtracking ---")
    # Scenario: Candidate fails Raft Consensus, has mastered some Tier 1/2 skills, but lacks multithreading & os fundamentals
    candidate_scores = {
        "cs_fundamentals": 90.0,
        "programming_basics": 85.0,
        "networking_tcp_ip": 80.0,
        "os_fundamentals": 45.0,  # FAILED
        "multithreading_concurrency": 40.0,  # FAILED
        "locks_and_atomics": 30.0,  # FAILED
        "raft_paxos_consensus": 25.0,  # FAILED
    }
    gap_result = svc.analyze_root_cause_gaps(
        candidate_mastery=candidate_scores,
        failed_skills=["raft_paxos_consensus"],
        passing_threshold=65.0,
    )
    assert gap_result["total_failed_skills"] == 1
    root_cause = gap_result["root_causes"][0]
    assert root_cause["failed_skill"] == "raft_paxos_consensus"
    # Root cause must be os_fundamentals (Tier 2 foundation)
    assert root_cause["root_cause_skill_id"] == "os_fundamentals"
    assert root_cause["root_cause_tier"] == 2
    assert "os_fundamentals" in gap_result["remediation_roadmap"]
    print(f"  [PASS] Root-cause accurately diagnosed: {root_cause['diagnosis']}")
    print(f"  [PASS] Remedy sequence: {' -> '.join(root_cause['remedy_sequence'])}")

    # Test isolated failure where foundational prerequisites are mastered
    isolated_scores = {
        "cs_fundamentals": 95.0,
        "os_fundamentals": 90.0,
        "multithreading_concurrency": 92.0,
        "networking_tcp_ip": 90.0,
        "distributed_systems_basics": 88.0,
        "cap_pacelc_theorems": 85.0,
        "locks_and_atomics": 80.0,
        "raft_paxos_consensus": 40.0,  # Only Raft is failed
    }
    iso_gap = svc.analyze_root_cause_gaps(
        candidate_mastery=isolated_scores,
        failed_skills=["raft_paxos_consensus"],
        passing_threshold=65.0,
    )
    iso_root = iso_gap["root_causes"][0]
    assert iso_root["root_cause_skill_id"] == "raft_paxos_consensus"
    print(f"  [PASS] Isolated failure correctly identified: {iso_root['diagnosis']}")

    # ── 5. TRANSITIVE CREDIT PROPAGATION ──────────────────────────────────────
    print("\n--- 5. Testing Transitive Credit Propagation with Distance Decay ---")
    demonstrated = {
        "raft_paxos_consensus": 95.0,  # Tier 5
    }
    inferred = svc.propagate_transitive_credit(demonstrated, decay_factor=0.85)
    # Direct skill preserved at 95.0
    assert inferred["raft_paxos_consensus"]["score"] == 95.0
    assert not inferred["raft_paxos_consensus"]["is_inferred"]

    # Immediate prerequisites (dist = 1) -> 95.0 * 0.85 = 80.75 -> 80.8
    assert inferred["cap_pacelc_theorems"]["is_inferred"]
    assert inferred["cap_pacelc_theorems"]["score"] == round(95.0 * 0.85, 1)

    # Two hops away (dist = 2) -> 95.0 * (0.85^2) = 68.6
    assert inferred["distributed_systems_basics"]["is_inferred"]
    assert inferred["distributed_systems_basics"]["score"] == round(95.0 * (0.85 ** 2), 1)

    # Multi-hop foundational ancestor
    assert "cs_fundamentals" in inferred
    assert inferred["cs_fundamentals"]["is_inferred"]
    print(f"  [PASS] Transitive credit successfully propagated to {len(inferred)} skills.")
    print(f"    - Demonstrated Raft: {inferred['raft_paxos_consensus']['score']}%")
    print(f"    - Inferred CAP (1 hop): {inferred['cap_pacelc_theorems']['score']}%")
    print(f"    - Inferred Dist Systems (2 hops): {inferred['distributed_systems_basics']['score']}%")
    print(f"    - Inferred CS Fundamentals: {inferred['cs_fundamentals']['score']}%")

    # ── 6. ROLE ARCHETYPE ALIGNMENT ───────────────────────────────────────────
    print("\n--- 6. Testing Role Archetype Alignment Evaluation ---")
    senior_backend_profile = {
        "data_structures_core": 85.0,
        "relational_sql": 90.0,
        "indexing_b_trees": 82.0,
        "transaction_isolation_acid": 78.0,
        "multithreading_concurrency": 80.0,
        "http_rest_protocols": 88.0,
        "grpc_protobuf": 76.0,
        "distributed_systems_basics": 80.0,
        "consistent_hashing": 75.0,
        "containerization_docker": 82.0,
    }
    role_eval = svc.evaluate_role_alignment(
        candidate_mastery=senior_backend_profile,
        role_key="senior_backend_l5",
    )
    assert role_eval["coverage_percentage"] == 100.0
    assert role_eval["verdict"] == "Ready for Role"
    assert role_eval["missing_skills_count"] == 0
    assert role_eval["verified_skills_count"] == 10
    print(f"  [PASS] Senior Backend L5 profile: 100% coverage, verdict: '{role_eval['verdict']}'")

    # Partial candidate test
    junior_profile = {
        "data_structures_core": 80.0,
        "relational_sql": 78.0,
        "http_rest_protocols": 76.0,
    }
    partial_eval = svc.evaluate_role_alignment(
        candidate_mastery=junior_profile,
        role_key="senior_backend_l5",
    )
    assert partial_eval["coverage_percentage"] == 30.0
    assert partial_eval["missing_skills_count"] == 7
    assert len(partial_eval["prioritized_learning_sequence"]) == 7
    print(f"  [PASS] Partial profile evaluated: {partial_eval['coverage_percentage']}% coverage, {partial_eval['missing_skills_count']} missing skills.")

    # ── 7. LEARNING PATHWAY GENERATOR ─────────────────────────────────────────
    print("\n--- 7. Testing Milestone Learning Pathway Generator ---")
    pathway = svc.generate_learning_pathway(
        candidate_mastery={"cs_fundamentals": 85.0, "programming_basics": 80.0},
        target_skill_id="indexing_b_trees",
    )
    assert pathway["target_skill_id"] == "indexing_b_trees"
    assert pathway["total_milestones"] >= 2
    steps = [m["skill_id"] for m in pathway["curriculum"]]
    # Invariant: data_structures_core and relational_sql must precede indexing_b_trees
    assert steps[-1] == "indexing_b_trees"
    assert "data_structures_core" in steps
    assert "relational_sql" in steps
    print(f"  [PASS] Pathway to 'indexing_b_trees' generated with {pathway['total_milestones']} steps ({pathway['estimated_total_hours']} total hours).")

    # ── 8. HTTP REST API ENDPOINTS INTEGRATION TEST ───────────────────────────
    print("\n--- 8. Testing HTTP REST Endpoints Coverage ---")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # GET /nodes
        resp = await client.get("/api/v1/skill-graph/nodes")
        assert resp.status_code == 200, resp.text
        nodes = resp.json()
        assert len(nodes) >= 25
        print(f"  [PASS] GET /api/v1/skill-graph/nodes -> {len(nodes)} nodes returned")

        # GET /nodes with tier filter
        resp_tier = await client.get("/api/v1/skill-graph/nodes?tier=5")
        assert resp_tier.status_code == 200
        tier5_nodes = resp_tier.json()
        assert all(n["tier"] == 5 for n in tier5_nodes)
        print(f"  [PASS] GET /api/v1/skill-graph/nodes?tier=5 -> {len(tier5_nodes)} Tier-5 nodes")

        # GET /nodes/{skill_id}
        resp_node = await client.get("/api/v1/skill-graph/nodes/raft_paxos_consensus")
        assert resp_node.status_code == 200
        assert resp_node.json()["name"] == "Distributed Consensus (Raft / Paxos)"
        print("  [PASS] GET /api/v1/skill-graph/nodes/raft_paxos_consensus -> 200 OK")

        # GET /taxonomy/dag
        resp_dag = await client.get("/api/v1/skill-graph/taxonomy/dag")
        assert resp_dag.status_code == 200
        dag_data = resp_dag.json()
        assert dag_data["total_nodes"] >= 25
        assert len(dag_data["edges"]) >= 20
        assert len(dag_data["tiers"]) == 5
        print(f"  [PASS] GET /api/v1/skill-graph/taxonomy/dag -> {dag_data['total_nodes']} nodes, {len(dag_data['edges'])} edges")

        # GET /roles
        resp_roles = await client.get("/api/v1/skill-graph/roles")
        assert resp_roles.status_code == 200
        roles_list = resp_roles.json()
        assert len(roles_list) == 3
        print(f"  [PASS] GET /api/v1/skill-graph/roles -> {len(roles_list)} roles")

        # POST /pathway
        resp_pathway = await client.post(
            "/api/v1/skill-graph/pathway",
            json={
                "target_skill_id": "raft_paxos_consensus",
                "candidate_mastery": {"cs_fundamentals": 90.0},
            },
        )
        assert resp_pathway.status_code == 200
        p_body = resp_pathway.json()
        assert p_body["total_milestones"] > 0
        print(f"  [PASS] POST /api/v1/skill-graph/pathway -> {p_body['total_milestones']} milestones")

        # POST /root-cause-gap
        resp_gap = await client.post(
            "/api/v1/skill-graph/root-cause-gap",
            json={
                "failed_skills": ["raft_paxos_consensus"],
                "candidate_mastery": {"os_fundamentals": 40.0},
                "passing_threshold": 65.0,
            },
        )
        assert resp_gap.status_code == 200
        g_body = resp_gap.json()
        assert len(g_body["root_causes"]) == 1
        print("  [PASS] POST /api/v1/skill-graph/root-cause-gap -> 200 OK")

        # POST /transitive-infer
        resp_infer = await client.post(
            "/api/v1/skill-graph/transitive-infer",
            json={
                "demonstrated_skills": {"raft_paxos_consensus": 92.0},
                "decay_factor": 0.85,
            },
        )
        assert resp_infer.status_code == 200
        i_body = resp_infer.json()
        assert i_body["transitively_inferred_count"] > 0
        print(f"  [PASS] POST /api/v1/skill-graph/transitive-infer -> {i_body['total_skills_credited']} skills credited")

        # POST /role-alignment
        resp_align = await client.post(
            "/api/v1/skill-graph/role-alignment",
            json={
                "role_key": "senior_backend_l5",
                "candidate_mastery": {"relational_sql": 85.0, "data_structures_core": 80.0},
            },
        )
        assert resp_align.status_code == 200
        a_body = resp_align.json()
        assert "coverage_percentage" in a_body
        print(f"  [PASS] POST /api/v1/skill-graph/role-alignment -> Coverage: {a_body['coverage_percentage']}%")

    print("\n========================================================")
    print("=== ALL PHASE 12 SKILL GRAPH TESTS PASSED (100%) ===")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase12_skill_graph_dag())
