# Component Architecture Documentation

## Frontend Structure Overview

The BeSunny.ai frontend is built with React 18 and TypeScript, following modern best practices for component organization, state management, and code splitting. The architecture emphasizes reusability, maintainability, and performance.

## Directory Structure

```
src/
├── components/           # Reusable UI components
│   ├── ui/             # shadcn/ui base components
│   ├── auth/           # Authentication components
│   ├── dashboard/      # Dashboard-specific components
│   ├── layout/         # Layout and navigation components
│   └── integrations/   # Third-party integration components
├── pages/              # Route components and page layouts
├── hooks/              # Custom React hooks
├── providers/          # Context providers and state management
├── lib/                # Utility libraries and services
├── types/              # TypeScript type definitions
├── config/             # Configuration files
└── styles/             # Global styles and CSS
```

## Core Component Categories

### 1. UI Components (`src/components/ui/`)

Base UI components built with shadcn/ui and Tailwind CSS:

- **Button**: Various button variants and sizes
- **Card**: Content containers with headers and content areas
- **Dialog**: Modal dialogs and overlays
- **Form**: Form components with validation
- **Input**: Text inputs, textareas, and form controls
- **Navigation**: Menus, tabs, and navigation elements
- **Feedback**: Toasts, alerts, and progress indicators

**Usage Example:**
```tsx
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Project Title</CardTitle>
  </CardHeader>
  <CardContent>
    <Button variant="default">Action</Button>
  </CardContent>
</Card>
```

### 2. Authentication Components (`src/components/auth/`)

User authentication and account management:

- **LoginForm**: User login interface
- **SignUpForm**: User registration interface
- **ForgotPasswordForm**: Password reset functionality
- **UserAccountMenu**: User profile and account options
- **ProtectedRoute**: Route protection wrapper

**Key Features:**
- Form validation with React Hook Form
- Error handling and user feedback
- Responsive design for mobile and desktop
- Integration with Supabase Auth

### 3. Dashboard Components (`src/components/dashboard/`)

Main application dashboard components:

- **MainWorkspace**: Primary dashboard layout
- **NavigationSidebar**: Left navigation panel
- **Header**: Top navigation bar
- **StatsGrid**: Dashboard statistics and metrics
- **DataFeed**: Activity feed and notifications
- **QuickActions**: Common action shortcuts

**Modal Components:**
- **ClassificationModal**: Document classification interface
- **TranscriptModal**: Meeting transcript viewer
- **EmailModal**: Email content viewer
- **DocumentModal**: Document preview and management
- **BotConfigurationModal**: AI bot setup interface

### 4. Layout Components (`src/components/layout/`)

Application layout and structure:

- **DashboardLayout**: Main dashboard wrapper
- **PageHeader**: Page title and breadcrumbs
- **Sidebar**: Collapsible navigation sidebar
- **ContentArea**: Main content container

## Component Architecture Patterns

### 1. Compound Component Pattern

Used for complex components with multiple related parts:

```tsx
// Example: Card component with header and content
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    Content goes here
  </CardContent>
</Card>
```

### 2. Render Props Pattern

For components that need to render different content:

```tsx
// Example: DataFeed component with custom item rendering
<DataFeed
  items={activities}
  renderItem={(item) => <CustomActivityItem item={item} />}
/>
```

### 3. Higher-Order Components (HOCs)

For cross-cutting concerns like authentication:

```tsx
// Example: ProtectedRoute wrapper
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>
```

## State Management Architecture

### 1. Local Component State

```tsx
const [isOpen, setIsOpen] = useState(false);
const [selectedItem, setSelectedItem] = useState(null);
```

### 2. Context-Based State

```tsx
// AuthProvider for user authentication state
const { user, signOut } = useAuth();

// ThemeProvider for theme preferences
const { theme, setTheme } = useTheme();
```

### 3. Server State with React Query

```tsx
// Data fetching and caching
const { data: projects, isLoading } = useQuery({
  queryKey: ['projects'],
  queryFn: () => fetchProjects()
});
```

### 4. Form State Management

```tsx
// React Hook Form integration
const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: initialValues
});
```

## Component Communication Patterns

### 1. Props Down, Events Up

```tsx
// Parent component passes data down
<ChildComponent 
  data={parentData} 
  onAction={handleChildAction} 
/>

// Child component emits events up
const handleClick = () => {
  onAction(childData);
};
```

### 2. Context for Deep Component Trees

```tsx
// Deep component access to shared state
const { user } = useAuth();
const { theme } = useTheme();
```

### 3. Custom Hooks for Logic Sharing

```tsx
// Reusable logic across components
const { data, loading, error, refetch } = useSupabase();
const { isMobile } = useMobile();
```

## Performance Optimization Patterns

### 1. Memoization

```tsx
// Prevent unnecessary re-renders
const memoizedValue = useMemo(() => {
  return expensiveCalculation(data);
}, [data]);

const MemoizedComponent = React.memo(ExpensiveComponent);
```

### 2. Code Splitting

```tsx
// Lazy load components
const LazyComponent = lazy(() => import('./LazyComponent'));

// Route-based code splitting
const ProjectPage = lazy(() => import('./pages/project'));
```

### 3. Virtual Scrolling

```tsx
// Efficient rendering of large lists
<VirtualList
  items={largeDataSet}
  height={400}
  itemHeight={50}
  renderItem={renderItem}
/>
```

## Component Testing Strategy

### 1. Unit Testing

```tsx
// Test individual component behavior
describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
});
```

### 2. Integration Testing

```tsx
// Test component interactions
describe('Form Submission', () => {
  it('submits form data correctly', async () => {
    render(<LoginForm onSubmit={mockSubmit} />);
    // Fill form and submit
    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));
    expect(mockSubmit).toHaveBeenCalledWith(expectedData);
  });
});
```

### 3. Accessibility Testing

```tsx
// Ensure components meet accessibility standards
it('has proper ARIA labels', () => {
  render(<Modal />);
  expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby');
});
```

## Component Documentation Standards

### 1. Component Props Interface

```tsx
interface ComponentProps {
  /** Primary content to display */
  children: React.ReactNode;
  /** Optional CSS class name */
  className?: string;
  /** Callback when component is clicked */
  onClick?: () => void;
  /** Whether component is disabled */
  disabled?: boolean;
}
```

### 2. Component Usage Examples

```tsx
/**
 * Button component with various variants and sizes
 * 
 * @example
 * ```tsx
 * <Button variant="default" size="lg">
 *   Click me
 * </Button>
 * ```
 */
export const Button: React.FC<ButtonProps> = ({ ... }) => {
  // Component implementation
};
```

### 3. Storybook Integration

```tsx
// Storybook stories for component development
export default {
  title: 'Components/Button',
  component: Button,
  parameters: {
    docs: {
      description: {
        component: 'A versatile button component with multiple variants'
      }
    }
  }
} as Meta;
```

## Component Library Guidelines

### 1. Design System Consistency

- **Color Palette**: Consistent color usage across components
- **Typography**: Standardized font sizes and weights
- **Spacing**: Consistent margin and padding values
- **Shadows**: Unified elevation system

### 2. Accessibility Standards

- **ARIA Labels**: Proper accessibility attributes
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: Semantic HTML structure
- **Color Contrast**: WCAG compliance

### 3. Responsive Design

- **Mobile First**: Mobile-optimized layouts
- **Breakpoints**: Consistent responsive breakpoints
- **Touch Targets**: Appropriate touch target sizes
- **Flexible Layouts**: Adaptive component layouts

## Future Component Enhancements

### 1. Advanced Patterns

- **Compound Components**: More complex component compositions
- **Render Props**: Flexible rendering patterns
- **Hooks Composition**: Custom hook combinations
- **Context Optimization**: Performance improvements

### 2. Component Library Expansion

- **Data Visualization**: Charts and graphs
- **Advanced Forms**: Complex form patterns
- **Animation System**: Smooth transitions and animations
- **Internationalization**: Multi-language support

### 3. Performance Improvements

- **Concurrent Features**: React 18 concurrent rendering
- **Suspense**: Better loading states
- **Transitions**: Smooth UI transitions
- **Optimization**: Bundle size and performance optimization
