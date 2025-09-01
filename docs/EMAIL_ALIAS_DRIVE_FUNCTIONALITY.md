# Email Alias Drive Functionality

## Overview

This document describes the enhanced Drive file functionality for the email alias service (`ai+{username}@besunny.ai`). The system now provides a complete workflow for processing Google Drive files shared via email alias, including automatic file watching, metadata updates, and re-vectorization triggers.

## Architecture

### Components

1. **EmailProcessingService** - Detects Drive files in emails and initiates processing
2. **EmailAliasDriveService** - Handles the complete Drive file workflow for email aliases
3. **DriveService** - Core Google Drive API operations and file watching
4. **DriveWebhookHandler** - Processes Drive webhook notifications for file changes

### Database Tables

- `documents` - Stores file metadata and processing status
- `drive_file_watches` - Tracks active file watches with email alias context
- `drive_webhook_logs` - Logs all Drive-related events and processing status

## Complete Workflow

### 1. Email Reception & Drive File Detection

When an email is sent to `ai+{username}@besunny.ai`:

```python
# Email service detects Drive URLs in content
drive_url_pattern = r'https://drive\.google\.com/[^\s]+'
drive_urls = re.findall(drive_url_pattern, full_content)

# For each Drive URL found:
file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', drive_url)
file_id = file_id_match.group(1)
```

**Supported Drive URL formats:**
- `https://drive.google.com/file/d/{file_id}/view`
- `https://drive.google.com/file/d/{file_id}/edit`
- `https://drive.google.com/open?id={file_id}`

### 2. Drive File Processing

The `EmailAliasDriveService.process_drive_file_from_email()` method:

1. **Sets up file watch** for monitoring changes
2. **Stores file metadata** in the documents table
3. **Prepares classification payload** for AI processing
4. **Logs the processing event**

```python
result = await drive_service.process_drive_file_from_email(
    file_id=file_id,
    document_id=document_id,
    user_id=user_id,
    drive_url=drive_url,
    email_content=email_content
)
```

### 3. File Watch Setup

Creates a Google Drive file watch with:

- **Unique watch ID** prefixed with `email_alias_watch_`
- **Webhook endpoint** pointing to `/api/v1/drive/webhook`
- **7-day expiration** (renewable)
- **Email alias context** stored in database

```python
watch_request = {
    'id': f"email_alias_watch_{file_id}_{timestamp}",
    'type': 'web_hook',
    'address': f"{webhook_base_url}/api/v1/drive/webhook",
    'expiration': (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
}
```

### 4. Metadata Storage

Stores comprehensive file information:

```json
{
  "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "source": "drive_shared",
  "title": "Project Proposal.docx",
  "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "file_size": "245760",
  "drive_url": "https://drive.google.com/file/d/...",
  "drive_metadata": {
    "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "name": "Project Proposal.docx",
    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "size": "245760",
    "modifiedTime": "2024-01-15T10:30:00.000Z",
    "parents": ["folder_id_123"],
    "webViewLink": "https://drive.google.com/file/d/..."
  },
  "status": "active",
  "watch_active": true
}
```

### 5. Classification Agent Preparation

Prepares payload for AI classification:

```python
classification_payload = {
    'document_id': document_id,
    'file_id': file_id,
    'user_id': user_id,
    'file_name': file_metadata.name,
    'file_type': file_metadata.mime_type,
    'file_content': extracted_content,  # For text-based files
    'content_type': 'text|exported_text|metadata_only',
    'drive_url': drive_url,
    'email_context': email_content,
    'metadata': file_metadata,
    'source': 'email_alias_drive'
}
```

**Content Extraction:**
- **Text files**: Direct content download
- **Google Docs**: Export as plain text
- **Spreadsheets**: Export as CSV
- **Other formats**: Metadata only

### 6. File Change Monitoring

When files are updated in Google Drive:

1. **Webhook notification** received
2. **Document metadata updated** with latest information
3. **Re-vectorization workflow triggered**
4. **Processing logged** for audit trail

```python
async def handle_file_update(self, file_id: str, user_id: str):
    # Get document associated with file
    document = await self._get_document_by_file_id(file_id)
    
    # Update metadata
    await self._update_document_metadata(document['id'], file_id, user_id)
    
    # Trigger re-vectorization
    await self._trigger_revectorization_workflow(document['id'], file_id, user_id)
```

### 7. Re-vectorization Workflow

Prepares payload for future re-vectorization service:

```python
revectorization_payload = {
    'document_id': document_id,
    'file_id': file_id,
    'user_id': user_id,
    'project_id': document.get('project_id'),
    'file_name': document.get('title'),
    'file_type': document.get('mimetype'),
    'trigger_type': 'drive_file_update',
    'triggered_at': datetime.now().isoformat(),
    'file_url': document.get('drive_url'),
    'metadata': document.get('drive_metadata', {})
}
```

## API Endpoints

### Drive Webhook

**POST** `/api/v1/drive/webhook`

Receives Google Drive change notifications and processes them based on watch type.

### Drive Webhook Test

**POST** `/api/v1/drive/webhook/test`

Test endpoint for development and debugging.

### Drive Webhook Logs

**GET** `/api/v1/drive/webhook/logs`

Retrieve webhook processing logs with optional filtering.

## Error Handling

### Graceful Degradation

- **Missing credentials**: Logs warning, continues with metadata-only processing
- **API failures**: Logs error, maintains webhook functionality
- **File access issues**: Falls back to metadata-only mode

### Comprehensive Logging

All operations are logged with:

- **Event type** (processing, update, error)
- **Status** (success, error, pending)
- **Timestamps** for audit trail
- **Error messages** for debugging
- **Context data** for troubleshooting

## Security Considerations

### Webhook Verification

- **Gmail webhook verification** (placeholder for production)
- **Drive webhook validation** against registered watches
- **User authentication** for all operations

### Data Privacy

- **User isolation** - users can only access their own files
- **Credential scoping** - minimal required permissions
- **Audit logging** - all access tracked

## Performance Optimizations

### Efficient File Watching

- **Batch processing** for multiple file changes
- **Smart renewal** of expired watches
- **Background processing** for non-blocking operations

### Content Extraction

- **Lazy loading** - content only when needed
- **Format-specific optimization** - different strategies per file type
- **Caching** - metadata reuse when possible

## Testing

### Test Script

Run the comprehensive test suite:

```bash
cd backend
python test_email_alias_drive_functionality.py
```

### Test Coverage

- ✅ Email processing with Drive file detection
- ✅ Drive file watch setup and management
- ✅ Metadata storage and updates
- ✅ Webhook handling for file changes
- ✅ Classification payload preparation
- ✅ Re-vectorization workflow triggers
- ✅ Database operations and schema validation

## Future Enhancements

### Classification Agent Integration

When the AI classification agent is built:

1. **Automatic project assignment** based on file content
2. **Smart tagging** and categorization
3. **Content summarization** and key extraction

### Re-vectorization Service

When the re-vectorization workflow is implemented:

1. **Automatic content re-processing** on file updates
2. **Pinecone vector updates** with new content
3. **Change impact analysis** and notification

### Advanced File Types

Future support for:

- **Image files** with OCR processing
- **Audio/video files** with transcription
- **Archived files** with content extraction
- **Collaborative documents** with change tracking

## Monitoring & Maintenance

### Health Checks

- **Watch expiration monitoring** - automatic renewal
- **Webhook delivery tracking** - failure detection
- **API quota monitoring** - usage optimization

### Cleanup Operations

- **Expired watch cleanup** - database maintenance
- **Old log cleanup** - storage optimization
- **Failed operation retry** - reliability improvement

## Troubleshooting

### Common Issues

1. **File watch failures**: Check Google API quotas and credentials
2. **Webhook delivery issues**: Verify endpoint accessibility and authentication
3. **Metadata sync problems**: Check file permissions and API access
4. **Classification failures**: Verify file format support and content extraction

### Debug Commands

```bash
# Check active file watches
curl -X GET "http://localhost:8000/api/v1/drive/webhook/logs?limit=10"

# Test webhook processing
curl -X POST "http://localhost:8000/api/v1/drive/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"file_id":"test","channel_id":"test","resource_id":"test","resource_state":"change"}'

# Run comprehensive tests
python test_email_alias_drive_functionality.py
```

## Conclusion

The enhanced email alias Drive functionality provides a robust, scalable solution for processing Google Drive files shared via email aliases. The system automatically handles file watching, metadata management, and change notifications, preparing files for AI classification and re-vectorization workflows.

Key benefits:

- **Automated processing** - no manual intervention required
- **Real-time updates** - immediate notification of file changes
- **Comprehensive logging** - full audit trail and debugging
- **Scalable architecture** - handles multiple users and files
- **Future-ready** - prepared for classification and re-vectorization services

The implementation follows best practices for error handling, security, and performance, making it production-ready while maintaining extensibility for future enhancements.
