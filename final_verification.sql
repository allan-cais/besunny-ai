-- Final verification: Check for any remaining problematic polling_enabled references
-- This query looks for actual field references, not just comments

-- Check for functions that actually try to access polling_enabled field
SELECT 
  routine_name,
  'FUNCTION' as type
FROM information_schema.routines 
WHERE routine_definition LIKE '%NEW.polling_enabled%'
   OR routine_definition LIKE '%OLD.polling_enabled%'
   OR routine_definition LIKE '%polling_enabled = TRUE%'
   OR routine_definition LIKE '%polling_enabled = FALSE%'
   OR routine_definition LIKE '%polling_enabled IS%'
   OR routine_definition LIKE '%polling_enabled.%'
  AND routine_schema = 'public'

UNION ALL

-- Check for views that reference polling_enabled
SELECT 
  table_name as routine_name,
  'VIEW' as type
FROM information_schema.views 
WHERE view_definition LIKE '%polling_enabled%'
  AND table_schema = 'public'

UNION ALL

-- Check for triggers that might reference polling_enabled
SELECT 
  trigger_name as routine_name,
  'TRIGGER' as type
FROM information_schema.triggers 
WHERE action_statement LIKE '%polling_enabled%'
  AND trigger_schema = 'public';

-- If this query returns no results, all problematic references are fixed! 