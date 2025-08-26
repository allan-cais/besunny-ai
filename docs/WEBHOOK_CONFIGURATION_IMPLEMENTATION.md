# Webhook Configuration Implementation

This document describes the implementation of comprehensive webhook configuration for attendee bots, ensuring consistent transcript retrieval functionality whether bots are auto-scheduled via virtual email or manually deployed from the UI.

## Overview

The system now provides **identical webhook configuration** for all attendee bots, regardless of how they were deployed. This ensures consistent functionality for transcript retrieval, chat message handling, and participant tracking.

## 🎯 **Webhook Triggers Implemented**

Based on the [Attendee.dev webhook documentation](https://docs.attendee.dev/guides/webhooks), all bots now include these essential triggers:

### **1. `bot.state_change`**
- **Purpose**: Notifies when the bot changes state (joins, leaves, starts recording, etc.)
- **Critical for**: Knowing when the meeting has ended and recording is available
- **Key Event**: `post_processing_completed` - indicates transcript is ready for retrieval

### **2. `transcript.update`**
- **Purpose**: Real-time transcript updates during the meeting
- **Critical for**: Live transcription monitoring and progress tracking
- **Data**: Individual utterances with speaker information and timestamps

### **3. `chat_messages.update`**
- **Purpose**: Chat message updates in the meeting
- **Critical for**: Monitoring bot interactions and participant communications
- **Data**: Chat messages with sender information and timestamps

### **4. `participant_events.join_leave`**
- **Purpose**: Participant join/leave events
- **Critical for**: Tracking meeting attendance and participation
- **Data**: Participant information and event timestamps

## 🔧 **Implementation Details**

### **Bot Creation with Webhooks**

```python
# In AttendeeService.create_bot_for_meeting()
bot_data = {
    "meeting_url": options['meeting_url'],
    "bot_name": options['bot_name'],
    "webhooks": [
        {
            "url": webhook_url,
            "triggers": [
                "bot.state_change",        # For meeting end/recording availability
                "transcript.update",        # Real-time transcript updates
                "chat_messages.update",     # Chat message updates
                "participant_events.join_leave"  # Participant tracking
            ]
        }
    ]
}
```

### **Deployment Method Tracking**

```python
# Add deployment method to track how bot was created
deployment_method = options.get('deployment_method', 'manual')
if deployment_method == 'automatic':
    bot_data["metadata"] = {
        "deployment_method": "automatic",
        "virtual_email_triggered": True,
        "created_via": "virtual_email_attendee"
    }
else:
    bot_data["metadata"] = {
        "deployment_method": "manual",
        "created_via": "ui_deployment"
    }
```

## 🔄 **Consistent Webhook Setup**

### **Auto-Scheduled Bots (Virtual Email)**

```python
# In VirtualEmailAttendeeService._schedule_attendee_bot()
bot_options = {
    'meeting_url': meeting_url,
    'bot_name': 'Sunny AI Notetaker',
    'bot_chat_message': 'Hi, I\'m here to transcribe this meeting!',
    'deployment_method': 'automatic'  # Mark as auto-scheduled
}

# Creates bot with comprehensive webhook configuration
result = await self.attendee_service.create_bot_for_meeting(bot_options, user_id)
```

### **Manually Deployed Bots (UI)**

```python
# In API endpoint /create-bot
options = {
    "meeting_url": request.meeting_url,
    "bot_name": request.bot_name,
    "deployment_method": "manual"  # Mark as manually deployed
}

# Creates bot with identical webhook configuration
result = await attendee_service.create_bot_for_meeting(options, current_user["id"])
```

## 📊 **Database Schema Updates**

### **New Fields Added**

#### **Meetings Table**
- `transcript_ready_for_classification` - Flag for classification agent processing
- `transcript_ready_for_embedding` - Flag for vector embedding workflow
- `bot_deployment_method` - Tracks deployment method (manual/automatic/scheduled)

#### **Meeting Bots Table**
- `deployment_method` - How the bot was deployed
- `metadata` - Additional deployment information
- `event_type` - Type of event that triggered state change
- `event_sub_type` - Sub-type of event that triggered state change

### **Migration Script**

```sql
-- Migration: 003_add_transcript_processing_fields.sql
ALTER TABLE meetings 
ADD COLUMN IF NOT EXISTS transcript_ready_for_classification BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS transcript_ready_for_embedding BOOLEAN DEFAULT false;

-- Update bot_status enum to include 'post_processing' state
ALTER TABLE meetings 
ADD CONSTRAINT meetings_bot_status_check 
CHECK (bot_status = ANY (ARRAY['pending', 'bot_scheduled', 'bot_joined', 'transcribing', 'post_processing', 'completed', 'failed']));
```

## 🚀 **Transcript Retrieval Workflow**

### **1. Meeting End Detection**

```python
# In AttendeeWebhookHandler._handle_bot_state_change()
if (event_type == 'post_processing_completed' and 
    new_state == 'ended' and 
    old_state == 'post_processing'):
    
    logger.info(f"Meeting ended and recording available for bot {bot_id}")
    
    # Trigger transcript retrieval
    await self._retrieve_final_transcript(bot_id, user_id)
    
    # Update meeting status to completed
    await self._update_meeting_status(bot_id, 'completed')
```

### **2. Automatic Transcript Retrieval**

```python
async def _retrieve_final_transcript(self, bot_id: str, user_id: str):
    """Retrieve final transcript when meeting ends."""
    try:
        # Get transcript from Attendee.dev API
        transcript_data = await self.attendee_service.get_transcript(bot_id)
        
        if transcript_data:
            # Store transcript in database
            await self._store_transcript(bot_id, transcript_data)
            
            # Update meeting record with transcript
            await self._update_meeting_transcript(bot_id, transcript_data)
            
            # Mark transcript as ready for future processing
            await self._mark_transcript_ready_for_processing(bot_id)
            
            logger.info(f"Final transcript retrieved and stored for bot {bot_id}")
            
    except Exception as e:
        logger.error(f"Failed to retrieve final transcript for bot {bot_id}: {e}")
```

### **3. Future Processing Flags**

```python
async def _mark_transcript_ready_for_processing(self, bot_id: str):
    """Mark transcript as ready for future classification and embedding processing."""
    try:
        # Find meeting by bot ID
        meeting_result = await self.supabase.table('meetings').select('id').eq('attendee_bot_id', bot_id).single().execute()
        
        if meeting_result.data:
            meeting_id = meeting_result.data['id']
            
            # Mark transcript as ready for future processing workflows
            await self.supabase.table('meetings').update({
                'transcript_ready_for_classification': True,
                'transcript_ready_for_embedding': True,
                'updated_at': datetime.now().isoformat()
            }).eq('id', meeting_id).execute()
            
            logger.info(f"Marked meeting {meeting_id} transcript as ready for future processing")
            
    except Exception as e:
        logger.error(f"Failed to mark transcript ready for processing for bot {bot_id}: {e}")
```

## 🧪 **Testing & Validation**

### **Webhook Configuration Consistency Test**

```python
async def test_webhook_configuration_consistency():
    """Test that both auto-scheduled and manually deployed bots get the same webhook configuration."""
    
    # Test 1: Auto-scheduled bot (virtual email)
    auto_bot_result = await virtual_email_service._schedule_attendee_bot(
        test_user_id, test_meeting_url, {}, {'username': 'testuser'}
    )
    
    # Test 2: Manually deployed bot (UI)
    manual_bot_options = {
        'meeting_url': test_meeting_url,
        'bot_name': 'Manual Test Bot',
        'deployment_method': 'manual'
    }
    
    manual_bot_result = await attendee_service.create_bot_for_meeting(
        manual_bot_options, test_user_id
    )
    
    # Verify both have the same webhook triggers
    expected_triggers = [
        "bot.state_change",
        "transcript.update", 
        "chat_messages.update",
        "participant_events.join_leave"
    ]
    
    assert set(auto_triggers) == set(expected_triggers)
    assert set(manual_triggers) == set(expected_triggers)
```

## 🔒 **Security & Validation**

### **Webhook Signature Verification**

Based on [Attendee.dev webhook documentation](https://docs.attendee.dev/guides/webhooks), webhooks include signature verification:

```python
# Verify webhook signature
signature_from_header = request.headers.get("X-Webhook-Signature")
signature_calculated = sign_payload(payload, webhook_secret)

if signature_calculated != signature_from_header:
    return "Invalid signature", 400
```

### **Input Validation**

- All webhook URLs must use HTTPS
- Maximum of 2 webhooks per bot
- Same URL cannot be used multiple times for the same bot

## 📈 **Performance & Monitoring**

### **Webhook Delivery**

- **Retry Policy**: Up to 3 retries with exponential backoff
- **Timeout**: 10-second response timeout
- **Priority**: Bot-level webhooks override project-level webhooks

### **Monitoring**

```python
# Log webhook configuration
logger.info(f"Creating bot with webhook configuration: {bot_data['webhooks']}")

# Track deployment method
logger.info(f"Bot created successfully for user {user_id}, bot ID: {result['id']}, deployment: {deployment_method}")

# Monitor transcript processing
logger.info(f"Marked meeting {meeting_id} transcript as ready for future processing")
```

## 🚀 **Next Steps**

### **Immediate**

1. **Deploy database migration** to add new fields
2. **Test webhook configuration** for both deployment methods
3. **Verify transcript retrieval** workflow

### **Future**

1. **Classification Agent Integration**: Process transcripts for project association
2. **Vector Embedding Workflow**: Process transcripts for searchability
3. **Advanced Analytics**: Track webhook delivery success rates
4. **Multi-Platform Support**: Extend to other calendar platforms

## 📚 **References**

- [Attendee.dev Webhook Documentation](https://docs.attendee.dev/guides/webhooks)
- [Attendee.dev API Reference](https://docs.attendee.dev/api-reference#tag/bots)
- [Virtual Email Attendee Implementation](docs/VIRTUAL_EMAIL_ATTENDEE_IMPLEMENTATION.md)

## 🎉 **Conclusion**

The webhook configuration implementation ensures **consistent functionality** across all attendee bots, whether they're auto-scheduled via virtual email or manually deployed from the UI. This provides a solid foundation for transcript retrieval and future processing workflows.

Key benefits:
- **Unified Experience**: Same webhook configuration regardless of deployment method
- **Complete Coverage**: All necessary triggers for transcript retrieval
- **Future-Ready**: Flags for classification agent and vector embedding workflows
- **Robust Monitoring**: Comprehensive logging and error handling
- **Scalable Architecture**: Supports both automated and manual bot deployment
