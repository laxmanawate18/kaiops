// API Constants and Type Definitions for KaiOPS UI
// Converted from TypeScript enums to JavaScript constants

export const UserRole = {
  USER: "user",
  ADMIN: "admin",
  TEAM_LEAD: "team_lead"
}

export const ApplicationType = {
  LOG_ANALYZER: "log_analyzer",
  INCIDENT_MANAGER: "incident_manager",
  MONITORING_DASHBOARD: "monitoring_dashboard",
  ALERT_SYSTEM: "alert_system",
  DEPLOYMENT_PIPELINE: "deployment_pipeline"
}

export const AgentType = {
  OBSERVABILITY_AGENT: "observability_agent",
  SECURITY_AGENT: "security_agent",
  DEPLOYMENT_AGENT: "deployment_agent",
  COST_AGENT: "cost_agent",
  METADATA_AGENT: "metadata_agent",
  SYNTHESIZER_AGENT: "synthesizer_agent",
  GITHUB_AGENT: "github_agent",
  CUSTOM_AGENT: "custom_agent"
}

export const AgentPriority = {
  PRIMARY: "primary",
  SECONDARY: "secondary"
}

export const PermissionType = {
  READ: "read",
  WRITE: "write",
  EXECUTE: "execute",
  ADMIN: "admin"
}

export const FeedbackType = {
  THUMBS_UP: "thumbs_up",
  THUMBS_DOWN: "thumbs_down",
  COPY: "copy",
  REWRITE: "rewrite"
}

export const FeedbackStatus = {
  PENDING: "pending",
  APPROVED: "approved",
  DENIED: "denied",
  RECLASSIFIED: "reclassified"
}

export const FeedbackCategory = {
  ACCURACY: "accuracy",
  RELEVANCE: "relevance",
  HELPFULNESS: "helpfulness",
  TONE: "tone",
  COMPLETENESS: "completeness",
  SAFETY: "safety",
  OTHER: "other"
}

export const DatasetType = {
  TRAINING: "training",
  EVALUATION: "evaluation",
  BOTH: "both"
}

// API Base URL
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
