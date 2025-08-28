"""
Schemas module for BeSunny.ai Python backend.
Defines all data models and schemas for the application.
"""

# Core schemas
from .user import User, UserCreate, UserUpdate, UserResponse
from .project import Project, ProjectCreate, ProjectUpdate, ProjectListResponse
from .document import (
    Document, DocumentCreate, DocumentUpdate, DocumentListResponse,
    DocumentSearchRequest, DocumentSearchResponse, DocumentBatchUpdateRequest,
    DocumentBatchUpdateResponse, DocumentImportRequest, DocumentImportResponse,
    DocumentChunk, DocumentChunkResponse, AIProcessingResult,
    VectorSearchRequest, VectorSearchResponse,
    DocumentType, DocumentStatus, ClassificationSource, DocumentMetadata
)
from .email import EmailListResponse
from .drive import DriveFile
from .calendar import (
    Meeting, MeetingListResponse,
    CalendarEvent
)

# AI Service schemas
# Note: These imports are commented out as they cause circular import issues
# from ..services.ai.ai_service import AIProcessingResult as AIServiceResult
# from ..services.ai.embedding_service import (
#     EmbeddingResult, VectorSearchResult, DocumentChunk as EmbeddingDocumentChunk
# )
# from ..services.ai.meeting_intelligence_service import (
#     MeetingTranscript, MeetingIntelligenceResult, ActionItem, AttendeeBotConfig,
#     TranscriptSegment, MeetingSummary
# )

# Classification schemas
from .classification import (
    ClassificationRequest, ClassificationResult, BatchClassificationRequest, BatchClassificationResult,
    ClassificationHistory, ClassificationMetrics, ClassificationPriority, ClassificationWorkflow
)

# Enterprise schemas - Phase 4
from .enterprise import (
    # Multi-tenancy
    TenantBase, TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    TenantTier, TenantStatus,
    
    # Billing
    BillingPlanBase, BillingPlanCreate, BillingPlanUpdate, BillingPlanResponse,
    SubscriptionBase, SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse,
    BillingProvider,
    
    # Usage tracking
    UsageRecordBase, UsageRecordCreate, UsageRecordResponse, UsageSummary, UsageSummaryResponse,
    UsageMetric,
    
    # Audit logging
    AuditLogBase, AuditLogCreate, AuditLogResponse, AuditLogListResponse, AuditAction,
    
    # Compliance
    ComplianceReportBase, ComplianceReportCreate, ComplianceReportUpdate, ComplianceReportResponse,
    ComplianceReportListResponse, ComplianceStandard,
    
    # Business Intelligence
    BIDashboardBase, BIDashboardCreate, BIDashboardUpdate, BIDashboardResponse, BIDashboardListResponse,
    
    # Workflow Automation
    WorkflowDefinitionBase, WorkflowDefinitionCreate, WorkflowDefinitionUpdate, WorkflowDefinitionResponse,
    WorkflowDefinitionListResponse, WorkflowExecutionBase, WorkflowExecutionCreate, WorkflowExecutionUpdate,
    WorkflowExecutionResponse, WorkflowExecutionListResponse,
    
    # Business Rules Engine
    BusinessRuleBase, BusinessRuleCreate, BusinessRuleUpdate, BusinessRuleResponse, BusinessRuleListResponse,
    
    # Analytics
    AnalyticsQueryBase, AnalyticsQueryCreate, AnalyticsQueryResponse,
    
    # Predictive Analytics
    MLModelBase, MLModelCreate, MLModelUpdate, MLModelResponse, MLModelListResponse
)

__all__ = [
    # Core schemas
    "User", "UserCreate", "UserUpdate", "UserResponse",
    "Project", "ProjectCreate", "ProjectUpdate", "ProjectListResponse",
    "Document", "DocumentCreate", "DocumentUpdate", "DocumentListResponse",
    "DocumentSearchRequest", "DocumentSearchResponse", "DocumentBatchUpdateRequest",
    "DocumentBatchUpdateResponse", "DocumentImportRequest", "DocumentImportResponse",
    "DocumentChunk", "DocumentChunkResponse", "AIProcessingResult",
    "VectorSearchRequest", "VectorSearchResponse",
    "DocumentType", "DocumentStatus", "ClassificationSource", "DocumentMetadata",
    "EmailListResponse",
    "DriveFile",
    "Meeting", "MeetingListResponse",
    "CalendarEvent",
    
    # AI Service schemas
    # Note: These are commented out due to circular import issues
    # "AIServiceResult",
    # "EmbeddingResult", "VectorSearchResult", "EmbeddingDocumentChunk",
    # "MeetingTranscript", "MeetingIntelligenceResult", "ActionItem", "AttendeeBotConfig",
    # "TranscriptSegment", "MeetingSummary",
    
    # Classification schemas
    "ClassificationRequest", "ClassificationResult", "BatchClassificationRequest", "BatchClassificationResult",
    "ClassificationHistory", "ClassificationMetrics", "ClassificationPriority", "ClassificationWorkflow",
    
    # Enterprise schemas - Phase 4
    "TenantBase", "TenantCreate", "TenantUpdate", "TenantResponse", "TenantListResponse",
    "TenantTier", "TenantStatus",
    "BillingPlanBase", "BillingPlanCreate", "BillingPlanUpdate", "BillingPlanResponse",
    "SubscriptionBase", "SubscriptionCreate", "SubscriptionUpdate", "SubscriptionResponse",
    "BillingProvider",
    "UsageRecordBase", "UsageRecordCreate", "UsageRecordResponse", "UsageSummary", "UsageSummaryResponse",
    "UsageMetric",
    "AuditLogBase", "AuditLogCreate", "AuditLogResponse", "AuditLogListResponse", "AuditAction",
    "ComplianceReportBase", "ComplianceReportCreate", "ComplianceReportUpdate", "ComplianceReportResponse",
    "ComplianceReportListResponse", "ComplianceStandard",
    "BIDashboardBase", "BIDashboardCreate", "BIDashboardUpdate", "BIDashboardResponse", "BIDashboardListResponse",
    "WorkflowDefinitionBase", "WorkflowDefinitionCreate", "WorkflowDefinitionUpdate", "WorkflowDefinitionResponse",
    "WorkflowDefinitionListResponse", "WorkflowExecutionBase", "WorkflowExecutionCreate", "WorkflowExecutionUpdate",
    "WorkflowExecutionResponse", "WorkflowExecutionListResponse",
    "BusinessRuleBase", "BusinessRuleCreate", "BusinessRuleUpdate", "BusinessRuleResponse", "BusinessRuleListResponse",
    "AnalyticsQueryBase", "AnalyticsQueryCreate", "AnalyticsQueryResponse",
    "MLModelBase", "MLModelCreate", "MLModelUpdate", "MLModelResponse", "MLModelListResponse"
]
