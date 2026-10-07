"""
Phase 13: Personalized Learning & SM-2 Spaced Repetition Test Suite
Validates:
1. Pure Mathematical SM-2 Algorithm (Intervals, Repetitions, Easiness Factor Updates, Lower Bound Invariants)
2. Ebbinghaus Forgetting Curve Retention Decay Calculation
3. Canonical Flashcard Catalog Verification against Phase 12 Skill DAG Nodes
4. Database Deck Seeding, Idempotency, and Due Queue Retrieval
5. Review Progression, Quality Ratings (0-5), and CandidateSkillMastery Sync
6. Deck Analytics, Mature/Young Card Segregation, and Retention Metrics
7. Full HTTP REST API Endpoints Coverage for SM-2 Learning
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.database import AsyncSessionLocal, Base, engine
from app.main import app
from app.models.skill_graph import CandidateSkillMastery
from app.models.sm2_card import SpacedRepetitionCard
from app.models.user import User, UserRole
from app.services.skill_graph_service import CANONICAL_SKILL_NODES
from app.services.sm2_learning_service import (
    CANONICAL_FLASHCARDS,
    SM2LearningService,
)


async def test_phase13_sm2_learning() -> None:
    print("\n========================================================")
    print("=== STARTING PHASE 13: PERSONALIZED LEARNING & SM-2 ===")
    print("========================================================\n")

    # ── 1. MATHEMATICAL SM-2 CORE TESTS ───────────────────────────────────────
    print("--- 1. Testing Mathematical SM-2 Algorithm Invariants ---")

    # 1.1 First review with quality 5 (Perfect recall)
    res1 = SM2LearningService.calculate_sm2_update(
        quality=5,
        repetition_count=0,
        interval_days=1,
        easiness_factor=2.5,
    )
    assert res1.repetition_count == 1
    assert res1.interval_days == 1
    assert res1.easiness_factor == 2.6  # 2.5 + (0.1 - 0) = 2.6
    assert res1.retention_score == 1.0
    print("  [PASS] Initial repetition (q=5): n=1, I=1, EF=2.6")

    # 1.2 Second review with quality 4 (Correct after hesitation)
    res2 = SM2LearningService.calculate_sm2_update(
        quality=4,
        repetition_count=1,
        interval_days=1,
        easiness_factor=2.6,
    )
    assert res2.repetition_count == 2
    assert res2.interval_days == 6  # 2nd successful rep interval is always 6
    assert res2.easiness_factor == 2.6  # 2.6 + (0.1 - 1*(0.08 + 0.02)) = 2.6
    print("  [PASS] Second repetition (q=4): n=2, I=6, EF=2.6")

    # 1.3 Third review with quality 5 (Geometrical growth)
    res3 = SM2LearningService.calculate_sm2_update(
        quality=5,
        repetition_count=2,
        interval_days=6,
        easiness_factor=2.6,
    )
    assert res3.repetition_count == 3
    # ceil(6 * 2.7) = ceil(16.2) = 17 or ceil(6 * 2.7) = 17
    assert res3.interval_days == 17
    assert res3.easiness_factor == 2.7
    print(f"  [PASS] Third repetition (q=5): n=3, I={res3.interval_days}, EF={res3.easiness_factor}")

    # 1.4 Failure review with quality 1 (Complete blackout / failure)
    res_fail = SM2LearningService.calculate_sm2_update(
        quality=1,
        repetition_count=5,
        interval_days=45,
        easiness_factor=2.5,
    )
    assert res_fail.repetition_count == 0  # Reset
    assert res_fail.interval_days == 1      # Reset to 1 day
    assert res_fail.easiness_factor < 2.5   # EF dropped
    print(f"  [PASS] Failure reset (q=1): n=0, I=1, EF dropped to {res_fail.easiness_factor}")

    # 1.5 EF Lower Bound: never drops below 1.3
    res_floor = SM2LearningService.calculate_sm2_update(
        quality=0,
        repetition_count=0,
        interval_days=1,
        easiness_factor=1.35,
    )
    assert res_floor.easiness_factor == 1.3  # clamped to floor
    print("  [PASS] Easiness factor floor invariant (EF >= 1.3) strictly enforced.")

    # 1.6 Ebbinghaus Forgetting Curve Decay
    ret_fresh = SM2LearningService.calculate_current_retention_probability(elapsed_days=0.0, interval_days=10)
    ret_halfway = SM2LearningService.calculate_current_retention_probability(elapsed_days=5.0, interval_days=10)
    ret_due = SM2LearningService.calculate_current_retention_probability(elapsed_days=10.0, interval_days=10)
    ret_overdue = SM2LearningService.calculate_current_retention_probability(elapsed_days=20.0, interval_days=10)

    assert ret_fresh == 1.0
    assert 0.5 < ret_halfway < 1.0
    assert 0.3 < ret_due < 0.4
    assert ret_overdue < ret_due
    print(f"  [PASS] Ebbinghaus forgetting curve verified: fresh={ret_fresh}, due={ret_due}, overdue={ret_overdue}")

    # ── 2. CANONICAL FLASHCARDS CATALOG VALIDATION ────────────────────────────
    print("\n--- 2. Validating Canonical Flashcards Catalog against Skill DAG ---")
    assert len(CANONICAL_FLASHCARDS) >= 15
    for card in CANONICAL_FLASHCARDS:
        assert card["skill_id"] in CANONICAL_SKILL_NODES, f"Card skill {card['skill_id']} not in Skill DAG!"
        assert 1 <= card["tier"] <= 5
        assert len(card["question_prompt"]) > 20
        assert len(card["answer_explanation"]) > 30
    print(f"  [PASS] All {len(CANONICAL_FLASHCARDS)} canonical flashcards map to valid Skill DAG nodes across Tiers 1-5.")

    # ── 3. DATABASE INTEGRATION & SERVICE WORKFLOW ────────────────────────────
    print("\n--- 3. Testing Database Deck Seeding, Review & Mastery Sync ---")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Create test candidate
        test_email = f"sm2_tester_{uuid.uuid4().hex[:8]}@platform.local"
        user = User(
            email=test_email,
            full_name="SM2 Test Candidate",
            hashed_password="Password123!",
            role=UserRole.candidate,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)

        svc = SM2LearningService(db=session)

        # 3.1 Seed deck
        seeded = await svc.seed_user_deck(user_id=user.id)
        assert len(seeded) >= 15
        print(f"  [PASS] Seeded {len(seeded)} cards into candidate deck.")

        # 3.2 Idempotency: second seeding should add 0 duplicates
        seeded_again = await svc.seed_user_deck(user_id=user.id)
        assert len(seeded_again) == 0
        print("  [PASS] Seeding idempotency verified (0 duplicate cards added).")

        # 3.3 Fetch due cards
        due_cards = await svc.get_due_cards(user_id=user.id, limit=10)
        assert len(due_cards) > 0
        target_card = due_cards[0]
        print(f"  [PASS] Retrieved {len(due_cards)} due cards. First: '{target_card.title}'")

        # 3.4 Submit successful review (q=5)
        review_result = await svc.submit_card_review(
            user_id=user.id,
            card_id=target_card.id,
            quality=5,
        )
        assert review_result["quality"] == 5
        assert review_result["repetition_count"] == 1
        assert review_result["interval_days"] == 1
        assert review_result["mastery_boost_applied"] > 0
        print(f"  [PASS] Review recorded. Mastery boost awarded: +{review_result['mastery_boost_applied']} pts.")

        # Verify CandidateSkillMastery updated
        mastery_res = await session.execute(
            CandidateSkillMastery.__table__.select().where(
                CandidateSkillMastery.user_id == user.id,
                CandidateSkillMastery.skill_id == target_card.skill_id,
            )
        )
        mastery_row = mastery_res.fetchone()
        assert mastery_row is not None
        assert mastery_row.mastery_score > 50.0
        print(f"  [PASS] CandidateSkillMastery automatically boosted to {mastery_row.mastery_score}%.")

        # 3.5 Submit second review for same card (q=4)
        review_result_2 = await svc.submit_card_review(
            user_id=user.id,
            card_id=target_card.id,
            quality=4,
        )
        assert review_result_2["repetition_count"] == 2
        assert review_result_2["interval_days"] == 6
        print(f"  [PASS] Second review processed. Next interval advanced to {review_result_2['interval_days']} days.")

        # 3.6 Deck stats calculation
        stats = await svc.get_deck_stats(user_id=user.id)
        assert stats["total_cards"] == len(seeded)
        assert stats["young_cards_count"] >= 1
        assert stats["total_reviews_completed"] == 2
        print(f"  [PASS] Deck stats verified: {stats['total_cards']} cards, avg retention: {stats['average_retention_pct']}%.")

        await session.commit()
        token = create_access_token(user.id, user.role.value)

    # ── 4. HTTP REST API ENDPOINTS TEST ───────────────────────────────────────
    print("\n--- 4. Testing HTTP REST Endpoints Coverage ---")
    transport = ASGITransport(app=app)
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # GET /learning/sm2/cards/due
        resp_due = await client.get("/api/v1/learning/sm2/cards/due", headers=headers)
        assert resp_due.status_code == 200, resp_due.text
        due_list = resp_due.json()
        assert len(due_list) > 0
        test_card_id = due_list[0]["id"]
        print(f"  [PASS] GET /api/v1/learning/sm2/cards/due -> {len(due_list)} cards")

        # POST /learning/sm2/cards/review
        resp_rev = await client.post(
            "/api/v1/learning/sm2/cards/review",
            headers=headers,
            json={"card_id": test_card_id, "quality": 5},
        )
        assert resp_rev.status_code == 200, resp_rev.text
        rev_data = resp_rev.json()
        assert rev_data["quality"] == 5
        print(f"  [PASS] POST /api/v1/learning/sm2/cards/review -> new interval: {rev_data['interval_days']}d")

        # GET /learning/sm2/deck
        resp_deck = await client.get("/api/v1/learning/sm2/deck", headers=headers)
        assert resp_deck.status_code == 200
        deck_list = resp_deck.json()
        assert len(deck_list) >= 15
        print(f"  [PASS] GET /api/v1/learning/sm2/deck -> {len(deck_list)} cards in user collection")

        # GET /learning/sm2/stats
        resp_stats = await client.get("/api/v1/learning/sm2/stats", headers=headers)
        assert resp_stats.status_code == 200
        stats_data = resp_stats.json()
        assert stats_data["total_cards"] >= 15
        assert stats_data["total_reviews_completed"] >= 1
        print(f"  [PASS] GET /api/v1/learning/sm2/stats -> Total reviews: {stats_data['total_reviews_completed']}")

        # GET /learning/sm2/cards/{card_id}
        resp_card = await client.get(f"/api/v1/learning/sm2/cards/{test_card_id}", headers=headers)
        assert resp_card.status_code == 200
        card_obj = resp_card.json()
        assert card_obj["id"] == test_card_id
        print(f"  [PASS] GET /api/v1/learning/sm2/cards/{test_card_id} -> '{card_obj['title']}'")

        # POST /learning/sm2/seed
        resp_seed = await client.post(
            "/api/v1/learning/sm2/seed",
            headers=headers,
            json={"skill_ids": ["raft_paxos_consensus"]},
        )
        assert resp_seed.status_code == 200
        print("  [PASS] POST /api/v1/learning/sm2/seed -> 200 OK")

    print("\n========================================================")
    print("=== ALL PHASE 13 SM-2 LEARNING TESTS PASSED (100%) ===")
    print("========================================================\n")


if __name__ == "__main__":
    asyncio.run(test_phase13_sm2_learning())
