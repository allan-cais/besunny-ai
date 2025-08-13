# Attendee Integration

This document describes the implementation of the Attendee integration for the besunny.ai application.

## Overview

Attendee is a meeting bot transcription platform that allows automated capture and transcription of meetings. This integration provides:

- Secure API key storage with app-layer encryption
- API key validation and testing
- Meeting bot deployment capabilities
- Transcript retrieval functionality

## Implementation Details

### Encryption

API keys are encrypted using AES-GCM with PBKDF2 key derivation:

- **Algorithm**: AES-GCM
- **Key Length**: 256 bits
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Storage**: Encrypted keys stored in `user_api_keys` table
- **Key Management**: App-level encryption key stored in localStorage

### Database Schema

The integration uses the existing `user_api_keys` table:

```sql
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    service TEXT NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(user_id, service)
);
```

### Components

#### AttendeeIntegration.tsx
- Main integration component
- Handles API key input and validation
- Manages connection status
- Provides setup instructions

#### api-keys.ts
- Service layer for API key management
- Encryption/decryption utilities
- Attendee API integration functions

#### encryption.ts
- Web Crypto API utilities
- AES-GCM encryption implementation
- Key derivation and management

### API Integration

The integration provides several utility functions for interacting with Attendee:

```typescript
// Test API key validity
await apiKeyService.testApiKey('attendee', apiKey);

// Send bot to meeting
await apiKeyService.sendBotToMeeting(userId, meetingUrl, options);

// Get meeting transcript
await apiKeyService.getMeetingTranscript(userId, meetingId);

// Make custom API calls
await apiKeyService.makeAttendeeApiCall(userId, '/endpoint', options);
```

### Security Features

1. **App-layer Encryption**: All API keys are encrypted before storage
2. **Row Level Security**: Database policies ensure users can only access their own keys
3. **Key Validation**: API keys are tested before storage
4. **Secure Key Storage**: Encryption key managed in browser localStorage
5. **Automatic Cleanup**: Keys are deleted when users disconnect

### Usage Flow

1. User visits integrations page
2. Clicks "GET API KEY" to visit attendee.dev
3. Generates API key on Attendee platform
4. Returns to app and enters API key
5. System validates key and stores encrypted version
6. User can now use Attendee features throughout the app

### Error Handling

- Invalid API keys are rejected with clear error messages
- Network errors are handled gracefully
- Encryption/decryption errors are logged and reported
- Database errors are caught and displayed to user

### Future Enhancements

- Meeting scheduling integration
- Real-time transcript streaming
- Custom bot configuration
- Meeting analytics and insights
- Bulk meeting processing

## API Endpoints Used

- `GET /api/v1/bots` - Validate API key and list bots
- `POST /api/v1/bots` - Create and send bot to meeting
- `GET /api/v1/bots/{id}/transcript` - Get meeting transcript

## Configuration

No additional environment variables are required. The integration uses the existing Supabase configuration and the Attendee API base URL is hardcoded to `https://app.attendee.dev`. 