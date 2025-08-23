"""
Calendar monitoring service for BeSunny.ai Python backend.
Monitors calendar sync health, detects issues, and provides alerts.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ...core.database import get_supabase
from ...core.config import get_settings

logger = logging.getLogger(__name__)


class CalendarHealthMetrics(BaseModel):
    """Calendar health metrics for monitoring."""
    user_id: str
    webhook_status: str
    last_sync: Optional[datetime]
    sync_frequency: str
    error_rate: float
    last_error: Optional[str]
    health_score: float
    timestamp: datetime


class CalendarAlert(BaseModel):
    """Calendar alert for monitoring issues."""
    alert_id: str
    user_id: str
    alert_type: str
    severity: str
    message: str
    details: Dict[str, Any]
    created_at: datetime
    resolved_at: Optional[datetime]
    status: str


class CalendarMonitoringService:
    """Service for monitoring calendar sync health and detecting issues."""
    
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase()
        
        # Alert thresholds
        self.error_rate_threshold = 0.1  # 10%
        self.sync_delay_threshold = timedelta(hours=2)
        self.webhook_failure_threshold = 3
        
        logger.info("Calendar Monitoring Service initialized")
    
    async def monitor_all_calendars(self) -> Dict[str, Any]:
        """
        Monitor all active calendars for health issues.
        
        Returns:
            Monitoring results and alerts
        """
        try:
            logger.info("Starting comprehensive calendar monitoring")
            
            # Get all active users with calendar integration
            active_users = await self._get_active_users_with_calendar()
            if not active_users:
                return {
                    'success': True,
                    'message': 'No active users with calendar integration found',
                    'total_users': 0,
                    'alerts_generated': 0
                }
            
            monitoring_results = []
            total_alerts = 0
            
            for user in active_users:
                try:
                    # Monitor individual user
                    user_result = await self.monitor_user_calendar(user['id'])
                    monitoring_results.append(user_result)
                    
                    if user_result.get('alerts'):
                        total_alerts += len(user_result['alerts'])
                        
                except Exception as e:
                    logger.error(f"Error monitoring user {user['id']}: {e}")
                    continue
            
            # Generate summary report
            summary = await self._generate_monitoring_summary(monitoring_results)
            
            # Store monitoring results
            await self._store_monitoring_results(summary)
            
            logger.info(f"Calendar monitoring completed: {total_alerts} alerts generated")
            
            return {
                'success': True,
                'total_users': len(active_users),
                'alerts_generated': total_alerts,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Calendar monitoring failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def monitor_user_calendar(self, user_id: str) -> Dict[str, Any]:
        """
        Monitor calendar health for a specific user.
        
        Args:
            user_id: User ID to monitor
            
        Returns:
            User monitoring results
        """
        try:
            logger.info(f"Monitoring calendar health for user {user_id}")
            
            # Get health metrics
            health_metrics = await self._get_user_health_metrics(user_id)
            
            # Check for issues
            issues = await self._detect_calendar_issues(user_id, health_metrics)
            
            # Generate alerts for issues
            alerts = []
            for issue in issues:
                alert = await self._create_calendar_alert(user_id, issue)
                if alert:
                    alerts.append(alert)
            
            # Calculate overall health score
            health_score = self._calculate_health_score(health_metrics, issues)
            
            return {
                'user_id': user_id,
                'health_metrics': health_metrics.dict(),
                'issues_detected': len(issues),
                'alerts': [alert.dict() for alert in alerts],
                'health_score': health_score,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to monitor user {user_id}: {e}")
            return {
                'user_id': user_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_user_health_metrics(self, user_id: str) -> CalendarHealthMetrics:
        """Get comprehensive health metrics for a user."""
        try:
            # Get webhook status
            webhook_result = await self.supabase.table('calendar_webhooks') \
                .select('*') \
                .eq('user_id', user_id) \
                .single() \
                .execute()
            
            webhook_status = 'active' if webhook_result.data and webhook_result.data.get('is_active') else 'inactive'
            
            # Get last sync time
            sync_result = await self.supabase.table('calendar_sync_states') \
                .select('last_sync_at') \
                .eq('user_id', user_id) \
                .single() \
                .execute()
            
            last_sync = None
            if sync_result.data and sync_result.data.get('last_sync_at'):
                last_sync = datetime.fromisoformat(sync_result.data['last_sync_at'].replace('Z', '+00:00'))
            
            # Calculate sync frequency
            sync_frequency = self._calculate_sync_frequency(user_id, last_sync)
            
            # Calculate error rate
            error_rate = await self._calculate_error_rate(user_id)
            
            # Get last error
            last_error = await self._get_last_error(user_id)
            
            # Calculate health score
            health_score = self._calculate_health_score_from_metrics(
                webhook_status, last_sync, error_rate
            )
            
            return CalendarHealthMetrics(
                user_id=user_id,
                webhook_status=webhook_status,
                last_sync=last_sync,
                sync_frequency=sync_frequency,
                error_rate=error_rate,
                last_error=last_error,
                health_score=health_score,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get health metrics for user {user_id}: {e}")
            return CalendarHealthMetrics(
                user_id=user_id,
                webhook_status='unknown',
                last_sync=None,
                sync_frequency='unknown',
                error_rate=1.0,
                last_error=str(e),
                health_score=0.0,
                timestamp=datetime.now()
            )
    
    async def _detect_calendar_issues(self, user_id: str, health_metrics: CalendarHealthMetrics) -> List[Dict[str, Any]]:
        """Detect calendar issues based on health metrics."""
        issues = []
        
        try:
            # Check webhook status
            if health_metrics.webhook_status != 'active':
                issues.append({
                    'type': 'webhook_inactive',
                    'severity': 'high',
                    'message': f'Calendar webhook is {health_metrics.webhook_status}',
                    'details': {'webhook_status': health_metrics.webhook_status}
                })
            
            # Check sync delay
            if health_metrics.last_sync:
                time_since_sync = datetime.now() - health_metrics.last_sync
                if time_since_sync > self.sync_delay_threshold:
                    issues.append({
                        'type': 'sync_delayed',
                        'severity': 'medium',
                        'message': f'Calendar sync delayed by {time_since_sync}',
                        'details': {
                            'last_sync': health_metrics.last_sync.isoformat(),
                            'delay_duration': str(time_since_sync)
                        }
                    })
            
            # Check error rate
            if health_metrics.error_rate > self.error_rate_threshold:
                issues.append({
                    'type': 'high_error_rate',
                    'severity': 'high',
                    'message': f'High error rate: {health_metrics.error_rate:.1%}',
                    'details': {'error_rate': health_metrics.error_rate}
                })
            
            # Check for consecutive failures
            consecutive_failures = await self._get_consecutive_failures(user_id)
            if consecutive_failures >= self.webhook_failure_threshold:
                issues.append({
                    'type': 'consecutive_failures',
                    'severity': 'critical',
                    'message': f'{consecutive_failures} consecutive webhook failures',
                    'details': {'consecutive_failures': consecutive_failures}
                })
            
            # Check for missing meetings
            missing_meetings = await self._detect_missing_meetings(user_id)
            if missing_meetings:
                issues.append({
                    'type': 'missing_meetings',
                    'severity': 'medium',
                    'message': f'{len(missing_meetings)} meetings may be missing',
                    'details': {'missing_meetings': missing_meetings}
                })
            
        except Exception as e:
            logger.error(f"Error detecting issues for user {user_id}: {e}")
            issues.append({
                'type': 'monitoring_error',
                'severity': 'high',
                'message': f'Error during issue detection: {e}',
                'details': {'error': str(e)}
            })
        
        return issues
    
    async def _create_calendar_alert(self, user_id: str, issue: Dict[str, Any]) -> Optional[CalendarAlert]:
        """Create a calendar alert for an issue."""
        try:
            alert_id = f"calendar_alert_{user_id}_{int(datetime.now().timestamp())}"
            
            alert = CalendarAlert(
                alert_id=alert_id,
                user_id=user_id,
                alert_type=issue['type'],
                severity=issue['severity'],
                message=issue['message'],
                details=issue['details'],
                created_at=datetime.now(),
                resolved_at=None,
                status='active'
            )
            
            # Store alert in database
            await self.supabase.table('calendar_alerts').insert(alert.dict()).execute()
            
            # Send notification if critical
            if issue['severity'] == 'critical':
                await self._send_critical_alert_notification(user_id, alert)
            
            logger.info(f"Created calendar alert {alert_id} for user {user_id}")
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert for user {user_id}: {e}")
            return None
    
    async def _send_critical_alert_notification(self, user_id: str, alert: CalendarAlert):
        """Send notification for critical alerts."""
        try:
            # This would integrate with your notification system
            # For now, just log the critical alert
            logger.warning(f"CRITICAL CALENDAR ALERT for user {user_id}: {alert.message}")
            
            # You could send email, Slack, etc. here
            # await notification_service.send_critical_alert(user_id, alert)
            
        except Exception as e:
            logger.error(f"Failed to send critical alert notification: {e}")
    
    def _calculate_health_score(self, health_metrics: CalendarHealthMetrics, issues: List[Dict[str, Any]]) -> float:
        """Calculate overall health score."""
        try:
            base_score = health_metrics.health_score
            
            # Deduct points for issues
            issue_penalties = {
                'critical': 0.4,
                'high': 0.2,
                'medium': 0.1,
                'low': 0.05
            }
            
            total_penalty = 0
            for issue in issues:
                penalty = issue_penalties.get(issue['severity'], 0)
                total_penalty += penalty
            
            final_score = max(0.0, base_score - total_penalty)
            return round(final_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0
    
    def _calculate_health_score_from_metrics(self, webhook_status: str, last_sync: Optional[datetime], error_rate: float) -> float:
        """Calculate health score from individual metrics."""
        try:
            score = 1.0
            
            # Webhook status penalty
            if webhook_status != 'active':
                score -= 0.3
            
            # Sync delay penalty
            if last_sync:
                time_since_sync = datetime.now() - last_sync
                if time_since_sync > timedelta(hours=1):
                    score -= 0.2
                elif time_since_sync > timedelta(minutes=30):
                    score -= 0.1
            
            # Error rate penalty
            score -= min(0.4, error_rate)
            
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating health score from metrics: {e}")
            return 0.0
    
    def _calculate_sync_frequency(self, user_id: str, last_sync: Optional[datetime]) -> str:
        """Calculate sync frequency based on recent activity."""
        try:
            if not last_sync:
                return 'unknown'
            
            time_since_sync = datetime.now() - last_sync
            
            if time_since_sync < timedelta(minutes=15):
                return 'very_frequent'
            elif time_since_sync < timedelta(hours=1):
                return 'frequent'
            elif time_since_sync < timedelta(hours=4):
                return 'normal'
            elif time_since_sync < timedelta(hours=12):
                return 'infrequent'
            else:
                return 'very_infrequent'
                
        except Exception as e:
            logger.error(f"Error calculating sync frequency: {e}")
            return 'unknown'
    
    async def _calculate_error_rate(self, user_id: str) -> float:
        """Calculate error rate for recent operations."""
        try:
            # Get recent webhook logs
            week_ago = datetime.now() - timedelta(days=7)
            
            result = await self.supabase.table('calendar_webhook_logs') \
                .select('processing_status') \
                .eq('user_id', user_id) \
                .gte('created_at', week_ago.isoformat()) \
                .execute()
            
            if not result.data:
                return 0.0
            
            total_operations = len(result.data)
            failed_operations = len([log for log in result.data if log.get('processing_status') == 'failed'])
            
            return failed_operations / total_operations if total_operations > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 1.0
    
    async def _get_last_error(self, user_id: str) -> Optional[str]:
        """Get the last error message for a user."""
        try:
            result = await self.supabase.table('calendar_webhook_logs') \
                .select('error_message') \
                .eq('user_id', user_id) \
                .not_.is_('error_message', 'null') \
                .order('created_at', desc=True) \
                .limit(1) \
                .single() \
                .execute()
            
            return result.data.get('error_message') if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting last error: {e}")
            return None
    
    async def _get_consecutive_failures(self, user_id: str) -> int:
        """Get count of consecutive failures."""
        try:
            result = await self.supabase.table('calendar_webhook_logs') \
                .select('processing_status') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .limit(10) \
                .execute()
            
            if not result.data:
                return 0
            
            consecutive_failures = 0
            for log in result.data:
                if log.get('processing_status') == 'failed':
                    consecutive_failures += 1
                else:
                    break
            
            return consecutive_failures
            
        except Exception as e:
            logger.error(f"Error getting consecutive failures: {e}")
            return 0
    
    async def _detect_missing_meetings(self, user_id: str) -> List[Dict[str, Any]]:
        """Detect potentially missing meetings."""
        try:
            # Get meetings from last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            
            result = await self.supabase.table('meetings') \
                .select('start_time, end_time, title') \
                .eq('user_id', user_id) \
                .gte('start_time', week_ago.isoformat()) \
                .execute()
            
            if not result.data:
                return []
            
            # Check for gaps in meeting schedule during business hours
            business_hours = []
            for meeting in result.data:
                start_time = datetime.fromisoformat(meeting['start_time'].replace('Z', '+00:00'))
                if start_time.hour >= 9 and start_time.hour <= 17:  # Business hours
                    business_hours.append(start_time)
            
            # Sort by time
            business_hours.sort()
            
            # Look for gaps longer than 4 hours during business hours
            missing_meetings = []
            for i in range(len(business_hours) - 1):
                gap = business_hours[i + 1] - business_hours[i]
                if gap > timedelta(hours=4):
                    missing_meetings.append({
                        'gap_start': business_hours[i].isoformat(),
                        'gap_end': business_hours[i + 1].isoformat(),
                        'gap_duration': str(gap)
                    })
            
            return missing_meetings
            
        except Exception as e:
            logger.error(f"Error detecting missing meetings: {e}")
            return []
    
    async def _get_active_users_with_calendar(self) -> List[Dict[str, Any]]:
        """Get all active users with calendar integration."""
        try:
            response = await self.supabase.table('users').select(
                'id, email, google_credentials, calendar_webhooks'
            ).eq('is_active', True).not_.is_('google_credentials', 'null').execute()
            
            if response.data:
                return response.data
            return []
            
        except Exception as e:
            logger.error(f"Error getting active users with calendar: {str(e)}")
            return []
    
    async def _generate_monitoring_summary(self, monitoring_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of monitoring results."""
        try:
            total_users = len(monitoring_results)
            healthy_users = len([r for r in monitoring_results if r.get('health_score', 0) >= 0.8])
            warning_users = len([r for r in monitoring_results if 0.5 <= r.get('health_score', 0) < 0.8])
            critical_users = len([r for r in monitoring_results if r.get('health_score', 0) < 0.5])
            
            total_alerts = sum(len(r.get('alerts', [])) for r in monitoring_results)
            
            avg_health_score = sum(r.get('health_score', 0) for r in monitoring_results) / total_users if total_users > 0 else 0
            
            return {
                'total_users': total_users,
                'healthy_users': healthy_users,
                'warning_users': warning_users,
                'critical_users': critical_users,
                'total_alerts': total_alerts,
                'average_health_score': round(avg_health_score, 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating monitoring summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _store_monitoring_results(self, summary: Dict[str, Any]):
        """Store monitoring results in database."""
        try:
            await self.supabase.table('calendar_monitoring_results').insert({
                'summary_data': summary,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"Error storing monitoring results: {e}")
    
    async def get_user_alerts(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get alerts for a specific user."""
        try:
            result = await self.supabase.table('calendar_alerts') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting user alerts: {e}")
            return []
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        try:
            await self.supabase.table('calendar_alerts') \
                .update({
                    'status': 'resolved',
                    'resolved_at': datetime.now().isoformat()
                }) \
                .eq('alert_id', alert_id) \
                .execute()
            
            logger.info(f"Alert {alert_id} marked as resolved")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
