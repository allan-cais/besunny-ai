"""
Enterprise API endpoints for Phase 4 features.
Includes multi-tenancy, billing, compliance, business intelligence, and ML services.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
import logging

from app.core.security import get_current_user
from app.services.enterprise import (
    MultiTenancyService, BillingService, UsageTrackingService,
    AuditService, ComplianceService, BusinessIntelligenceService,
    WorkflowService, BusinessRulesService, AnalyticsService, MLService
)
from app.models.schemas.enterprise import (
    # Multi-tenancy
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    # Billing
    BillingPlanCreate, BillingPlanUpdate, BillingPlanResponse, BillingPlanListResponse,
    SubscriptionCreate, SubscriptionResponse, SubscriptionListResponse,
    # Usage tracking
    UsageSummary, UsageSummaryResponse,
    # Audit
    AuditLogResponse, AuditLogListResponse,
    # Compliance
    ComplianceReportResponse, ComplianceReportListResponse,
    # Business Intelligence
    BIDashboardResponse, BIDashboardListResponse,
    # Workflows
    WorkflowDefinitionResponse, WorkflowDefinitionListResponse,
    WorkflowExecutionResponse, WorkflowExecutionListResponse,
    # Business Rules
    BusinessRuleResponse, BusinessRuleListResponse,
    # Analytics
    AnalyticsQuery, AnalyticsResult,
    # ML Models
    MLModelCreate, MLModelUpdate, MLModelResponse, MLModelListResponse,
    MLTrainingJob, MLPredictionRequest, MLPredictionResponse, MLModelMetrics
)

logger = logging.getLogger(__name__)

# Create enterprise router
router = APIRouter(prefix="/enterprise", tags=["enterprise"])

# Initialize services
multi_tenancy_service = MultiTenancyService()
billing_service = BillingService()
usage_tracking_service = UsageTrackingService()
audit_service = AuditService()
compliance_service = ComplianceService()
bi_service = BusinessIntelligenceService()
workflow_service = WorkflowService()
business_rules_service = BusinessRulesService()
analytics_service = AnalyticsService()
ml_service = MLService()


# Multi-tenancy endpoints
@router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new tenant."""
    try:
        return await multi_tenancy_service.create_tenant(tenant_data, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to create tenant: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get tenant by ID."""
    try:
        tenant = await multi_tenancy_service.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    except Exception as e:
        logger.error(f"Failed to get tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    limit: int = Query(50, ge=1, le=100, description="Number of tenants to return"),
    offset: int = Query(0, ge=0, description="Number of tenants to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List tenants with pagination."""
    try:
        return await multi_tenancy_service.list_tenants(
            admin_user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to list tenants: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_data: TenantUpdate,
    tenant_id: str = Path(..., description="Tenant ID"),
    current_user: dict = Depends(get_current_user)
):
    """Update tenant."""
    try:
        return await multi_tenancy_service.update_tenant(tenant_id, tenant_data, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to update tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Billing endpoints
@router.post("/billing/plans", response_model=BillingPlanResponse)
async def create_billing_plan(
    plan_data: BillingPlanCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new billing plan."""
    try:
        return await billing_service.create_plan(plan_data, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to create billing plan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/billing/plans", response_model=BillingPlanListResponse)
async def list_billing_plans(
    limit: int = Query(50, ge=1, le=100, description="Number of plans to return"),
    offset: int = Query(0, ge=0, description="Number of plans to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List billing plans."""
    try:
        return await billing_service.list_plans(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to list billing plans: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/billing/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new subscription."""
    try:
        return await billing_service.create_subscription(subscription_data, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Usage tracking endpoints
@router.get("/usage/summary", response_model=UsageSummaryResponse)
async def get_usage_summary(
    tenant_id: str = Query(..., description="Tenant ID"),
    period_start: str = Query(..., description="Period start date (ISO format)"),
    period_end: str = Query(..., description="Period end date (ISO format)"),
    current_user: dict = Depends(get_current_user)
):
    """Get usage summary for a tenant."""
    try:
        return await usage_tracking_service.get_usage_summary(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            user_id=current_user["id"]
        )
    except Exception as e:
        logger.error(f"Failed to get usage summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Audit endpoints
@router.get("/audit/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    tenant_id: str = Query(..., description="Tenant ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List audit logs with filtering."""
    try:
        return await audit_service.list_audit_logs(
            tenant_id=tenant_id,
            action=action,
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to list audit logs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Compliance endpoints
@router.get("/compliance/reports", response_model=ComplianceReportListResponse)
async def list_compliance_reports(
    tenant_id: str = Query(..., description="Tenant ID"),
    standard: Optional[str] = Query(None, description="Filter by compliance standard"),
    limit: int = Query(50, ge=1, le=100, description="Number of reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List compliance reports."""
    try:
        return await compliance_service.list_compliance_reports(
            tenant_id=tenant_id,
            standard=standard,
            limit=limit,
            offset=offset,
            user_id=current_user["id"]
        )
    except Exception as e:
        logger.error(f"Failed to list compliance reports: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Business Intelligence endpoints
@router.get("/bi/dashboards", response_model=BIDashboardListResponse)
async def list_bi_dashboards(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of dashboards to return"),
    offset: int = Query(0, ge=0, description="Number of dashboards to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List BI dashboards."""
    try:
        return await bi_service.list_dashboards(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            user_id=current_user["id"]
        )
    except Exception as e:
        logger.error(f"Failed to list BI dashboards: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Workflow endpoints
@router.get("/workflows/definitions", response_model=WorkflowDefinitionListResponse)
async def list_workflow_definitions(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of workflows to return"),
    offset: int = Query(0, ge=0, description="Number of workflows to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List workflow definitions."""
    try:
        return await workflow_service.list_workflow_definitions(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            user_id=current_user["id"]
        )
    except Exception as e:
        logger.error(f"Failed to list workflow definitions: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Business Rules endpoints
@router.get("/business-rules", response_model=BusinessRuleListResponse)
async def list_business_rules(
    tenant_id: str = Query(..., description="Tenant ID"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    limit: int = Query(50, ge=1, le=100, description="Number of rules to return"),
    offset: int = Query(0, ge=0, description="Number of rules to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List business rules."""
    try:
        return await business_rules_service.list_business_rules(
            tenant_id=tenant_id,
            rule_type=rule_type,
            limit=limit,
            offset=offset,
            user_id=current_user["id"]
        )
    except Exception as e:
        logger.error(f"Failed to list business rules: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Analytics endpoints
@router.post("/analytics/query", response_model=AnalyticsResult)
async def execute_analytics_query(
    query: AnalyticsQuery,
    current_user: dict = Depends(get_current_user)
):
    """Execute analytics query."""
    try:
        return await analytics_service.execute_query(query, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to execute analytics query: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ML Model endpoints
@router.post("/ml/models", response_model=MLModelResponse)
async def create_ml_model(
    model_data: MLModelCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new ML model."""
    try:
        return await ml_service.create_model(model_data, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to create ML model: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ml/models/{model_id}", response_model=MLModelResponse)
async def get_ml_model(
    model_id: str = Path(..., description="ML Model ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get ML model by ID."""
    try:
        model = await ml_service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="ML model not found")
        return model
    except Exception as e:
        logger.error(f"Failed to get ML model {model_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ml/models", response_model=MLModelListResponse)
async def list_ml_models(
    model_type: Optional[str] = Query(None, description="Filter by model type"),
    status: Optional[str] = Query(None, description="Filter by model status"),
    limit: int = Query(50, ge=1, le=100, description="Number of models to return"),
    offset: int = Query(0, ge=0, description="Number of models to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List ML models with filtering."""
    try:
        return await ml_service.list_models(
            user_id=current_user["id"],
            model_type=model_type,
            status=status,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to list ML models: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/ml/models/{model_id}", response_model=MLModelResponse)
async def update_ml_model(
    model_data: MLModelUpdate,
    model_id: str = Path(..., description="ML Model ID"),
    current_user: dict = Depends(get_current_user)
):
    """Update ML model."""
    try:
        return await ml_service.update_model(model_id, model_data, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to update ML model {model_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ml/models/{model_id}")
async def delete_ml_model(
    model_id: str = Path(..., description="ML Model ID"),
    current_user: dict = Depends(get_current_user)
):
    """Delete ML model."""
    try:
        success = await ml_service.delete_model(model_id, current_user["id"])
        if success:
            return {"message": "ML model deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete ML model")
    except Exception as e:
        logger.error(f"Failed to delete ML model {model_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ml/models/{model_id}/train", response_model=MLTrainingJob)
async def train_ml_model(
    model_id: str = Path(..., description="ML Model ID"),
    current_user: dict = Depends(get_current_user)
):
    """Start ML model training."""
    try:
        return await ml_service.train_model(model_id, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to start training for model {model_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ml/models/{model_id}/predict", response_model=MLPredictionResponse)
async def make_ml_prediction(
    prediction_request: MLPredictionRequest,
    model_id: str = Path(..., description="ML Model ID"),
    current_user: dict = Depends(get_current_user)
):
    """Make prediction using ML model."""
    try:
        return await ml_service.make_prediction(model_id, prediction_request, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to make prediction with model {model_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ml/models/{model_id}/metrics", response_model=MLModelMetrics)
async def get_ml_model_metrics(
    model_id: str = Path(..., description="ML Model ID"),
    current_user: dict = Depends(get_current_user)
):
    """Get ML model performance metrics."""
    try:
        return await ml_service.get_model_metrics(model_id, current_user["id"])
    except Exception as e:
        logger.error(f"Failed to get metrics for model {model_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ml/models/{model_id}/export")
async def export_ml_model(
    model_id: str = Path(..., description="ML Model ID"),
    format: str = Query("onnx", description="Export format"),
    current_user: dict = Depends(get_current_user)
):
    """Export ML model in specified format."""
    try:
        export_data = await ml_service.export_model(model_id, current_user["id"], format)
        return export_data
    except Exception as e:
        logger.error(f"Failed to export model {model_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
