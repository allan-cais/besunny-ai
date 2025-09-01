"""
Unified Webhook Tracking Service
Tracks webhook activity across all services using webhook_activity_tracking table
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from ...core.supabase_config import get_supabase_service_client

logger = logging.getLogger(__name__)

class WebhookTrackingService:
    """Unified service for tracking webhook activity across all services."""
    
    # Database constraint-compliant values
    VALID_SERVICES = ['calendar', 'drive', 'gmail', 'attendee']
    VALID_WEBHOOK_TYPES = ['push', 'polling', 'hybrid']
    
    def __init__(self):
        self.supabase = get_supabase_service_client()
    
    def _map_service_to_valid(self, service: str) -> str:
        """Map service names to valid database values."""
        service_mapping = {
            'gmail': 'gmail',
            'drive': 'drive', 
            'attendee_bot': 'attendee',
            'calendar': 'calendar'
        }
        return service_mapping.get(service, 'gmail')  # Default to gmail if unknown
    
    def _map_webhook_type_to_valid(self, webhook_type: str) -> str:
        """Map webhook types to valid database values."""
        # Most webhooks are push-based, so map to 'push'
        if 'webhook' in webhook_type.lower() or 'notification' in webhook_type.lower():
            return 'push'
        elif 'poll' in webhook_type.lower() or 'cron' in webhook_type.lower():
            return 'polling'
        else:
            return 'push'  # Default to push
    
    async def track_webhook_activity(
        self,
        service: str,
        webhook_type: str,
        user_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track webhook activity in the unified webhook_activity_tracking table.
        
        Args:
            service: Service name (will be mapped to valid values: calendar, drive, gmail, attendee)
            webhook_type: Type of webhook event (will be mapped to valid values: push, polling, hybrid)
            user_id: Optional user ID associated with the webhook
            success: Whether the webhook processing was successful
            error_message: Error message if processing failed
            metadata: Additional metadata for the webhook event
            
        Returns:
            True if tracking was successful, False otherwise
        """
        try:
            # Map to valid database values
            valid_service = self._map_service_to_valid(service)
            valid_webhook_type = self._map_webhook_type_to_valid(webhook_type)
            
            current_time = datetime.now().isoformat()
            
            # Check if tracking record exists for this service
            result = self.supabase.table('webhook_activity_tracking').select('*').eq('service', valid_service).execute()
            
            if result.data:
                # Update existing record
                existing_record = result.data[0]
                current_failures = existing_record.get('webhook_failures', 0)
                
                update_data = {
                    'webhook_type': valid_webhook_type,
                    'last_webhook_received': current_time,
                    'webhook_failures': current_failures + (0 if success else 1),
                    'is_active': True,  # Keep active if we're receiving webhooks
                    'updated_at': current_time
                }
                
                # Update user_id if provided
                if user_id:
                    update_data['user_id'] = user_id
                
                self.supabase.table('webhook_activity_tracking').update(update_data).eq('service', valid_service).execute()
                logger.info(f"Updated webhook tracking for {valid_service}: {valid_webhook_type}")
                
            else:
                # Create new tracking record
                tracking_data = {
                    'service': valid_service,
                    'webhook_type': valid_webhook_type,
                    'user_id': user_id,
                    'last_webhook_received': current_time,
                    'webhook_failures': 0 if success else 1,
                    'is_active': True,
                    'created_at': current_time,
                    'updated_at': current_time
                }
                
                self.supabase.table('webhook_activity_tracking').insert(tracking_data).execute()
                logger.info(f"Created new webhook tracking for {valid_service}: {valid_webhook_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking webhook activity for {service}: {e}")
            return False
    
    async def get_webhook_health_summary(self) -> Dict[str, Any]:
        """Get overall webhook health summary across all services."""
        try:
            result = self.supabase.table('webhook_activity_tracking').select('*').execute()
            
            if not result.data:
                return {"status": "no_data", "services": []}
            
            services = []
            total_failures = 0
            active_services = 0
            
            for record in result.data:
                service_info = {
                    'service': record['service'],
                    'webhook_type': record['webhook_type'],
                    'last_webhook': record.get('last_webhook_received', 'unknown'),
                    'failures': record['webhook_failures'],
                    'is_active': record['is_active'],
                    'health_status': 'healthy' if record['webhook_failures'] == 0 else 'degraded' if record['webhook_failures'] < 5 else 'unhealthy'
                }
                
                services.append(service_info)
                total_failures += record['webhook_failures']
                if record['is_active']:
                    active_services += 1
            
            overall_health = 'healthy' if total_failures == 0 else 'degraded' if total_failures < 10 else 'unhealthy'
            
            return {
                "status": "success",
                "overall_health": overall_health,
                "total_services": len(services),
                "active_services": active_services,
                "total_failures": total_failures,
                "services": services
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook health summary: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_service_webhook_status(self, service: str) -> Optional[Dict[str, Any]]:
        """Get webhook status for a specific service."""
        try:
            valid_service = self._map_service_to_valid(service)
            result = self.supabase.table('webhook_activity_tracking').select('*').eq('service', valid_service).execute()
            
            if result.data:
                record = result.data[0]
                return {
                    'service': record['service'],
                    'webhook_type': record['webhook_type'],
                    'last_webhook': record.get('last_webhook_received', 'unknown'),
                    'failures': record['webhook_failures'],
                    'is_active': record['is_active'],
                    'health_status': 'healthy' if record['webhook_failures'] == 0 else 'degraded' if record['webhook_failures'] < 5 else 'unhealthy'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting webhook status for {service}: {e}")
            return None
    
    async def deactivate_service_webhooks(self, service: str) -> bool:
        """Deactivate webhooks for a specific service."""
        try:
            valid_service = self._map_service_to_valid(service)
            self.supabase.table('webhook_activity_tracking').update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq('service', valid_service).execute()
            
            logger.info(f"Deactivated webhooks for service: {valid_service}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating webhooks for {service}: {e}")
            return False
    
    async def reset_service_failures(self, service: str) -> bool:
        """Reset failure count for a specific service."""
        try:
            valid_service = self._map_service_to_valid(service)
            self.supabase.table('webhook_activity_tracking').update({
                'webhook_failures': 0,
                'updated_at': datetime.now().isoformat()
            }).eq('service', valid_service).execute()
            
            logger.info(f"Reset failures for service: {valid_service}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting failures for {service}: {e}")
            return False
