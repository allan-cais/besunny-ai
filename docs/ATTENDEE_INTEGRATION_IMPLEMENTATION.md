# Attendee Integration Implementation Guide

This document provides a comprehensive overview of the Attendee integration implementation for BeSunny.ai, including architecture, API endpoints, webhook handling, and usage examples.

## Overview

The Attendee integration provides a complete solution for creating and managing meeting bots that automatically transcribe meetings. The system includes:

- **Bot Management**: Create, monitor, and delete meeting bots
- **Real-time Transcription**: Webhook-based transcript updates during meetings
- **Chat Integration**: Send and receive chat messages through bots
- **Participant Tracking**: Monitor who joins and leaves meetings
- **Comprehensive Logging**: Track all webhook events and API calls

## Architecture

### Core Components

1. **AttendeeService** (`backend/app/services/attendee/attendee_service.py`)
   - Main service for bot management
   - Handles API communication with Attendee.dev
   - Manages bot lifecycle and status updates

2. **AttendeeWebhookHandler** (`backend/app/services/attendee/attendee_webhook_handler.py`)
   - Processes incoming webhook notifications
   - Stores transcript segments, chat messages, and participant events
   - Updates meeting status in real-time

3. **API Endpoints** (`backend/app/api/v1/attendee.py`)
   - RESTful API for bot operations
   - User authentication and authorization
   - Input validation and error handling

4. **Webhook Endpoint** (`backend/app/api/v1/webhooks/attendee_webhook.py`)
   - Receives webhook notifications from Attendee.dev
   - Signature verification for security
   - Routes webhooks to appropriate handlers

### Database Schema

The integration uses several tables to store data:

- **`meeting_bots`**: Bot information and status
- **`transcript_segments`**: Individual transcript segments with timestamps
- **`chat_messages`**: Chat messages exchanged during meetings
- **`participant_events`**: Participant join/leave events
- **`attendee_webhook_logs`**: Webhook processing logs

## API Endpoints

### Bot Management

#### Create Bot
```http
POST /api/v1/attendee/create-bot
```

**Request Body:**
```json
{
  "meeting_url": "https://zoom.us/j/123456789",
  "bot_name": "Sunny AI Notetaker",
  "bot_chat_message": "Hi, I'm here to transcribe this meeting!"
}
```

**Response:**
```json
{
  "success": true,
  "bot_id": "bot_abc123",
  "project_id": "proj_xyz789",
  "status": "created"
}
```

#### List User Bots
```http
GET /api/v1/attendee/bots
```

#### Get Bot Status
```http
GET /api/v1/attendee/bot-status/{bot_id}
```

#### Delete Bot
```http
DELETE /api/v1/attendee/bot/{bot_id}
```

### Transcript and Chat

#### Get Transcript
```http
GET /api/v1/attendee/transcript/{bot_id}
```

#### Get Chat Messages
```http
GET /api/v1/attendee/chat-messages/{bot_id}?limit=100
```

#### Send Chat Message
```http
POST /api/v1/attendee/send-chat/{bot_id}
```

**Request Body:**
```json
{
  "message": "Hello everyone!",
  "to": "everyone"
}
```

### Recording Control

#### Pause Recording
```http
POST /api/v1/attendee/pause-recording/{bot_id}
```

#### Resume Recording
```http
POST /api/v1/attendee/resume-recording/{bot_id}
```

## Webhook Handling

### Webhook Endpoint
```http
POST /api/v1/webhooks/attendee/{user_id}
```

### Supported Webhook Triggers

1. **`bot.state_change`**: Bot status changes (created, recording, ended, etc.)
2. **`transcript.update`**: Real-time transcript updates during meetings
3. **`chat_messages.update`**: New chat messages in the meeting
4. **`participant_events.join_leave`**: Participants joining or leaving

### Webhook Payload Examples

#### Bot State Change
```json
{
  "idempotency_key": "webhook_123",
  "bot_id": "bot_abc123",
  "trigger": "bot.state_change",
  "data": {
    "new_state": "ended",
    "old_state": "post_processing",
    "created_at": "2024-01-01T12:00:00Z",
    "event_type": "post_processing_completed",
    "event_sub_type": null
  }
}
```

#### Transcript Update
```json
{
  "idempotency_key": "webhook_456",
  "bot_id": "bot_abc123",
  "trigger": "transcript.update",
  "data": {
    "speaker_name": "John Doe",
    "speaker_uuid": "speaker_123",
    "timestamp_ms": 60000,
    "duration_ms": 5000,
    "transcription": {
      "transcript": "Hello, this is a test message.",
      "words": [...]
    }
  }
}
```

## Configuration

### Environment Variables

```bash
# Attendee API configuration
ATTENDEE_API_BASE_URL=https://app.attendee.dev
MASTER_ATTENDEE_API_KEY=your_attendee_api_key

# Webhook configuration
WEBHOOK_BASE_URL=https://your-domain.com
```

### Bot Creation with Webhooks

When creating a bot, the system automatically configures webhooks with all supported triggers:

```python
bot_data = {
    "meeting_url": "https://zoom.us/j/123",
    "bot_name": "Sunny AI Notetaker",
    "webhooks": [
        {
            "url": "https://your-domain.com/api/v1/webhooks/attendee/{user_id}",
            "triggers": [
                "bot.state_change",
                "transcript.update",
                "chat_messages.update",
                "participant_events.join_leave"
            ]
        }
    ]
}
```

## Usage Examples

### Frontend Integration

#### Creating a Bot
```typescript
import { apiKeyService } from '../lib/api-keys';

const createBot = async (meetingUrl: string) => {
  try {
    const result = await apiKeyService.sendBotToMeeting(meetingUrl, {
      bot_chat_message: {
        message: "Hi, I'm here to transcribe this meeting!",
        to: "everyone"
      }
    });
    
    console.log('Bot created:', result.bot_id);
    return result;
  } catch (error) {
    console.error('Failed to create bot:', error);
  }
};
```

#### Calendar Integration
```typescript
import { calendarService } from '../lib/calendar-service';

const deployBotToMeeting = async (meetingId: string) => {
  try {
    const result = await calendarService.sendBotToMeeting(meetingId, {
      bot_name: "Sunny AI Notetaker",
      bot_chat_message: "Hi, I'm here to transcribe this meeting!"
    });
    
    if (result.ok) {
      console.log('Bot deployed successfully:', result.bot_id);
    } else {
      console.error('Bot deployment failed:', result.error);
    }
  } catch (error) {
    console.error('Error deploying bot:', error);
  }
};
```

### Backend Usage

#### Service Integration
```python
from app.services.attendee import AttendeeService

async def create_meeting_bot(meeting_url: str, user_id: str):
    service = AttendeeService()
    
    result = await service.create_bot_for_meeting({
        "meeting_url": meeting_url,
        "bot_name": "Sunny AI Notetaker",
        "bot_chat_message": "Hi, I'm here to transcribe this meeting!"
    }, user_id)
    
    if result["success"]:
        print(f"Bot created: {result['bot_id']}")
        return result
    else:
        print(f"Error: {result['error']}")
        return None
```

## Security Features

### Webhook Signature Verification

All incoming webhooks are verified using HMAC-SHA256 signatures:

```python
def verify_webhook_signature(payload: Dict[str, Any], signature: str, secret: str) -> bool:
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    secret_decoded = base64.b64decode(secret)
    
    expected_signature = base64.b64encode(
        hmac.new(secret_decoded, canonical_payload.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')
    
    return hmac.compare_digest(signature, expected_signature)
```

### Row Level Security

All database tables use Row Level Security (RLS) policies to ensure users can only access their own data:

```sql
CREATE POLICY "Users can view their own meeting bots" ON meeting_bots
    FOR SELECT USING (auth.uid() = user_id);
```

## Error Handling

### API Error Responses

```json
{
  "success": false,
  "error": "Missing required field: meeting_url"
}
```

### Webhook Error Handling

- Invalid signatures return 200 status to prevent retries
- Processing errors are logged but don't cause webhook failures
- All webhooks return 200 status to prevent Attendee.dev retries

## Monitoring and Logging

### Webhook Logs

All webhook requests are logged in the `attendee_webhook_logs` table for debugging and monitoring.

### Service Logging

The service includes comprehensive logging for all operations:

```python
logger.info(f"Bot created successfully for user {user_id}, bot ID: {result['id']}")
logger.error(f"Failed to create bot for user {user_id}: {e}")
```

## Testing

### Running Tests

```bash
# Run all Attendee service tests
pytest backend/tests/test_attendee_service.py -v

# Run specific test class
pytest backend/tests/test_attendee_service.py::TestAttendeeService -v

# Run with coverage
pytest backend/tests/test_attendee_service.py --cov=app.services.attendee --cov-report=html
```

### Test Coverage

The test suite covers:
- Bot creation and management
- Webhook processing for all trigger types
- Error handling and edge cases
- Database operations
- API integration

## Deployment

### Database Migration

Run the database migration to create required tables:

```bash
# Apply the migration
psql -d your_database -f backend/database/migrations/001_create_attendee_tables.sql
```

### Environment Setup

1. Set required environment variables
2. Ensure webhook endpoint is publicly accessible
3. Configure Attendee.dev API key
4. Test webhook endpoint accessibility

### Health Checks

The webhook endpoint includes a health check:

```http
GET /api/v1/webhooks/attendee/{user_id}/verify
```

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving**: Check endpoint accessibility and signature verification
2. **Bot Creation Fails**: Verify API key and meeting URL format
3. **Transcript Not Updating**: Check webhook configuration and database permissions

### Debug Steps

1. Check webhook logs in `attendee_webhook_logs` table
2. Verify API key configuration
3. Test webhook endpoint accessibility
4. Check database connection and permissions

## Future Enhancements

### Planned Features

- **Auto-scheduling**: Automatically deploy bots for upcoming meetings
- **Advanced Analytics**: Meeting insights and participant analytics
- **Integration APIs**: Connect with other meeting platforms
- **Custom Bot Configurations**: Advanced bot behavior customization

### Performance Optimizations

- **Caching**: Cache frequently accessed bot status and transcript data
- **Batch Processing**: Process multiple webhooks in batches
- **Async Processing**: Background processing for heavy operations

## Support

For issues or questions about the Attendee integration:

1. Check the webhook logs for error details
2. Review the test suite for usage examples
3. Consult the Attendee.dev API documentation
4. Check the service logs for detailed error information

## Conclusion

The Attendee integration provides a robust, secure, and scalable solution for meeting bot management and transcription. The webhook-based architecture ensures real-time updates while maintaining system reliability and performance.
