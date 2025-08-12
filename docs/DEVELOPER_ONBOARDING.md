# Developer Onboarding Guide

## Welcome to BeSunny.ai!

This guide will help you get up and running with the BeSunny.ai project as quickly as possible. Whether you're a frontend developer, backend developer, or full-stack engineer, this guide covers everything you need to know.

## Quick Start (5 minutes)

### Prerequisites
- **Node.js**: Version 18 or higher
- **Git**: Latest version
- **Code Editor**: VS Code (recommended) or your preferred editor
- **Browser**: Chrome, Firefox, or Safari

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/besunny-ai.git
cd besunny-ai
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Set Up Environment
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

### 4. Start Development Server
```bash
npm run dev
```

### 5. Open in Browser
Navigate to `http://localhost:5173`

🎉 **You're ready to develop!**

## Project Overview

### What is BeSunny.ai?
BeSunny.ai is an intelligent development workspace that integrates multiple productivity tools and AI capabilities to streamline project management, document processing, and team collaboration.

### Key Features
- **Project Management**: AI-assisted project setup and organization
- **Document Intelligence**: Multi-format document processing with AI classification
- **Meeting Management**: Calendar integration with AI transcription
- **Virtual Email System**: Unique email addresses for document ingestion
- **Google Drive Integration**: Real-time file monitoring and synchronization
- **AI Chat Assistant**: Context-aware project assistance

### Technology Stack
- **Frontend**: React 18 + TypeScript + Vite
- **UI Components**: shadcn/ui + Tailwind CSS
- **Backend**: Supabase (PostgreSQL + Edge Functions)
- **Authentication**: Supabase Auth
- **AI Services**: OpenAI GPT models
- **Integrations**: Google APIs, N8N workflows

## Project Structure

```
besunny-ai/
├── src/                    # Source code
│   ├── components/        # React components
│   │   ├── ui/           # Base UI components (shadcn/ui)
│   │   ├── auth/         # Authentication components
│   │   ├── dashboard/    # Dashboard-specific components
│   │   ├── layout/       # Layout components
│   │   └── integrations/ # Third-party integration components
│   ├── pages/            # Route components
│   ├── hooks/            # Custom React hooks
│   ├── providers/        # Context providers
│   ├── lib/              # Utility libraries and services
│   ├── types/            # TypeScript type definitions
│   └── config/           # Configuration files
├── supabase/              # Supabase configuration and functions
│   ├── functions/        # Edge functions
│   ├── migrations/       # Database migrations
│   └── config.toml       # Supabase configuration
├── docs/                  # Project documentation
├── public/                # Static assets
└── package.json           # Dependencies and scripts
```

## Development Environment Setup

### 1. Required Software

#### Node.js and npm
```bash
# Check if Node.js is installed
node --version  # Should be 18.x or higher
npm --version   # Should be 9.x or higher

# Install Node.js (if needed)
# Visit https://nodejs.org/ or use nvm
```

#### Git
```bash
# Check if Git is installed
git --version

# Configure Git (if first time)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

#### VS Code (Recommended)
- Download from [code.visualstudio.com](https://code.visualstudio.com/)
- Install recommended extensions:
  - **ES7+ React/Redux/React-Native snippets**
  - **Tailwind CSS IntelliSense**
  - **TypeScript Importer**
  - **Prettier - Code formatter**
  - **ESLint**

### 2. Environment Configuration

#### Create Environment File
```bash
cp .env.example .env.local
```

#### Required Environment Variables
```env
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Google OAuth (Optional for development)
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI Configuration (Optional for development)
VITE_OPENAI_API_KEY=your-openai-api-key

# N8N Webhook (Optional for development)
VITE_N8N_WEBHOOK_URL=your-n8n-webhook-url
```

#### Get Supabase Credentials
1. Go to [supabase.com](https://supabase.com)
2. Create a new project or use existing one
3. Go to Settings → API
4. Copy Project URL and anon public key

### 3. Database Setup

#### Run Migrations
```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-ref

# Run migrations
supabase db push
```

#### Verify Database Connection
```bash
# Check if tables are created
supabase db diff
```

## Development Workflow

### 1. Daily Development Process

#### Start Your Day
```bash
# Pull latest changes
git pull origin main

# Install any new dependencies
npm install

# Start development server
npm run dev
```

#### Development Cycle
1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes**: Write code, add tests
3. **Test Locally**: Ensure everything works
4. **Commit Changes**: `git commit -m "feat: add your feature"`
5. **Push Branch**: `git push origin feature/your-feature-name`
6. **Create PR**: Open pull request on GitHub

#### End of Day
```bash
# Commit any remaining changes
git add .
git commit -m "feat: work in progress"

# Push to your branch
git push origin feature/your-feature-name
```

### 2. Code Quality Standards

#### TypeScript
- All new code must be written in TypeScript
- Use strict type checking
- Avoid `any` type - use proper interfaces
- Export types from `src/types/index.ts`

#### Code Style
- Use Prettier for formatting
- Follow ESLint rules
- Use meaningful variable and function names
- Add JSDoc comments for complex functions

#### Component Structure
```tsx
// Component template
import React from 'react';
import { ComponentProps } from './types';

interface ComponentProps {
  /** Description of the prop */
  title: string;
  /** Optional description */
  description?: string;
  /** Callback function */
  onAction: () => void;
}

export const Component: React.FC<ComponentProps> = ({
  title,
  description,
  onAction
}) => {
  return (
    <div>
      <h1>{title}</h1>
      {description && <p>{description}</p>}
      <button onClick={onAction}>Action</button>
    </div>
  );
};
```

### 3. Testing

#### Run Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- --testPathPattern=ComponentName
```

#### Writing Tests
```tsx
// Component test template
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Component } from './Component';

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component title="Test" onAction={() => {}} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('calls onAction when button is clicked', async () => {
    const mockAction = jest.fn();
    render(<Component title="Test" onAction={mockAction} />);
    
    await userEvent.click(screen.getByRole('button'));
    expect(mockAction).toHaveBeenCalledTimes(1);
  });
});
```

## Key Concepts

### 1. State Management

#### Local State
```tsx
const [isOpen, setIsOpen] = useState(false);
const [data, setData] = useState<DataType[]>([]);
```

#### Global State (Context)
```tsx
// Use existing contexts
const { user } = useAuth();
const { theme, setTheme } = useTheme();
```

#### Server State (React Query)
```tsx
const { data, isLoading, error } = useQuery({
  queryKey: ['projects'],
  queryFn: () => fetchProjects()
});
```

### 2. Component Patterns

#### Compound Components
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

#### Render Props
```tsx
<DataFeed
  items={activities}
  renderItem={(item) => <CustomItem item={item} />}
/>
```

#### Custom Hooks
```tsx
const { data, loading, error, refetch } = useSupabase();
const { isMobile } = useMobile();
```

### 3. Routing

#### Route Structure
```tsx
// Protected routes
<Route 
  path="/dashboard" 
  element={
    <ProtectedRoute>
      <DashboardLayout />
    </ProtectedRoute>
  } 
/>

// Dynamic routes
<Route path="/project/:projectId" element={<ProjectDashboard />} />
```

#### Navigation
```tsx
import { useNavigate, useParams } from 'react-router-dom';

const navigate = useNavigate();
const { projectId } = useParams();

// Navigate to route
navigate('/dashboard');

// Navigate with parameters
navigate(`/project/${projectId}`);
```

## Common Tasks

### 1. Adding a New Page

#### Create Page Component
```tsx
// src/pages/NewPage.tsx
import React from 'react';
import { PageHeader } from '@/components/layout/PageHeader';

const NewPage: React.FC = () => {
  return (
    <div className="px-4 pt-12 pb-8">
      <PageHeader title="New Page" description="Page description" />
      {/* Page content */}
    </div>
  );
};

export default NewPage;
```

#### Add Route
```tsx
// src/App.tsx
import NewPage from './pages/NewPage';

// Add to routes
<Route 
  path="/new-page" 
  element={
    <ProtectedRoute>
      <DashboardLayout />
    </ProtectedRoute>
  } 
>
  <Route index element={<NewPage />} />
</Route>
```

#### Add Navigation
```tsx
// src/components/layout/NavigationSidebar.tsx
{
  name: 'New Page',
  href: '/new-page',
  icon: IconComponent,
  current: pathname === '/new-page'
}
```

### 2. Adding a New Component

#### Create Component
```tsx
// src/components/NewComponent.tsx
import React from 'react';

interface NewComponentProps {
  title: string;
  onAction?: () => void;
}

export const NewComponent: React.FC<NewComponentProps> = ({
  title,
  onAction
}) => {
  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold">{title}</h3>
      {onAction && (
        <button 
          onClick={onAction}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
        >
          Action
        </button>
      )}
    </div>
  );
};
```

#### Export from Index
```tsx
// src/components/index.ts
export { NewComponent } from './NewComponent';
```

#### Add Types
```tsx
// src/types/index.ts
export interface NewComponentData {
  id: string;
  title: string;
  description?: string;
}
```

### 3. Adding API Integration

#### Create Service
```tsx
// src/lib/new-service.ts
import { supabase } from './supabase';

export const newService = {
  async getData(): Promise<DataType[]> {
    const { data, error } = await supabase
      .from('table_name')
      .select('*');
    
    if (error) throw error;
    return data || [];
  },

  async createData(item: CreateDataType): Promise<DataType> {
    const { data, error } = await supabase
      .from('table_name')
      .insert(item)
      .select()
      .single();
    
    if (error) throw error;
    return data;
  }
};
```

#### Create Hook
```tsx
// src/hooks/use-new-service.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { newService } from '@/lib/new-service';

export const useNewService = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['new-data'],
    queryFn: newService.getData
  });

  const createMutation = useMutation({
    mutationFn: newService.createData,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['new-data'] });
    }
  });

  return {
    data,
    isLoading,
    error,
    create: createMutation.mutate,
    isCreating: createMutation.isPending
  };
};
```

## Debugging and Troubleshooting

### 1. Common Issues

#### Build Errors
```bash
# Clear build cache
rm -rf node_modules/.vite
npm run build

# Check TypeScript errors
npx tsc --noEmit
```

#### Runtime Errors
- Check browser console for JavaScript errors
- Check Network tab for API failures
- Use React DevTools for component debugging

#### Database Issues
```bash
# Check database connection
supabase status

# Reset database (development only)
supabase db reset
```

### 2. Debug Tools

#### React DevTools
- Install browser extension
- Use Components tab to inspect component tree
- Use Profiler tab to analyze performance

#### VS Code Debugging
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Launch Chrome",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/src"
    }
  ]
}
```

#### Console Logging
```tsx
// Use structured logging
console.group('Component State');
console.log('Props:', props);
console.log('State:', state);
console.groupEnd();

// Use debug flag
if (process.env.NODE_ENV === 'development') {
  console.log('Debug info:', data);
}
```

## Performance Optimization

### 1. Code Splitting
```tsx
// Lazy load components
const LazyComponent = lazy(() => import('./LazyComponent'));

// Route-based splitting
const ProjectPage = lazy(() => import('./pages/project'));
```

### 2. Memoization
```tsx
// Memoize expensive calculations
const memoizedValue = useMemo(() => {
  return expensiveCalculation(data);
}, [data]);

// Memoize components
const MemoizedComponent = React.memo(ExpensiveComponent);
```

### 3. Virtual Scrolling
```tsx
// For large lists
<VirtualList
  items={largeDataSet}
  height={400}
  itemHeight={50}
  renderItem={renderItem}
/>
```

## Deployment

### 1. Development Deployment
```bash
# Build for development
npm run build:dev

# Preview build
npm run preview
```

### 2. Production Deployment
```bash
# Build for production
npm run build

# Deploy to Netlify (if configured)
netlify deploy --prod
```

### 3. Environment Management
```bash
# Set production environment variables
cp .env.local .env.production

# Update with production values
VITE_SUPABASE_URL=https://prod-project.supabase.co
VITE_SUPABASE_ANON_KEY=prod-anon-key
```

## Getting Help

### 1. Documentation
- **Project Overview**: `docs/PROJECT_OVERVIEW.md`
- **Technical Architecture**: `docs/TECHNICAL_ARCHITECTURE.md`
- **Component Architecture**: `docs/COMPONENT_ARCHITECTURE.md`
- **API Reference**: `docs/API_REFERENCE.md`

### 2. Code Examples
- **Component Library**: `src/components/ui/`
- **Page Examples**: `src/pages/`
- **Hook Examples**: `src/hooks/`
- **Service Examples**: `src/lib/`

### 3. Support Channels
- **GitHub Issues**: Report bugs and request features
- **Discord Community**: Ask questions and get help
- **Code Reviews**: Learn from team feedback
- **Pair Programming**: Work with experienced developers

### 4. Learning Resources
- **React Documentation**: [react.dev](https://react.dev/)
- **TypeScript Handbook**: [typescriptlang.org](https://www.typescriptlang.org/)
- **Tailwind CSS**: [tailwindcss.com](https://tailwindcss.com/)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)

## Next Steps

### 1. First Week Goals
- [ ] Set up development environment
- [ ] Run the application locally
- [ ] Understand project structure
- [ ] Make your first commit
- [ ] Review existing code patterns

### 2. First Month Goals
- [ ] Contribute to a small feature
- [ ] Write tests for your code
- [ ] Participate in code reviews
- [ ] Understand the full development workflow
- [ ] Learn about the business domain

### 3. Ongoing Development
- [ ] Stay updated with project changes
- [ ] Contribute to documentation
- [ ] Share knowledge with team
- [ ] Suggest improvements
- [ ] Help onboard new developers

## Welcome to the Team! 🎉

You're now part of the BeSunny.ai development team. We're excited to have you on board and can't wait to see what you'll build!

If you have any questions or need help with anything, don't hesitate to ask. The team is here to support you and help you succeed.

**Happy coding!** 🚀
