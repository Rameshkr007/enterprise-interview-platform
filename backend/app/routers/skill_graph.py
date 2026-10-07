from __future__ import annotations

from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.skill_graph import (
    InferredSkillCredit,
    MilestoneStepResponse,
    PathwayRequest,
    PathwayResponse,
    RoleAlignmentRequest,
    RoleAlignmentResponse,
    RoleSkillStatus,
    RootCauseDiagnosis,
    RootCauseGapRequest,
    RootCauseGapResponse,
    SkillEdgeResponse,
    SkillGraphDagResponse,
    SkillNodeResponse,
    TransitiveInferRequest,
    TransitiveInferResponse,
)
from app.services.skill_graph_service import (
    CANONICAL_SKILL_NODES,
    ROLE_ARCHETYPES,
    SkillGraphService,
)

router = APIRouter(prefix="/skill-graph", tags=["Skill Graph & DAG Taxonomy"])


def get_skill_service(db: Annotated[AsyncSession, Depends(get_db)]) -> SkillGraphService:
    return SkillGraphService(db=db)


@router.get("/nodes", response_model=list[SkillNodeResponse])
async def list_skill_nodes(
    category: str | None = Query(default=None, description="Filter by category"),
    tier: int | None = Query(default=None, ge=1, le=5, description="Filter by tier 1-5"),
    svc: SkillGraphService = Depends(get_skill_service),
) -> list[SkillNodeResponse]:
    """Retrieve all skill nodes in the DAG taxonomy with optional category and tier filtering."""
    nodes = svc.get_all_nodes()
    if category:
        nodes = [n for n in nodes if n.category.lower() == category.lower()]
    if tier is not None:
        nodes = [n for n in nodes if n.tier == tier]
    return [
        SkillNodeResponse(
            id=n.id,
            name=n.name,
            category=n.category,
            tier=n.tier,
            description=n.description,
            prerequisites=n.prerequisites,
            specializations=n.specializations,
            complements=n.complements,
            equivalents=n.equivalents,
        )
        for n in nodes
    ]


@router.get("/nodes/{skill_id}", response_model=SkillNodeResponse)
async def get_skill_node(
    skill_id: str,
    svc: SkillGraphService = Depends(get_skill_service),
) -> SkillNodeResponse:
    """Retrieve detailed metadata and edges for a specific skill node."""
    node = svc.get_node(skill_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill node '{skill_id}' not found in taxonomy.",
        )
    return SkillNodeResponse(
        id=node.id,
        name=node.name,
        category=node.category,
        tier=node.tier,
        description=node.description,
        prerequisites=node.prerequisites,
        specializations=node.specializations,
        complements=node.complements,
        equivalents=node.equivalents,
    )


@router.get("/taxonomy/dag", response_model=SkillGraphDagResponse)
async def get_full_dag(
    svc: SkillGraphService = Depends(get_skill_service),
) -> SkillGraphDagResponse:
    """Returns the complete Directed Acyclic Graph with all nodes and directed dependency edges."""
    nodes = svc.get_all_nodes()
    edges: list[SkillEdgeResponse] = []
    categories_set: set[str] = set()
    tiers_set: set[int] = set()

    for n in nodes:
        categories_set.add(n.category)
        tiers_set.add(n.tier)

        for p in n.prerequisites:
            edges.append(SkillEdgeResponse(source=p, target=n.id, type="prerequisite"))
        for c in n.complements:
            edges.append(SkillEdgeResponse(source=n.id, target=c, type="complementary"))
        for s in n.specializations:
            edges.append(SkillEdgeResponse(source=n.id, target=s, type="specialization"))

    node_responses = [
        SkillNodeResponse(
            id=n.id,
            name=n.name,
            category=n.category,
            tier=n.tier,
            description=n.description,
            prerequisites=n.prerequisites,
            specializations=n.specializations,
            complements=n.complements,
            equivalents=n.equivalents,
        )
        for n in nodes
    ]

    return SkillGraphDagResponse(
        nodes=node_responses,
        edges=edges,
        total_nodes=len(node_responses),
        categories=sorted(categories_set),
        tiers=sorted(tiers_set),
    )


@router.get("/roles", response_model=list[dict[str, Any]])
async def list_role_archetypes() -> list[dict[str, Any]]:
    """Lists enterprise role archetypes and target skills."""
    return [
        {
            "role_key": k,
            "title": v["title"],
            "department": v["department"],
            "description": v["description"],
            "target_skills": v["target_skills"],
            "passing_threshold": v["passing_threshold"],
        }
        for k, v in ROLE_ARCHETYPES.items()
    ]


@router.post("/pathway", response_model=PathwayResponse)
async def generate_pathway(
    req: PathwayRequest,
    svc: SkillGraphService = Depends(get_skill_service),
) -> PathwayResponse:
    """Generates a topologically sorted milestone curriculum to master target skill."""
    try:
        pathway_data = svc.generate_learning_pathway(
            candidate_mastery=req.candidate_mastery,
            target_skill_id=req.target_skill_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    curriculum = [
        MilestoneStepResponse(
            step=m["step"],
            skill_id=m["skill_id"],
            name=m["name"],
            tier=m["tier"],
            category=m["category"],
            current_score=m["current_score"],
            target_score=m["target_score"],
            estimated_study_hours=m["estimated_study_hours"],
            concept_summary=m["concept_summary"],
        )
        for m in pathway_data["curriculum"]
    ]

    return PathwayResponse(
        target_skill_id=pathway_data["target_skill_id"],
        target_skill_name=pathway_data["target_skill_name"],
        total_milestones=pathway_data["total_milestones"],
        estimated_total_hours=pathway_data["estimated_total_hours"],
        curriculum=curriculum,
    )


@router.post("/root-cause-gap", response_model=RootCauseGapResponse)
async def analyze_root_cause_gaps(
    req: RootCauseGapRequest,
    svc: SkillGraphService = Depends(get_skill_service),
) -> RootCauseGapResponse:
    """Traverses DAG backwards to identify earliest foundational unmastered root causes for failed skills."""
    result = svc.analyze_root_cause_gaps(
        candidate_mastery=req.candidate_mastery,
        failed_skills=req.failed_skills,
        passing_threshold=req.passing_threshold,
    )

    diagnoses = [
        RootCauseDiagnosis(
            failed_skill=r["failed_skill"],
            failed_skill_name=r["failed_skill_name"],
            root_cause_skill_id=r["root_cause_skill_id"],
            root_cause_skill_name=r["root_cause_skill_name"],
            root_cause_tier=r["root_cause_tier"],
            candidate_score=r["candidate_score"],
            diagnosis=r["diagnosis"],
            remedy_sequence=r["remedy_sequence"],
        )
        for r in result["root_causes"]
    ]

    return RootCauseGapResponse(
        total_failed_skills=result["total_failed_skills"],
        root_causes=diagnoses,
        all_unmastered_skills=result["all_unmastered_skills"],
        remediation_roadmap=result["remediation_roadmap"],
    )


@router.post("/transitive-infer", response_model=TransitiveInferResponse)
async def propagate_transitive_credit(
    req: TransitiveInferRequest,
    svc: SkillGraphService = Depends(get_skill_service),
) -> TransitiveInferResponse:
    """Propagates credit from demonstrated high-tier skills backwards to prerequisite ancestors using distance decay."""
    inferred_results = svc.propagate_transitive_credit(
        demonstrated_skills=req.demonstrated_skills,
        decay_factor=req.decay_factor,
    )

    mastery_map: dict[str, InferredSkillCredit] = {}
    direct_count = 0
    inferred_count = 0

    for sid, data in inferred_results.items():
        if data["is_inferred"]:
            inferred_count += 1
        else:
            direct_count += 1
        mastery_map[sid] = InferredSkillCredit(
            score=data["score"],
            confidence=data["confidence"],
            is_inferred=data["is_inferred"],
            source=data["source"],
            tier=data["tier"],
        )

    return TransitiveInferResponse(
        mastery_map=mastery_map,
        total_skills_credited=len(mastery_map),
        directly_demonstrated_count=direct_count,
        transitively_inferred_count=inferred_count,
    )


@router.post("/role-alignment", response_model=RoleAlignmentResponse)
async def evaluate_role_alignment(
    req: RoleAlignmentRequest,
    svc: SkillGraphService = Depends(get_skill_service),
) -> RoleAlignmentResponse:
    """Evaluates candidate skill mastery profile against an enterprise role archetype."""
    eval_data = svc.evaluate_role_alignment(
        candidate_mastery=req.candidate_mastery,
        role_key=req.role_key,
    )

    verified = [
        RoleSkillStatus(
            skill_id=s["skill_id"],
            name=s["name"],
            tier=s["tier"],
            score=s["score"],
        )
        for s in eval_data["verified_skills"]
    ]

    missing = [
        RoleSkillStatus(
            skill_id=s["skill_id"],
            name=s["name"],
            tier=s["tier"],
            score=s["score"],
            delta_needed=s.get("delta_needed"),
        )
        for s in eval_data["missing_skills"]
    ]

    return RoleAlignmentResponse(
        role_key=eval_data["role_key"],
        role_title=eval_data["role_title"],
        department=eval_data["department"],
        coverage_percentage=eval_data["coverage_percentage"],
        composite_readiness=eval_data["composite_readiness"],
        role_passing_threshold=eval_data["role_passing_threshold"],
        verdict=eval_data["verdict"],
        verified_skills_count=eval_data["verified_skills_count"],
        missing_skills_count=eval_data["missing_skills_count"],
        verified_skills=verified,
        missing_skills=missing,
        prioritized_learning_sequence=eval_data["prioritized_learning_sequence"],
    )
