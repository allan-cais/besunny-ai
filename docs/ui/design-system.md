# Design System

## Overview

Kirit Askuno uses a consistent design system built with Tailwind CSS to ensure a cohesive user experience across all components and pages.

## Color Palette

### Primary Colors
- **Blue**: `#3B82F6` (blue-600) - Primary actions, links
- **Blue Dark**: `#1D4ED8` (blue-700) - Hover states
- **Blue Light**: `#DBEAFE` (blue-100) - Backgrounds, highlights

### Neutral Colors
- **Gray 900**: `#111827` - Primary text
- **Gray 700**: `#374151` - Secondary text
- **Gray 500**: `#6B7280` - Muted text
- **Gray 200**: `#E5E7EB` - Borders
- **Gray 100**: `#F3F4F6` - Backgrounds
- **Gray 50**: `#F9FAFB` - Page backgrounds

### Status Colors
- **Success**: `#10B981` (emerald-500)
- **Warning**: `#F59E0B` (amber-500)
- **Error**: `#EF4444` (red-500)
- **Info**: `#3B82F6` (blue-500)

## Typography

### Font Family
- **Primary**: System UI stack (system-ui, sans-serif)
- **Monospace**: For code snippets and technical content

### Font Sizes
- **Display**: `text-4xl` (36px) - Page titles
- **Heading 1**: `text-3xl` (30px) - Section titles
- **Heading 2**: `text-2xl` (24px) - Subsection titles
- **Heading 3**: `text-xl` (20px) - Component titles
- **Body**: `text-base` (16px) - Regular text
- **Small**: `text-sm` (14px) - Captions, metadata
- **Extra Small**: `text-xs` (12px) - Labels, timestamps

### Font Weights
- **Light**: `font-light` (300)
- **Normal**: `font-normal` (400)
- **Medium**: `font-medium` (500)
- **Semibold**: `font-semibold` (600)
- **Bold**: `font-bold` (700)

## Spacing

### Scale
- **xs**: `0.25rem` (4px)
- **sm**: `0.5rem` (8px)
- **md**: `1rem` (16px)
- **lg**: `1.5rem` (24px)
- **xl**: `2rem` (32px)
- **2xl**: `3rem` (48px)
- **3xl**: `4rem` (64px)

## Components

### Buttons

#### Primary Button
```html
<button class="btn-primary">
  Primary Action
</button>
```

#### Secondary Button
```html
<button class="btn-secondary">
  Secondary Action
</button>
```

#### Button States
- **Default**: Standard styling
- **Hover**: Darker background color
- **Active**: Pressed state
- **Disabled**: Reduced opacity, no interaction

### Cards

#### Standard Card
```html
<div class="card">
  <h3 class="text-lg font-semibold mb-2">Card Title</h3>
  <p class="text-gray-600">Card content goes here.</p>
</div>
```

### Forms

#### Input Field
```html
<input class="input-field" type="text" placeholder="Enter text..." />
```

#### Form Layout
- Use consistent spacing between form elements
- Group related fields together
- Provide clear labels and help text
- Show validation states clearly

## Layout

### Container
- **Max Width**: `max-w-7xl` (1280px)
- **Padding**: Responsive padding (`px-4 sm:px-6 lg:px-8`)
- **Centered**: Auto margins for centering

### Grid System
- **1 Column**: Mobile (default)
- **2 Columns**: Tablet (`md:grid-cols-2`)
- **3+ Columns**: Desktop (`lg:grid-cols-3`)

## Responsive Design

### Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

### Mobile-First Approach
- Start with mobile styles
- Add tablet and desktop styles with responsive prefixes
- Test on actual devices

## Accessibility

### Color Contrast
- Ensure sufficient contrast ratios (WCAG AA compliant)
- Don't rely solely on color to convey information
- Provide alternative indicators for color-coded information

### Focus States
- Visible focus indicators for keyboard navigation
- Consistent focus styling across all interactive elements
- Logical tab order

### Screen Readers
- Semantic HTML structure
- Proper ARIA labels and roles
- Alt text for images
- Descriptive link text

## Animation

### Transitions
- **Duration**: 150ms for micro-interactions
- **Easing**: `transition-colors` for color changes
- **Hover**: Subtle feedback for interactive elements

### Loading States
- Skeleton screens for content loading
- Spinner animations for actions
- Progress indicators for long operations

## Best Practices

1. **Consistency**: Use the same patterns throughout the application
2. **Simplicity**: Keep designs clean and uncluttered
3. **Accessibility**: Design for all users, including those with disabilities
4. **Performance**: Optimize for fast loading and smooth interactions
5. **Maintainability**: Use reusable components and consistent naming 