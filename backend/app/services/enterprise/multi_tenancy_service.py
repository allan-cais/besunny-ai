"""
Multi-tenancy service for Phase 4 enterprise features.
Handles tenant isolation, resource quotas, and tenant management.
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
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse,
    TenantTier, TenantStatus
)
from app.core.security import get_current_user_optional
from app.core.database import get_db

logger = logging.getLogger(__name__)


class MultiTenancyService:
    """Service for managing multi-tenancy features."""
    
    def __init__(self):
        self.settings = get_settings()
        self._tenant_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def create_tenant(self, tenant_data: TenantCreate, admin_user_id: str) -> TenantResponse:
        """Create a new tenant."""
        try:
            # Validate tenant limits
            await self._validate_tenant_limits()
            
            # Create tenant record
            tenant_id = str(uuid.uuid4())
            tenant = {
                "id": tenant_id,
                "name": tenant_data.name,
                "domain": tenant_data.domain,
                "tier": tenant_data.tier,
                "status": TenantStatus.PENDING,
                "max_users": tenant_data.max_users,
                "max_projects": tenant_data.max_projects,
                "max_storage_gb": tenant_data.max_storage_gb,
                "custom_branding": tenant_data.custom_branding,
                "sso_enabled": tenant_data.sso_enabled,
                "compliance_standards": tenant_data.compliance_standards,
                "data_residency_region": tenant_data.data_residency_region,
                "metadata": tenant_data.metadata,
                "admin_user_id": admin_user_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Store in database (placeholder for now)
            # In production, this would use proper database models
            self._tenant_cache[tenant_id] = tenant
            
            # Set trial period for non-free tiers
            if tenant_data.tier != TenantTier.FREE:
                tenant["trial_ends_at"] = datetime.utcnow() + timedelta(days=30)
            
            logger.info(f"Created tenant {tenant_id} with tier {tenant_data.tier}")
            
            return TenantResponse(
                id=tenant_id,
                created_at=tenant["created_at"],
                updated_at=tenant["updated_at"],
                admin_user_id=admin_user_id,
                current_user_count=0,
                current_project_count=0,
                current_storage_gb=Decimal("0"),
                trial_ends_at=tenant.get("trial_ends_at"),
                subscription_ends_at=None,
                **{k: v for k, v in tenant.items() if k not in ["id", "created_at", "updated_at", "admin_user_id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to create tenant: {str(e)}")
            raise
    
    async def get_tenant(self, tenant_id: str) -> Optional[TenantResponse]:
        """Get tenant by ID."""
        try:
            # Check cache first
            if tenant_id in self._tenant_cache:
                tenant = self._tenant_cache[tenant_id]
                return TenantResponse(
                    id=tenant_id,
                    created_at=tenant["created_at"],
                    updated_at=tenant["updated_at"],
                    admin_user_id=tenant["admin_user_id"],
                    current_user_count=await self._get_tenant_user_count(tenant_id),
                    current_project_count=await self._get_tenant_project_count(tenant_id),
                    current_storage_gb=await self._get_tenant_storage_usage(tenant_id),
                    trial_ends_at=tenant.get("trial_ends_at"),
                    subscription_ends_at=tenant.get("subscription_ends_at"),
                    **{k: v for k, v in tenant.items() if k not in ["id", "created_at", "updated_at", "admin_user_id"]}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {str(e)}")
            return None
    
    async def update_tenant(self, tenant_id: str, tenant_data: TenantUpdate) -> Optional[TenantResponse]:
        """Update tenant information."""
        try:
            if tenant_id not in self._tenant_cache:
                return None
            
            tenant = self._tenant_cache[tenant_id]
            
            # Update fields
            for field, value in tenant_data.dict(exclude_unset=True).items():
                if value is not None:
                    tenant[field] = value
            
            tenant["updated_at"] = datetime.utcnow()
            
            # Validate resource limits
            await self._validate_tenant_resource_limits(tenant_id)
            
            logger.info(f"Updated tenant {tenant_id}")
            
            return await self.get_tenant(tenant_id)
            
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {str(e)}")
            return None
    
    async def list_tenants(
        self, 
        page: int = 1, 
        size: int = 20,
        tier: Optional[TenantTier] = None,
        status: Optional[TenantStatus] = None
    ) -> TenantListResponse:
        """List tenants with pagination and filtering."""
        try:
            # Filter tenants
            tenants = list(self._tenant_cache.values())
            
            if tier:
                tenants = [t for t in tenants if t["tier"] == tier]
            
            if status:
                tenants = [t for t in tenants if t["status"] == status]
            
            # Pagination
            total = len(tenants)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_tenants = tenants[start_idx:end_idx]
            
            # Convert to response models
            tenant_responses = []
            for tenant in paginated_tenants:
                tenant_response = await self.get_tenant(tenant["id"])
                if tenant_response:
                    tenant_responses.append(tenant_response)
            
            return TenantListResponse(
                tenants=tenant_responses,
                total=total,
                page=page,
                size=size,
                has_more=end_idx < total
            )
            
        except Exception as e:
            logger.error(f"Failed to list tenants: {str(e)}")
            return TenantListResponse(
                tenants=[],
                total=0,
                page=page,
                size=size,
                has_more=False
            )
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant and all associated data."""
        try:
            if tenant_id not in self._tenant_cache:
                return False
            
            # Check if tenant has active subscriptions
            if await self._has_active_subscriptions(tenant_id):
                raise ValueError("Cannot delete tenant with active subscriptions")
            
            # Delete tenant data (placeholder)
            # In production, this would cascade delete all related data
            del self._tenant_cache[tenant_id]
            
            logger.info(f"Deleted tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {str(e)}")
            return False
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[TenantResponse]:
        """Get tenant by domain."""
        try:
            for tenant in self._tenant_cache.values():
                if tenant.get("domain") == domain:
                    return await self.get_tenant(tenant["id"])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant by domain {domain}: {str(e)}")
            return None
    
    async def get_tenant_by_user(self, user_id: str) -> Optional[TenantResponse]:
        """Get tenant by user ID."""
        try:
            for tenant in self._tenant_cache.values():
                if tenant.get("admin_user_id") == user_id:
                    return await self.get_tenant(tenant["id"])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant by user {user_id}: {str(e)}")
            return None
    
    async def check_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """Check if user has access to tenant."""
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Admin has full access
            if tenant.admin_user_id == user_id:
                return True
            
            # Check if user is member of tenant
            # In production, this would check a tenant_users table
            return await self._is_tenant_member(tenant_id, user_id)
            
        except Exception as e:
            logger.error(f"Failed to check tenant access: {str(e)}")
            return False
    
    async def get_tenant_quota_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get current quota usage for tenant."""
        try:
            tenant = await self.get_tenant(tenant_id)
            if not tenant:
                return {}
            
            current_users = await self._get_tenant_user_count(tenant_id)
            current_projects = await self._get_tenant_project_count(tenant_id)
            current_storage = await self._get_tenant_storage_usage(tenant_id)
            
            return {
                "users": {
                    "current": current_users,
                    "limit": tenant.max_users,
                    "percentage": (current_users / tenant.max_users) * 100
                },
                "projects": {
                    "current": current_projects,
                    "limit": tenant.max_projects,
                    "percentage": (current_projects / tenant.max_projects) * 100
                },
                "storage": {
                    "current": float(current_storage),
                    "limit": tenant.max_storage_gb,
                    "percentage": (float(current_storage) / tenant.max_storage_gb) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get quota usage for tenant {tenant_id}: {str(e)}")
            return {}
    
    async def enforce_tenant_quotas(self, tenant_id: str) -> bool:
        """Enforce tenant quotas and suspend if exceeded."""
        try:
            usage = await self.get_tenant_quota_usage(tenant_id)
            tenant = await self.get_tenant(tenant_id)
            
            if not tenant:
                return False
            
            # Check if any quota is exceeded
            quota_exceeded = any(
                usage[key]["percentage"] > 100 
                for key in ["users", "projects", "storage"]
            )
            
            if quota_exceeded:
                # Suspend tenant
                await self.update_tenant(tenant_id, TenantUpdate(status=TenantStatus.SUSPENDED))
                logger.warning(f"Tenant {tenant_id} suspended due to quota exceeded")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enforce quotas for tenant {tenant_id}: {str(e)}")
            return False
    
    async def migrate_tenant_data(self, source_tenant_id: str, target_tenant_id: str) -> bool:
        """Migrate data between tenants."""
        try:
            # Validate both tenants exist
            source_tenant = await self.get_tenant(source_tenant_id)
            target_tenant = await self.get_tenant(target_tenant_id)
            
            if not source_tenant or not target_tenant:
                return False
            
            # Check target tenant has sufficient capacity
            source_usage = await self.get_tenant_quota_usage(source_tenant_id)
            target_usage = await self.get_tenant_quota_usage(target_tenant_id)
            
            # Validate capacity
            if not self._validate_migration_capacity(source_usage, target_usage, target_tenant):
                raise ValueError("Target tenant insufficient capacity for migration")
            
            # Perform migration (placeholder)
            # In production, this would move actual data
            logger.info(f"Migrated data from tenant {source_tenant_id} to {target_tenant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate tenant data: {str(e)}")
            return False
    
    # Private helper methods
    async def _validate_tenant_limits(self) -> None:
        """Validate tenant creation limits."""
        if not self.settings.enable_multi_tenancy:
            raise ValueError("Multi-tenancy is not enabled")
        
        current_tenant_count = len(self._tenant_cache)
        if current_tenant_count >= self.settings.max_tenants_per_instance:
            raise ValueError("Maximum tenant limit reached")
    
    async def _validate_tenant_resource_limits(self, tenant_id: str) -> None:
        """Validate tenant resource limits."""
        usage = await self.get_tenant_quota_usage(tenant_id)
        
        for resource, data in usage.items():
            if data["percentage"] > 100:
                raise ValueError(f"Tenant {resource} quota exceeded")
    
    async def _get_tenant_user_count(self, tenant_id: str) -> int:
        """Get current user count for tenant."""
        # Placeholder - in production, this would query the database
        return 1
    
    async def _get_tenant_project_count(self, tenant_id: str) -> int:
        """Get current project count for tenant."""
        # Placeholder - in production, this would query the database
        return 2
    
    async def _get_tenant_storage_usage(self, tenant_id: str) -> Decimal:
        """Get current storage usage for tenant in GB."""
        # Placeholder - in production, this would query the database
        return Decimal("1.5")
    
    async def _has_active_subscriptions(self, tenant_id: str) -> bool:
        """Check if tenant has active subscriptions."""
        # Placeholder - in production, this would query the database
        return False
    
    async def _is_tenant_member(self, tenant_id: str, user_id: str) -> bool:
        """Check if user is a member of the tenant."""
        # Placeholder - in production, this would query the database
        return False
    
    def _validate_migration_capacity(
        self, 
        source_usage: Dict[str, Any], 
        target_usage: Dict[str, Any], 
        target_tenant: TenantResponse
    ) -> bool:
        """Validate target tenant has capacity for migration."""
        for resource in ["users", "projects", "storage"]:
            source_current = source_usage[resource]["current"]
            target_current = target_usage[resource]["current"]
            target_limit = getattr(target_tenant, f"max_{resource}")
            
            if target_current + source_current > target_limit:
                return False
        
        return True
    
    async def cleanup_expired_trials(self) -> int:
        """Clean up expired trial tenants."""
        try:
            cleaned_count = 0
            current_time = datetime.utcnow()
            
            for tenant_id, tenant in self._tenant_cache.items():
                if (tenant.get("trial_ends_at") and 
                    tenant["trial_ends_at"] < current_time and
                    tenant["status"] == TenantStatus.TRIAL):
                    
                    # Suspend expired trial
                    await self.update_tenant(tenant_id, TenantUpdate(status=TenantStatus.SUSPENDED))
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired trial tenants")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired trials: {str(e)}")
            return 0
    
    async def get_tenant_statistics(self) -> Dict[str, Any]:
        """Get overall tenant statistics."""
        try:
            total_tenants = len(self._tenant_cache)
            active_tenants = len([t for t in self._tenant_cache.values() if t["status"] == TenantStatus.ACTIVE])
            trial_tenants = len([t for t in self._tenant_cache.values() if t["status"] == TenantStatus.TRIAL])
            suspended_tenants = len([t for t in self._tenant_cache.values() if t["status"] == TenantStatus.SUSPENDED])
            
            tier_distribution = {}
            for tenant in self._tenant_cache.values():
                tier = tenant["tier"]
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
            
            return {
                "total_tenants": total_tenants,
                "active_tenants": active_tenants,
                "trial_tenants": trial_tenants,
                "suspended_tenants": suspended_tenants,
                "tier_distribution": tier_distribution,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get tenant statistics: {str(e)}")
            return {}


# Global service instance
multi_tenancy_service = MultiTenancyService()
