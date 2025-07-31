# Email Classification Flow Documentation

## Overview

The email classification system processes incoming emails and Google Drive notifications, automatically classifying them to the appropriate project using AI-powered analysis. This document outlines the complete flow from email ingestion to project classification.

## 📬 Email Ingestion Flow

### 1. Email Reception
- **Email Address**: `ai+{username}@besunny.ai`
- **Source**: Gmail webhook or Google Drive notification
- **Processing**: `process-inbound-emails` Edge Function

### 2. User Lookup & Document Creation
```typescript
// Extract username from email address
const username = extractUsernameFromEmail('ai+johndoe@besunny.ai'); // Returns: 'johndoe'

// Look up user in database
const user = await findUserByUsername(supabase, username);

// Create document record (project_id initially null)
const documentId = await createDocumentFromEmail(supabase, user.id, gmailMessage, subject, sender);
```

### 3. Project Metadata Retrieval
```typescript
// Get all active projects for the user
const projects = await getActiveProjectsForUser(supabase, user.id);
```

## 🧠 Classification Payload Structure

### buildClassificationPayload() Function

The `buildClassificationPayload()` function constructs a comprehensive payload containing:

- **Document metadata** (email content, sender, subject)
- **Project classification schema** (tags, categories, keywords)
- **Clean signals** for the LLM to reason over

```typescript
function buildClassificationPayload({
  document,
  user,
  projects
}: {
  document: Document;
  user: User;
  projects: Project[];
}): ClassificationPayload {
  return {
    document_id: document.id,
    user_id: user.id,
    type: document.source === 'gmail' ? 'email' : 'drive_notification',
    source: document.source,
    title: document.title,
    author: document.author,
    received_at: document.received_at,
    content: document.summary,
    metadata: {
      gmail_message_id: document.source_id,
      filename: document.title,
      mimetype: document.mimetype || null,
      notification_type: document.source === 'drive_notification' ? 'drive_shared' : undefined
    },
    project_metadata: projects.map(project => ({
      project_id: project.id,
      normalized_tags: project.normalized_tags,
      categories: project.categories,
      reference_keywords: project.reference_keywords,
      notes: project.notes,
      classification_signals: project.classification_signals,
      entity_patterns: project.entity_patterns
    }))
  };
}
```

## 📤 Example Classification Payload

```json
{
  "document_id": "d8c3d123-b9d0-4a45-bced-d12cb69a54c3",
  "user_id": "23f7713e-2281-498d-bb31-fc2140d4f0f6",
  "type": "email",
  "source": "gmail",
  "title": "Updated storyboard for launch",
  "author": "lauren@agency.com",
  "received_at": "2025-07-21T16:42:00.000Z",
  "content": "Hey team — attaching the new storyboard for the summer campaign. Please review.",
  "metadata": {
    "gmail_message_id": "18e9ad7dc0a12345",
    "filename": "Updated storyboard for launch",
    "mimetype": null,
    "notification_type": null
  },
  "project_metadata": [
    {
      "project_id": "c119adba-8452-11ec-a8a3-0242ac120002",
      "normalized_tags": ["summer campaign", "hero video", "cutdown"],
      "categories": ["Video Production"],
      "reference_keywords": ["storyboard", "script", "shooting schedule"],
      "notes": "Main video deliverable for summer brand launch",
      "classification_signals": {
        "confidence_thresholds": {
          "email": { "subject_match": 0.7, "sender_match": 0.8, "content_match": 0.6 }
        },
        "temporal_relevance": {
          "active_period": ["2025-07-01", "2025-09-01"]
        }
      },
      "entity_patterns": {
        "people": {
          "lauren@agency.com": { "role": "creative", "confidence": 0.95 }
        },
        "locations": ["LA", "Soundstage 5"]
      }
    },
    {
      "project_id": "f8e7d6c5-4321-11ec-b987-0242ac120003",
      "normalized_tags": ["marketing materials", "brand assets"],
      "categories": ["Marketing"],
      "reference_keywords": ["brand guidelines", "logo", "style guide"],
      "notes": "Brand asset management and marketing materials",
      "classification_signals": {
        "confidence_thresholds": {
          "email": { "subject_match": 0.6, "sender_match": 0.7, "content_match": 0.5 }
        }
      },
      "entity_patterns": {
        "people": {
          "marketing@company.com": { "role": "marketing", "confidence": 0.9 }
        }
      }
    }
  ]
}
```

## 🎯 Classification Agent Processing

### What the N8N Classification Agent Does:

1. **Content Analysis**: Compares email content, subject, and sender against each project's semantic signals
2. **Scoring**: Calculates confidence scores for each project based on:
   - Subject line matches
   - Sender email/domain matches
   - Content keyword matches
   - Entity pattern matches
3. **Decision Making**: Returns the best-matching `project_id` or marks as unclassified if below threshold
4. **Learning**: Updates classification feedback for future improvements

### Example Classification Response:
```json
{
  "success": true,
  "classified_project_id": "c119adba-8452-11ec-a8a3-0242ac120002",
  "confidence_score": 0.87,
  "classification_reason": "High match on 'storyboard' keyword and sender 'lauren@agency.com' matches project entity patterns",
  "alternative_projects": [
    {
      "project_id": "f8e7d6c5-4321-11ec-b987-0242ac120003",
      "confidence_score": 0.23,
      "reason": "Low match - only general marketing terms"
    }
  ]
}
```

## 🗄️ Database Schema

### Projects Table Classification Fields

```sql
-- Classification metadata
normalized_tags TEXT[]           -- Semantic concepts for matching
categories TEXT[]               -- High-level project categories
reference_keywords TEXT[]       -- Key terms indicating project relevance
notes TEXT                      -- Human-readable project summary

-- Enhanced classification signals
classification_signals JSONB    -- Advanced metadata for LLM reasoning
entity_patterns JSONB           -- People, emails, locations, organizations

-- Tracking and learning
pinecone_document_count INTEGER -- Documents in Pinecone namespace
last_classification_at TIMESTAMP -- Most recent classification
classification_feedback JSONB   -- Learning data from results
```

### Example Project Data:
```sql
INSERT INTO projects (
  id, name, description, status, created_by,
  normalized_tags, categories, reference_keywords, notes,
  classification_signals, entity_patterns
) VALUES (
  'c119adba-8452-11ec-a8a3-0242ac120002',
  'Summer Campaign Video',
  'Main video deliverable for summer brand launch',
  'active',
  '23f7713e-2281-498d-bb31-fc2140d4f0f6',
  ARRAY['summer campaign', 'hero video', 'cutdown'],
  ARRAY['Video Production'],
  ARRAY['storyboard', 'script', 'shooting schedule'],
  'Main video deliverable for summer brand launch',
  '{
    "confidence_thresholds": {
      "email": {"subject_match": 0.7, "sender_match": 0.8, "content_match": 0.6}
    },
    "temporal_relevance": {
      "active_period": ["2025-07-01", "2025-09-01"]
    }
  }',
  '{
    "people": {
      "lauren@agency.com": {"role": "creative", "confidence": 0.95}
    },
    "locations": ["LA", "Soundstage 5"]
  }'
);
```

## 🔄 Complete Flow Example

### 1. Email Received
```
From: lauren@agency.com
To: ai+johndoe@besunny.ai
Subject: Updated storyboard for launch
Content: Hey team — attaching the new storyboard for the summer campaign. Please review.
```

### 2. Process-Inbound-Emails Function
```typescript
// Extract username: 'johndoe'
// Look up user: { id: '23f7713e-2281-498d-bb31-fc2140d4f0f6', username: 'johndoe' }
// Create document: { id: 'd8c3d123-b9d0-4a45-bced-d12cb69a54c3', project_id: null }
// Get projects: [Project1, Project2, Project3]
// Build payload: ClassificationPayload
// Send to N8N: POST /n8n-classification-webhook
```

### 3. N8N Classification Agent
```typescript
// Analyze content against project metadata
// Score each project:
// - Project1 (Summer Campaign): 0.87 (high match on 'storyboard' + sender)
// - Project2 (Marketing): 0.23 (low match)
// - Project3 (Internal): 0.05 (no match)

// Return: { classified_project_id: 'c119adba-8452-11ec-a8a3-0242ac120002' }
```

### 4. Document Update
```typescript
// Update document with classified project_id
await supabase
  .from('documents')
  .update({ project_id: 'c119adba-8452-11ec-a8a3-0242ac120002' })
  .eq('id', 'd8c3d123-b9d0-4a45-bced-d12cb69a54c3');

// Update project classification tracking
await supabase
  .from('projects')
  .update({ 
    last_classification_at: new Date().toISOString(),
    pinecone_document_count: sql`pinecone_document_count + 1`
  })
  .eq('id', 'c119adba-8452-11ec-a8a3-0242ac120002');
```

## 🚀 Implementation Notes

### Environment Variables
```bash
N8N_CLASSIFICATION_WEBHOOK_URL=https://your-n8n-instance.com/webhook/classification
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Error Handling
- **User not found**: Log attempt, don't create document
- **No active projects**: Send empty project_metadata array
- **N8N webhook failure**: Log error, document remains unclassified
- **Classification timeout**: Document stays unclassified for manual review

### Performance Considerations
- Projects are ordered by `last_classification_at` for efficient matching
- GIN indexes on classification fields for fast queries
- Full-text search index for semantic matching
- Classification feedback helps improve future accuracy

### Monitoring
- All processing is logged in `email_processing_logs` table
- Classification success/failure rates tracked
- Project classification activity monitored
- Performance metrics available via database queries 