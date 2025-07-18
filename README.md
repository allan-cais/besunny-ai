# Sunny.ai - Intelligent Workspace

A modern, intelligent development workspace built with React, TypeScript, and Supabase.

## Features

- **User Authentication**: Complete Supabase authentication system with login, signup, and password reset
- **User Management**: Profile editing and account management
- **Real-time Chat**: AI-powered chat interface with message history
- **Modern UI**: Beautiful, responsive interface built with shadcn/ui components
- **Theme Support**: Light, dark, and system theme modes
- **Project Management**: Organize your work with projects and knowledge spaces
- **Virtual Email Addresses**: Unique email addresses for document ingestion
- **Google Drive Integration**: Real-time file monitoring and synchronization
- **Document Management**: Intelligent document processing and classification

## Authentication Setup

This application uses Supabase for authentication. To set up authentication:

1. **Create a Supabase Project**:
   - Go to [supabase.com](https://supabase.com) and create a new project
   - Note your project URL and anon key

2. **Configure Environment Variables**:
   - Copy `env.example` to `.env.local`
   - Update the Supabase configuration:
   ```env
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   ```

3. **Database Setup**:
   - The application will automatically create user records in the `users` table when users sign up
   - Make sure your Supabase project has the required tables (users, projects, chat_sessions, etc.)

## Getting Started

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Set up Environment Variables**:
   ```bash
   cp env.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```

4. **Open in Browser**:
   Navigate to `http://localhost:5173`

## Authentication Flow

1. **Landing Page**: Users start at the main landing page
2. **Authentication**: Click "LOGIN" to access the authentication page
3. **Sign Up/Login**: Users can create accounts or sign in with existing credentials
4. **Dashboard**: Authenticated users are redirected to the main dashboard
5. **Account Management**: Users can manage their profile and account settings via the account menu

## User Management

- **Profile Editing**: Users can update their name and view their email
- **Account Settings**: Access to settings and integrations (placeholder)
- **Logout**: Secure logout functionality
- **Password Reset**: Users can reset their password via email

## Project Structure

```
src/
├── components/
│   ├── auth/           # Authentication components
│   │   ├── LoginForm.tsx
│   │   ├── SignUpForm.tsx
│   │   ├── ForgotPasswordForm.tsx
│   │   ├── UserAccountMenu.tsx
│   │   └── ProtectedRoute.tsx
│   └── ui/             # UI components
├── pages/
│   ├── auth.tsx        # Authentication page
│   ├── dashboard.tsx   # Main dashboard
│   └── index.tsx       # Landing page
├── providers/
│   ├── AuthProvider.tsx    # Authentication context
│   └── ThemeProvider.tsx   # Theme context
└── lib/
    └── supabase.ts     # Supabase client and types
```

## Technologies Used

- **Frontend**: React 18, TypeScript, Vite
- **UI Components**: shadcn/ui, Tailwind CSS
- **Authentication**: Supabase Auth
- **Database**: Supabase PostgreSQL
- **State Management**: React Context, React Query
- **Routing**: React Router DOM

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_SUPABASE_URL` | Your Supabase project URL | Yes |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anon key | Yes |
| `VITE_N8N_WEBHOOK_URL` | N8N webhook URL for AI chat | No |
| `VITE_N8N_DRIVESYNC_WEBHOOK_URL` | N8N webhook URL for Drive sync | No |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Database Setup

### Required Tables

The application uses the existing database tables in your Supabase project:

1. **users** - Stores user information (created automatically by Supabase Auth)
2. **projects** - Stores project information with `created_by` field linking to users
3. **chat_sessions** - Stores chat session information
4. **chat_messages** - Stores individual chat messages
5. **documents** - Stores document information with Google Drive integration
6. **drive_file_watches** - Tracks Google Drive file monitoring
7. **drive_webhook_logs** - Audit trail for Drive webhook events

### Project Management

- Users can create new projects via the "+ Project" button in the Projects menu
- Projects are automatically linked to the creator via the `created_by` field
- Users can see all projects they have created
- The existing `projects` table structure is used without modification

## Google Drive Integration

The application includes a comprehensive Google Drive File Watch System:

### Features
- **Real-time File Monitoring**: Automatically detect changes to Google Drive files
- **Webhook Processing**: Handle file updates and deletions via Google Drive webhooks
- **Status Tracking**: Visual indicators for file watch status and sync state
- **n8n Integration**: Automatic triggering of n8n workflows for file synchronization

### Setup
1. **Google Service Account**: Configure Google service account credentials in Supabase environment variables
2. **Edge Functions**: Deploy the `subscribe-to-drive-file` and `drive-webhook-handler` functions
3. **Database Migration**: Run the Google Drive File Watch migration (`009_add_google_drive_file_watch.sql`)
4. **n8n Webhook**: Configure the `N8N_DRIVESYNC_WEBHOOK_URL` environment variable

### Usage
- Users can subscribe to Google Drive files via the `GoogleDriveWatchManager` component
- File changes are automatically detected and processed
- Status badges show current watch state and last sync time
- Deleted files are automatically marked and cleaned up

For detailed implementation information, see [Google Drive File Watch System Documentation](docs/GOOGLE_DRIVE_FILE_WATCH_SYSTEM.md).

## User Management
