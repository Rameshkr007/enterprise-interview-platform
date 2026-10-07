// ── Common API Envelopes ──────────────────────────────────────────────────────
export interface ApiMeta {
  request_id?: string
  timestamp: string
  processing_ms?: number
}

export interface ApiErrorDetail {
  code: string
  message: string
  details?: unknown
  request_id?: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: ApiErrorDetail
  meta: ApiMeta
}

// ── Auth & Tenancy ───────────────────────────────────────────────────────────
export type UserRole =
  | 'candidate'
  | 'recruiter'
  | 'interviewer'
  | 'org_admin'
  | 'platform_admin'

export type OrganizationTier = 'free' | 'starter' | 'growth' | 'enterprise'

export interface Organization {
  id: string
  name: string
  slug: string
  tier: OrganizationTier
  is_active: boolean
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  org_id?: string | null
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface AuditLog {
  id: string
  org_id?: string | null
  user_id?: string | null
  action: string
  entity_type: string
  entity_id?: string | null
  ip_address?: string | null
  user_agent?: string | null
  payload: Record<string, unknown>
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// ── ATS ───────────────────────────────────────────────────────────────────────
export interface SkillGap {
  skill_name: string
  gap_type: 'missing' | 'partial'
  jd_importance: number
  semantic_distance: number
  suggested_courses: string[]
}

export interface MatchedSkill {
  skill_name: string
  resume_evidence: string
  confidence: number
}

export interface AtsAnalysisResult {
  id: string
  resume_id: string
  jd_id: string
  cosine_similarity: number
  match_tier: 'poor' | 'fair' | 'good' | 'excellent'
  recommendation: 'APPLY' | 'IMPROVE_THEN_APPLY' | 'LOW_PRIORITY'
  technical_score: number
  experience_score: number
  education_score: number
  project_score: number
  seniority_fit: string
  overall_score: number
  skill_gaps: SkillGap[]
  matched_skills: MatchedSkill[]
  skill_gap_details?: unknown[]
  section_scores: Record<string, number>
  explainable_summary: string
  created_at: string
}

export interface JobMatchSummary {
  jd_id: string
  title: string
  company?: string | null
  overall_score: number
  recommendation: 'APPLY' | 'IMPROVE_THEN_APPLY' | 'LOW_PRIORITY'
  match_tier: 'poor' | 'fair' | 'good' | 'excellent'
  technical_score: number
  seniority_fit: string
  critical_gaps: string[]
  key_strengths: string[]
}

// ── Interview ─────────────────────────────────────────────────────────────────
export interface AnswerEvaluationResult {
  technical_accuracy: number
  concept_understanding: number
  problem_solving: number
  relevance: number
  completeness: number
  communication: number
  structure: number
  clarity: number
  overall_score: number
  strengths: string[]
  weaknesses: string[]
  evidence: string[]
  recommended_follow_up: string
}

export interface InterviewPlanItem {
  topic: string
  category: string
  priority: number
  rationale: string
  target_difficulty: string
  status: string
}

export interface TopicMasteryItem {
  topic: string
  score: number
  turns_count: number
  status: string
}

export interface FinalEvaluationSummary {
  overall_score: number
  hiring_recommendation: string
  summary: string
  key_strengths: string[]
  growth_areas: string[]
  topic_scores: Record<string, number>
  total_turns: number
}

export interface InterviewSession {
  id: string
  user_id: string
  org_id?: string | null
  status: 'pending' | 'active' | 'completed' | 'error'
  current_difficulty: 'easy' | 'medium' | 'hard' | 'expert'
  current_topic?: string | null
  current_question_index: number
  target_question_count: number
  langgraph_thread_id: string | null
  aggregate_score: number | null
  started_at: string | null
  completed_at?: string | null
  created_at: string
}

export interface TurnResponse {
  id: string
  session_id: string
  turn_index: number
  question_text: string
  question_category: string
  question_difficulty: string
  question_rationale?: string | null
  raw_transcript?: string | null
  audio_metrics?: Record<string, unknown> | null
  eval_scores?: AnswerEvaluationResult | Record<string, unknown> | null
  eval_feedback?: string | null
  created_at: string
}

export interface NextQuestionResponse {
  question_text: string
  category: string
  difficulty: string
  rationale: string
  turn_index: number
  is_complete: boolean
  evaluation?: AnswerEvaluationResult | null
  topic_mastery?: Record<string, TopicMasteryItem> | null
  final_summary?: FinalEvaluationSummary | null
}

export interface SessionStateResponse {
  session_id: string
  status: string
  current_turn: number
  target_question_count: number
  current_difficulty: string
  current_topic?: string | null
  interview_plan: InterviewPlanItem[]
  topic_mastery: Record<string, TopicMasteryItem>
  candidate_strengths: string[]
  candidate_weaknesses: string[]
  last_question?: string | null
  last_evaluation?: AnswerEvaluationResult | null
  all_turn_scores: number[]
  is_complete: boolean
  final_summary?: FinalEvaluationSummary | null
}

// ── WebSocket Messages ─────────────────────────────────────────────────────────
export type WsMessageType =
  | 'auth'
  | 'ping'
  | 'pong'
  | 'reconnect'
  | 'session_recovered'
  | 'audio_chunk'
  | 'audio_end'
  | 'text_answer'
  | 'partial_transcript'
  | 'final_transcript'
  | 'question'
  | 'warning'
  | 'error'
  | 'complete'

export interface WsMessage {
  type: WsMessageType
  payload: Record<string, unknown>
}

export interface QuestionPayload {
  text: string
  turn_index: number
  difficulty: string
  category: string
  rationale?: string
  transcript?: string
  audio_metrics?: AudioMetrics
  evaluation?: AnswerEvaluationResult
  topic_mastery?: Record<string, TopicMasteryItem>
}

export interface AudioMetrics {
  duration_s: number
  speaking_duration_s: number
  silence_duration_s: number
  silence_intervals: number[][]
  silence_count: number
  silence_ratio: number
  average_pause_s: number
  longest_pause_s: number
  pitch_mean_hz: number
  pitch_std_hz: number
  pitch_variance_score: number
  speech_rate_wpm: number
  energy_mean: number
  energy_std: number
  speech_stability: number
  clarity_score: number
  filler_words: Array<{ word: string; count: number; positions: number[] }>
  filler_count: number
  filler_ratio: number
  filler_word_rate: number
  filler_trend: 'improving' | 'stable' | 'degrading'
}

// ── Report ────────────────────────────────────────────────────────────────────
export interface SessionReport {
  id: string
  session_id: string
  user_id: string
  final_score: number
  percentile_rank: number | null
  overall_audio_metrics: {
    avg_silence_ratio: number
    avg_pitch_variance_score: number
    avg_filler_rate: number
    avg_speech_rate_wpm: number
    confidence_score: number
  }
  category_scores: Record<string, number>
  difficulty_progression: Array<{
    turn_index: number
    difficulty: string
    composite_score: number | null
  }>
  skill_coverage_delta: unknown[]
  strengths: string[]
  improvement_areas: string[]
  recommended_resources: unknown[]
  generated_at: string
}

// ── API Error ─────────────────────────────────────────────────────────────────
export interface ApiError {
  error_code: string
  message: string
  details?: unknown
}

// ── Resume Intelligence & Parsing ──────────────────────────────────────────────
export interface ResumeSection {
  id: string
  resume_id: string
  section_type: string
  heading: string
  content: string
  sequence_order: number
  created_at: string
}

export interface ResumeChunk {
  id: string
  resume_id: string
  section_id?: string | null
  chunk_index: number
  chunk_text: string
  token_count: number
  metadata_: Record<string, unknown>
  created_at: string
}

export interface CandidateSkill {
  id: string
  resume_id: string
  user_id: string
  skill_name: string
  normalized_name: string
  category: string
  confidence: number
  years_experience?: number | null
  proficiency_level: string
  evidence_text: string
  created_at: string
}

export interface ResumeUploadResponse {
  resume_id: string
  file_name: string
  word_count: number
  section_count: number
  chunk_count: number
  skill_count: number
  status: string
}

export interface ParsedResumeDetail {
  id: string
  user_id: string
  file_name: string
  s3_key: string
  parsed_text: string
  structured_data: Record<string, unknown>
  parsing_status: string
  created_at: string
  sections: ResumeSection[]
  chunks: ResumeChunk[]
  skills: CandidateSkill[]
}

export interface CandidateSkillProfile {
  resume_id: string
  user_id: string
  total_skills: number
  skills_by_category: Record<string, CandidateSkill[]>
  top_skills: CandidateSkill[]
}

// ── Phase 7: Specialized Interview Engines ────────────────────────────────────

// 1. Coding Interview & Sandbox
export interface TestCaseResult {
  test_index: number
  is_public: boolean
  passed: boolean
  input_repr: string
  expected_repr: string
  actual_repr?: string | null
  execution_time_ms: number
  error?: string | null
  stdout?: string
}

export interface StaticAnalysisMetrics {
  estimated_time_complexity: string
  estimated_space_complexity: string
  cyclomatic_complexity: number
  lines_of_code: number
  quality_score: number
  suggestions: string[]
}

export interface SandboxExecutionResult {
  success: boolean
  total_tests: number
  passed_tests: number
  failed_tests: number
  pass_rate: number
  total_execution_time_ms: number
  test_results: TestCaseResult[]
  static_analysis: StaticAnalysisMetrics
  security_passed: boolean
  error?: string | null
}

// 2. System Design Architecture Evaluation
export interface ArchitecturePillarScore {
  pillar_name: string
  score: number
  weight: number
  strengths: string[]
  weaknesses: string[]
  critical_missing_elements: string[]
}

export interface BuzzwordAnalysis {
  total_buzzwords_detected: number
  justified_buzzwords: string[]
  unjustified_buzzwords: Array<{ buzzword: string; advice: string; missing_context: string }>
  buzzword_density_score: number
  penalty_applied: number
}

export interface SystemDesignEvaluation {
  overall_score: number
  tier: string
  pillar_scores: Record<string, ArchitecturePillarScore>
  buzzword_analysis: BuzzwordAnalysis
  single_points_of_failure: string[]
  bottlenecks: string[]
  scale_readiness: string
  key_tradeoffs: string[]
  recommendation: string
}

// 3. Behavioral STAR Evaluation
export interface STARElement {
  name: 'Situation' | 'Task' | 'Action' | 'Result' | 'Learning'
  content: string
  score: number
  clarity: number
  feedback: string
  key_phrases: string[]
}

export interface OwnershipMetrics {
  i_count: number
  we_count: number
  i_we_ratio: number
  ownership_level: string
  explanation: string
}

export interface BehavioralFlag {
  flag_type: string
  severity: 'critical' | 'warning' | 'info'
  description: string
  recommendation: string
}

export interface STARBehavioralEvaluation {
  overall_score: number
  star_breakdown: Record<string, STARElement>
  ownership_metrics: OwnershipMetrics
  flags: BehavioralFlag[]
  quantifiable_metrics_found: string[]
  competency_scores: Record<string, number>
  strengths: string[]
  improvement_areas: string[]
  bar_raiser_verdict: string
  actionable_reframe: string
}

// ── Phase 8: Learning Engine, Candidate AI Twin & Recruiter Copilot ───────────

// Feature 12: Personalized Learning Engine
export interface LearningResource {
  title: string
  type: 'article' | 'documentation' | 'video' | 'paper'
  estimated_minutes: number
  ref: string
}

export interface LearningPracticeTask {
  task_name: string
  instructions: string
  type: string
}

export interface LearningDaySchedule {
  day: number
  theme: string
  objectives: string[]
  reading_resources: LearningResource[]
  practice_tasks: LearningPracticeTask[]
  is_completed: boolean
  completed_at: string | null
}

export interface ReassessmentQuizItem {
  id: number
  question: string
  rubric: string
  max_points: number
}

export interface LearningPlan {
  id: string
  user_id: string
  title: string
  detected_gap: string
  source_session_id?: string | null
  category: string
  status: 'active' | 'completed' | 'paused' | 'abandoned'
  target_completion_days: number
  current_day: number
  daily_schedule: LearningDaySchedule[]
  reassessment_quiz: ReassessmentQuizItem[]
  reassessment_score?: number | null
  reassessment_passed?: boolean | null
  created_at: string
  updated_at: string
}

export interface ReassessmentResult {
  plan_id: string
  reassessment_score: number
  passed: boolean
  status: string
  feedback: Array<{
    question_id: number
    score: number
    max_score: number
    rubric_criterion?: string
  }>
  message: string
}

// Feature 13: Candidate AI Twin & Feature 16: Explainable AI
export interface TwinHistoryEvent {
  event_type: 'interview_session' | 'coding_submission' | 'sm2_retention' | 'plan_completed' | string
  event_id: string
  title: string
  score: number
  delta: number
  timestamp: string
  metadata?: Record<string, unknown>
}

export interface CohortPercentile {
  metric: string
  candidate_score: number
  percentile_rank: number
  cohort_mean: number
  cohort_top_quartile: number
}

export interface TwinBenchmark {
  user_id: string
  overall_percentile: number
  cohort_name: string
  metrics: CohortPercentile[]
  growth_velocity_status: 'accelerating' | 'steady' | 'plateauing' | 'regressing' | string
  generated_at: string
}

export interface CandidateTwin {
  id: string
  user_id: string
  overall_readiness_score: number
  technical_mastery: Record<string, any>
  communication_metrics: {
    avg_clarity: number
    avg_pace_wpm: number
    avg_filler_ratio: number
    avg_confidence: number
  }
  system_design_mastery: {
    overall_score: number
    anti_buzzword_discipline: number
    evaluations_count: number
  }
  coding_mastery: {
    overall_score: number
    pass_rate: number
    submissions_count: number
    average_cyclomatic: number
  }
  behavioral_mastery: {
    overall_score: number
    i_we_ownership_ratio: number
    evaluations_count: number
  }
  weak_areas: Array<{
    topic: string
    score: number
    severity: string
    evidence_turns: number
    status: string
  }>
  strong_areas: Array<{
    topic: string
    score: number
    confidence: number
  }>
  historical_trajectory: TwinHistoryEvent[]
  growth_velocity: number
  updated_at: string
}

export interface ExplainScoreResult {
  dimension: string
  assigned_score: number
  what_was_evaluated: string
  evidence_found: string[]
  score_rationale: string
  what_is_missing: string[]
  actionable_improvement_roadmap: string[]
  weights_breakdown?: Record<string, number>
  calibration_sample_size?: Record<string, number>
  projected_score_uplift?: number
}

// Feature 14: Recruiter Copilot
export interface RecruiterRequisition {
  id: string
  org_id?: string | null
  created_by: string
  title: string
  department: string
  seniority_level: string
  description: string
  required_skills: string[]
  rubric_weights: Record<string, number>
  hiring_threshold: number
  status: 'draft' | 'active' | 'paused' | 'closed'
  created_at: string
  updated_at: string
}

export interface RequisitionCandidate {
  id: string
  requisition_id: string
  candidate_id: string
  status: 'invited' | 'in_progress' | 'interviewed' | 'review_required' | 'offer' | 'rejected'
  stage_evaluations: Record<string, number>
  composite_score?: number | null
  hiring_recommendation?: string | null
  evidence_summary?: {
    role_title: string
    composite_score: number
    hiring_threshold: number
    skill_match_percentage: number
    verified_skills: string[]
    missing_skills: string[]
    growth_velocity: number
    modalities: Record<string, number>
    recommendation: string
    copilot_narrative: string
  } | null
  recruiter_notes?: string | null
  invited_at: string
  updated_at: string
}

export interface CandidateComparisonMatrix {
  requisition_id: string
  role_title: string
  rubric_weights: Record<string, number>
  hiring_threshold: number
  total_compared: number
  top_candidate_id?: string | null

  matrix: Array<{
    candidate_id: string
    full_name: string
    email: string
    composite_score: number | null
    hiring_recommendation: string | null
    skill_match_percentage: number
    verified_skills: string[]
    missing_skills: string[]
    modalities: Record<string, number>
    communication: {
      confidence: number
      pace_wpm: number
      filler_ratio: number
    }
    growth_velocity: number
  }>
}

export interface TalentPoolMatch {
  candidate_id: string
  full_name: string
  email: string
  readiness_score: number
  skill_match_percentage: number
  verified_skills: string[]
  growth_velocity: number
}

// ── Phase 15: Recruiter Platform & Copilot ──────────────────────────────────
export type CandidateStage = 'invited' | 'in_progress' | 'interviewed' | 'review_required' | 'offer' | 'rejected'

export interface RequisitionUpdateRequest {
  title?: string
  department?: string
  seniority_level?: string
  description?: string
  required_skills?: string[]
  rubric_weights?: Record<string, number>
  hiring_threshold?: number
  status?: 'draft' | 'active' | 'paused' | 'closed'
}

export interface CandidateStageUpdateRequest {
  stage: CandidateStage
  recruiter_notes?: string
}

export interface RequisitionCalibration {
  requisition_id: string
  role_title: string
  current_threshold: number
  sample_size: number
  percentiles: {
    mean: number
    median: number
    p75: number
    p90: number
    min: number
    max: number
  }
  qualification_rate_pct: number
  current_qualified_count: number
  sensitivity_curve: Array<{
    threshold: number
    qualified_count: number
    qualification_rate_pct: number
  }>
}

export interface ExecutiveDebriefMemo {
  requisition_id: string
  candidate_id: string
  candidate_name: string
  role_title: string
  composite_score: number
  hiring_recommendation: string
  generated_at: string
  memo_markdown: string
  modality_evidence: {
    rubric_weights?: Record<string, number>
    modalities?: Record<string, number>
    verified_skills?: string[]
    missing_skills?: string[]
    skill_match_pct?: number
    growth_velocity?: number
    sm2_retention_score?: number
    dag_skills_verified?: number
  }
}

// ── Phase 9: Production Observability, AI Governance & Enterprise Analytics ───

export interface AIUsageSummary {
  total_calls: number
  total_prompt_tokens: number
  total_completion_tokens: number
  total_tokens: number
  total_estimated_cost_usd: number
  by_tier: Record<string, { calls: number; tokens: number; cost_usd: number }>
  by_operation: Record<string, { calls: number; tokens: number; cost_usd: number }>
}

export interface OrganizationBudgetStatus {
  id: string
  org_id: string
  monthly_budget_usd: number
  current_spend_usd: number
  remaining_budget_usd: number
  utilization_pct: number
  is_alert_triggered: boolean
  is_hard_limit_reached: boolean
  hard_limit_action: 'degrade_to_cheap' | 'block'
  billing_cycle_start: string
  updated_at: string
}

export interface CircuitBreakerStatus {
  name: string
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN'
  failure_count: number
  success_count: number
  failure_threshold: number
  recovery_timeout_s: number
  total_calls: number
  total_failures: number
  total_fallbacks: number
  bulkhead_concurrency_limit: number
  bulkhead_active_calls: number
  last_failure_time?: string | null
  last_state_change: string
}

export interface LatencyPercentiles {
  p50_ms: number
  p95_ms: number
  p99_ms: number
  avg_ms: number
  min_ms: number
  max_ms: number
  sample_count: number
}

export interface ObservabilityMetricsSummary {
  uptime_seconds: number
  total_requests: number
  total_errors: number
  global_error_rate_pct: number
  overall_latency: LatencyPercentiles
  by_endpoint_latency: Record<string, LatencyPercentiles>
  services_slo: Array<{
    service_name: string
    slo_target_pct: number
    actual_availability_pct: number
    error_budget_remaining_pct: number
    total_requests: number
    error_count: number
    burn_rate: number
  }>
}

export interface DeepHealthCheckResult {
  status: 'healthy' | 'degraded' | 'critical'
  app_version: string
  environment: string
  timestamp: string
  components: Record<string, { status: string; latency_ms: number; details?: string | null }>
}

export interface EnterpriseOverview {
  total_candidates: number
  active_requisitions: number
  completed_interviews: number
  overall_readiness_avg: number
  readiness_distribution: {
    needs_work_count: number
    progressing_count: number
    interview_ready_count: number
    bar_raiser_count: number
    total_candidates: number
  }
  domain_breakdown: Array<{
    domain: string
    average_score: number
    candidate_count: number
  }>
  avg_velocity_score: number
  hiring_recommendation_rate: number
}

export interface RecruiterFunnelMetrics {
  total_pipeline: number
  stages: Array<{
    stage: string
    count: number
    conversion_rate_pct: number
  }>
  avg_time_to_hire_days: number
  offer_acceptance_rate_pct: number
}

export interface SkillShortageAnalysis {
  total_candidates_analyzed: number
  shortages: Array<{
    skill_name: string
    gap_count: number
    severity: 'high' | 'medium' | 'low'
    percentage_of_pool: number
  }>
}

export interface LearningImpactMetrics {
  total_plans_generated: number
  completed_plans: number
  in_progress_plans: number
  completion_rate_pct: number
  avg_pre_reassessment_score: number
  avg_post_reassessment_score: number
  avg_score_improvement_pct: number
}

// ── Phase 16: Enterprise Analytics & Observability ──────────────────────────
export interface TalentSupplyDemandItem {
  skill_name: string
  candidate_supply_count: number
  requisition_demand_count: number
  supply_demand_ratio: number
  shortage_level: 'critical' | 'moderate' | 'balanced' | 'surplus'
  projected_time_to_fill_days: number
}

export interface TalentSupplyDemandResponse {
  total_skills_tracked: number
  critical_shortage_count: number
  skills: TalentSupplyDemandItem[]
}

export interface EnterpriseRoiMetrics {
  total_interviews_conducted: number
  recruiter_hours_saved: number
  cost_savings_usd: number
  ai_infrastructure_cost_usd: number
  net_roi_multiple: number
  avg_candidate_score_lift: number
  time_to_fill_reduction_pct: number
  department_metrics: Record<string, { interviews: number; time_to_fill_days: number; satisfaction_score: number }>
}

export interface SpanRecord {
  span_name: string
  service: string
  duration_ms: number
  status: 'ok' | 'error'
  metadata?: Record<string, any>
}

export interface TraceRecord {
  trace_id: string
  correlation_id: string
  root_endpoint: string
  total_duration_ms: number
  spans: SpanRecord[]
  status: 'ok' | 'error'
  timestamp: string
}

export interface TraceListResponse {
  total_traces: number
  traces: TraceRecord[]
}

export interface SystemAlertItem {
  id: string
  severity: 'critical' | 'warning' | 'info'
  rule: string
  title: string
  message: string
  metric_value: number
  threshold_value: number
  triggered_at: string
  acknowledged: boolean
  acknowledged_at?: string | null
}

export interface AlertListResponse {
  total_alerts: number
  active_count: number
  alerts: SystemAlertItem[]
}

export interface AlertAcknowledgeResponse {
  id: string
  acknowledged: boolean
  acknowledged_at: string
  message: string
}


// ── Phase 11: System Design & Behavioral Studio Types ─────────────────────────
export interface GraphComponentNode {
  id: string
  name: string
  type: string
  replicas?: number
  is_clustered?: boolean
}

export interface GraphConnection {
  from: string
  to: string
  protocol?: string
}

export interface ValidateGraphRequest {
  components: GraphComponentNode[]
  connections: GraphConnection[]
}

export interface ValidateGraphResponse {
  is_resilient: boolean
  resilience_score: number
  spof_nodes: string[]
  warnings: string[]
  redundancy_report: Record<string, { type: string; replicas: number; clustered: boolean }>
  recommendations: string[]
}

export interface CapacityEstimateRequest {
  scenario_key: string
  estimates: {
    read_qps?: number
    write_qps?: number
    daily_storage_gb?: number
    bandwidth_gbps?: number
    ram_cache_gb?: number
  }
}

export interface CapacityEstimateResponse {
  overall_accuracy_score: number
  rating: string
  benchmark_model: Record<string, unknown>
  metric_evaluations: Record<string, {
    metric: string
    candidate_estimate: number | null
    benchmark: number
    accuracy_score: number
    evaluation: string
  }>
  feedback: string[]
}

export interface ClarificationRequest {
  scenario_key: string
  question: string
}

export interface ClarificationResponse {
  scenario_key: string
  question: string
  answer: string
  bar_raiser_tips: string[]
}

export interface LeadershipCompetency {
  id: string
  framework: string
  title: string
  description: string
}

export interface BehavioralQuestion {
  id: string
  competency: string
  title: string
  question: string
  evaluation_criteria: string[]
}

export interface FollowUpProbe {
  probe_type: string
  question: string
  rationale: string
}

export interface FollowUpProbesResponse {
  question: string
  competency: string
  probes: FollowUpProbe[]
  weakest_area: string
}

export interface STARReframeResponse {
  competency: string
  original_word_count: number
  reframed_story: string
  key_enhancements: string[]
  bar_raiser_score_uplift: string
}

// ── Phase 12: Skill Graph & DAG Taxonomy Types ────────────────────────────────
export interface SkillNode {
  id: string
  name: string
  category: string
  tier: number // 1 to 5
  description: string
  prerequisites: string[]
  specializations: string[]
  complements: string[]
  equivalents: string[]
}

export interface SkillEdge {
  source: string
  target: string
  type: 'prerequisite' | 'specialization' | 'complementary' | 'equivalent' | string
}

export interface SkillGraphDag {
  nodes: SkillNode[]
  edges: SkillEdge[]
  total_nodes: number
  categories: string[]
  tiers: number[]
}

export interface MilestoneStep {
  step: number
  skill_id: string
  name: string
  tier: number
  category: string
  current_score: number
  target_score: number
  estimated_study_hours: number
  concept_summary: string
}

export interface PathwayPlan {
  target_skill_id: string
  target_skill_name: string
  total_milestones: number
  estimated_total_hours: number
  curriculum: MilestoneStep[]
}

export interface RootCauseDiagnosis {
  failed_skill: string
  failed_skill_name: string
  root_cause_skill_id: string
  root_cause_skill_name: string
  root_cause_tier: number
  candidate_score: number
  diagnosis: string
  remedy_sequence: string[]
}

export interface RootCauseGapReport {
  total_failed_skills: number
  root_causes: RootCauseDiagnosis[]
  all_unmastered_skills: string[]
  remediation_roadmap: string[]
}

export interface InferredCredit {
  score: number
  confidence: number
  is_inferred: boolean
  source: string
  tier: number
}

export interface TransitiveCreditReport {
  mastery_map: Record<string, InferredCredit>
  total_skills_credited: number
  directly_demonstrated_count: number
  transitively_inferred_count: number
}

export interface RoleSkillStatus {
  skill_id: string
  name: string
  tier: number
  score: number
  delta_needed?: number | null
}

export interface RoleAlignmentReport {
  role_key: string
  role_title: string
  department: string
  coverage_percentage: number
  composite_readiness: number
  role_passing_threshold: number
  verdict: string
  verified_skills_count: number
  missing_skills_count: number
  verified_skills: RoleSkillStatus[]
  missing_skills: RoleSkillStatus[]
  prioritized_learning_sequence: string[]
}

export interface RoleArchetype {
  role_key: string
  title: string
  department: string
  description: string
  target_skills: string[]
  passing_threshold: number
}

// ── Phase 13: SuperMemo-2 Spaced Repetition Types ────────────────────────────
export interface SpacedRepetitionCard {
  id: string
  user_id: string
  skill_id: string
  concept_key: string
  title: string
  question_prompt: string
  answer_explanation: string
  key_takeaway: string
  category: string
  tier: number
  repetition_count: number
  easiness_factor: number
  interval_days: number
  retention_score: number
  last_quality?: number | null
  last_reviewed_at?: string | null
  next_review_due: string
}

export interface SM2ReviewSubmit {
  card_id: string
  quality: number // 0 to 5
}

export interface SM2ReviewResult {
  card_id: string
  concept_key: string
  title: string
  quality: number
  repetition_count: number
  interval_days: number
  easiness_factor: number
  retention_score: number
  next_review_due: string
  mastery_boost_applied: number
}

export interface SM2DeckStats {
  total_cards: number
  due_today_count: number
  mature_cards_count: number
  young_cards_count: number
  new_cards_count: number
  average_retention_pct: number
  total_reviews_completed: number
  current_streak_days: number
}

// ── Phase 17: Security Hardening & Rate Limiting ────────────────────────────
export interface SecurityPostureResponse {
  status: string
  timestamp: string
  audit_ledger: {
    is_valid: boolean
    total_entries: number
    head_hash: string
  }
  rate_limiting: {
    engine_status: string
    algorithm: string
    default_limit_rpm: number
    window_seconds: number
    active_buckets_count: number
    route_throttles: Record<string, number>
  }
  pii_vault: {
    vault_entries_count: number
    supported_entities: string[]
    encryption_algorithm: string
  }
  prompt_guard: {
    firewall_status: string
    rules_loaded_count: number
    total_scans: number
    total_threats_blocked: number
    threats_by_category: Record<string, number>
  }
  security_headers: {
    hsts_enabled: boolean
    csp_enabled: boolean
    x_frame_options: string
    x_content_type_options: string
    permissions_policy: string
  }
}

export interface AuditLedgerEntry {
  id: string
  sequence: number
  action: string
  entity_type: string
  entity_id?: string | null
  user_id?: string | null
  created_at: string
  previous_hash: string
  entry_hash: string
  is_valid: boolean
}

export interface AuditLedgerListResponse {
  total_entries: number
  entries: AuditLedgerEntry[]
}

export interface AuditLedgerVerificationResponse {
  is_valid: boolean
  total_entries: number
  head_hash: string
  broken_at_entry_id?: string | null
  sequence?: number | null
  reason?: string | null
  verification_time_ms: number
  message: string
}

export interface PiiSanitizeRequest {
  text: string
  entity_types?: string[] | null
  reversible?: boolean
}

export interface PiiSanitizeResponse {
  sanitized_text: string
  entities_found_count: number
  entities_by_type: Record<string, number>
  surrogate_tokens: string[]
  reversible: boolean
}

export interface PiiRevealRequest {
  surrogate_tokens: string[]
  justification: string
}

export interface PiiRevealResponse {
  revealed_entities: Record<string, string>
  tokens_resolved_count: number
  justification: string
  revealed_at: string
}

export interface DetectedPattern {
  rule_id: string
  severity: string
  category: string
  matched_substring: string
  description: string
}

export interface PromptGuardScanRequest {
  prompt_text: string
  context_type?: string
}

export interface PromptGuardScanResponse {
  threat_level: 'safe' | 'suspicious' | 'blocked'
  risk_score: number
  is_safe: boolean
  detected_patterns: DetectedPattern[]
  sanitized_text: string
  details: string
}

export interface RateLimitStatusResponse {
  client_key: string
  limit: number
  remaining: number
  reset_seconds: number
  is_blocked: boolean
  route_rules: Record<string, number>
}

export interface RateLimitResetResponse {
  message: string
  client_key: string
  cleared: boolean
}

// Phase 18: Diagnostics & Master E2E Testing Studio
export interface SuiteResult {
  phase: number
  name: string
  file: string
  tier: string
  category: string
  passed: boolean
  exit_code: number
  duration_seconds: number
  timestamp: string
  log_snippet?: string | null
}

export interface DiagnosticsReportResponse {
  total_suites: number
  passed_count: number
  failed_count: number
  pass_rate_percentage: number
  last_run_timestamp: string | null
  is_fully_passing: boolean
  suites: SuiteResult[]
}

export interface ComponentHealthItem {
  name: string
  subsystem: string
  status: 'healthy' | 'degraded' | 'unhealthy' | string
  latency_ms: number
  details?: string | null
}

export interface SystemHealthMatrixResponse {
  overall_status: string
  timestamp: string
  components: ComponentHealthItem[]
  active_sre_alerts: number
  verified_audit_chain: boolean
}

export interface DiagnosticsRunResponse {
  phase: number
  suite_name: string
  file: string
  passed: boolean
  exit_code: number
  duration_seconds: number
  timestamp: string
  output_summary: string
}

// ── Phase 19: Performance Profiling & Caching ──────────────────────────────
export interface CacheNamespaceItem {
  namespace: string
  keys_count: number
  l2_ttl_default_seconds: number
}

export interface CacheStatsData {
  l1: {
    size: number
    max_items: number
    hits: number
    misses: number
    hit_ratio_pct: number
  }
  l2: {
    hits: number
    misses: number
    hit_ratio_pct: number
  }
  overall: {
    effective_hit_ratio_pct: number
    total_cache_hits: number
    total_cache_misses: number
  }
  semantic_llm_cache: {
    hits: number
    tokens_saved: number
    cost_saved_usd: number
  }
  namespaces: CacheNamespaceItem[]
}

export interface CachePurgeResult {
  cleared_keys_count: number
  namespace: string | null
  message: string
}

export interface SlowQueryRecord {
  statement: string
  fingerprint: string
  duration_ms: number
  is_slow: boolean
  is_n_plus_one: boolean
  timestamp: number
}

export interface NPlusOneAlert {
  fingerprint: string
  frequency: number
  statement: string
  recommendation: string
  timestamp: number
}

export interface FingerprintStat {
  fingerprint: string
  statement_sample: string
  call_count: number
  total_duration_ms: number
  min_duration_ms: number
  max_duration_ms: number
  avg_duration_ms: number
  is_slow: boolean
  is_n_plus_one: boolean
}

export interface SlowQueriesData {
  total_queries_executed: number
  total_duration_ms: number
  average_duration_ms: number
  slow_query_count: number
  n_plus_one_alerts_count: number
  slow_threshold_ms: number
  top_slow_queries: SlowQueryRecord[]
  top_fingerprints: FingerprintStat[]
  n_plus_one_warnings: NPlusOneAlert[]
}

export interface RouteLatencyItem {
  route: string
  request_count: number
  error_count: number
  error_rate_pct: number
  p50_ms: number
  p90_ms: number
  p95_ms: number
  p99_ms: number
  avg_ms: number
  min_ms: number
  max_ms: number
}

export interface EndpointMetricsData {
  total_endpoints_tracked: number
  metrics: RouteLatencyItem[]
}

export interface SyntheticBenchmarkResult {
  workload: string
  iterations: number
  cold_latency_avg_ms: number
  warm_latency_avg_ms: number
  speedup_multiplier: number
  operations_per_second: number
  cold_p99_ms: number
  warm_p99_ms: number
  message: string
}

// ── Phase 20: Production Packaging & Deployment Orchestration ───────────────
export interface ContainerStatus {
  service: string
  container_name: string
  status: 'running' | 'healthy' | 'stopped' | 'restarting' | 'degraded'
  image: string
  ports: string[]
  uptime: string
  cpu_percent: number
  memory_mb: number
}

export interface EnvironmentAuditItem {
  key: string
  value_masked: string
  is_secret: boolean
  is_set: boolean
  category: string
  description: string
}

export interface MigrationStatusItem {
  revision: string
  down_revision: string | null
  description: string
  is_applied: boolean
  is_head: boolean
  applied_at: string | null
}

export interface ServiceHealthProbe {
  service: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  latency_ms: number
  message: string
  details: Record<string, unknown>
}

export interface SystemResources {
  cpu_percent: number
  memory_total_mb: number
  memory_used_mb: number
  memory_percent: number
  disk_total_gb: number
  disk_free_gb: number
  disk_used_percent: number
}

export interface DeploymentHealthCheckResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  environment: string
  probes: ServiceHealthProbe[]
  system_resources: SystemResources
}

export interface DeploymentStatusResponse {
  app_name: string
  version: string
  environment: string
  debug_mode: boolean
  uptime_seconds: number
  started_at: string
  git_commit: string
  git_branch: string
  python_version: string
  platform: string
  maintenance_mode: boolean
  maintenance_reason: string | null
  current_migration_head: string
  migrations_applied_count: number
  containers: ContainerStatus[]
}

export interface MaintenanceModeToggleRequest {
  enabled: boolean
  reason?: string | null
}

export interface MaintenanceModeResponse {
  maintenance_mode: boolean
  reason: string | null
  updated_at: string
  toggled_by?: string | null
}
