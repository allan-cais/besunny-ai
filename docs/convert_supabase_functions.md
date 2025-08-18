# Supabase Edge Functions to Python Backend Conversion Roadmap

## Executive Summary

This document provides a comprehensive roadmap for converting all Supabase edge functions to Python backend functionality within the existing FastAPI-based architecture. The conversion will consolidate the distributed edge function logic into centralized, maintainable backend services while preserving all existing functionality and improving performance, monitoring, and development velocity.

## Current State Analysis

### Supabase Edge Functions Overview

The current system consists of **32 edge functions** across several functional categories:

1. **Core Services** (8 functions)
2. **Polling Services** (6 functions) 
3. **Webhook Handlers** (4 functions)
4. **Cron Jobs** (6 functions)
5. **OAuth & Authentication** (3 functions)
6. **AI & Classification** (2 functions)
7. **Utility Functions** (3 functions)

### Existing Backend Infrastructure

The Python backend already has:
- FastAPI application structure
- Service layer architecture
- Database models and schemas
- Google services integration
- AI service integration
- Redis caching
- Celery task queue

## Conversion Strategy

### Phase 1: Core Service Migration (Weeks 1-3)
Convert the most critical and frequently used services first.

### Phase 2: Polling & Sync Services (Weeks 4-6)
Migrate the polling and synchronization services.

### Phase 3: Webhook Handlers & Cron Jobs (Weeks 7-9)
Convert webhook handlers and scheduled tasks.

### Phase 4: OAuth & Authentication (Weeks 10-11)
Migrate authentication and OAuth services.

### Phase 5: AI & Classification (Weeks 12-13)
Convert AI-powered services.

### Phase 6: Testing & Optimization (Weeks 14-16)
Comprehensive testing and performance optimization.

## Detailed Function Analysis & Conversion Plan

### 1. Core Services

#### 1.1 Attendee Service (`attendee-service`)
**Current Implementation**: 444 lines of TypeScript
**Functionality**: Meeting bot management, transcript retrieval, chat functionality

**Conversion Plan**:
```python
# backend/app/services/attendee/attendee_service.py
class AttendeeService:
    async def poll_all_meetings(self) -> List[Dict]
    async def send_bot_to_meeting(self, options: Dict, user_id: str) -> Dict
    async def get_bot_status(self, bot_id: str) -> Dict
    async def get_transcript(self, bot_id: str) -> Dict
    async def auto_schedule_bots(self, user_id: str) -> List[Dict]
    async def get_chat_messages(self, bot_id: str) -> List[Dict]
    async def send_chat_message(self, bot_id: str, message: str, to: str) -> Dict
    async def get_participant_events(self, bot_id: str) -> List[Dict]
    async def pause_recording(self, bot_id: str) -> Dict
    async def resume_recording(self, bot_id: str) -> Dict
```

**API Endpoints**:
```python
# backend/app/api/v1/attendee.py
@router.post("/poll-all")
@router.post("/send-bot")
@router.get("/bot-status/{bot_id}")
@router.get("/transcript/{bot_id}")
@router.post("/auto-schedule")
@router.get("/chat-messages/{bot_id}")
@router.post("/send-chat")
@router.get("/participant-events/{bot_id}")
@router.post("/pause-recording")
@router.post("/resume-recording")
```

**Dependencies**: 
- Attendee API integration
- Meeting management
- Transcript processing
- Chat functionality

**Priority**: HIGH - Core meeting functionality

#### 1.2 Calendar Polling Service (`calendar-polling-service`)
**Current Implementation**: 484 lines of TypeScript
**Functionality**: Google Calendar synchronization, event processing, smart polling

**Conversion Plan**:
```python
# backend/app/services/calendar/calendar_polling_service.py
class CalendarPollingService:
    async def poll_calendar_for_user(self, user_id: str) -> Dict
    async def process_calendar_event(self, event: Dict, user_id: str, credentials: Dict) -> Dict
    async def handle_deleted_event(self, event_id: str, user_id: str) -> Dict
    async def extract_meeting_url(self, event: Dict) -> Optional[str]
    async def smart_calendar_polling(self, user_id: str) -> Dict
```

**API Endpoints**:
```python
# backend/app/api/v1/calendar.py
@router.post("/poll/{user_id}")
@router.post("/sync/{user_id}")
@router.post("/process-event")
@router.post("/handle-deletion")
```

**Dependencies**:
- Google Calendar API
- Meeting extraction
- Event processing
- Smart polling logic

**Priority**: HIGH - Core calendar functionality

#### 1.3 Drive Polling Service (`drive-polling-service`)
**Current Implementation**: 365 lines of TypeScript
**Functionality**: Google Drive file monitoring, change detection, n8n integration

**Conversion Plan**:
```python
# backend/app/services/drive/drive_polling_service.py
class DrivePollingService:
    async def poll_drive_for_file(self, file_id: str, document_id: str) -> Dict
    async def check_file_changes(self, file_id: str, access_token: str) -> Dict
    async def handle_file_deletion(self, document_id: str, project_id: str, file_id: str) -> None
    async def send_to_n8n_webhook(self, document_id: str, project_id: str, file_id: str, action: str) -> bool
    async def smart_drive_polling(self, file_id: str, document_id: str) -> Dict
```

**API Endpoints**:
```python
# backend/app/api/v1/drive.py
@router.post("/poll/{file_id}")
@router.post("/check-changes/{file_id}")
@router.post("/handle-deletion")
@router.post("/n8n-webhook")
```

**Dependencies**:
- Google Drive API
- File change detection
- n8n webhook integration
- Document management

**Priority**: HIGH - Core drive functionality

#### 1.4 Gmail Polling Service (`gmail-polling-service`)
**Current Implementation**: 383 lines of TypeScript
**Functionality**: Gmail monitoring, virtual email detection, email processing

**Conversion Plan**:
```python
# backend/app/services/email/gmail_polling_service.py
class GmailPollingService:
    async def poll_gmail_for_user(self, user_email: str) -> Dict
    async def process_virtual_email_detection(self, user_email: str, message_id: str, virtual_emails: List[Dict]) -> None
    async def check_for_virtual_emails(self, to_emails: List[str], cc_emails: List[str]) -> List[Dict]
    async def extract_email_addresses(self, headers: List[Dict], header_name: str) -> List[str]
    async def smart_gmail_polling(self, user_email: str) -> Dict
```

**API Endpoints**:
```python
# backend/app/api/v1/email.py
@router.post("/poll-gmail/{user_email}")
@router.post("/process-virtual-email")
@router.post("/detect-virtual-emails")
@router.post("/extract-addresses")
```

**Dependencies**:
- Gmail API
- Virtual email detection
- Email processing
- Document creation

**Priority**: HIGH - Core email functionality

#### 1.5 Enhanced Adaptive Sync Service (`enhanced-adaptive-sync-service`)
**Current Implementation**: 594 lines of TypeScript
**Functionality**: Multi-service synchronization, activity tracking, adaptive sync intervals

**Conversion Plan**:
```python
# backend/app/services/sync/enhanced_adaptive_sync_service.py
class EnhancedAdaptiveSyncService:
    async def sync_all_services(self, user_id: str, force_sync: bool = False) -> List[Dict]
    async def sync_calendar(self, user_id: str, force_sync: bool = False) -> Dict
    async def sync_drive(self, user_id: str, force_sync: bool = False) -> Dict
    async def sync_gmail(self, user_id: str, force_sync: bool = False) -> Dict
    async def sync_attendee(self, user_id: str, force_sync: bool = False) -> Dict
    async def record_user_activity(self, user_id: str, activity_type: str) -> None
    async def update_user_activity_state(self, user_id: str, results: List[Dict]) -> None
    async def calculate_next_sync_interval(self, user_id: str, results: List[Dict]) -> int
```

**API Endpoints**:
```python
# backend/app/api/v1/sync.py
@router.post("/sync-all/{user_id}")
@router.post("/sync/{service}/{user_id}")
@router.post("/record-activity")
@router.get("/next-sync/{user_id}")
```

**Dependencies**:
- All service integrations
- Activity tracking
- Sync optimization
- Performance metrics

**Priority**: HIGH - Core sync functionality

#### 1.6 Project Onboarding AI (`project-onboarding-ai`)
**Current Implementation**: 312 lines of TypeScript
**Functionality**: AI-powered project metadata generation, OpenAI integration

**Conversion Plan**:
```python
# backend/app/services/ai/project_onboarding_service.py
class ProjectOnboardingAIService:
    async def process_project_onboarding(self, project_id: str, user_id: str, summary: Dict) -> Dict
    async def generate_project_metadata(self, summary: Dict) -> Dict
    async def validate_metadata(self, metadata: Dict) -> bool
    async def update_project_metadata(self, project_id: str, metadata: Dict) -> bool
    async def create_project_metadata_record(self, project_id: str, metadata: Dict) -> bool
```

**API Endpoints**:
```python
# backend/app/api/v1/ai.py
@router.post("/project-onboarding")
@router.post("/generate-metadata")
@router.post("/validate-metadata")
@router.put("/update-metadata/{project_id}")
```

**Dependencies**:
- OpenAI API
- Project management
- Metadata generation
- AI processing

**Priority**: MEDIUM - AI enhancement

#### 1.7 Google OAuth Login (`google-oauth-login`)
**Current Implementation**: 211 lines of TypeScript
**Functionality**: Google OAuth authentication, user creation, session management

**Conversion Plan**:
```python
# backend/app/services/auth/google_oauth_service.py
class GoogleOAuthService:
    async def handle_oauth_callback(self, code: str) -> Dict
    async def exchange_code_for_tokens(self, code: str) -> Dict
    async def get_user_info(self, access_token: str) -> Dict
    async def create_or_update_user(self, user_info: Dict, tokens: Dict) -> str
    async def create_user_session(self, user_id: str) -> Dict
    async def refresh_access_token(self, refresh_token: str) -> Dict
```

**API Endpoints**:
```python
# backend/app/api/v1/auth.py
@router.post("/google/oauth/callback")
@router.post("/google/oauth/refresh")
@router.get("/google/user-info")
@router.post("/google/session")
```

**Dependencies**:
- Google OAuth API
- User management
- Session handling
- Token refresh

**Priority**: HIGH - Authentication core

#### 1.8 Exchange Google Token (`exchange-google-token`)
**Current Implementation**: Basic token exchange
**Functionality**: Google token refresh and exchange

**Conversion Plan**:
```python
# backend/app/services/auth/google_token_service.py
class GoogleTokenService:
    async def exchange_token(self, refresh_token: str) -> Dict
    async def refresh_user_tokens(self, user_id: str) -> Dict
    async def validate_token(self, access_token: str) -> bool
    async def revoke_tokens(self, user_id: str) -> bool
```

**API Endpoints**:
```python
# backend/app/api/v1/auth.py
@router.post("/google/token/exchange")
@router.post("/google/token/refresh")
@router.post("/google/token/validate")
@router.post("/google/token/revoke")
```

**Priority**: MEDIUM - Token management

### 2. Polling Services

#### 2.1 Attendee Polling Service (`attendee-polling-service`)
**Current Implementation**: Basic polling wrapper
**Functionality**: Meeting status polling

**Conversion Plan**:
```python
# backend/app/services/attendee/attendee_polling_service.py
class AttendeePollingService:
    async def poll_meeting_status(self, meeting_id: str) -> Dict
    async def poll_all_user_meetings(self, user_id: str) -> List[Dict]
    async def handle_polling_results(self, results: List[Dict]) -> Dict
```

**Priority**: MEDIUM - Polling enhancement

#### 2.2 Calendar Polling Service (`calendar-polling-service`)
**Current Implementation**: Already covered in core services
**Priority**: N/A - Already planned

#### 2.3 Drive Polling Service (`drive-polling-service`)
**Current Implementation**: Already covered in core services
**Priority**: N/A - Already planned

#### 2.4 Gmail Polling Service (`gmail-polling-service`)
**Current Implementation**: Already covered in core services
**Priority**: N/A - Already planned

#### 2.5 Attendee Polling Cron (`attendee-polling-cron`)
**Current Implementation**: Scheduled polling execution
**Functionality**: Batch meeting polling

**Conversion Plan**:
```python
# backend/app/services/attendee/attendee_polling_cron.py
class AttendeePollingCronService:
    async def execute_polling_cron(self) -> Dict
    async def poll_all_active_meetings(self) -> Dict
    async def handle_cron_results(self, results: List[Dict]) -> Dict
```

**Celery Task**:
```python
# backend/app/core/celery_app.py
@celery_app.task
def attendee_polling_cron():
    service = AttendeePollingCronService()
    return asyncio.run(service.execute_polling_cron())
```

**Priority**: MEDIUM - Scheduled tasks

#### 2.6 Gmail Polling Cron (`gmail-polling-cron`)
**Current Implementation**: Scheduled Gmail polling
**Functionality**: Batch email processing

**Conversion Plan**:
```python
# backend/app/services/email/gmail_polling_cron.py
class GmailPollingCronService:
    async def execute_polling_cron(self) -> Dict
    async def poll_all_active_gmail_accounts(self) -> Dict
    async def handle_cron_results(self, results: List[Dict]) -> Dict
```

**Celery Task**:
```python
# backend/app/core/celery_app.py
@celery_app.task
def gmail_polling_cron():
    service = GmailPollingCronService()
    return asyncio.run(service.execute_polling_cron())
```

**Priority**: MEDIUM - Scheduled tasks

### 3. Webhook Handlers

#### 3.1 Calendar Webhook Public (`calendar-webhook-public`)
**Current Implementation**: 273 lines of TypeScript
**Functionality**: Google Calendar webhook processing, event synchronization

**Conversion Plan**:
```python
# backend/app/api/v1/webhooks/calendar_webhook.py
@router.post("/webhooks/calendar")
@router.get("/webhooks/calendar/verify")
async def handle_calendar_webhook(request: Request) -> Dict
async def verify_webhook_challenge(challenge: str) -> str
async def process_calendar_webhook(user_id: str, webhook_data: Dict) -> Dict
```

**Priority**: HIGH - Webhook core

#### 3.2 Drive Webhook Handler (`drive-webhook-handler`)
**Current Implementation**: Google Drive webhook processing
**Functionality**: File change notifications

**Conversion Plan**:
```python
# backend/app/api/v1/webhooks/drive_webhook.py
@router.post("/webhooks/drive")
async def handle_drive_webhook(request: Request) -> Dict
async def process_drive_webhook(webhook_data: Dict) -> Dict
async def handle_file_change(file_id: str, change_type: str) -> Dict
```

**Priority**: HIGH - Webhook core

#### 3.3 Gmail Notification Handler (`gmail-notification-handler`)
**Current Implementation**: Gmail webhook processing
**Functionality**: Email notifications

**Conversion Plan**:
```python
# backend/app/api/v1/webhooks/gmail_webhook.py
@router.post("/webhooks/gmail")
async def handle_gmail_webhook(request: Request) -> Dict
async def process_gmail_webhook(webhook_data: Dict) -> Dict
async def handle_email_notification(notification: Dict) -> Dict
```

**Priority**: HIGH - Webhook core

#### 3.4 Google Calendar Webhook (`google-calendar-webhook`)
**Current Implementation**: Alternative calendar webhook
**Functionality**: Calendar event processing

**Conversion Plan**:
```python
# backend/app/api/v1/webhooks/google_calendar_webhook.py
@router.post("/webhooks/google-calendar")
async def handle_google_calendar_webhook(request: Request) -> Dict
async def process_google_calendar_webhook(webhook_data: Dict) -> Dict
```

**Priority**: MEDIUM - Alternative webhook

### 4. Cron Jobs

#### 4.1 Calendar Polling Cron (`calendar-polling-cron`)
**Current Implementation**: 144 lines of TypeScript
**Functionality**: Scheduled calendar synchronization

**Conversion Plan**:
```python
# backend/app/services/calendar/calendar_polling_cron.py
class CalendarPollingCronService:
    async def execute_polling_cron(self) -> Dict
    async def poll_all_active_calendars(self) -> Dict
    async def handle_cron_results(self, results: List[Dict]) -> Dict
```

**Celery Task**:
```python
# backend/app/core/celery_app.py
@celery_app.task
def calendar_polling_cron():
    service = CalendarPollingCronService()
    return asyncio.run(service.execute_polling_cron())
```

**Priority**: MEDIUM - Scheduled tasks

#### 4.2 Drive Polling Cron (`drive-polling-cron`)
**Current Implementation**: Scheduled drive synchronization
**Functionality**: File change polling

**Conversion Plan**:
```python
# backend/app/services/drive/drive_polling_cron.py
class DrivePollingCronService:
    async def execute_polling_cron(self) -> Dict
    async def poll_all_active_files(self) -> Dict
    async def handle_cron_results(self, results: List[Dict]) -> Dict
```

**Celery Task**:
```python
# backend/app/core/celery_app.py
@celery_app.task
def drive_polling_cron():
    service = DrivePollingCronService()
    return asyncio.run(service.execute_polling_cron())
```

**Priority**: MEDIUM - Scheduled tasks

#### 4.3 Renew Calendar Watches (`renew-calendar-watches`)
**Current Implementation**: Calendar watch renewal
**Functionality**: Webhook renewal

**Conversion Plan**:
```python
# backend/app/services/calendar/calendar_watch_renewal_service.py
class CalendarWatchRenewalService:
    async def renew_expired_watches(self) -> Dict
    async def renew_user_watches(self, user_id: str) -> Dict
    async def handle_renewal_results(self, results: List[Dict]) -> Dict
```

**Celery Task**:
```python
# backend/app/core/celery_app.py
@celery_app.task
def renew_calendar_watches():
    service = CalendarWatchRenewalService()
    return asyncio.run(service.renew_expired_watches())
```

**Priority**: MEDIUM - Maintenance tasks

#### 4.4 Renew Calendar Webhooks (`renew-calendar-webhooks`)
**Current Implementation**: Webhook renewal
**Functionality**: Calendar webhook management

**Conversion Plan**:
```python
# backend/app/services/calendar/calendar_webhook_renewal_service.py
class CalendarWebhookRenewalService:
    async def renew_expired_webhooks(self) -> Dict
    async def renew_user_webhooks(self, user_id: str) -> Dict
    async def handle_renewal_results(self, results: List[Dict]) -> Dict
```

**Celery Task**:
```python
# backend/app/core/celery_app.py
@celery_app.task
def renew_calendar_webhooks():
    service = CalendarWebhookRenewalService()
    return asyncio.run(service.renew_expired_webhooks())
```

**Priority**: MEDIUM - Maintenance tasks

### 5. OAuth & Authentication

#### 5.1 Google OAuth Login (`google-oauth-login`)
**Current Implementation**: Already covered in core services
**Priority**: N/A - Already planned

#### 5.2 Exchange Google Token (`exchange-google-token`)
**Current Implementation**: Already covered in core services
**Priority**: N/A - Already planned

#### 5.3 Refresh Google Token (`refresh-google-token`)
**Current Implementation**: Token refresh service
**Functionality**: Google token management

**Conversion Plan**:
```python
# backend/app/services/auth/google_token_refresh_service.py
class GoogleTokenRefreshService:
    async def refresh_user_token(self, user_id: str) -> Dict
    async def refresh_expired_tokens(self) -> Dict
    async def handle_refresh_results(self, results: List[Dict]) -> Dict
```

**Priority**: MEDIUM - Token management

### 6. AI & Classification

#### 6.1 Project Onboarding AI (`project-onboarding-ai`)
**Current Implementation**: Already covered in core services
**Priority**: N/A - Already planned

#### 6.2 Auto Schedule Bots (`auto-schedule-bots`)
**Current Implementation**: Bot scheduling automation
**Functionality**: Meeting bot management

**Conversion Plan**:
```python
# backend/app/services/ai/auto_schedule_bots_service.py
class AutoScheduleBotsService:
    async def auto_schedule_user_bots(self, user_id: str) -> Dict
    async def schedule_meeting_bot(self, meeting: Dict, user_id: str) -> Dict
    async def handle_scheduling_results(self, results: List[Dict]) -> Dict
```

**Priority**: MEDIUM - AI enhancement

### 7. Utility Functions

#### 7.1 Set Username (`set-username`)
**Current Implementation**: Username management
**Functionality**: Virtual email setup

**Conversion Plan**:
```python
# backend/app/services/user/username_service.py
class UsernameService:
    async def set_username(self, user_id: str, username: str) -> Dict
    async def validate_username(self, username: str) -> bool
    async def generate_virtual_email(self, username: str) -> str
```

**Priority**: MEDIUM - User management

#### 7.2 Setup Gmail Watch (`setup-gmail-watch`)
**Current Implementation**: Gmail webhook setup
**Functionality**: Email monitoring setup

**Conversion Plan**:
```python
# backend/app/services/email/gmail_watch_setup_service.py
class GmailWatchSetupService:
    async def setup_gmail_watch(self, user_id: str, user_email: str) -> Dict
    async def create_gmail_watch(self, user_email: str, credentials: Dict) -> Dict
    async def handle_watch_setup(self, user_id: str, watch_data: Dict) -> Dict
```

**Priority**: MEDIUM - Setup services

#### 7.3 Subscribe to Drive File (`subscribe-to-drive-file`)
**Current Implementation**: Drive file monitoring setup
**Functionality**: File watch creation

**Conversion Plan**:
```python
# backend/app/services/drive/drive_file_subscription_service.py
class DriveFileSubscriptionService:
    async def subscribe_to_file(self, user_id: str, document_id: str, file_id: str) -> Dict
    async def create_file_watch(self, file_id: str, webhook_url: str, credentials: Dict) -> Dict
    async def handle_subscription(self, user_id: str, subscription_data: Dict) -> Dict
```

**Priority**: MEDIUM - Setup services

## Implementation Architecture

### Service Layer Structure

```
backend/app/services/
├── attendee/
│   ├── attendee_service.py
│   ├── attendee_polling_service.py
│   └── attendee_polling_cron.py
├── calendar/
│   ├── calendar_service.py
│   ├── calendar_polling_service.py
│   ├── calendar_polling_cron.py
│   ├── calendar_watch_renewal_service.py
│   └── calendar_webhook_renewal_service.py
├── drive/
│   ├── drive_service.py
│   ├── drive_polling_service.py
│   ├── drive_polling_cron.py
│   └── drive_file_subscription_service.py
├── email/
│   ├── email_service.py
│   ├── gmail_polling_service.py
│   ├── gmail_polling_cron.py
│   └── gmail_watch_setup_service.py
├── auth/
│   ├── google_oauth_service.py
│   ├── google_token_service.py
│   └── google_token_refresh_service.py
├── ai/
│   ├── ai_service.py
│   ├── project_onboarding_service.py
│   └── auto_schedule_bots_service.py
├── sync/
│   └── enhanced_adaptive_sync_service.py
├── user/
│   └── username_service.py
└── webhooks/
    ├── calendar_webhook.py
    ├── drive_webhook.py
    └── gmail_webhook.py
```

### API Layer Structure

```
backend/app/api/v1/
├── attendee.py
├── calendar.py
├── drive.py
├── email.py
├── auth.py
├── ai.py
├── sync.py
├── user.py
└── webhooks/
    ├── calendar_webhook.py
    ├── drive_webhook.py
    └── gmail_webhook.py
```

### Celery Task Structure

```
backend/app/core/celery_app.py
├── attendee_polling_cron
├── calendar_polling_cron
├── drive_polling_cron
├── gmail_polling_cron
├── renew_calendar_watches
├── renew_calendar_webhooks
└── refresh_google_tokens
```

## Database Schema Updates

### New Tables Required

```sql
-- Enhanced sync tracking
CREATE TABLE user_sync_states (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    change_frequency TEXT CHECK (change_frequency IN ('low', 'medium', 'high')),
    virtual_email_activity BOOLEAN DEFAULT FALSE,
    auto_scheduled_meetings INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Sync performance metrics
CREATE TABLE sync_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    sync_type TEXT NOT NULL,
    total_processed INTEGER DEFAULT 0,
    total_created INTEGER DEFAULT 0,
    total_updated INTEGER DEFAULT 0,
    total_deleted INTEGER DEFAULT 0,
    virtual_emails_detected INTEGER DEFAULT 0,
    auto_scheduled_meetings INTEGER DEFAULT 0,
    sync_duration_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- User activity logs
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    activity_type TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Enhanced webhook tracking
CREATE TABLE webhook_activity_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    service TEXT NOT NULL,
    webhook_type TEXT NOT NULL,
    last_webhook_received TIMESTAMP WITH TIME ZONE,
    webhook_failures INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Enhanced Existing Tables

```sql
-- Add sync optimization fields to existing tables
ALTER TABLE calendar_webhooks ADD COLUMN IF NOT EXISTS last_poll_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE calendar_webhooks ADD COLUMN IF NOT EXISTS sync_token TEXT;
ALTER TABLE calendar_webhooks ADD COLUMN IF NOT EXISTS webhook_failures INTEGER DEFAULT 0;

ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS last_poll_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE drive_file_watches ADD COLUMN IF NOT EXISTS last_webhook_received TIMESTAMP WITH TIME ZONE;

ALTER TABLE gmail_watches ADD COLUMN IF NOT EXISTS last_poll_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE gmail_watches ADD COLUMN IF NOT EXISTS last_webhook_received TIMESTAMP WITH TIME ZONE;
```

## Environment Variables

### Required Environment Variables

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_LOGIN_REDIRECT_URI=https://your-domain.com/auth/google/callback

# Google Service Account (for Drive API)
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...
GOOGLE_SERVICE_ACCOUNT_KEY_ID=your-key-id
GOOGLE_PROJECT_ID=your-project-id

# Attendee API
MASTER_ATTENDEE_API_KEY=your_attendee_api_key

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# N8N Webhooks
N8N_CLASSIFICATION_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-classification
N8N_DRIVESYNC_WEBHOOK_URL=https://n8n.customaistudio.io/webhook/kirit-drivesync

# Redis (for caching and Celery)
REDIS_URL=redis://localhost:6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Testing Strategy

### Unit Tests

```python
# backend/app/tests/test_attendee_service.py
class TestAttendeeService:
    async def test_poll_all_meetings(self)
    async def test_send_bot_to_meeting(self)
    async def test_get_transcript(self)
    async def test_auto_schedule_bots(self)

# backend/app/tests/test_calendar_polling_service.py
class TestCalendarPollingService:
    async def test_poll_calendar_for_user(self)
    async def test_process_calendar_event(self)
    async def test_handle_deleted_event(self)

# backend/app/tests/test_drive_polling_service.py
class TestDrivePollingService:
    async def test_poll_drive_for_file(self)
    async def test_check_file_changes(self)
    async def test_handle_file_deletion(self)
```

### Integration Tests

```python
# backend/app/tests/test_integration.py
class TestServiceIntegration:
    async def test_full_sync_workflow(self)
    async def test_webhook_processing(self)
    async def test_cron_job_execution(self)
    async def test_oauth_flow(self)
```

### Performance Tests

```python
# backend/app/tests/test_performance.py
class TestPerformance:
    async def test_sync_performance(self)
    async def test_concurrent_requests(self)
    async def test_memory_usage(self)
    async def test_database_performance(self)
```

## Deployment & Migration

### Phase 1: Backend Development (Weeks 1-6)

1. **Week 1-2**: Core service development
   - Attendee service
   - Calendar polling service
   - Drive polling service

2. **Week 3-4**: Additional core services
   - Gmail polling service
   - Enhanced adaptive sync service
   - Google OAuth service

3. **Week 5-6**: AI and classification services
   - Project onboarding AI
   - Auto schedule bots

### Phase 2: Webhook & Cron Migration (Weeks 7-9)

1. **Week 7**: Webhook handlers
   - Calendar webhook
   - Drive webhook
   - Gmail webhook

2. **Week 8**: Cron job services
   - Polling cron jobs
   - Renewal services

3. **Week 9**: Utility services
   - Username management
   - Watch setup services

### Phase 3: Testing & Optimization (Weeks 10-13)

1. **Week 10-11**: Comprehensive testing
   - Unit tests
   - Integration tests
   - Performance tests

2. **Week 12-13**: Optimization and bug fixes
   - Performance optimization
   - Error handling improvements
   - Documentation updates

### Phase 4: Production Migration (Weeks 14-16)

1. **Week 14**: Staging deployment
   - Backend deployment
   - Database migration
   - Integration testing

2. **Week 15**: Production deployment
   - Gradual rollout
   - Monitoring setup
   - Performance tracking

3. **Week 16**: Post-migration
   - Edge function decommissioning
   - Performance analysis
   - Documentation updates

## Monitoring & Observability

### Metrics to Track

1. **Service Performance**
   - Response times
   - Throughput
   - Error rates
   - Resource usage

2. **Sync Performance**
   - Sync success rates
   - Processing times
   - Data volumes
   - Failure patterns

3. **User Experience**
   - API response times
   - Webhook delivery rates
   - Cron job success rates
   - Error resolution times

### Logging Strategy

```python
# Structured logging for all services
logger.info("Calendar sync completed", extra={
    "user_id": user_id,
    "events_processed": processed_count,
    "sync_duration_ms": duration,
    "success": True
})

# Error logging with context
logger.error("Drive sync failed", extra={
    "user_id": user_id,
    "file_id": file_id,
    "error": str(error),
    "retry_count": retry_count
})
```

### Health Checks

```python
# Health check endpoints for all services
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "calendar": await calendar_service.health_check(),
            "drive": await drive_service.health_check(),
            "gmail": await gmail_service.health_check(),
            "attendee": await attendee_service.health_check()
        }
    }
```

## Risk Mitigation

### Technical Risks

1. **Data Loss During Migration**
   - Comprehensive backup strategy
   - Gradual migration approach
   - Rollback procedures

2. **Performance Degradation**
   - Performance testing before migration
   - Monitoring during migration
   - Optimization strategies

3. **Integration Failures**
   - Thorough testing of all integrations
   - Fallback mechanisms
   - Error handling improvements

### Business Risks

1. **Service Disruption**
   - Minimal downtime migration
   - User communication plan
   - Support team preparation

2. **Data Inconsistency**
   - Data validation procedures
   - Consistency checks
   - Audit trails

## Success Metrics

### Technical Metrics

1. **Performance Improvements**
   - 20-30% reduction in API response times
   - 50% improvement in sync efficiency
   - 90%+ webhook delivery success rate

2. **Reliability Improvements**
   - 99.9% uptime target
   - <1% error rate
   - <100ms average response time

3. **Scalability Improvements**
   - Support for 10x current user load
   - Efficient resource utilization
   - Horizontal scaling capability

### Business Metrics

1. **User Experience**
   - Faster sync times
   - More reliable notifications
   - Better error handling

2. **Development Velocity**
   - Faster feature development
   - Easier debugging
   - Better code maintainability

3. **Operational Efficiency**
   - Reduced infrastructure costs
   - Better monitoring capabilities
   - Easier maintenance

## Conclusion

The conversion from Supabase edge functions to Python backend services represents a significant architectural improvement that will:

1. **Centralize Logic**: Consolidate distributed functionality into maintainable services
2. **Improve Performance**: Leverage Python's async capabilities and better caching
3. **Enhance Monitoring**: Provide comprehensive observability and metrics
4. **Simplify Development**: Enable faster feature development and easier debugging
5. **Reduce Costs**: Optimize resource utilization and reduce edge function costs
6. **Improve Reliability**: Better error handling and recovery mechanisms

The phased approach ensures minimal disruption while maximizing the benefits of the new architecture. Each phase builds upon the previous one, allowing for iterative improvements and early validation of the new system.

The final result will be a robust, scalable, and maintainable backend that provides all the functionality of the current edge functions while offering significant improvements in performance, reliability, and development velocity.
