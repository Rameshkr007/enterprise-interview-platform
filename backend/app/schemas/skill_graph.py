from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class SkillNodeResponse(BaseModel):
    id: str
    name: str
    category: str
    tier: int
    description: str
    prerequisites: list[str] = Field(default_factory=list)
    specializations: list[str] = Field(default_factory=list)
    complements: list[str] = Field(default_factory=list)
    equivalents: list[str] = Field(default_factory=list)


class SkillEdgeResponse(BaseModel):
    source: str
    target: str
    type: str  # "prerequisite" | "specialization" | "complementary" | "equivalent"


class SkillGraphDagResponse(BaseModel):
    nodes: list[SkillNodeResponse]
    edges: list[SkillEdgeResponse]
    total_nodes: int
    categories: list[str]
    tiers: list[int]


class PathwayRequest(BaseModel):
    target_skill_id: str
    candidate_mastery: dict[str, float] = Field(default_factory=dict)


class MilestoneStepResponse(BaseModel):
    step: int
    skill_id: str
    name: str
    tier: int
    category: str
    current_score: float
    target_score: float
    estimated_study_hours: int
    concept_summary: str


class PathwayResponse(BaseModel):
    target_skill_id: str
    target_skill_name: str
    total_milestones: int
    estimated_total_hours: int
    curriculum: list[MilestoneStepResponse]


class RootCauseGapRequest(BaseModel):
    failed_skills: list[str]
    candidate_mastery: dict[str, float] = Field(default_factory=dict)
    passing_threshold: float = Field(default=65.0, ge=0.0, le=100.0)


class RootCauseDiagnosis(BaseModel):
    failed_skill: str
    failed_skill_name: str
    root_cause_skill_id: str
    root_cause_skill_name: str
    root_cause_tier: int
    candidate_score: float
    diagnosis: str
    remedy_sequence: list[str]


class RootCauseGapResponse(BaseModel):
    total_failed_skills: int
    root_causes: list[RootCauseDiagnosis]
    all_unmastered_skills: list[str]
    remediation_roadmap: list[str]


class TransitiveInferRequest(BaseModel):
    demonstrated_skills: dict[str, float]
    decay_factor: float = Field(default=0.85, ge=0.1, le=1.0)


class InferredSkillCredit(BaseModel):
    score: float
    confidence: float
    is_inferred: bool
    source: str
    tier: int


class TransitiveInferResponse(BaseModel):
    mastery_map: dict[str, InferredSkillCredit]
    total_skills_credited: int
    directly_demonstrated_count: int
    transitively_inferred_count: int


class RoleAlignmentRequest(BaseModel):
    role_key: str = "senior_backend_l5"
    candidate_mastery: dict[str, float] = Field(default_factory=dict)


class RoleSkillStatus(BaseModel):
    skill_id: str
    name: str
    tier: int
    score: float
    delta_needed: float | None = None


class RoleAlignmentResponse(BaseModel):
    role_key: str
    role_title: str
    department: str
    coverage_percentage: float
    composite_readiness: float
    role_passing_threshold: float
    verdict: str
    verified_skills_count: int
    missing_skills_count: int
    verified_skills: list[RoleSkillStatus]
    missing_skills: list[RoleSkillStatus]
    prioritized_learning_sequence: list[str]
