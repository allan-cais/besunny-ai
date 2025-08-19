# Dashboard Components

This directory contains the refactored dashboard components that were extracted from the original `dashboard.tsx` file to improve maintainability and code organization.

## Component Structure

### Core Components

- **`Header.tsx`** - The main header component with search, theme toggle, and user account menu
- **`NavigationSidebar.tsx`** - The left sidebar with navigation items, projects, and chats
- **`MainWorkspace.tsx`** - The main content area that renders different views based on active state

### Feature Components

- **`StatsGrid.tsx`** - Displays dashboard statistics (active projects, files processed, uptime)
- **`QuickActions.tsx`** - Quick action buttons for common tasks
- **`DataFeed.tsx`** - Data feed component for browsing connected information sources
- **`FeedItemDetail.tsx`** - Detailed view for individual feed items

### Shared Types

- **`types.ts`** - TypeScript interfaces and types used across dashboard components
- **`index.ts`** - Barrel export file for easy importing

## Refactoring Benefits

1. **Improved Maintainability** - Each component has a single responsibility
2. **Better Code Organization** - Related functionality is grouped together
3. **Easier Testing** - Components can be tested in isolation
4. **Reduced File Size** - The main dashboard file went from ~1100 lines to ~300 lines
5. **Better Reusability** - Components can be reused in other parts of the application

## Usage

```tsx
import {
  Header,
  NavigationSidebar,
  MainWorkspace,
  DashboardChatSession,
  AIChatSession
} from '@/components/dashboard';
```

## Component Dependencies

- All components use the shared UI components from `@/components/ui/`
- Components depend on the auth and theme providers
- Navigation components integrate with Supabase for data persistence
- Components use Lucide React for icons

## State Management

The main dashboard component manages the overall state and passes it down to child components through props. Each component manages its own local state for UI interactions like dialogs and form inputs. 