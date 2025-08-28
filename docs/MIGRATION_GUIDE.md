# Migration Guide: Old Framework → New Framework

## 🚨 Breaking Changes

### 1. **supabaseService → New API Structure**

**OLD WAY:**
```tsx
import { supabaseService } from '@/lib/supabase';

// Using old service
const projects = await supabaseService.getProjects();
const project = await supabaseService.createProject(data);
```

**NEW WAY:**
```tsx
import { api } from '@/lib/api';
import { useProjects, useCreateProject } from '@/hooks/use-api';

// Using new hooks
const { data: projects, isLoading } = useProjects();
const createProject = useCreateProject();
createProject.mutate(projectData);
```

### 2. **ChatSession Type Changes**

**OLD INTERFACE:**
```tsx
interface ChatSession {
  id: string;
  user_id?: string;
  project_id?: string;
  name?: string;
  started_at: string;
  ended_at?: string;
}
```

**NEW INTERFACE:**
```tsx
interface ChatSession {
  id: string;
  project_id?: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}
```

### 3. **PersonData Type Removed**

The `PersonData` type has been removed. Use the new `Entity` type instead:

**OLD:**
```tsx
import { PersonData } from '@/types';
```

**NEW:**
```tsx
import { Entity } from '@/types';

// Entity type includes:
interface Entity {
  name: string;
  type: 'person' | 'organization' | 'location' | 'date' | 'amount';
  value: string;
  confidence: number;
}
```

## 🔄 Migration Steps

### Step 1: Update Imports
Replace old service imports with new API structure:

```tsx
// OLD
import { supabaseService } from '@/lib/supabase';

// NEW
import { api } from '@/lib/api';
import { useProjects, useCreateProject } from '@/hooks/use-api';
```

### Step 2: Replace Service Calls with Hooks
```tsx
// OLD
const [projects, setProjects] = useState([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
  const fetchProjects = async () => {
    setLoading(true);
    try {
      const data = await supabaseService.getProjects();
      setProjects(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };
  fetchProjects();
}, []);

// NEW
const { data: projects, isLoading, error } = useProjects();
```

### Step 3: Update Mutations
```tsx
// OLD
const handleCreate = async (data) => {
  try {
    await supabaseService.createProject(data);
    // Refresh data manually
  } catch (error) {
    console.error(error);
  }
};

// NEW
const createProject = useCreateProject();

const handleCreate = (data) => {
  createProject.mutate(data);
  // Data automatically refreshes via React Query
};
```

### Step 4: Update Type Imports
```tsx
// OLD
import type { PersonData, ExtendedProject } from '@/types';

// NEW
import type { Entity, Project } from '@/types';
```

## 📝 Component Migration Examples

### Project Page Migration
```tsx
// OLD
import { supabaseService, supabase } from '@/lib/supabase';
import type { Project, Meeting, Document, PersonData } from '@/types';

// NEW
import { supabase } from '@/lib/supabase';
import type { Project, Meeting, Document, Entity } from '@/types';
import { useProjects, useProject } from '@/hooks/use-api';
```

### Dashboard Layout Migration
```tsx
// OLD
import { supabaseService } from '@/lib/supabase';

// Check if configured
if (!supabaseService?.isConfigured?.()) {
  // Handle not configured
}

// Update project
await supabaseService.updateProject(projectId, updates);

// NEW
import { api } from '@/lib/api';
import { useUpdateProject } from '@/hooks/use-api';

const updateProject = useUpdateProject();

// Update project
updateProject.mutate({ id: projectId, updates });
```

## 🎯 Benefits After Migration

1. **Automatic Caching**: React Query handles data caching automatically
2. **Loading States**: Built-in loading and error states
3. **Optimistic Updates**: Better user experience with immediate feedback
4. **Type Safety**: Comprehensive TypeScript support
5. **Error Handling**: Automatic error handling and user feedback
6. **Performance**: Efficient re-renders and data fetching

## 🚨 Common Issues & Solutions

### Issue: "supabaseService is not defined"
**Solution**: Replace with new API structure using hooks

### Issue: "Property 'started_at' does not exist on type 'ChatSession'"
**Solution**: Use `created_at` instead of `started_at`

### Issue: "PersonData type not found"
**Solution**: Use `Entity` type with `type: 'person'`

### Issue: "entity_patterns property does not exist"
**Solution**: Use the new `classification` property on documents

## 📚 Next Steps

1. **Update all imports** to use new API structure
2. **Replace service calls** with React Query hooks
3. **Update type references** to use new interfaces
4. **Test functionality** to ensure everything works
5. **Remove old code** that's no longer needed

## 🆘 Need Help?

- Check the new API documentation in `src/hooks/use-api.ts`
- Review the new types in `src/types/index.ts`
- Use the new API service classes in `src/lib/api.ts`
- Follow the patterns in the updated components
