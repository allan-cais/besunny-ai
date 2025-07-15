# Project Onboarding Wizard

## Overview

The Project Onboarding Wizard is a new chat-like interface that guides users through creating a new project by asking a series of structured questions. It replaces the previous simple form-based project creation dialog with an interactive, step-by-step questionnaire.

## Features

- **Chat-like Interface**: Simulates a real-time messaging experience with thinking animations
- **Step-by-step Questions**: Guides users through 10 predefined questions with natural pauses
- **Data Validation**: Ensures all required fields are completed
- **Inline Editing**: Users can edit any answer directly in the summary view without restarting the chat
- **Summary Review**: Shows a complete summary with inline editing capabilities
- **n8n Integration**: Sends structured data to n8n webhook for further processing

## Questions Asked

1. **Project Name**: What's the project name?
2. **Overview**: How would you describe this project in one sentence?
3. **Keywords**: What keywords or phrases are likely to appear in emails or files about this project? (comma-separated)
4. **Deliverables**: What are the expected deliverables?
5. **Internal Lead**: Who is the internal lead for this project?
6. **Agency Lead**: Who is the agency lead for this project?
7. **Client Lead**: Who is the client lead for this project?
8. **Shoot Date**: What is the primary shoot date or date range?
9. **Location**: Where is the shoot location?
10. **References**: Any reference links or attachments? (optional)

## Data Flow

1. **User clicks "New Project"** in the navigation sidebar
2. **Backend creates project** in Supabase and returns `project_id`
3. **Frontend wizard opens** and starts the questionnaire
4. **User answers questions** one by one in chat format
5. **Data is collected** in local state as user progresses
6. **Summary is displayed** for review and editing
7. **On confirmation**:
   - Project is updated in Supabase with collected data
   - Structured payload is sent to n8n webhook
   - User is redirected to the new project

## Webhook Payload

The wizard sends the following JSON structure to the n8n webhook:

```json
{
  "project_id": "<uuid>",
  "user_id": "<uuid>",
  "summary": {
    "project_name": "...",
    "overview": "...",
    "keywords": ["..."],
    "deliverables": "...",
    "contacts": {
      "internal_lead": "...",
      "agency_lead": "...",
      "client_lead": "..."
    },
    "shoot_date": "...",
    "location": "...",
    "references": "..."
  }
}
```

## Environment Variables

- `VITE_N8N_PROJECT_ONBOARDING_WEBHOOK_URL`: Specific webhook URL for project onboarding
- Falls back to `VITE_N8N_WEBHOOK_URL` if not set

## Technical Implementation

### Component Structure

- **Main Component**: `CreateProjectDialog.tsx`
- **State Management**: React hooks for chat messages, current question, and collected data
- **UI Components**: Uses existing shadcn/ui components (Dialog, Button, Input, Textarea)
- **Styling**: Consistent with existing design system (mono font, stone/zinc color scheme)

### Key Features

- **Auto-scroll**: Chat automatically scrolls to bottom on new messages
- **Auto-focus**: Input field is automatically focused when question changes
- **Thinking Animation**: Shows "..." with bouncing dots between questions to simulate processing
- **Keyboard Navigation**: Enter key submits answers (Shift+Enter for new lines in textarea)
- **Progress Indicator**: Shows current question number and total questions
- **Inline Editing**: Edit any answer directly in the summary with save/cancel buttons
- **Keyboard Shortcuts**: Enter to save, Escape to cancel during editing
- **Error Handling**: Displays errors and allows retry
- **Loading States**: Shows loading indicators during submission

### Data Types

```typescript
interface ProjectOnboardingData {
  project_name: string;
  overview: string;
  keywords: string[];
  deliverables: string;
  contacts: {
    internal_lead: string;
    agency_lead: string;
    client_lead: string;
  };
  shoot_date: string;
  location: string;
  references: string;
}

interface ChatMessage {
  id: string;
  type: 'bot' | 'user';
  content: string;
  timestamp: Date;
  isTyping?: boolean;
}
```

## User Experience

1. **Welcome Message**: Friendly introduction explaining the process
2. **Question Flow**: One question at a time with clear, specific prompts
3. **Thinking Pause**: System shows "..." animation between questions (1.5 seconds)
4. **Input Flexibility**: Text inputs for short answers, textareas for longer responses
5. **Visual Feedback**: Typing indicators, progress tracking, and clear messaging
6. **Review Phase**: Complete summary with inline editing capabilities
7. **Inline Editing**: Click edit button → modify value → save/cancel → return to summary
8. **Confirmation**: Clear final step with loading state during submission

## Benefits

- **Better Data Quality**: Structured questions ensure consistent, complete project information
- **Improved UX**: Chat interface feels more natural and engaging
- **Data Integration**: Structured output enables better downstream processing
- **Error Prevention**: Step-by-step approach reduces incomplete submissions
- **Scalability**: Easy to add/modify questions or integrate with other systems

## Future Enhancements

- **Question Customization**: Allow different question sets based on project type
- **File Uploads**: Support for reference attachments
- **Auto-save**: Save progress if user leaves and returns
- **Template Support**: Pre-fill answers based on project templates
- **Validation Rules**: More sophisticated input validation
- **Multi-language Support**: Internationalization for questions and UI 