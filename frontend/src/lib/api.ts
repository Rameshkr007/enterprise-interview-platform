import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import type {
  AtsAnalysisResult,
  InterviewSession,
  NextQuestionResponse,
  Organization,
  SessionReport,
  TokenResponse,
  User,
  ResumeUploadResponse,
  ParsedResumeDetail,
  CandidateSkillProfile,
  ResumeChunk,
  JobMatchSummary,
  SessionStateResponse,
  TurnResponse,
  LearningPlan,
  CandidateTwin,
  TwinHistoryEvent,
  TwinBenchmark,
  ExplainScoreResult,
  RecruiterRequisition,
  RequisitionCandidate,
  RequisitionUpdateRequest,
  CandidateStageUpdateRequest,
  RequisitionCalibration,
  ExecutiveDebriefMemo,
  CandidateComparisonMatrix,
  TalentPoolMatch,
  ObservabilityMetricsSummary,
  DeepHealthCheckResult,
  CircuitBreakerStatus,
  OrganizationBudgetStatus,
  AIUsageSummary,
  EnterpriseOverview,
  RecruiterFunnelMetrics,
  SkillShortageAnalysis,
  LearningImpactMetrics,
  TalentSupplyDemandResponse,
  EnterpriseRoiMetrics,
  TraceListResponse,
  TraceRecord,
  AlertListResponse,
  AlertAcknowledgeResponse,
  SystemDesignEvaluation,
  ValidateGraphRequest,
  ValidateGraphResponse,
  CapacityEstimateRequest,
  CapacityEstimateResponse,
  ClarificationRequest,
  ClarificationResponse,
  LeadershipCompetency,
  BehavioralQuestion,
  STARBehavioralEvaluation,
  FollowUpProbesResponse,
  STARReframeResponse,
  SkillNode,
  SkillGraphDag,
  PathwayPlan,
  RootCauseGapReport,
  TransitiveCreditReport,
  RoleAlignmentReport,
  RoleArchetype,
  SpacedRepetitionCard,
  SM2ReviewSubmit,
  SM2ReviewResult,
  SM2DeckStats,
  SecurityPostureResponse,
  AuditLedgerListResponse,
  AuditLedgerVerificationResponse,
  PiiSanitizeResponse,
  PiiRevealResponse,
  PromptGuardScanResponse,
  RateLimitStatusResponse,
  RateLimitResetResponse,
  DiagnosticsReportResponse,
  DiagnosticsRunResponse,
  SystemHealthMatrixResponse,
  CacheStatsData,
  CachePurgeResult,
  SlowQueriesData,
  EndpointMetricsData,
  SyntheticBenchmarkResult,
  ContainerStatus,
  EnvironmentAuditItem,
  MigrationStatusItem,
  ServiceHealthProbe,
  DeploymentHealthCheckResponse,
  DeploymentStatusResponse,
  MaintenanceModeResponse,
} from './types'

export function getBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return 'https://enterprise-interview-platform.onrender.com/api/v1'
  }
  return 'http://localhost:8000/api/v1'
}

const BASE_URL = getBaseUrl()

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

function createAxiosInstance(): AxiosInstance {
  const instance = axios.create({
    baseURL: BASE_URL,
    timeout: 30_000,
    headers: { 'Content-Type': 'application/json' },
  })

  instance.interceptors.request.use((config) => {
    config.baseURL = getBaseUrl()
    if (typeof window !== 'undefined' && config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  })

  instance.interceptors.response.use(
    (res) => res,
    async (err: AxiosError) => {
      const originalRequest = err.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined

      if (err.response?.status === 401 && originalRequest && !originalRequest._retry) {
        if (typeof window === 'undefined') {
          return Promise.reject(err)
        }

        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          return Promise.reject(err)
        }

        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject })
          })
            .then((token) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`
              }
              return instance(originalRequest)
            })
            .catch((queueErr) => Promise.reject(queueErr))
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
          const { data } = await axios.post<TokenResponse>(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })

          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
          }

          processQueue(null, data.access_token)
          return instance(originalRequest)
        } catch (refreshErr) {
          processQueue(refreshErr, null)
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          return Promise.reject(refreshErr)
        } finally {
          isRefreshing = false
        }
      }

      return Promise.reject(err)
    }
  )

  return instance
}

export const api = createAxiosInstance()

// ── Auth ───────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; full_name: string; password: string; role?: string; org_id?: string }) =>
    api.post<User>('/auth/register', data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post<TokenResponse>('/auth/login', data).then((r) => r.data),

  refresh: (refresh_token: string) =>
    axios.post<TokenResponse>(`${BASE_URL}/auth/refresh`, { refresh_token }).then((r) => r.data),

  logout: (refresh_token?: string) =>
    api.post<{ status: string }>('/auth/logout', { refresh_token }).then((r) => r.data),

  me: () => api.get<User>('/auth/me').then((r) => r.data),
}

// ── Organizations & Tenants ───────────────────────────────────────────────────
export const orgApi = {
  create: (data: { name: string; slug: string; tier?: string; settings?: Record<string, unknown> }) =>
    api.post<Organization>('/organizations', data).then((r) => r.data),

  getMe: () => api.get<Organization>('/organizations/me').then((r) => r.data),

  updateMe: (data: Partial<Organization>) =>
    api.patch<Organization>('/organizations/me', data).then((r) => r.data),

  getMembers: () => api.get<User[]>('/organizations/me/members').then((r) => r.data),

  inviteMember: (data: { email: string; full_name: string; role?: string }) =>
    api.post<User>('/organizations/me/invite', data).then((r) => r.data),
}

// ── ATS ───────────────────────────────────────────────────────────────────────
export const atsApi = {
  uploadResume: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api
      .post<{ resume_id: string; word_count: number }>('/ats/resume', form)
      .then((r) => r.data)
  },

  createJd: (data: { title: string; company?: string; raw_text: string }) =>
    api.post<{ jd_id: string }>('/ats/job-description', data).then((r) => r.data),

  analyze: (resume_id: string, jd_id: string) =>
    api.post<AtsAnalysisResult>('/ats/analyze', { resume_id, jd_id }).then((r) => r.data),

  getAnalysis: (id: string) =>
    api.get<AtsAnalysisResult>(`/ats/analysis/${id}`).then((r) => r.data),

  listJobs: () =>
    api.get<Array<{ id: string; title: string; company?: string; seniority_level: string; skills: string[] }>>('/ats/jobs').then((r) => r.data),

  multiMatch: (resume_id: string, jd_ids: string[]) =>
    api.post<JobMatchSummary[]>('/ats/multi-match', { resume_id, jd_ids }).then((r) => r.data),
}

// ── Interview ─────────────────────────────────────────────────────────────────
export const interviewApi = {
  createSession: (data: {
    resume_id?: string
    jd_id?: string
    ats_analysis_id?: string
    target_question_count?: number
    focus_categories?: string[]
    starting_difficulty?: 'easy' | 'medium' | 'hard' | 'expert'
    adaptive_mode?: boolean
  }) => api.post<InterviewSession>('/interview/session', data).then((r) => r.data),

  getSession: (id: string) =>
    api.get<InterviewSession>(`/interview/session/${id}`).then((r) => r.data),

  getSessions: () =>
    api.get<InterviewSession[]>('/interview/sessions').then((r) => r.data),

  getState: (id: string) =>
    api.get<SessionStateResponse>(`/interview/session/${id}/state`).then((r) => r.data),

  getTurns: (id: string) =>
    api.get<TurnResponse[]>(`/interview/session/${id}/turns`).then((r) => r.data),

  submitAnswer: (data: {
    session_id: string
    turn_index: number
    audio_bytes_b64?: string
    answer_text?: string
    language?: string
  }) => api.post<NextQuestionResponse>('/interview/answer', data).then((r) => r.data),

  finalizeSession: (id: string) =>
    api.post<InterviewSession>(`/interview/session/${id}/finalize`).then((r) => r.data),
}

// ── Reports ────────────────────────────────────────────────────────────────────
export const reportApi = {
  generate: (session_id: string) =>
    api.post<SessionReport>(`/reports/generate/${session_id}`).then((r) => r.data),

  getBySession: (session_id: string) =>
    api.get<SessionReport>(`/reports/session/${session_id}`).then((r) => r.data),

  getById: (report_id: string) =>
    api.get<SessionReport>(`/reports/${report_id}`).then((r) => r.data),
}

// ── Resume Intelligence & Parsing ──────────────────────────────────────────────
export const resumeIntelligenceApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api
      .post<ResumeUploadResponse>('/resumes/upload', form)
      .then((r) => r.data)
  },

  getMyResumes: () => api.get<ResumeUploadResponse[]>('/resumes/me').then((r) => r.data),

  getDetail: (resume_id: string) =>
    api.get<ParsedResumeDetail>(`/resumes/${resume_id}`).then((r) => r.data),

  getSkills: (resume_id: string) =>
    api.get<CandidateSkillProfile>(`/resumes/${resume_id}/skills`).then((r) => r.data),

  getChunks: (resume_id: string) =>
    api.get<ResumeChunk[]>(`/resumes/${resume_id}/chunks`).then((r) => r.data),
}

// ── Learning Engine (Feature 12) ──────────────────────────────────────────────
export const learningApi = {
  generatePlan: (data: { gap_id?: string; skill_name: string; target_role?: string }) =>
    api.post<LearningPlan>('/learning/plans/generate', data).then((r) => r.data),

  getMyPlans: () => api.get<LearningPlan[]>('/learning/plans/my').then((r) => r.data),

  getPlan: (id: string) => api.get<LearningPlan>(`/learning/plans/${id}`).then((r) => r.data),

  completeMilestone: (id: string, day: number) =>
    api.post<LearningPlan>(`/learning/plans/${id}/milestone/${day}`).then((r) => r.data),

  submitReassessment: (id: string, answers: Record<string, string>) =>
    api.post<{ reassessment_score: number; status: string; gap_resolved: boolean }>(
      `/learning/plans/${id}/reassess`,
      { answers }
    ).then((r) => r.data),
}

// ── Candidate AI Twin (Features 13, 14 & 16) ──────────────────────────────────
export const twinApi = {
  getMyTwin: () => api.get<CandidateTwin>('/twin/me').then((r) => r.data),

  syncTwin: () => api.post<CandidateTwin>('/twin/sync').then((r) => r.data),

  getHistory: (eventType?: string) =>
    api
      .get<TwinHistoryEvent[]>('/twin/history', {
        params: eventType ? { event_type: eventType } : {},
      })
      .then((r) => r.data),

  getBenchmarks: () => api.get<TwinBenchmark>('/twin/benchmarks').then((r) => r.data),

  getTwin: (user_id: string) => api.get<CandidateTwin>(`/candidate-twin/${user_id}`).then((r) => r.data),

  explainScore: (dimension: string) =>
    api.get<ExplainScoreResult>(`/twin/explain/${dimension}`).then((r) => r.data),
}

// ── Recruiter Copilot (Feature 14) ────────────────────────────────────────────
export const recruiterApi = {
  createRequisition: (data: {
    title: string
    department?: string
    seniority_level?: string
    description?: string
    required_skills?: string[]
    rubric_weights?: Record<string, number>
    hiring_threshold?: number
  }) => api.post<RecruiterRequisition>('/recruiter/requisitions', data).then((r) => r.data),

  getRequisitions: () => api.get<RecruiterRequisition[]>('/recruiter/requisitions').then((r) => r.data),

  inviteCandidate: (req_id: string, candidate_id: string) =>
    api.post<{ message: string }>(`/recruiter/requisitions/${req_id}/invite`, { candidate_id }).then((r) => r.data),

  evaluateCandidate: (req_id: string, candidate_id: string) =>
    api.post<{ score: number; recommendation: string; summary: string }>(
      `/recruiter/requisitions/${req_id}/evaluate/${candidate_id}`
    ).then((r) => r.data),

  compareCandidates: (req_id: string, candidate_ids?: string[]) =>
    api.post<CandidateComparisonMatrix>(`/recruiter/requisitions/${req_id}/compare`, { candidate_ids }).then((r) => r.data),

  getRequisition: (req_id: string) =>
    api.get<RecruiterRequisition>(`/recruiter/requisitions/${req_id}`).then((r) => r.data),

  updateRequisition: (req_id: string, data: RequisitionUpdateRequest) =>
    api.patch<RecruiterRequisition>(`/recruiter/requisitions/${req_id}`, data).then((r) => r.data),

  getCandidates: (req_id: string, stage?: string) =>
    api.get<RequisitionCandidate[]>(`/recruiter/requisitions/${req_id}/candidates`, {
      params: { stage },
    }).then((r) => r.data),

  updateCandidateStage: (req_id: string, candidate_id: string, data: CandidateStageUpdateRequest) =>
    api.patch<RequisitionCandidate>(`/recruiter/requisitions/${req_id}/candidates/${candidate_id}/stage`, data).then((r) => r.data),

  getCalibration: (req_id: string) =>
    api.get<RequisitionCalibration>(`/recruiter/requisitions/${req_id}/calibration`).then((r) => r.data),

  getDebriefMemo: (req_id: string, candidate_id: string) =>
    api.get<ExecutiveDebriefMemo>(`/recruiter/requisitions/${req_id}/debrief-memo/${candidate_id}`).then((r) => r.data),

  searchTalentPool: (min_readiness?: number, required_skills?: string[]) =>
    api.get<TalentPoolMatch[]>('/recruiter/talent-pool/search', {
      params: { min_readiness, required_skills: required_skills?.join(',') },
    }).then((r) => r.data),
}

// ── Observability & Resilience (Features 17 & 19) ─────────────────────────────
export const observabilityApi = {
  getMetricsSummary: () => api.get<ObservabilityMetricsSummary>('/observability/metrics/summary').then((r) => r.data),

  getDeepHealth: () => api.get<DeepHealthCheckResult>('/observability/health/deep').then((r) => r.data),

  getCircuitBreakers: () =>
    api.get<{ circuit_breakers: CircuitBreakerStatus[] }>('/resilience/circuit-breakers').then((r) => r.data),

  resetCircuitBreaker: (name: string) =>
    api.post<{ message: string }>(`/resilience/circuit-breakers/${name}/reset`).then((r) => r.data),

  tripCircuitBreaker: (name: string) =>
    api.post<{ message: string }>(`/resilience/circuit-breakers/${name}/trip`).then((r) => r.data),

  getTraces: (min_duration_ms?: number, status?: string) =>
    api.get<TraceListResponse>('/observability/traces', { params: { min_duration_ms, status } }).then((r) => r.data),

  getTraceById: (trace_id: string) =>
    api.get<TraceRecord>(`/observability/traces/${trace_id}`).then((r) => r.data),

  getAlerts: (only_active?: boolean) =>
    api.get<AlertListResponse>('/observability/alerts', { params: { only_active } }).then((r) => r.data),

  acknowledgeAlert: (alert_id: string) =>
    api.post<AlertAcknowledgeResponse>(`/observability/alerts/${alert_id}/acknowledge`).then((r) => r.data),

  getPrometheusMetrics: () =>
    api.get<string>('/observability/metrics/prometheus').then((r) => r.data),
}

// ── AI Governance & Cost Control (Feature 18) ─────────────────────────────────
export const governanceApi = {
  getPricing: () => api.get<{ pricing: Array<{ tier: string; recommended_model: string; prompt_per_1m_usd: number; completion_per_1m_usd: number; description: string }> }>('/ai-governance/pricing').then((r) => r.data),

  getMyUsage: () => api.get<AIUsageSummary>('/ai-governance/usage/my').then((r) => r.data),

  getOrgBudget: () => api.get<OrganizationBudgetStatus>('/ai-governance/budget').then((r) => r.data),

  updateOrgBudget: (data: { monthly_budget_usd: number; alert_threshold_pct?: number; hard_limit_action?: string }) =>
    api.post<OrganizationBudgetStatus>('/ai-governance/budget', data).then((r) => r.data),
}

// ── Enterprise Analytics (Feature 15) ─────────────────────────────────────────
export const enterpriseAnalyticsApi = {
  getOverview: () => api.get<EnterpriseOverview>('/analytics/enterprise/overview').then((r) => r.data),

  getFunnel: () => api.get<RecruiterFunnelMetrics>('/analytics/enterprise/recruiter-funnel').then((r) => r.data),

  getSkillShortages: () => api.get<SkillShortageAnalysis>('/analytics/enterprise/skill-shortages').then((r) => r.data),

  getLearningImpact: () => api.get<LearningImpactMetrics>('/analytics/enterprise/learning-impact').then((r) => r.data),

  getSupplyDemand: () => api.get<TalentSupplyDemandResponse>('/analytics/enterprise/supply-demand').then((r) => r.data),

  getRoiMetrics: () => api.get<EnterpriseRoiMetrics>('/analytics/enterprise/roi-metrics').then((r) => r.data),
}

export const systemDesignApi = {
  getScenarios: () =>
    api.get<Array<{ key: string; title: string; domain: string; prompt: string; target_scale: string; key_focus_areas: string[] }>>('/system-design/scenarios').then((r) => r.data),

  getPillars: () =>
    api.get<{ pillars: Array<{ id: string; name: string; weight: number }>; anti_buzzword_policy: string }>('/system-design/pillars').then((r) => r.data),

  createChallenge: (session_id: string, scenario_key?: string) =>
    api.post<{
      challenge_id: string
      session_id: string
      title: string
      domain: string
      prompt: string
      target_scale: string
      key_focus_areas: string[]
      template_sections: string[]
    }>('/system-design/challenge', { session_id, scenario_key }).then((r) => r.data),

  evaluate: (data: {
    session_id: string
    problem_title: string
    problem_prompt: string
    architecture_sections: Record<string, string>
    whiteboard_components?: Array<Record<string, unknown>>
  }) => api.post<SystemDesignEvaluation>('/system-design/evaluate', data).then((r) => r.data),

  validateGraph: (data: ValidateGraphRequest) =>
    api.post<ValidateGraphResponse>('/system-design/validate-graph', data).then((r) => r.data),

  estimateCapacity: (data: CapacityEstimateRequest) =>
    api.post<CapacityEstimateResponse>('/system-design/capacity-estimate', data).then((r) => r.data),

  askClarification: (data: ClarificationRequest) =>
    api.post<ClarificationResponse>('/system-design/clarify', data).then((r) => r.data),

  getScenarioDetail: (scenario_key: string) =>
    api.get<{ key: string; title: string; domain: string; prompt: string; target_scale: string; key_focus_areas: string[] }>(`/system-design/scenarios/${scenario_key}`).then((r) => r.data),
}

export const behavioralApi = {
  getCompetencies: () =>
    api.get<LeadershipCompetency[]>('/behavioral/competencies').then((r) => r.data),

  getQuestions: (competency?: string) =>
    api.get<BehavioralQuestion[]>('/behavioral/questions', { params: competency ? { competency } : {} }).then((r) => r.data),

  getQuestionDetail: (question_id: string) =>
    api.get<BehavioralQuestion>(`/behavioral/questions/${question_id}`).then((r) => r.data),

  evaluateSTAR: (data: {
    session_id?: string
    question: string
    answer_transcript: string
    competency: string
  }) => api.post<STARBehavioralEvaluation>('/behavioral/evaluate-star', data).then((r) => r.data),

  generateProbes: (data: {
    question: string
    answer_transcript: string
    competency: string
  }) => api.post<FollowUpProbesResponse>('/behavioral/follow-up-probes', data).then((r) => r.data),

  reframeStory: (data: {
    question: string
    raw_answer: string
    competency: string
  }) => api.post<STARReframeResponse>('/behavioral/reframe', data).then((r) => r.data),
}

export const skillGraphApi = {
  getNodes: (category?: string, tier?: number) =>
    api
      .get<SkillNode[]>('/skill-graph/nodes', {
        params: { ...(category ? { category } : {}), ...(tier ? { tier } : {}) },
      })
      .then((r) => r.data),

  getNode: (skillId: string) =>
    api.get<SkillNode>(`/skill-graph/nodes/${skillId}`).then((r) => r.data),

  getDag: () => api.get<SkillGraphDag>('/skill-graph/taxonomy/dag').then((r) => r.data),

  getRoles: () => api.get<RoleArchetype[]>('/skill-graph/roles').then((r) => r.data),

  getPathway: (targetSkillId: string, candidateMastery: Record<string, number> = {}) =>
    api
      .post<PathwayPlan>('/skill-graph/pathway', {
        target_skill_id: targetSkillId,
        candidate_mastery: candidateMastery,
      })
      .then((r) => r.data),

  getRootCauseGaps: (
    failedSkills: string[],
    candidateMastery: Record<string, number> = {},
    passingThreshold: number = 65.0
  ) =>
    api
      .post<RootCauseGapReport>('/skill-graph/root-cause-gap', {
        failed_skills: failedSkills,
        candidate_mastery: candidateMastery,
        passing_threshold: passingThreshold,
      })
      .then((r) => r.data),

  propagateTransitive: (
    demonstratedSkills: Record<string, number>,
    decayFactor: number = 0.85
  ) =>
    api
      .post<TransitiveCreditReport>('/skill-graph/transitive-infer', {
        demonstrated_skills: demonstratedSkills,
        decay_factor: decayFactor,
      })
      .then((r) => r.data),

  evaluateRoleAlignment: (
    roleKey: string = 'senior_backend_l5',
    candidateMastery: Record<string, number> = {}
  ) =>
    api
      .post<RoleAlignmentReport>('/skill-graph/role-alignment', {
        role_key: roleKey,
        candidate_mastery: candidateMastery,
      })
      .then((r) => r.data),
}

export const sm2LearningApi = {
  getDueCards: (limit: number = 20) =>
    api
      .get<SpacedRepetitionCard[]>('/learning/sm2/cards/due', { params: { limit } })
      .then((r) => r.data),

  submitReview: (data: SM2ReviewSubmit) =>
    api.post<SM2ReviewResult>('/learning/sm2/cards/review', data).then((r) => r.data),

  getStats: () => api.get<SM2DeckStats>('/learning/sm2/stats').then((r) => r.data),

  getDeck: (tier?: number, skillId?: string) =>
    api
      .get<SpacedRepetitionCard[]>('/learning/sm2/deck', {
        params: { ...(tier !== undefined ? { tier } : {}), ...(skillId ? { skill_id: skillId } : {}) },
      })
      .then((r) => r.data),

  getCardDetail: (cardId: string) =>
    api.get<SpacedRepetitionCard>(`/learning/sm2/cards/${cardId}`).then((r) => r.data),

  seedDeck: (skillIds?: string[]) =>
    api
      .post<{ cards_seeded: number; message: string }>('/learning/sm2/seed', {
        skill_ids: skillIds ?? null,
      })
      .then((r) => r.data),
}

// ── Phase 17: Security Hardening & Rate Limiting ────────────────────────────
export const securityApi = {
  getPosture: () => api.get<SecurityPostureResponse>('/security/posture').then((r) => r.data),

  verifyAuditLedger: (orgId?: string) =>
    api.post<AuditLedgerVerificationResponse>('/security/audit/verify', null, { params: { org_id: orgId } }).then((r) => r.data),

  getAuditLedger: (limit?: number) =>
    api.get<AuditLedgerListResponse>('/security/audit/ledger', { params: { limit } }).then((r) => r.data),

  sanitizePii: (text: string, reversible: boolean = true, entityTypes?: string[]) =>
    api.post<PiiSanitizeResponse>('/security/pii/sanitize', { text, reversible, entity_types: entityTypes }).then((r) => r.data),

  revealPii: (surrogateTokens: string[], justification: string) =>
    api.post<PiiRevealResponse>('/security/pii/reveal', { surrogate_tokens: surrogateTokens, justification }).then((r) => r.data),

  inspectPrompt: (promptText: string, contextType: string = 'candidate_response') =>
    api.post<PromptGuardScanResponse>('/security/prompt-guard/inspect', { prompt_text: promptText, context_type: contextType }).then((r) => r.data),

  getRateLimitStatus: (clientKey?: string) =>
    api.get<RateLimitStatusResponse>('/security/rate-limits/status', { params: { client_key: clientKey } }).then((r) => r.data),

  resetRateLimit: (clientKey: string) =>
    api.post<RateLimitResetResponse>('/security/rate-limits/reset', { client_key: clientKey }).then((r) => r.data),
}

// ── Phase 18: Diagnostics & Master E2E Testing Studio ────────────────────────
export const diagnosticsApi = {
  getSuites: () =>
    api.get<DiagnosticsReportResponse>('/diagnostics/suites').then((r) => r.data),

  runSuite: (phase?: number) =>
    api
      .post<DiagnosticsRunResponse>('/diagnostics/run', { phase: phase ?? null })
      .then((r) => r.data),

  getSystemHealth: () =>
    api.get<SystemHealthMatrixResponse>('/diagnostics/system-health').then((r) => r.data),
}

// ── Phase 19: Performance Profiling & Hierarchical Caching ─────────────────
export const performanceApi = {
  getCacheStats: () =>
    api.get<CacheStatsData>('/performance/cache/stats').then((r) => r.data),

  purgeCache: (namespace?: string, purgeAll: boolean = false) =>
    api
      .post<CachePurgeResult>('/performance/cache/purge', {
        namespace: namespace ?? null,
        purge_all: purgeAll,
      })
      .then((r) => r.data),

  getSlowQueries: () =>
    api.get<SlowQueriesData>('/performance/queries/slow').then((r) => r.data),

  resetQueryProfiler: () =>
    api.post<{ status: string; message: string }>('/performance/queries/reset').then((r) => r.data),

  getEndpointMetrics: () =>
    api.get<EndpointMetricsData>('/performance/endpoints/metrics').then((r) => r.data),

  runBenchmark: (iterations: number = 50, workload: string = 'cache_read') =>
    api
      .post<SyntheticBenchmarkResult>('/performance/benchmark/run', {
        iterations,
        workload,
      })
      .then((r) => r.data),
}

// ── Phase 20: Production Deployment & Orchestration ─────────────────────────
export const deploymentApi = {
  getStatus: () =>
    api.get<DeploymentStatusResponse>('/deployment/status').then((r) => r.data),

  getEnvAudit: () =>
    api.get<EnvironmentAuditItem[]>('/deployment/env-audit').then((r) => r.data),

  getMigrations: () =>
    api.get<MigrationStatusItem[]>('/deployment/migrations').then((r) => r.data),

  runHealthCheck: () =>
    api.post<DeploymentHealthCheckResponse>('/deployment/health-check').then((r) => r.data),

  toggleMaintenance: (enabled: boolean, reason?: string | null) =>
    api
      .post<MaintenanceModeResponse>('/deployment/maintenance', {
        enabled,
        reason: reason ?? null,
      })
      .then((r) => r.data),
}

export interface PaymentPlan {
  id: string
  name: string
  monthly_price: number
  yearly_price: number
  credits: number
  automations: number
  features: string[]
}

export interface CheckoutSessionData {
  session_id: string
  plan_id: string
  amount: number
  currency: string
  billing_cycle: string
  status: string
  checkout_url: string
  client_secret: string
}

export interface SubscriptionData {
  user_id: string
  tier: string
  credits_remaining: number
  credits_total: number
  billing_cycle: string
  status: string
  expires_at: string
  features: string[]
}

export const paymentApi = {
  getPlans: () =>
    api.get<{ plans: PaymentPlan[] }>('/payments/plans').then((r) => r.data.plans),

  createCheckoutSession: (data: {
    plan_id: string
    billing_cycle?: 'monthly' | 'yearly'
    payment_method?: 'card' | 'upi' | 'netbanking' | 'test'
    currency?: string
  }) => api.post<CheckoutSessionData>('/payments/create-checkout-session', data).then((r) => r.data),

  verifyPayment: (data: { session_id: string; payment_id?: string; signature?: string }) =>
    api.post<{ success: boolean; message: string; subscription: SubscriptionData }>('/payments/verify', data).then((r) => r.data),

  getSubscription: () =>
    api.get<SubscriptionData>('/payments/subscription').then((r) => r.data),

  askAssistant: (message: string) =>
    api.post<{ reply: string; suggested_action?: string; action_href?: string }>('/payments/assistant-chat', { message }).then((r) => r.data),
}







