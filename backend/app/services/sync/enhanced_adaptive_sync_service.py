"""
Enhanced adaptive sync service for BeSunny.ai Python backend.
Handles multi-service synchronization, activity tracking, and adaptive sync intervals.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings
from ..attendee.attendee_service import AttendeeService
from ..calendar.calendar_polling_service import CalendarPollingService
from ..drive.drive_polling_service import DrivePollingService
from ..email.gmail_polling_service import GmailPollingService

logger = logging.getLogger(__name__)


class SyncResult(BaseModel):
    """Result of a sync operation."""
    service: str
    user_id: str
    success: bool
    items_processed: int
    items_created: int
    items_updated: int
    items_deleted: int
    processing_time_ms: int
    error_message: Optional[str] = None
    timestamp: datetime


class MultiServiceSyncResult(BaseModel):
    """Result of a multi-service sync operation."""
    user_id: str
    services_synced: List[str]
    total_items_processed: int
    total_items_created: int
    total_items_updated: int
    total_items_deleted: int
    total_processing_time_ms: int
    success: bool
    errors: List[str]
    timestamp: datetime


class UserActivityState(BaseModel):
    """User activity state for sync optimization."""
    user_id: str
    last_sync_at: datetime
    change_frequency: str  # 'low', 'medium', 'high'
    virtual_email_activity: bool
    auto_scheduled_meetings: int
    sync_priority: str  # 'low', 'normal', 'high'
    next_sync_interval: int  # minutes
    updated_at: datetime


class EnhancedAdaptiveSyncService:
    """Service for coordinating multi-service synchronization with adaptive optimization."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        
        # Initialize service dependencies
        self.attendee_service = AttendeeService()
        self.calendar_service = CalendarPollingService()
        self.drive_service = DrivePollingService()
        self.gmail_service = GmailPollingService()
        
        logger.info("Enhanced Adaptive Sync Service initialized")
    
    async def sync_all_services(self, user_id: str, force_sync: bool = False) -> List[Dict[str, Any]]:
        """
        Synchronize all services for a user.
        
        Args:
            user_id: User ID to sync
            force_sync: Force sync regardless of timing
            
        Returns:
            List of sync results for each service
        """
        try:
            logger.info(f"Starting multi-service sync for user {user_id}")
            
            # Check if we should sync based on user activity
            if not force_sync:
                should_sync = await self._should_sync_user(user_id)
                if not should_sync:
                    return [{
                        'skipped': True,
                        'reason': 'User activity optimization',
                        'user_id': user_id,
                        'next_sync_in_minutes': await self._get_next_sync_interval(user_id)
                    }]
            
            # Get user's email for Gmail sync
            user_email = await self._get_user_email(user_id)
            if not user_email:
                return [{
                    'success': False,
                    'error': 'User email not found',
                    'user_id': user_id
                }]
            
            # Execute sync for each service
            sync_results = []
            
            # Calendar sync
            calendar_result = await self.sync_calendar(user_id, force_sync)
            sync_results.append(calendar_result)
            
            # Drive sync
            drive_result = await self.sync_drive(user_id, force_sync)
            sync_results.append(drive_result)
            
            # Gmail sync
            gmail_result = await self.sync_gmail(user_id, user_email, force_sync)
            sync_results.append(gmail_result)
            
            # Attendee sync
            attendee_result = await self.sync_attendee(user_id, force_sync)
            sync_results.append(attendee_result)
            
            # Record user activity
            await self._record_user_activity(user_id, 'multi_service_sync')
            
            # Update user activity state
            await self._update_user_activity_state(user_id, sync_results)
            
            # Calculate next sync interval
            next_sync_interval = await self._calculate_next_sync_interval(user_id, sync_results)
            
            logger.info(f"Multi-service sync completed for user {user_id}: {len(sync_results)} services synced")
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Multi-service sync failed for user {user_id}: {e}")
            return [{
                'success': False,
                'error': str(e),
                'user_id': user_id
            }]
    
    async def sync_calendar(self, user_id: str, force_sync: bool = False) -> Dict[str, Any]:
        """
        Synchronize calendar for a user.
        
        Args:
            user_id: User ID to sync
            force_sync: Force sync regardless of timing
            
        Returns:
            Calendar sync result
        """
        try:
            start_time = datetime.now()
            
            # Execute smart calendar polling
            result = await self.calendar_service.smart_calendar_polling(user_id)
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            if result.get('skipped'):
                return {
                    'service': 'calendar',
                    'user_id': user_id,
                    'skipped': True,
                    'reason': result.get('reason'),
                    'processing_time_ms': processing_time
                }
            
            # Create sync result
            sync_result = SyncResult(
                service='calendar',
                user_id=user_id,
                success=result.get('success', False),
                items_processed=result.get('events_processed', 0),
                items_created=result.get('events_created', 0),
                items_updated=result.get('events_updated', 0),
                items_deleted=result.get('events_deleted', 0),
                processing_time_ms=processing_time,
                error_message=result.get('error'),
                timestamp=datetime.now()
            )
            
            # Store sync result
            await self._store_sync_result(sync_result)
            
            return {
                'service': 'calendar',
                'user_id': user_id,
                'success': result.get('success', False),
                'items_processed': result.get('events_processed', 0),
                'items_created': result.get('events_created', 0),
                'items_updated': result.get('events_updated', 0),
                'items_deleted': result.get('events_deleted', 0),
                'processing_time_ms': processing_time,
                'error': result.get('error')
            }
            
        except Exception as e:
            logger.error(f"Calendar sync failed for user {user_id}: {e}")
            return {
                'service': 'calendar',
                'user_id': user_id,
                'success': False,
                'error': str(e)
            }
    
    async def sync_drive(self, user_id: str, force_sync: bool = False) -> Dict[str, Any]:
        """
        Synchronize Drive for a user.
        
        Args:
            user_id: User ID to sync
            force_sync: Force sync regardless of timing
            
        Returns:
            Drive sync result
        """
        try:
            start_time = datetime.now()
            
            # Get user's active Drive files
            active_files = await self._get_user_active_drive_files(user_id)
            
            if not active_files:
                return {
                    'service': 'drive',
                    'user_id': user_id,
                    'success': True,
                    'items_processed': 0,
                    'items_created': 0,
                    'items_updated': 0,
                    'items_deleted': 0,
                    'processing_time_ms': 0,
                    'message': 'No active Drive files to sync'
                }
            
            # Sync each file
            total_processed = 0
            total_created = 0
            total_updated = 0
            total_deleted = 0
            
            for file_info in active_files:
                try:
                    result = await self.drive_service.smart_drive_polling(
                        file_info['file_id'], 
                        file_info['document_id']
                    )
                    
                    if result.get('success'):
                        total_processed += 1
                        if result.get('file_updated'):
                            total_updated += 1
                        if result.get('file_deleted'):
                            total_deleted += 1
                    elif result.get('skipped'):
                        continue
                        
                except Exception as e:
                    logger.error(f"Failed to sync Drive file {file_info['file_id']}: {e}")
                    continue
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            # Create sync result
            sync_result = SyncResult(
                service='drive',
                user_id=user_id,
                success=True,
                items_processed=total_processed,
                items_created=total_created,
                items_updated=total_updated,
                items_deleted=total_deleted,
                processing_time_ms=processing_time,
                timestamp=datetime.now()
            )
            
            # Store sync result
            await self._store_sync_result(sync_result)
            
            return {
                'service': 'drive',
                'user_id': user_id,
                'success': True,
                'items_processed': total_processed,
                'items_created': total_created,
                'items_updated': total_updated,
                'items_deleted': total_deleted,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Drive sync failed for user {user_id}: {e}")
            return {
                'service': 'drive',
                'user_id': user_id,
                'success': False,
                'error': str(e)
            }
    
    async def sync_gmail(self, user_id: str, user_email: str, force_sync: bool = False) -> Dict[str, Any]:
        """
        Synchronize Gmail for a user.
        
        Args:
            user_id: User ID to sync
            user_email: User's email address
            force_sync: Force sync regardless of timing
            
        Returns:
            Gmail sync result
        """
        try:
            start_time = datetime.now()
            
            # Execute smart Gmail polling
            result = await self.gmail_service.smart_gmail_polling(user_email)
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            if result.get('skipped'):
                return {
                    'service': 'gmail',
                    'user_id': user_id,
                    'skipped': True,
                    'reason': result.get('reason'),
                    'processing_time_ms': processing_time
                }
            
            # Create sync result
            sync_result = SyncResult(
                service='gmail',
                user_id=user_id,
                success=result.get('success', False),
                items_processed=result.get('messages_processed', 0),
                items_created=result.get('documents_created', 0),
                items_updated=0,  # Gmail doesn't update existing messages
                items_deleted=0,  # Gmail doesn't delete messages in this context
                processing_time_ms=processing_time,
                error_message=result.get('error'),
                timestamp=datetime.now()
            )
            
            # Store sync result
            await self._store_sync_result(sync_result)
            
            return {
                'service': 'gmail',
                'user_id': user_id,
                'success': result.get('success', False),
                'items_processed': result.get('messages_processed', 0),
                'items_created': result.get('documents_created', 0),
                'items_updated': 0,
                'items_deleted': 0,
                'processing_time_ms': processing_time,
                'error': result.get('error')
            }
            
        except Exception as e:
            logger.error(f"Gmail sync failed for user {user_id}: {e}")
            return {
                'service': 'gmail',
                'user_id': user_id,
                'success': False,
                'error': str(e)
            }
    
    async def sync_attendee(self, user_id: str, force_sync: bool = False) -> Dict[str, Any]:
        """
        Synchronize attendee/meeting data for a user.
        
        Args:
            user_id: User ID to sync
            force_sync: Force sync regardless of timing
            
        Returns:
            Attendee sync result
        """
        try:
            start_time = datetime.now()
            
            # Execute smart attendee polling
            result = await self.attendee_service.poll_all_meetings(user_id)
            
            processing_time = (datetime.now() - start_time).microseconds // 1000
            
            # Create sync result
            sync_result = SyncResult(
                service='attendee',
                user_id=user_id,
                success=True,
                items_processed=len(result),
                items_created=0,  # Attendee sync doesn't create new items
                items_updated=len(result),  # All polled meetings are updated
                items_deleted=0,
                processing_time_ms=processing_time,
                timestamp=datetime.now()
            )
            
            # Store sync result
            await self._store_sync_result(sync_result)
            
            return {
                'service': 'attendee',
                'user_id': user_id,
                'success': True,
                'items_processed': len(result),
                'items_created': 0,
                'items_updated': len(result),
                'items_deleted': 0,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Attendee sync failed for user {user_id}: {e}")
            return {
                'service': 'attendee',
                'user_id': user_id,
                'success': False,
                'error': str(e)
            }
    
    async def record_user_activity(self, user_id: str, activity_type: str) -> None:
        """
        Record user activity for sync optimization.
        
        Args:
            user_id: User ID
            activity_type: Type of activity
        """
        try:
            activity_data = {
                "user_id": user_id,
                "activity_type": activity_type,
                "timestamp": datetime.now().isoformat()
            }
            
            self.supabase.table("user_activity_logs").insert(activity_data).execute()
            
            logger.info(f"Recorded user activity: {activity_type} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to record user activity: {e}")
    
    async def update_user_activity_state(self, user_id: str, results: List[Dict[str, Any]]) -> None:
        """
        Update user activity state based on sync results.
        
        Args:
            user_id: User ID
            results: List of sync results
        """
        try:
            # Calculate total activity metrics
            total_processed = sum(r.get('items_processed', 0) for r in results)
            total_created = sum(r.get('items_created', 0) for r in results)
            total_updated = sum(r.get('items_updated', 0) for r in results)
            total_deleted = sum(r.get('items_deleted', 0) for r in results)
            
            # Determine change frequency
            total_changes = total_created + total_updated + total_deleted
            if total_changes == 0:
                change_frequency = 'low'
            elif total_changes <= 10:
                change_frequency = 'medium'
            else:
                change_frequency = 'high'
            
            # Check for virtual email activity
            gmail_result = next((r for r in results if r.get('service') == 'gmail'), {})
            virtual_email_activity = gmail_result.get('items_created', 0) > 0
            
            # Check for auto-scheduled meetings
            attendee_result = next((r for r in results if r.get('service') == 'attendee'), {})
            auto_scheduled_meetings = attendee_result.get('items_created', 0)
            
            # Determine sync priority
            if change_frequency == 'high' or virtual_email_activity:
                sync_priority = 'high'
            elif change_frequency == 'medium':
                sync_priority = 'normal'
            else:
                sync_priority = 'low'
            
            # Calculate next sync interval
            next_sync_interval = await self._calculate_next_sync_interval(user_id, results)
            
            # Update user activity state
            state_data = {
                'user_id': user_id,
                'last_sync_at': datetime.now().isoformat(),
                'change_frequency': change_frequency,
                'virtual_email_activity': virtual_email_activity,
                'auto_scheduled_meetings': auto_scheduled_meetings,
                'sync_priority': sync_priority,
                'next_sync_interval': next_sync_interval,
                'updated_at': datetime.now().isoformat()
            }
            
            self.supabase.table("user_sync_states").upsert(state_data).execute()
            
            logger.info(f"Updated user activity state for user {user_id}: {change_frequency} frequency, {sync_priority} priority")
            
        except Exception as e:
            logger.error(f"Failed to update user activity state: {e}")
    
    async def calculate_next_sync_interval(self, user_id: str, results: List[Dict[str, Any]]) -> int:
        """
        Calculate next sync interval based on sync results and user activity.
        
        Args:
            user_id: User ID
            results: List of sync results
            
        Returns:
            Next sync interval in minutes
        """
        try:
            # Get current user activity state
            current_state = await self._get_user_activity_state(user_id)
            
            # Calculate total changes
            total_changes = sum(
                r.get('items_created', 0) + r.get('items_updated', 0) + r.get('items_deleted', 0)
                for r in results
            )
            
            # Base interval calculation
            if total_changes == 0:
                # No changes - increase interval
                base_interval = current_state.get('next_sync_interval', 30)
                new_interval = min(base_interval * 1.5, 120)  # Max 2 hours
            elif total_changes <= 5:
                # Low activity - moderate interval
                new_interval = 30
            elif total_changes <= 20:
                # Medium activity - frequent sync
                new_interval = 15
            else:
                # High activity - very frequent sync
                new_interval = 10
            
            # Adjust based on virtual email activity
            gmail_result = next((r for r in results if r.get('service') == 'gmail'), {})
            if gmail_result.get('items_created', 0) > 0:
                # Virtual emails detected - sync more frequently
                new_interval = max(new_interval // 2, 5)
            
            # Adjust based on meeting activity
            attendee_result = next((r for r in results if r.get('service') == 'attendee'), {})
            if attendee_result.get('items_updated', 0) > 0:
                # Active meetings - sync more frequently
                new_interval = max(new_interval // 1.5, 5)
            
            return int(new_interval)
            
        except Exception as e:
            logger.error(f"Failed to calculate next sync interval: {e}")
            return 30  # Default to 30 minutes
    
    # Private helper methods
    
    async def _should_sync_user(self, user_id: str) -> bool:
        """Determine if a user should be synced based on activity patterns."""
        try:
            # Get user's last sync time
            last_sync = await self._get_user_last_sync(user_id)
            if not last_sync:
                return True  # First sync
            
            # Get next sync interval
            next_interval = await self._get_next_sync_interval(user_id)
            
            # Check if enough time has passed
            time_since_last_sync = datetime.now() - last_sync
            if time_since_last_sync < timedelta(minutes=next_interval):
                return False
            
            # Check for recent user activity
            last_activity = await self._get_user_last_activity(user_id)
            if last_activity:
                time_since_activity = datetime.now() - last_activity
                if time_since_activity < timedelta(minutes=15):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to determine if user should be synced: {e}")
            return True
    
    async def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user's email address."""
        try:
            result = self.supabase.table("users") \
                .select("email") \
                .eq("id", user_id) \
                .single() \
                .execute()
            
            return result.data.get('email') if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get user email for {user_id}: {e}")
            return None
    
    async def _get_user_active_drive_files(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's active Drive files."""
        try:
            result = self.supabase.table("drive_file_watches") \
                .select("file_id, document_id") \
                .eq("user_id", user_id) \
                .eq("status", "active") \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get active Drive files for user {user_id}: {e}")
            return []
    
    async def _record_user_activity(self, user_id: str, activity_type: str):
        """Record user activity."""
        await self.record_user_activity(user_id, activity_type)
    
    async def _update_user_activity_state(self, user_id: str, results: List[Dict[str, Any]]):
        """Update user activity state."""
        await self.update_user_activity_state(user_id, results)
    
    async def _store_sync_result(self, result: SyncResult):
        """Store sync result in database."""
        try:
            result_data = result.dict()
            result_data['timestamp'] = result_data['timestamp'].isoformat()
            
            self.supabase.table("sync_results").insert(result_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to store sync result: {e}")
    
    async def _get_user_activity_state(self, user_id: str) -> Dict[str, Any]:
        """Get user's current activity state."""
        try:
            result = self.supabase.table("user_sync_states") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data if result.data else {}
            
        except Exception as e:
            logger.error(f"Failed to get user activity state: {e}")
            return {}
    
    async def _get_user_last_sync(self, user_id: str) -> Optional[datetime]:
        """Get user's last sync time."""
        try:
            result = self.supabase.table("user_sync_states") \
                .select("last_sync_at") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data and result.data.get('last_sync_at'):
                return datetime.fromisoformat(result.data['last_sync_at'].replace('Z', '+00:00'))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user last sync: {e}")
            return None
    
    async def _get_next_sync_interval(self, user_id: str) -> int:
        """Get user's next sync interval."""
        try:
            result = self.supabase.table("user_sync_states") \
                .select("next_sync_interval") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            return result.data.get('next_sync_interval', 30) if result.data else 30
            
        except Exception as e:
            logger.error(f"Failed to get next sync interval: {e}")
            return 30
    
    async def _get_user_last_activity(self, user_id: str) -> Optional[datetime]:
        """Get user's last activity timestamp."""
        try:
            result = self.supabase.table("user_activity_logs") \
                .select("timestamp") \
                .eq("user_id", user_id) \
                .order("timestamp", desc=True) \
                .limit(1) \
                .single() \
                .execute()
            
            if result.data and result.data.get('timestamp'):
                return datetime.fromisoformat(result.data['timestamp'].replace('Z', '+00:00'))
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user last activity: {e}")
            return None
    
    async def sync_all_users(self) -> List[Dict[str, Any]]:
        """Sync all services for all users."""
        try:
            logger.info("Starting sync for all users")
            
            # Get all active users
            users = await self._get_all_active_users()
            if not users:
                return [{
                    'success': True,
                    'message': 'No active users found',
                    'total_users': 0
                }]
            
            # Sync each user
            all_results = []
            for user in users:
                user_result = await self.sync_all_services(user['id'], force_sync=False)
                all_results.extend(user_result)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Sync all users failed: {e}")
            return [{
                'success': False,
                'error': str(e),
                'total_users': 0
            }]
    
    async def sync_all_calendars(self) -> List[Dict[str, Any]]:
        """Sync calendar for all users."""
        try:
            logger.info("Starting calendar sync for all users")
            
            # Get all active users
            users = await self._get_all_active_users()
            if not users:
                return [{
                    'success': True,
                    'message': 'No active users found',
                    'total_users': 0
                }]
            
            # Sync calendar for each user
            all_results = []
            for user in users:
                user_result = await self.sync_calendar(user['id'], force_sync=False)
                all_results.append(user_result)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Sync all calendars failed: {e}")
            return [{
                'success': False,
                'error': str(e),
                'total_users': 0
            }]
    
    async def sync_all_drives(self) -> List[Dict[str, Any]]:
        """Sync drive for all users."""
        try:
            logger.info("Starting drive sync for all users")
            
            # Get all active users
            users = await self._get_all_active_users()
            if not users:
                return [{
                    'success': True,
                    'message': 'No active users found',
                    'total_users': 0
                }]
            
            # Sync drive for each user
            all_results = []
            for user in users:
                user_result = await self.sync_drive(user['id'], force_sync=False)
                all_results.append(user_result)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Sync all drives failed: {e}")
            return [{
                'success': False,
                'error': str(e),
                'total_users': 0
            }]
    
    async def sync_all_gmails(self) -> List[Dict[str, Any]]:
        """Sync Gmail for all users."""
        try:
            logger.info("Starting Gmail sync for all users")
            
            # Get all active users
            users = await self._get_all_active_users()
            if not users:
                return [{
                    'success': True,
                    'message': 'No active users found',
                    'total_users': 0
                }]
            
            # Sync Gmail for each user
            all_results = []
            for user in users:
                user_email = await self._get_user_email(user['id'])
                if user_email:
                    user_result = await self.sync_gmail(user['id'], user_email, force_sync=False)
                    all_results.append(user_result)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Sync all Gmail accounts failed: {e}")
            return [{
                'success': False,
                'error': str(e),
                'total_users': 0
            }]
    
    async def sync_all_attendees(self) -> List[Dict[str, Any]]:
        """Sync attendee for all users."""
        try:
            logger.info("Starting attendee sync for all users")
            
            # Get all active users
            users = await self._get_all_active_users()
            if not users:
                return [{
                    'success': True,
                    'message': 'No active users found',
                    'total_users': 0
                }]
            
            # Sync attendee for each user
            all_results = []
            for user in users:
                user_result = await self.sync_attendee(user['id'], force_sync=False)
                all_results.append(user_result)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Sync all attendees failed: {e}")
            return [{
                'success': False,
                'error': str(e),
                'total_users': 0
            }]
    
    async def optimize_all_sync_intervals(self) -> Dict[str, Any]:
        """Optimize sync intervals for all users."""
        try:
            logger.info("Starting sync interval optimization for all users")
            
            # Get all active users
            users = await self._get_all_active_users()
            if not users:
                return {
                    'success': True,
                    'message': 'No active users found',
                    'total_users': 0
                }
            
            # Optimize intervals for each user
            optimized_count = 0
            for user in users:
                try:
                    await self._optimize_user_sync_interval(user['id'])
                    optimized_count += 1
                except Exception as e:
                    logger.error(f"Failed to optimize sync interval for user {user['id']}: {e}")
            
            return {
                'success': True,
                'message': f'Optimized sync intervals for {optimized_count} users',
                'total_users': len(users),
                'optimized_users': optimized_count
            }
            
        except Exception as e:
            logger.error(f"Sync interval optimization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_users': 0
            }
    
    async def _get_all_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users."""
        try:
            result = self.supabase.table("users") \
                .select("id") \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get all active users: {e}")
            return []
    
    async def _optimize_user_sync_interval(self, user_id: str):
        """Optimize sync interval for a specific user."""
        try:
            # Get user's activity patterns
            activity_state = await self._get_user_activity_state(user_id)
            
            # Calculate optimal interval based on activity
            if activity_state.get('change_frequency') == 'high':
                optimal_interval = 15  # 15 minutes for high activity
            elif activity_state.get('change_frequency') == 'medium':
                optimal_interval = 30  # 30 minutes for medium activity
            else:
                optimal_interval = 60  # 60 minutes for low activity
            
            # Update user's sync interval
            await self._update_user_sync_interval(user_id, optimal_interval)
            
        except Exception as e:
            logger.error(f"Failed to optimize sync interval for user {user_id}: {e}")
    
    async def _update_user_sync_interval(self, user_id: str, interval_minutes: int):
        """Update user's sync interval."""
        try:
            self.supabase.table("user_sync_states") \
                .upsert({
                    'user_id': user_id,
                    'next_sync_interval': interval_minutes,
                    'updated_at': datetime.now().isoformat()
                }) \
                .execute()
            
        except Exception as e:
            logger.error(f"Failed to update sync interval for user {user_id}: {e}")
