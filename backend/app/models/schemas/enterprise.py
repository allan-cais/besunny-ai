"""
Enterprise schemas for Phase 4 features.
Includes multi-tenancy, billing, usage tracking, and enterprise capabilities.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal


class TenantTier(str, Enum):
    """Tenant subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class TenantStatus(str, Enum):
    """Tenant account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PENDING = "pending"
    TRIAL = "trial"


class BillingProvider(str, Enum):
    """Supported billing providers."""
    STRIPE = "stripe"
    CHARGEBEE = "chargebee"
    RECURLY = "recurly"
    CUSTOM = "custom"


class UsageMetric(str, Enum):
    """Usage metrics for tracking."""
    API_CALLS = "api_calls"
    DOCUMENT_PROCESSING = "document_processing"
    STORAGE_GB = "storage_gb"
    AI_MODEL_CALLS = "ai_model_calls"
    MEETING_TRANSCRIPTS = "meeting_transcripts"
    USER_SEATS = "user_seats"


class ComplianceStandard(str, Enum):
    """Compliance standards supported."""
    GDPR = "gdpr"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    ISO27001 = "iso27001"
    CCPA = "ccpa"


class AuditAction(str, Enum):
    """Audit log actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    ACCESS = "access"


# Base Models
class TenantBase(BaseModel):
    """Base tenant model."""
    name: str = Field(..., min_length=1, max_length=200)
    domain: Optional[str] = Field(None, max_length=255)
    tier: TenantTier = Field(default=TenantTier.FREE)
    status: TenantStatus = Field(default=TenantStatus.PENDING)
    max_users: int = Field(default=5, ge=1)
    max_projects: int = Field(default=10, ge=1)
    max_storage_gb: int = Field(default=10, ge=1)
    custom_branding: bool = Field(default=False)
    sso_enabled: bool = Field(default=False)
    compliance_standards: List[ComplianceStandard] = Field(default_factory=list)
    data_residency_region: str = Field(default="us-east-1")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TenantCreate(TenantBase):
    """Create tenant request."""
    admin_email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    admin_name: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=1)


class TenantUpdate(BaseModel):
    """Update tenant request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    domain: Optional[str] = Field(None, max_length=255)
    tier: Optional[TenantTier] = None
    status: Optional[TenantStatus] = None
    max_users: Optional[int] = Field(None, ge=1)
    max_projects: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[int] = Field(None, ge=1)
    custom_branding: Optional[bool] = None
    sso_enabled: Optional[bool] = None
    compliance_standards: Optional[List[ComplianceStandard]] = None
    data_residency_region: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantResponse(TenantBase):
    """Tenant response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    admin_user_id: str
    current_user_count: int
    current_project_count: int
    current_storage_gb: Decimal
    trial_ends_at: Optional[datetime]
    subscription_ends_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Billing Models
class BillingPlanBase(BaseModel):
    """Base billing plan model."""
    name: str = Field(..., min_length=1, max_length=100)
    tier: TenantTier
    price_monthly: Decimal = Field(..., ge=0)
    price_yearly: Decimal = Field(..., ge=0)
    features: List[str] = Field(default_factory=list)
    limits: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = Field(default=True)


class BillingPlanCreate(BillingPlanBase):
    """Create billing plan request."""
    pass


class BillingPlanUpdate(BaseModel):
    """Update billing plan request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price_monthly: Optional[Decimal] = Field(None, ge=0)
    price_yearly: Optional[Decimal] = Field(None, ge=0)
    features: Optional[List[str]] = None
    limits: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class BillingPlanResponse(BillingPlanBase):
    """Billing plan response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BillingPlanListResponse(BaseModel):
    """Response containing a list of billing plans."""
    plans: List[BillingPlanResponse]
    total_count: int
    limit: int
    offset: int


class SubscriptionBase(BaseModel):
    """Base subscription model."""
    tenant_id: str
    plan_id: str
    status: str = Field(..., pattern=r"^(active|canceled|past_due|unpaid|trialing)$")
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = Field(default=False)
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubscriptionCreate(SubscriptionBase):
    """Create subscription request."""
    pass


class SubscriptionUpdate(BaseModel):
    """Update subscription request."""
    status: Optional[str] = Field(None, pattern=r"^(active|canceled|past_due|unpaid|trialing)$")
    cancel_at_period_end: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionResponse(SubscriptionBase):
    """Subscription response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    plan: BillingPlanResponse
    
    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Response containing a list of subscriptions."""
    subscriptions: List[SubscriptionResponse]
    total_count: int
    limit: int
    offset: int


# Usage Tracking Models
class UsageRecordBase(BaseModel):
    """Base usage record model."""
    tenant_id: str
    metric: UsageMetric
    value: Decimal = Field(..., ge=0)
    unit: str = Field(..., min_length=1, max_length=20)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UsageRecordCreate(UsageRecordBase):
    """Create usage record request."""
    pass


class UsageRecordResponse(UsageRecordBase):
    """Usage record response model."""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    """Usage summary for a tenant."""
    tenant_id: str
    metric: UsageMetric
    total_value: Decimal
    unit: str
    period_start: datetime
    period_end: datetime
    daily_breakdown: List[Dict[str, Any]] = Field(default_factory=list)


# Audit Logging Models
class AuditLogBase(BaseModel):
    """Base audit log model."""
    tenant_id: str
    user_id: str
    action: AuditAction
    resource_type: str = Field(..., min_length=1, max_length=50)
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditLogCreate(AuditLogBase):
    """Create audit log request."""
    pass


class AuditLogResponse(AuditLogBase):
    """Audit log response model."""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Compliance Models
class ComplianceReportBase(BaseModel):
    """Base compliance report model."""
    tenant_id: str
    standard: ComplianceStandard
    report_type: str = Field(..., min_length=1, max_length=50)
    report_date: datetime
    status: str = Field(..., pattern=r"^(pass|fail|pending|in_progress)$")
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComplianceReportCreate(ComplianceReportBase):
    """Create compliance report request."""
    pass


class ComplianceReportUpdate(BaseModel):
    """Update compliance report request."""
    status: Optional[str] = Field(None, pattern=r"^(pass|fail|pending|in_progress)$")
    findings: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ComplianceReportResponse(ComplianceReportBase):
    """Compliance report response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Business Intelligence Models
class BIDashboardBase(BaseModel):
    """Base BI dashboard model."""
    tenant_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    dashboard_type: str = Field(..., min_length=1, max_length=50)
    widgets: List[Dict[str, Any]] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(default=300, ge=60)  # 5 minutes minimum
    is_public: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BIDashboardCreate(BIDashboardBase):
    """Create BI dashboard request."""
    pass


class BIDashboardUpdate(BaseModel):
    """Update BI dashboard request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    filters: Optional[Dict[str, Any]] = None
    refresh_interval: Optional[int] = Field(None, ge=60)
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class BIDashboardResponse(BIDashboardBase):
    """BI dashboard response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


# Workflow Automation Models
class WorkflowDefinitionBase(BaseModel):
    """Base workflow definition model."""
    tenant_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    triggers: List[Dict[str, Any]] = Field(default_factory=list)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    """Create workflow definition request."""
    pass


class WorkflowDefinitionUpdate(BaseModel):
    """Update workflow definition request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    triggers: Optional[List[Dict[str, Any]]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    """Workflow definition response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class WorkflowExecutionBase(BaseModel):
    """Base workflow execution model."""
    workflow_id: str
    tenant_id: str
    status: str = Field(..., pattern=r"^(pending|running|completed|failed|cancelled)$")
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """Create workflow execution request."""
    pass


class WorkflowExecutionUpdate(BaseModel):
    """Update workflow execution request."""
    status: Optional[str] = Field(None, pattern=r"^(pending|running|completed|failed|cancelled)$")
    output_data: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(WorkflowExecutionBase):
    """Workflow execution response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    workflow: WorkflowDefinitionResponse
    
    class Config:
        from_attributes = True


# Business Rules Engine Models
class BusinessRuleBase(BaseModel):
    """Base business rule model."""
    tenant_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    rule_type: str = Field(..., min_length=1, max_length=50)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    priority: int = Field(default=100, ge=1, le=1000)
    is_active: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BusinessRuleCreate(BusinessRuleBase):
    """Create business rule request."""
    pass


class BusinessRuleUpdate(BaseModel):
    """Update business rule request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, min_length=1, max_length=50)
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class BusinessRuleResponse(BusinessRuleBase):
    """Business rule response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


# Analytics Models
class AnalyticsQueryBase(BaseModel):
    """Base analytics query model."""
    tenant_id: str
    query_name: str = Field(..., min_length=1, max_length=200)
    query_type: str = Field(..., min_length=1, max_length=50)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    time_range: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


class AnalyticsQueryCreate(AnalyticsQueryBase):
    """Create analytics query request."""
    pass


class AnalyticsQueryResponse(AnalyticsQueryBase):
    """Analytics query response model."""
    id: str
    created_at: datetime
    results: Dict[str, Any]
    execution_time_ms: int
    cached: bool = False
    
    class Config:
        from_attributes = True


class AnalyticsQuery(BaseModel):
    """Analytics query model."""
    query_type: str
    parameters: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None


class AnalyticsResult(BaseModel):
    """Analytics result model."""
    query_id: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: datetime


# Machine Learning Models
class MLModelType(str, Enum):
    """ML model types."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    RECOMMENDATION = "recommendation"
    ANOMALY_DETECTION = "anomaly_detection"


class MLModelStatus(str, Enum):
    """ML model status."""
    DRAFT = "draft"
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ARCHIVED = "archived"


class MLModelBase(BaseModel):
    """Base ML model model."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    model_type: MLModelType
    version: str = Field(..., pattern=r"^v\d+\.\d+\.\d+$")
    status: MLModelStatus = Field(default=MLModelStatus.DRAFT)
    configuration: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_data_config: Optional[Dict[str, Any]] = None
    validation_data_config: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class MLModelCreate(MLModelBase):
    """Create ML model request."""
    pass


class MLModelUpdate(BaseModel):
    """Update ML model request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[MLModelStatus] = None
    configuration: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class MLTrainingJob(BaseModel):
    """ML model training job."""
    id: str
    model_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_by: str
    progress: Optional[float] = Field(None, ge=0, le=1)
    error_message: Optional[str] = None


class MLPredictionRequest(BaseModel):
    """ML model prediction request."""
    input_data: Dict[str, Any]
    model_version: Optional[str] = None
    prediction_type: Optional[str] = None


class MLPredictionResponse(BaseModel):
    """ML model prediction response."""
    id: str
    model_id: str
    input_data: Dict[str, Any]
    prediction_result: Dict[str, Any]
    created_at: datetime
    created_by: str


class MLModelResponse(MLModelBase):
    """ML model response model."""
    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class MLModelMetrics(BaseModel):
    """ML model performance metrics."""
    model_id: str
    accuracy: float = Field(..., ge=0, le=1)
    precision: float = Field(..., ge=0, le=1)
    recall: float = Field(..., ge=0, le=1)
    f1_score: float = Field(..., ge=0, le=1)
    training_time_seconds: int
    inference_time_ms: int
    total_predictions: int
    last_updated: datetime


# Response Models for Lists
class TenantListResponse(BaseModel):
    """List of tenants response."""
    tenants: List[TenantResponse]
    total: int
    page: int
    size: int
    has_more: bool


class UsageSummaryResponse(BaseModel):
    """Usage summary response."""
    tenant_id: str
    summaries: List[UsageSummary]
    total_usage: Dict[str, Any]
    period_start: datetime
    period_end: datetime


class AuditLogListResponse(BaseModel):
    """List of audit logs response."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    size: int
    has_more: bool


class ComplianceReportListResponse(BaseModel):
    """List of compliance reports response."""
    reports: List[ComplianceReportResponse]
    total: int
    page: int
    size: int
    has_more: bool


class BIDashboardListResponse(BaseModel):
    """List of BI dashboards response."""
    dashboards: List[BIDashboardResponse]
    total: int
    page: int
    size: int
    has_more: bool


class WorkflowDefinitionListResponse(BaseModel):
    """List of workflow definitions response."""
    workflows: List[WorkflowDefinitionResponse]
    total: int
    page: int
    size: int
    has_more: bool


class WorkflowExecutionListResponse(BaseModel):
    """List of workflow executions response."""
    executions: List[WorkflowExecutionResponse]
    total: int
    page: int
    size: int
    has_more: bool


class BusinessRuleListResponse(BaseModel):
    """List of business rules response."""
    rules: List[BusinessRuleResponse]
    total: int
    page: int
    size: int
    has_more: bool


class MLModelListResponse(BaseModel):
    """List of ML models response."""
    models: List[MLModelResponse]
    total: int
    limit: int
    offset: int
