"""
Billing service for Phase 4 enterprise features.
Handles subscription management, billing plans, and payment processing.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.schemas.enterprise import (
    BillingPlanCreate, BillingPlanUpdate, BillingPlanResponse,
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse,
    TenantTier, BillingProvider
)
from app.core.security import get_current_user_optional
from app.core.database import get_db

logger = logging.getLogger(__name__)


class BillingService:
    """Service for managing billing and subscriptions."""
    
    def __init__(self):
        self.settings = get_settings()
        self._plans_cache = {}
        self._subscriptions_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Initialize default billing plans
        self._initialize_default_plans()
    
    def _initialize_default_plans(self):
        """Initialize default billing plans."""
        default_plans = [
            {
                "id": str(uuid.uuid4()),
                "name": "Free",
                "tier": TenantTier.FREE,
                "price_monthly": Decimal("0"),
                "price_yearly": Decimal("0"),
                "features": [
                    "Basic document processing",
                    "5 projects",
                    "1GB storage",
                    "Email support"
                ],
                "limits": {
                    "max_users": 1,
                    "max_projects": 5,
                    "max_storage_gb": 1,
                    "api_calls_per_month": 1000,
                    "ai_processing_per_month": 100
                },
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Pro",
                "tier": TenantTier.PRO,
                "price_monthly": Decimal("29.99"),
                "price_yearly": Decimal("299.99"),
                "features": [
                    "Advanced document processing",
                    "25 projects",
                    "10GB storage",
                    "Priority support",
                    "Custom branding",
                    "Advanced analytics"
                ],
                "limits": {
                    "max_users": 5,
                    "max_projects": 25,
                    "max_storage_gb": 10,
                    "api_calls_per_month": 10000,
                    "ai_processing_per_month": 1000
                },
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Enterprise",
                "tier": TenantTier.ENTERPRISE,
                "price_monthly": Decimal("99.99"),
                "price_yearly": Decimal("999.99"),
                "features": [
                    "Enterprise document processing",
                    "Unlimited projects",
                    "100GB storage",
                    "24/7 support",
                    "Custom branding",
                    "Advanced analytics",
                    "SSO integration",
                    "Compliance reporting",
                    "Custom integrations"
                ],
                "limits": {
                    "max_users": 50,
                    "max_projects": -1,  # Unlimited
                    "max_storage_gb": 100,
                    "api_calls_per_month": 100000,
                    "ai_processing_per_month": 10000
                },
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for plan in default_plans:
            self._plans_cache[plan["id"]] = plan
    
    async def create_billing_plan(self, plan_data: BillingPlanCreate) -> BillingPlanResponse:
        """Create a new billing plan."""
        try:
            plan_id = str(uuid.uuid4())
            plan = {
                "id": plan_id,
                "name": plan_data.name,
                "tier": plan_data.tier,
                "price_monthly": plan_data.price_monthly,
                "price_yearly": plan_data.price_yearly,
                "features": plan_data.features,
                "limits": plan_data.limits,
                "is_active": plan_data.is_active,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            self._plans_cache[plan_id] = plan
            
            logger.info(f"Created billing plan {plan_id}: {plan_data.name}")
            
            return BillingPlanResponse(**plan)
            
        except Exception as e:
            logger.error(f"Failed to create billing plan: {str(e)}")
            raise
    
    async def get_billing_plan(self, plan_id: str) -> Optional[BillingPlanResponse]:
        """Get billing plan by ID."""
        try:
            if plan_id in self._plans_cache:
                plan = self._plans_cache[plan_id]
                return BillingPlanResponse(**plan)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get billing plan {plan_id}: {str(e)}")
            return None
    
    async def update_billing_plan(self, plan_id: str, plan_data: BillingPlanUpdate) -> Optional[BillingPlanResponse]:
        """Update billing plan."""
        try:
            if plan_id not in self._plans_cache:
                return None
            
            plan = self._plans_cache[plan_id]
            
            # Update fields
            for field, value in plan_data.dict(exclude_unset=True).items():
                if value is not None:
                    plan[field] = value
            
            plan["updated_at"] = datetime.utcnow()
            
            logger.info(f"Updated billing plan {plan_id}")
            
            return BillingPlanResponse(**plan)
            
        except Exception as e:
            logger.error(f"Failed to update billing plan {plan_id}: {str(e)}")
            return None
    
    async def list_billing_plans(
        self, 
        tier: Optional[TenantTier] = None,
        active_only: bool = True
    ) -> List[BillingPlanResponse]:
        """List billing plans with optional filtering."""
        try:
            plans = list(self._plans_cache.values())
            
            if tier:
                plans = [p for p in plans if p["tier"] == tier]
            
            if active_only:
                plans = [p for p in plans if p["is_active"]]
            
            return [BillingPlanResponse(**plan) for plan in plans]
            
        except Exception as e:
            logger.error(f"Failed to list billing plans: {str(e)}")
            return []
    
    async def delete_billing_plan(self, plan_id: str) -> bool:
        """Delete a billing plan."""
        try:
            if plan_id not in self._plans_cache:
                return False
            
            # Check if plan is in use
            if await self._is_plan_in_use(plan_id):
                raise ValueError("Cannot delete plan that is currently in use")
            
            del self._plans_cache[plan_id]
            
            logger.info(f"Deleted billing plan {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete billing plan {plan_id}: {str(e)}")
            return False
    
    async def create_subscription(
        self, 
        tenant_id: str, 
        plan_id: str,
        start_date: Optional[datetime] = None
    ) -> Optional[SubscriptionResponse]:
        """Create a new subscription."""
        try:
            # Validate plan exists
            plan = await self.get_billing_plan(plan_id)
            if not plan:
                raise ValueError("Billing plan not found")
            
            # Set start date
            if not start_date:
                start_date = datetime.utcnow()
            
            # Calculate end date (monthly subscription)
            end_date = start_date + timedelta(days=30)
            
            # Check for trial period
            trial_start = None
            trial_end = None
            if plan.tier != TenantTier.FREE:
                trial_start = start_date
                trial_end = start_date + timedelta(days=14)  # 14-day trial
            
            subscription_id = str(uuid.uuid4())
            subscription = {
                "id": subscription_id,
                "tenant_id": tenant_id,
                "plan_id": plan_id,
                "status": "trialing" if trial_start else "active",
                "current_period_start": start_date,
                "current_period_end": end_date,
                "cancel_at_period_end": False,
                "trial_start": trial_start,
                "trial_end": trial_end,
                "metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            self._subscriptions_cache[subscription_id] = subscription
            
            logger.info(f"Created subscription {subscription_id} for tenant {tenant_id}")
            
            return SubscriptionResponse(
                id=subscription_id,
                created_at=subscription["created_at"],
                updated_at=subscription["updated_at"],
                plan=plan,
                **{k: v for k, v in subscription.items() if k not in ["id", "created_at", "updated_at", "plan_id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            return None
    
    async def get_subscription(self, subscription_id: str) -> Optional[SubscriptionResponse]:
        """Get subscription by ID."""
        try:
            if subscription_id in self._subscriptions_cache:
                subscription = self._subscriptions_cache[subscription_id]
                plan = await self.get_billing_plan(subscription["plan_id"])
                if plan:
                    return SubscriptionResponse(
                        id=subscription_id,
                        created_at=subscription["created_at"],
                        updated_at=subscription["updated_at"],
                        plan=plan,
                        **{k: v for k, v in subscription.items() if k not in ["id", "created_at", "updated_at", "plan_id"]}
                    )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get subscription {subscription_id}: {str(e)}")
            return None
    
    async def get_tenant_subscription(self, tenant_id: str) -> Optional[SubscriptionResponse]:
        """Get active subscription for a tenant."""
        try:
            for subscription in self._subscriptions_cache.values():
                if subscription["tenant_id"] == tenant_id:
                    return await self.get_subscription(subscription["id"])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant subscription for {tenant_id}: {str(e)}")
            return None
    
    async def update_subscription(
        self, 
        subscription_id: str, 
        subscription_data: SubscriptionUpdate
    ) -> Optional[SubscriptionResponse]:
        """Update subscription."""
        try:
            if subscription_id not in self._subscriptions_cache:
                return None
            
            subscription = self._subscriptions_cache[subscription_id]
            
            # Update fields
            for field, value in subscription_data.dict(exclude_unset=True).items():
                if value is not None:
                    subscription[field] = value
            
            subscription["updated_at"] = datetime.utcnow()
            
            logger.info(f"Updated subscription {subscription_id}")
            
            return await self.get_subscription(subscription_id)
            
        except Exception as e:
            logger.error(f"Failed to update subscription {subscription_id}: {str(e)}")
            return None
    
    async def cancel_subscription(self, subscription_id: str, cancel_at_period_end: bool = True) -> bool:
        """Cancel a subscription."""
        try:
            subscription = await self.get_subscription(subscription_id)
            if not subscription:
                return False
            
            if cancel_at_period_end:
                # Cancel at period end
                await self.update_subscription(
                    subscription_id, 
                    SubscriptionUpdate(cancel_at_period_end=True)
                )
                logger.info(f"Subscription {subscription_id} will be cancelled at period end")
            else:
                # Cancel immediately
                await self.update_subscription(
                    subscription_id, 
                    SubscriptionUpdate(status="canceled")
                )
                logger.info(f"Subscription {subscription_id} cancelled immediately")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {str(e)}")
            return False
    
    async def renew_subscription(self, subscription_id: str) -> bool:
        """Renew a subscription for another period."""
        try:
            subscription = await self.get_subscription(subscription_id)
            if not subscription:
                return False
            
            # Calculate new period
            new_start = subscription.current_period_end
            new_end = new_start + timedelta(days=30)
            
            # Update subscription
            await self.update_subscription(
                subscription_id,
                SubscriptionUpdate(
                    current_period_start=new_start,
                    current_period_end=new_end,
                    cancel_at_period_end=False
                )
            )
            
            logger.info(f"Renewed subscription {subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to renew subscription {subscription_id}: {str(e)}")
            return False
    
    async def process_payment(self, subscription_id: str, amount: Decimal, payment_method: str) -> bool:
        """Process payment for subscription."""
        try:
            # In production, this would integrate with Stripe, Chargebee, etc.
            subscription = await self.get_subscription(subscription_id)
            if not subscription:
                return False
            
            # Simulate payment processing
            payment_successful = await self._simulate_payment_processing(amount, payment_method)
            
            if payment_successful:
                # Update subscription status
                await self.update_subscription(
                    subscription_id,
                    SubscriptionUpdate(status="active")
                )
                
                logger.info(f"Payment processed successfully for subscription {subscription_id}")
                return True
            else:
                # Mark as past due
                await self.update_subscription(
                    subscription_id,
                    SubscriptionUpdate(status="past_due")
                )
                
                logger.warning(f"Payment failed for subscription {subscription_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to process payment for subscription {subscription_id}: {str(e)}")
            return False
    
    async def get_subscription_analytics(self, tenant_id: str) -> Dict[str, Any]:
        """Get subscription analytics for a tenant."""
        try:
            subscription = await self.get_tenant_subscription(tenant_id)
            if not subscription:
                return {}
            
            # Calculate metrics
            days_remaining = (subscription.current_period_end - datetime.utcnow()).days
            trial_days_remaining = 0
            if subscription.trial_end:
                trial_days_remaining = max(0, (subscription.trial_end - datetime.utcnow()).days)
            
            return {
                "subscription_id": subscription.id,
                "plan_name": subscription.plan.name,
                "plan_tier": subscription.plan.tier,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "days_remaining": days_remaining,
                "trial_days_remaining": trial_days_remaining,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "monthly_price": subscription.plan.price_monthly,
                "yearly_price": subscription.plan.price_yearly,
                "features": subscription.plan.features,
                "limits": subscription.plan.limits
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription analytics for tenant {tenant_id}: {str(e)}")
            return {}
    
    async def get_billing_statistics(self) -> Dict[str, Any]:
        """Get overall billing statistics."""
        try:
            total_subscriptions = len(self._subscriptions_cache)
            active_subscriptions = len([
                s for s in self._subscriptions_cache.values() 
                if s["status"] in ["active", "trialing"]
            ])
            canceled_subscriptions = len([
                s for s in self._subscriptions_cache.values() 
                if s["status"] == "canceled"
            ])
            
            # Calculate revenue (simplified)
            monthly_revenue = Decimal("0")
            yearly_revenue = Decimal("0")
            
            for subscription in self._subscriptions_cache.values():
                if subscription["status"] in ["active", "trialing"]:
                    plan = await self.get_billing_plan(subscription["plan_id"])
                    if plan:
                        monthly_revenue += plan.price_monthly
                        yearly_revenue += plan.price_yearly
            
            return {
                "total_subscriptions": total_subscriptions,
                "active_subscriptions": active_subscriptions,
                "canceled_subscriptions": canceled_subscriptions,
                "monthly_revenue": monthly_revenue,
                "yearly_revenue": yearly_revenue,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get billing statistics: {str(e)}")
            return {}
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle webhook from billing provider."""
        try:
            # In production, this would handle webhooks from Stripe, Chargebee, etc.
            webhook_type = webhook_data.get("type")
            
            if webhook_type == "invoice.payment_succeeded":
                return await self._handle_payment_success(webhook_data)
            elif webhook_type == "invoice.payment_failed":
                return await self._handle_payment_failure(webhook_data)
            elif webhook_type == "customer.subscription.deleted":
                return await self._handle_subscription_deletion(webhook_data)
            else:
                logger.info(f"Unhandled webhook type: {webhook_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to handle webhook: {str(e)}")
            return False
    
    # Private helper methods
    async def _is_plan_in_use(self, plan_id: str) -> bool:
        """Check if a billing plan is currently in use."""
        return any(s["plan_id"] == plan_id for s in self._subscriptions_cache.values())
    
    async def _simulate_payment_processing(self, amount: Decimal, payment_method: str) -> bool:
        """Simulate payment processing (placeholder)."""
        # In production, this would integrate with actual payment processors
        import random
        return random.random() > 0.1  # 90% success rate
    
    async def _handle_payment_success(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle successful payment webhook."""
        # Update subscription status
        subscription_id = webhook_data.get("data", {}).get("object", {}).get("subscription")
        if subscription_id:
            await self.update_subscription(
                subscription_id,
                SubscriptionUpdate(status="active")
            )
        return True
    
    async def _handle_payment_failure(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle failed payment webhook."""
        # Update subscription status
        subscription_id = webhook_data.get("data", {}).get("object", {}).get("subscription")
        if subscription_id:
            await self.update_subscription(
                subscription_id,
                SubscriptionUpdate(status="past_due")
            )
        return True
    
    async def _handle_subscription_deletion(self, webhook_data: Dict[str, Any]) -> bool:
        """Handle subscription deletion webhook."""
        # Mark subscription as canceled
        subscription_id = webhook_data.get("data", {}).get("object", {}).get("id")
        if subscription_id:
            await self.update_subscription(
                subscription_id,
                SubscriptionUpdate(status="canceled")
            )
        return True
    
    async def cleanup_expired_subscriptions(self) -> int:
        """Clean up expired subscriptions."""
        try:
            cleaned_count = 0
            current_time = datetime.utcnow()
            
            for subscription_id, subscription in self._subscriptions_cache.items():
                if (subscription["current_period_end"] < current_time and
                    subscription["status"] in ["active", "trialing"]):
                    
                    # Mark as expired
                    await self.update_subscription(
                        subscription_id,
                        SubscriptionUpdate(status="past_due")
                    )
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired subscriptions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired subscriptions: {str(e)}")
            return 0


# Global service instance
billing_service = BillingService()
