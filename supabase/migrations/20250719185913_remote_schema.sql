drop policy "Users can insert document chunks" on "public"."document_chunks";

drop policy "Users can read chunks in their projects" on "public"."document_chunks";

drop policy "Users can insert documents" on "public"."documents";

drop policy "Users can read documents in their projects" on "public"."documents";

drop policy "Users can insert projects" on "public"."projects";

drop policy "Users can read their own projects" on "public"."projects";

alter table "public"."chat_sessions" drop constraint "chat_sessions_project_id_fkey";

alter table "public"."document_chunks" drop constraint "document_chunks_project_id_fkey";

alter table "public"."documents" drop constraint "documents_project_id_fkey";

alter table "public"."knowledge_spaces" drop constraint "knowledge_spaces_project_id_fkey";

alter table "public"."receipts" drop constraint "receipts_project_id_fkey";

alter table "public"."summaries" drop constraint "summaries_project_id_fkey";

create table "public"."drive_file_watches" (
    "id" uuid not null default gen_random_uuid(),
    "document_id" uuid,
    "project_id" uuid,
    "file_id" text not null,
    "channel_id" text not null,
    "resource_id" text not null,
    "expiration" timestamp with time zone not null,
    "is_active" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."drive_file_watches" enable row level security;

create table "public"."drive_webhook_logs" (
    "id" uuid not null default gen_random_uuid(),
    "document_id" uuid,
    "project_id" uuid,
    "file_id" text not null,
    "channel_id" text not null,
    "resource_id" text not null,
    "resource_state" text not null,
    "webhook_received_at" timestamp with time zone default now(),
    "n8n_webhook_sent" boolean default false,
    "n8n_webhook_response" text,
    "n8n_webhook_sent_at" timestamp with time zone,
    "error_message" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."drive_webhook_logs" enable row level security;

create table "public"."email_processing_logs" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid,
    "gmail_message_id" text not null,
    "inbound_address" text not null,
    "extracted_username" text,
    "subject" text,
    "sender" text,
    "received_at" timestamp with time zone default now(),
    "processed_at" timestamp with time zone,
    "status" text default 'pending'::text,
    "error_message" text,
    "document_id" uuid,
    "n8n_webhook_sent" boolean default false,
    "n8n_webhook_response" text,
    "created_at" timestamp with time zone default now()
);


alter table "public"."email_processing_logs" enable row level security;

create table "public"."project_metadata" (
    "project_id" uuid not null,
    "normalized_tags" text[],
    "categories" text[],
    "reference_keywords" text[],
    "notes" text,
    "created_at" timestamp without time zone default now()
);


alter table "public"."project_metadata" enable row level security;

alter table "public"."agent_logs" enable row level security;

alter table "public"."chat_messages" enable row level security;

alter table "public"."chat_sessions" enable row level security;

alter table "public"."document_chunks" enable row level security;

alter table "public"."document_tags" enable row level security;

alter table "public"."documents" drop column "file_url";

alter table "public"."documents" add column "file_id" text;

alter table "public"."documents" add column "last_synced_at" timestamp with time zone;

alter table "public"."documents" add column "status" text default 'active'::text;

alter table "public"."documents" add column "watch_active" boolean default false;

alter table "public"."documents" enable row level security;

alter table "public"."knowledge_spaces" enable row level security;

alter table "public"."meetings" add column "auto_bot_notification_sent" boolean default false;

alter table "public"."meetings" add column "auto_scheduled_via_email" boolean default false;

alter table "public"."meetings" add column "bot_configuration" jsonb;

alter table "public"."meetings" add column "bot_deployment_method" text default 'manual'::text;

alter table "public"."meetings" add column "final_transcript_ready" boolean default false;

alter table "public"."meetings" add column "last_polled_at" timestamp with time zone;

alter table "public"."meetings" add column "next_poll_at" timestamp with time zone;

alter table "public"."meetings" add column "poll_interval_minutes" integer default 5;

alter table "public"."meetings" add column "polling_enabled" boolean default true;

alter table "public"."meetings" add column "real_time_transcript" jsonb;

alter table "public"."meetings" add column "transcript_duration_seconds" integer;

alter table "public"."meetings" add column "transcript_metadata" jsonb;

alter table "public"."meetings" add column "transcript_retrieved_at" timestamp with time zone;

alter table "public"."meetings" add column "transcript_summary" text;

alter table "public"."meetings" add column "virtual_email_attendee" text;

alter table "public"."projects" enable row level security;

alter table "public"."receipts" enable row level security;

alter table "public"."subscriptions" enable row level security;

alter table "public"."summaries" enable row level security;

alter table "public"."sync_tracking" enable row level security;

alter table "public"."tags" enable row level security;

alter table "public"."users" add column "username" text;

alter table "public"."users" add column "username_set_at" timestamp with time zone;

alter table "public"."users" enable row level security;

CREATE UNIQUE INDEX drive_file_watches_pkey ON public.drive_file_watches USING btree (id);

CREATE UNIQUE INDEX drive_webhook_logs_pkey ON public.drive_webhook_logs USING btree (id);

CREATE UNIQUE INDEX email_processing_logs_pkey ON public.email_processing_logs USING btree (id);

CREATE INDEX idx_chat_messages_has_chunks ON public.chat_messages USING btree (session_id) WHERE ((used_chunks IS NOT NULL) AND (array_length(used_chunks, 1) > 0));

CREATE INDEX idx_chat_messages_recent ON public.chat_messages USING btree (created_at DESC);

CREATE INDEX idx_chat_messages_role ON public.chat_messages USING btree (role);

CREATE INDEX idx_chat_messages_session_created ON public.chat_messages USING btree (session_id, created_at);

CREATE INDEX idx_chat_messages_session_role ON public.chat_messages USING btree (session_id, role);

CREATE INDEX idx_chat_messages_session_role_date ON public.chat_messages USING btree (session_id, role, created_at);

CREATE INDEX idx_chat_sessions_active ON public.chat_sessions USING btree (started_at) WHERE (ended_at IS NULL);

CREATE INDEX idx_chat_sessions_date_range ON public.chat_sessions USING btree (started_at, ended_at);

CREATE INDEX idx_chat_sessions_name ON public.chat_sessions USING btree (name) WHERE (name IS NOT NULL);

CREATE INDEX idx_chat_sessions_started_at ON public.chat_sessions USING btree (started_at);

CREATE INDEX idx_chat_sessions_user_project_date ON public.chat_sessions USING btree (user_id, project_id, started_at);

CREATE INDEX idx_document_chunks_project_id ON public.document_chunks USING btree (project_id);

CREATE INDEX idx_document_tags_document_id ON public.document_tags USING btree (document_id);

CREATE INDEX idx_documents_file_id ON public.documents USING btree (file_id);

CREATE INDEX idx_documents_last_synced_at ON public.documents USING btree (last_synced_at);

CREATE INDEX idx_documents_project_id ON public.documents USING btree (project_id);

CREATE INDEX idx_documents_status ON public.documents USING btree (status);

CREATE INDEX idx_documents_watch_active ON public.documents USING btree (watch_active);

CREATE INDEX idx_drive_file_watches_channel_id ON public.drive_file_watches USING btree (channel_id);

CREATE INDEX idx_drive_file_watches_created_at ON public.drive_file_watches USING btree (created_at);

CREATE INDEX idx_drive_file_watches_document_id ON public.drive_file_watches USING btree (document_id);

CREATE INDEX idx_drive_file_watches_expiration ON public.drive_file_watches USING btree (expiration);

CREATE INDEX idx_drive_file_watches_file_id ON public.drive_file_watches USING btree (file_id);

CREATE UNIQUE INDEX idx_drive_file_watches_file_id_unique ON public.drive_file_watches USING btree (file_id) WHERE (is_active = true);

CREATE INDEX idx_drive_file_watches_is_active ON public.drive_file_watches USING btree (is_active);

CREATE INDEX idx_drive_file_watches_project_id ON public.drive_file_watches USING btree (project_id);

CREATE INDEX idx_drive_file_watches_resource_id ON public.drive_file_watches USING btree (resource_id);

CREATE INDEX idx_drive_webhook_logs_document_id ON public.drive_webhook_logs USING btree (document_id);

CREATE INDEX idx_drive_webhook_logs_file_id ON public.drive_webhook_logs USING btree (file_id);

CREATE INDEX idx_drive_webhook_logs_n8n_webhook_sent ON public.drive_webhook_logs USING btree (n8n_webhook_sent);

CREATE INDEX idx_drive_webhook_logs_project_id ON public.drive_webhook_logs USING btree (project_id);

CREATE INDEX idx_drive_webhook_logs_resource_state ON public.drive_webhook_logs USING btree (resource_state);

CREATE INDEX idx_drive_webhook_logs_webhook_received_at ON public.drive_webhook_logs USING btree (webhook_received_at);

CREATE INDEX idx_email_processing_logs_gmail_message_id ON public.email_processing_logs USING btree (gmail_message_id);

CREATE INDEX idx_email_processing_logs_received_at ON public.email_processing_logs USING btree (received_at);

CREATE INDEX idx_email_processing_logs_status ON public.email_processing_logs USING btree (status);

CREATE INDEX idx_email_processing_logs_user_id ON public.email_processing_logs USING btree (user_id);

CREATE INDEX idx_knowledge_spaces_project_id ON public.knowledge_spaces USING btree (project_id);

CREATE INDEX idx_meetings_auto_scheduled_via_email ON public.meetings USING btree (auto_scheduled_via_email);

CREATE INDEX idx_meetings_bot_deployment_method ON public.meetings USING btree (bot_deployment_method);

CREATE INDEX idx_meetings_bot_status_polling ON public.meetings USING btree (bot_status, next_poll_at) WHERE ((bot_status = ANY (ARRAY['bot_scheduled'::text, 'bot_joined'::text, 'transcribing'::text])) AND (next_poll_at IS NOT NULL));

CREATE INDEX idx_meetings_final_transcript_ready ON public.meetings USING btree (final_transcript_ready);

CREATE INDEX idx_meetings_last_polled_at ON public.meetings USING btree (last_polled_at);

CREATE INDEX idx_meetings_next_poll_at ON public.meetings USING btree (next_poll_at) WHERE (next_poll_at IS NOT NULL);

CREATE INDEX idx_meetings_polling_enabled ON public.meetings USING btree (polling_enabled);

CREATE INDEX idx_projects_created_by ON public.projects USING btree (created_by);

CREATE INDEX idx_receipts_project_id ON public.receipts USING btree (project_id);

CREATE INDEX idx_subscriptions_created_at ON public.subscriptions USING btree (created_at);

CREATE INDEX idx_subscriptions_expiring ON public.subscriptions USING btree (current_period_end) WHERE (status = 'active'::text);

CREATE INDEX idx_subscriptions_external_customer ON public.subscriptions USING btree (external_customer_id) WHERE (external_customer_id IS NOT NULL);

CREATE UNIQUE INDEX idx_subscriptions_external_unique ON public.subscriptions USING btree (payment_provider, external_subscription_id) WHERE (external_subscription_id IS NOT NULL);

CREATE UNIQUE INDEX idx_subscriptions_one_active_per_user ON public.subscriptions USING btree (user_id) WHERE (status = 'active'::text);

CREATE INDEX idx_subscriptions_payment_method ON public.subscriptions USING btree (payment_method_id) WHERE (payment_method_id IS NOT NULL);

CREATE INDEX idx_subscriptions_period_dates ON public.subscriptions USING btree (current_period_start, current_period_end);

CREATE INDEX idx_subscriptions_tier ON public.subscriptions USING btree (tier);

CREATE INDEX idx_summaries_project_id ON public.summaries USING btree (project_id);

CREATE INDEX idx_tags_created_by ON public.tags USING btree (created_by);

CREATE INDEX idx_users_id ON public.users USING btree (id);

CREATE INDEX idx_users_username ON public.users USING btree (username);

CREATE UNIQUE INDEX project_metadata_pkey ON public.project_metadata USING btree (project_id);

CREATE UNIQUE INDEX users_username_key ON public.users USING btree (username);

alter table "public"."drive_file_watches" add constraint "drive_file_watches_pkey" PRIMARY KEY using index "drive_file_watches_pkey";

alter table "public"."drive_webhook_logs" add constraint "drive_webhook_logs_pkey" PRIMARY KEY using index "drive_webhook_logs_pkey";

alter table "public"."email_processing_logs" add constraint "email_processing_logs_pkey" PRIMARY KEY using index "email_processing_logs_pkey";

alter table "public"."project_metadata" add constraint "project_metadata_pkey" PRIMARY KEY using index "project_metadata_pkey";

alter table "public"."chat_messages" add constraint "check_chat_message_chunks" CHECK (((used_chunks IS NULL) OR (array_length(used_chunks, 1) > 0))) not valid;

alter table "public"."chat_messages" validate constraint "check_chat_message_chunks";

alter table "public"."chat_messages" add constraint "check_chat_message_content" CHECK (((message IS NULL) OR (length(TRIM(BOTH FROM message)) > 0))) not valid;

alter table "public"."chat_messages" validate constraint "check_chat_message_content";

alter table "public"."chat_messages" add constraint "check_chat_message_role" CHECK ((role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text]))) not valid;

alter table "public"."chat_messages" validate constraint "check_chat_message_role";

alter table "public"."chat_messages" add constraint "check_chat_message_session" CHECK ((session_id IS NOT NULL)) not valid;

alter table "public"."chat_messages" validate constraint "check_chat_message_session";

alter table "public"."chat_sessions" add constraint "check_chat_session_dates" CHECK (((ended_at IS NULL) OR (ended_at >= started_at))) not valid;

alter table "public"."chat_sessions" validate constraint "check_chat_session_dates";

alter table "public"."chat_sessions" add constraint "check_chat_session_name" CHECK (((name IS NULL) OR (length(TRIM(BOTH FROM name)) > 0))) not valid;

alter table "public"."chat_sessions" validate constraint "check_chat_session_name";

alter table "public"."documents" add constraint "documents_status_check" CHECK ((status = ANY (ARRAY['active'::text, 'updated'::text, 'deleted'::text, 'error'::text]))) not valid;

alter table "public"."documents" validate constraint "documents_status_check";

alter table "public"."drive_file_watches" add constraint "drive_file_watches_document_id_fkey" FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE not valid;

alter table "public"."drive_file_watches" validate constraint "drive_file_watches_document_id_fkey";

alter table "public"."drive_file_watches" add constraint "drive_file_watches_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."drive_file_watches" validate constraint "drive_file_watches_project_id_fkey";

alter table "public"."drive_webhook_logs" add constraint "drive_webhook_logs_document_id_fkey" FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE not valid;

alter table "public"."drive_webhook_logs" validate constraint "drive_webhook_logs_document_id_fkey";

alter table "public"."drive_webhook_logs" add constraint "drive_webhook_logs_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."drive_webhook_logs" validate constraint "drive_webhook_logs_project_id_fkey";

alter table "public"."email_processing_logs" add constraint "email_processing_logs_document_id_fkey" FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL not valid;

alter table "public"."email_processing_logs" validate constraint "email_processing_logs_document_id_fkey";

alter table "public"."email_processing_logs" add constraint "email_processing_logs_status_check" CHECK ((status = ANY (ARRAY['pending'::text, 'processed'::text, 'failed'::text, 'user_not_found'::text]))) not valid;

alter table "public"."email_processing_logs" validate constraint "email_processing_logs_status_check";

alter table "public"."email_processing_logs" add constraint "email_processing_logs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE not valid;

alter table "public"."email_processing_logs" validate constraint "email_processing_logs_user_id_fkey";

alter table "public"."meetings" add constraint "meetings_bot_deployment_method_check" CHECK ((bot_deployment_method = ANY (ARRAY['manual'::text, 'automatic'::text, 'scheduled'::text]))) not valid;

alter table "public"."meetings" validate constraint "meetings_bot_deployment_method_check";

alter table "public"."project_metadata" add constraint "project_metadata_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."project_metadata" validate constraint "project_metadata_project_id_fkey";

alter table "public"."users" add constraint "users_username_key" UNIQUE using index "users_username_key";

alter table "public"."chat_sessions" add constraint "chat_sessions_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL not valid;

alter table "public"."chat_sessions" validate constraint "chat_sessions_project_id_fkey";

alter table "public"."document_chunks" add constraint "document_chunks_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."document_chunks" validate constraint "document_chunks_project_id_fkey";

alter table "public"."documents" add constraint "documents_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."documents" validate constraint "documents_project_id_fkey";

alter table "public"."knowledge_spaces" add constraint "knowledge_spaces_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."knowledge_spaces" validate constraint "knowledge_spaces_project_id_fkey";

alter table "public"."receipts" add constraint "receipts_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."receipts" validate constraint "receipts_project_id_fkey";

alter table "public"."summaries" add constraint "summaries_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE not valid;

alter table "public"."summaries" validate constraint "summaries_project_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.auto_schedule_bot_for_virtual_email()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  meeting_record RECORD;
BEGIN
  -- Find meetings that have virtual email attendees but no bot scheduled yet
  FOR meeting_record IN
    SELECT 
      m.id,
      m.title,
      m.meeting_url,
      m.start_time,
      m.end_time,
      m.user_id,
      m.google_calendar_event_id
    FROM meetings m
    WHERE m.auto_scheduled_via_email = TRUE
      AND m.bot_deployment_method = 'scheduled'
      AND m.bot_status = 'pending'
      AND m.meeting_url IS NOT NULL
      AND m.start_time > NOW() -- Only future meetings
  LOOP
    -- Update meeting to indicate bot is being scheduled
    UPDATE meetings 
    SET 
      bot_deployment_method = 'automatic',
      bot_status = 'bot_scheduled',
      updated_at = NOW()
    WHERE id = meeting_record.id;
    
    -- Log the auto-scheduling
    INSERT INTO calendar_sync_logs (
      user_id, 
      sync_type, 
      status, 
      events_processed,
      meetings_created,
      error_message
    ) VALUES (
      meeting_record.user_id,
      'auto_bot_scheduling',
      'completed',
      1,
      1,
      'Auto-scheduled bot for meeting: ' || meeting_record.title
    );
  END LOOP;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.deactivate_expired_drive_watches()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
DECLARE
  affected_rows INTEGER;
BEGIN
  UPDATE drive_file_watches 
  SET is_active = FALSE, updated_at = NOW()
  WHERE expiration < NOW() AND is_active = TRUE;
  
  GET DIAGNOSTICS affected_rows = ROW_COUNT;
  
  -- Also update documents to reflect inactive watches
  UPDATE documents 
  SET watch_active = FALSE, updated_at = NOW()
  WHERE id IN (
    SELECT document_id FROM drive_file_watches 
    WHERE expiration < NOW() AND is_active = FALSE
  );
  
  RETURN affected_rows;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.extract_username_from_email(email_address text)
 RETURNS text
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN split_part(email_address, '@', 1);
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_active_drive_file_watch(search_file_id text)
 RETURNS TABLE(id uuid, document_id uuid, project_id uuid, file_id text, channel_id text, resource_id text, expiration timestamp with time zone, is_active boolean)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT 
    dfw.id,
    dfw.document_id,
    dfw.project_id,
    dfw.file_id,
    dfw.channel_id,
    dfw.resource_id,
    dfw.expiration,
    dfw.is_active
  FROM drive_file_watches dfw
  WHERE dfw.file_id = search_file_id 
    AND dfw.is_active = TRUE
    AND dfw.expiration > NOW();
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_document_by_channel_id(search_channel_id text)
 RETURNS TABLE(document_id uuid, project_id uuid, file_id text, title text, status text)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT 
    d.id,
    d.project_id,
    d.file_id,
    d.title,
    d.status
  FROM documents d
  WHERE d.id::TEXT = search_channel_id;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_meetings_for_polling()
 RETURNS TABLE(id uuid, user_id uuid, attendee_bot_id uuid, bot_status text, title text, meeting_url text, next_poll_at timestamp with time zone)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT 
    m.id,
    m.user_id,
    m.attendee_bot_id,
    m.bot_status,
    m.title,
    m.meeting_url,
    m.next_poll_at
  FROM meetings m
  WHERE m.polling_enabled = TRUE
    AND m.attendee_bot_id IS NOT NULL
    AND m.bot_status IN ('bot_scheduled', 'bot_joined', 'transcribing')
    AND (m.next_poll_at IS NULL OR m.next_poll_at <= NOW())
    AND m.user_id = auth.uid();
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_session_message_count(session_uuid uuid)
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN (
    SELECT COUNT(*) 
    FROM chat_messages 
    WHERE session_id = session_uuid
  );
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_user_active_sessions(user_uuid uuid)
 RETURNS TABLE(session_id uuid, session_name text, started_at timestamp with time zone, message_count integer)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT 
    cs.id,
    cs.name,
    cs.started_at,
    get_session_message_count(cs.id) as message_count
  FROM chat_sessions cs
  WHERE cs.user_id = user_uuid
    AND cs.ended_at IS NULL
  ORDER BY cs.started_at DESC;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_user_by_username(search_username text)
 RETURNS TABLE(user_id uuid, email text, name text, username text)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT 
    u.id,
    u.email,
    u.name,
    u.username
  FROM users u
  WHERE u.username = search_username;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_user_project_ids()
 RETURNS TABLE(project_id uuid)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT id FROM projects WHERE created_by = auth.uid();
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_user_recent_messages(user_uuid uuid, limit_count integer DEFAULT 10)
 RETURNS TABLE(message_id uuid, session_id uuid, role text, message text, created_at timestamp with time zone)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT 
    cm.id,
    cm.session_id,
    cm.role,
    cm.message,
    cm.created_at
  FROM chat_messages cm
  JOIN chat_sessions cs ON cm.session_id = cs.id
  WHERE cs.user_id = user_uuid
  ORDER BY cm.created_at DESC
  LIMIT limit_count;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_user_session_stats(user_uuid uuid)
 RETURNS TABLE(total_sessions integer, active_sessions integer, total_messages integer, avg_messages_per_session numeric)
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN QUERY
  SELECT 
    COUNT(DISTINCT cs.id) as total_sessions,
    COUNT(DISTINCT CASE WHEN cs.ended_at IS NULL THEN cs.id END) as active_sessions,
    COUNT(cm.id) as total_messages,
    ROUND(AVG(session_counts.message_count), 2) as avg_messages_per_session
  FROM chat_sessions cs
  LEFT JOIN chat_messages cm ON cs.id = cm.session_id
  LEFT JOIN (
    SELECT 
      session_id,
      COUNT(*) as message_count
    FROM chat_messages
    GROUP BY session_id
  ) session_counts ON cs.id = session_counts.session_id
  WHERE cs.user_id = user_uuid;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.set_user_username(user_uuid uuid, new_username text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  -- Check if username is already taken
  IF EXISTS (SELECT 1 FROM users WHERE username = new_username AND id != user_uuid) THEN
    RETURN FALSE;
  END IF;
  
  -- Update the username
  UPDATE users 
  SET username = new_username, username_set_at = NOW()
  WHERE id = user_uuid;
  
  RETURN FOUND;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_chat_messages_activity()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  -- Track when messages are modified (if we add updated_at later)
  -- For now, just ensure created_at is set properly
  IF NEW.created_at IS NULL THEN
    NEW.created_at = NOW();
  END IF;
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_chat_sessions_activity()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  -- Update ended_at when session is marked as ended
  IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
    NEW.ended_at = NOW();
  END IF;
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_drive_file_watches_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_next_poll_time()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.next_poll_time = NOW() + INTERVAL '5 minutes';
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_subscriptions_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_username_set_at()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.username_set_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.user_has_project_access(project_uuid uuid)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM projects 
    WHERE id = project_uuid AND created_by = auth.uid()
  );
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_bots_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_calendar_webhooks_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_meetings_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public'
AS $function$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$function$
;

grant delete on table "public"."drive_file_watches" to "anon";

grant insert on table "public"."drive_file_watches" to "anon";

grant references on table "public"."drive_file_watches" to "anon";

grant select on table "public"."drive_file_watches" to "anon";

grant trigger on table "public"."drive_file_watches" to "anon";

grant truncate on table "public"."drive_file_watches" to "anon";

grant update on table "public"."drive_file_watches" to "anon";

grant delete on table "public"."drive_file_watches" to "authenticated";

grant insert on table "public"."drive_file_watches" to "authenticated";

grant references on table "public"."drive_file_watches" to "authenticated";

grant select on table "public"."drive_file_watches" to "authenticated";

grant trigger on table "public"."drive_file_watches" to "authenticated";

grant truncate on table "public"."drive_file_watches" to "authenticated";

grant update on table "public"."drive_file_watches" to "authenticated";

grant delete on table "public"."drive_file_watches" to "service_role";

grant insert on table "public"."drive_file_watches" to "service_role";

grant references on table "public"."drive_file_watches" to "service_role";

grant select on table "public"."drive_file_watches" to "service_role";

grant trigger on table "public"."drive_file_watches" to "service_role";

grant truncate on table "public"."drive_file_watches" to "service_role";

grant update on table "public"."drive_file_watches" to "service_role";

grant delete on table "public"."drive_webhook_logs" to "anon";

grant insert on table "public"."drive_webhook_logs" to "anon";

grant references on table "public"."drive_webhook_logs" to "anon";

grant select on table "public"."drive_webhook_logs" to "anon";

grant trigger on table "public"."drive_webhook_logs" to "anon";

grant truncate on table "public"."drive_webhook_logs" to "anon";

grant update on table "public"."drive_webhook_logs" to "anon";

grant delete on table "public"."drive_webhook_logs" to "authenticated";

grant insert on table "public"."drive_webhook_logs" to "authenticated";

grant references on table "public"."drive_webhook_logs" to "authenticated";

grant select on table "public"."drive_webhook_logs" to "authenticated";

grant trigger on table "public"."drive_webhook_logs" to "authenticated";

grant truncate on table "public"."drive_webhook_logs" to "authenticated";

grant update on table "public"."drive_webhook_logs" to "authenticated";

grant delete on table "public"."drive_webhook_logs" to "service_role";

grant insert on table "public"."drive_webhook_logs" to "service_role";

grant references on table "public"."drive_webhook_logs" to "service_role";

grant select on table "public"."drive_webhook_logs" to "service_role";

grant trigger on table "public"."drive_webhook_logs" to "service_role";

grant truncate on table "public"."drive_webhook_logs" to "service_role";

grant update on table "public"."drive_webhook_logs" to "service_role";

grant delete on table "public"."email_processing_logs" to "anon";

grant insert on table "public"."email_processing_logs" to "anon";

grant references on table "public"."email_processing_logs" to "anon";

grant select on table "public"."email_processing_logs" to "anon";

grant trigger on table "public"."email_processing_logs" to "anon";

grant truncate on table "public"."email_processing_logs" to "anon";

grant update on table "public"."email_processing_logs" to "anon";

grant delete on table "public"."email_processing_logs" to "authenticated";

grant insert on table "public"."email_processing_logs" to "authenticated";

grant references on table "public"."email_processing_logs" to "authenticated";

grant select on table "public"."email_processing_logs" to "authenticated";

grant trigger on table "public"."email_processing_logs" to "authenticated";

grant truncate on table "public"."email_processing_logs" to "authenticated";

grant update on table "public"."email_processing_logs" to "authenticated";

grant delete on table "public"."email_processing_logs" to "service_role";

grant insert on table "public"."email_processing_logs" to "service_role";

grant references on table "public"."email_processing_logs" to "service_role";

grant select on table "public"."email_processing_logs" to "service_role";

grant trigger on table "public"."email_processing_logs" to "service_role";

grant truncate on table "public"."email_processing_logs" to "service_role";

grant update on table "public"."email_processing_logs" to "service_role";

grant delete on table "public"."project_metadata" to "anon";

grant insert on table "public"."project_metadata" to "anon";

grant references on table "public"."project_metadata" to "anon";

grant select on table "public"."project_metadata" to "anon";

grant trigger on table "public"."project_metadata" to "anon";

grant truncate on table "public"."project_metadata" to "anon";

grant update on table "public"."project_metadata" to "anon";

grant delete on table "public"."project_metadata" to "authenticated";

grant insert on table "public"."project_metadata" to "authenticated";

grant references on table "public"."project_metadata" to "authenticated";

grant select on table "public"."project_metadata" to "authenticated";

grant trigger on table "public"."project_metadata" to "authenticated";

grant truncate on table "public"."project_metadata" to "authenticated";

grant update on table "public"."project_metadata" to "authenticated";

grant delete on table "public"."project_metadata" to "service_role";

grant insert on table "public"."project_metadata" to "service_role";

grant references on table "public"."project_metadata" to "service_role";

grant select on table "public"."project_metadata" to "service_role";

grant trigger on table "public"."project_metadata" to "service_role";

grant truncate on table "public"."project_metadata" to "service_role";

grant update on table "public"."project_metadata" to "service_role";

create policy "Service role can manage agent logs"
on "public"."agent_logs"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete agent logs"
on "public"."agent_logs"
as permissive
for delete
to public
using (((auth.role() = 'service_role'::text) OR false));


create policy "Users can insert agent logs"
on "public"."agent_logs"
as permissive
for insert
to public
with check (((auth.role() = 'service_role'::text) OR false));


create policy "Users can update agent logs"
on "public"."agent_logs"
as permissive
for update
to public
using (((auth.role() = 'service_role'::text) OR false));


create policy "Users can view agent logs in their projects"
on "public"."agent_logs"
as permissive
for select
to public
using (((auth.role() = 'service_role'::text) OR false));


create policy "Service role can manage chat messages"
on "public"."chat_messages"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete messages from own sessions"
on "public"."chat_messages"
as permissive
for delete
to public
using ((EXISTS ( SELECT 1
   FROM chat_sessions
  WHERE ((chat_sessions.id = chat_messages.session_id) AND (chat_sessions.user_id = auth.uid())))));


create policy "Users can insert messages to own sessions"
on "public"."chat_messages"
as permissive
for insert
to public
with check ((EXISTS ( SELECT 1
   FROM chat_sessions
  WHERE ((chat_sessions.id = chat_messages.session_id) AND (chat_sessions.user_id = auth.uid())))));


create policy "Users can update messages from own sessions"
on "public"."chat_messages"
as permissive
for update
to public
using ((EXISTS ( SELECT 1
   FROM chat_sessions
  WHERE ((chat_sessions.id = chat_messages.session_id) AND (chat_sessions.user_id = auth.uid())))));


create policy "Users can view messages from own sessions"
on "public"."chat_messages"
as permissive
for select
to public
using ((EXISTS ( SELECT 1
   FROM chat_sessions
  WHERE ((chat_sessions.id = chat_messages.session_id) AND (chat_sessions.user_id = auth.uid())))));


create policy "Service role can manage chat sessions"
on "public"."chat_sessions"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete own chat sessions"
on "public"."chat_sessions"
as permissive
for delete
to public
using ((auth.uid() = user_id));


create policy "Users can insert own chat sessions"
on "public"."chat_sessions"
as permissive
for insert
to public
with check ((auth.uid() = user_id));


create policy "Users can update own chat sessions"
on "public"."chat_sessions"
as permissive
for update
to public
using ((auth.uid() = user_id));


create policy "Users can view own chat sessions"
on "public"."chat_sessions"
as permissive
for select
to public
using ((auth.uid() = user_id));


create policy "Service role can manage document chunks"
on "public"."document_chunks"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete chunks in their projects"
on "public"."document_chunks"
as permissive
for delete
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can insert chunks in their projects"
on "public"."document_chunks"
as permissive
for insert
to public
with check ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can update chunks in their projects"
on "public"."document_chunks"
as permissive
for update
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can view chunks in their projects"
on "public"."document_chunks"
as permissive
for select
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Service role can manage document tags"
on "public"."document_tags"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete document tags in their projects"
on "public"."document_tags"
as permissive
for delete
to public
using ((document_id IN ( SELECT d.id
   FROM (documents d
     JOIN projects p ON ((d.project_id = p.id)))
  WHERE (p.created_by = auth.uid()))));


create policy "Users can insert document tags in their projects"
on "public"."document_tags"
as permissive
for insert
to public
with check ((document_id IN ( SELECT d.id
   FROM (documents d
     JOIN projects p ON ((d.project_id = p.id)))
  WHERE (p.created_by = auth.uid()))));


create policy "Users can update document tags in their projects"
on "public"."document_tags"
as permissive
for update
to public
using ((document_id IN ( SELECT d.id
   FROM (documents d
     JOIN projects p ON ((d.project_id = p.id)))
  WHERE (p.created_by = auth.uid()))));


create policy "Users can view document tags in their projects"
on "public"."document_tags"
as permissive
for select
to public
using ((document_id IN ( SELECT d.id
   FROM (documents d
     JOIN projects p ON ((d.project_id = p.id)))
  WHERE (p.created_by = auth.uid()))));


create policy "Service role can manage documents"
on "public"."documents"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete documents in their projects"
on "public"."documents"
as permissive
for delete
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can insert documents in their projects"
on "public"."documents"
as permissive
for insert
to public
with check ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can update documents in their projects"
on "public"."documents"
as permissive
for update
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can view documents in their projects"
on "public"."documents"
as permissive
for select
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Service can delete drive file watches"
on "public"."drive_file_watches"
as permissive
for delete
to public
using (true);


create policy "Service can insert drive file watches"
on "public"."drive_file_watches"
as permissive
for insert
to public
with check (true);


create policy "Service can update drive file watches"
on "public"."drive_file_watches"
as permissive
for update
to public
using (true);


create policy "Users can view own drive file watches"
on "public"."drive_file_watches"
as permissive
for select
to public
using ((document_id IN ( SELECT d.id
   FROM (documents d
     JOIN projects p ON ((d.project_id = p.id)))
  WHERE (p.created_by = auth.uid()))));


create policy "Service can insert drive webhook logs"
on "public"."drive_webhook_logs"
as permissive
for insert
to public
with check (true);


create policy "Service can update drive webhook logs"
on "public"."drive_webhook_logs"
as permissive
for update
to public
using (true);


create policy "Users can view own drive webhook logs"
on "public"."drive_webhook_logs"
as permissive
for select
to public
using ((document_id IN ( SELECT d.id
   FROM (documents d
     JOIN projects p ON ((d.project_id = p.id)))
  WHERE (p.created_by = auth.uid()))));


create policy "Service can insert email processing logs"
on "public"."email_processing_logs"
as permissive
for insert
to public
with check (true);


create policy "Service can update email processing logs"
on "public"."email_processing_logs"
as permissive
for update
to public
using (true);


create policy "Users can view own email processing logs"
on "public"."email_processing_logs"
as permissive
for select
to public
using ((auth.uid() = user_id));


create policy "Service role can manage knowledge spaces"
on "public"."knowledge_spaces"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete knowledge spaces in their projects"
on "public"."knowledge_spaces"
as permissive
for delete
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can insert knowledge spaces in their projects"
on "public"."knowledge_spaces"
as permissive
for insert
to public
with check ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can update knowledge spaces in their projects"
on "public"."knowledge_spaces"
as permissive
for update
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can view knowledge spaces in their projects"
on "public"."knowledge_spaces"
as permissive
for select
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Service role can manage project metadata"
on "public"."project_metadata"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete project metadata in their projects"
on "public"."project_metadata"
as permissive
for delete
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can insert project metadata in their projects"
on "public"."project_metadata"
as permissive
for insert
to public
with check ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can update project metadata in their projects"
on "public"."project_metadata"
as permissive
for update
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can view project metadata in their projects"
on "public"."project_metadata"
as permissive
for select
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can delete own projects"
on "public"."projects"
as permissive
for delete
to public
using ((auth.uid() = created_by));


create policy "Users can insert own projects"
on "public"."projects"
as permissive
for insert
to public
with check ((auth.uid() = created_by));


create policy "Users can update own projects"
on "public"."projects"
as permissive
for update
to public
using ((auth.uid() = created_by));


create policy "Users can view own projects"
on "public"."projects"
as permissive
for select
to public
using ((auth.uid() = created_by));


create policy "Service role can manage receipts"
on "public"."receipts"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete receipts in their projects"
on "public"."receipts"
as permissive
for delete
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can insert receipts in their projects"
on "public"."receipts"
as permissive
for insert
to public
with check ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can update receipts in their projects"
on "public"."receipts"
as permissive
for update
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can view receipts in their projects"
on "public"."receipts"
as permissive
for select
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Service role can manage subscriptions"
on "public"."subscriptions"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete own subscriptions"
on "public"."subscriptions"
as permissive
for delete
to public
using ((auth.uid() = user_id));


create policy "Users can insert own subscriptions"
on "public"."subscriptions"
as permissive
for insert
to public
with check ((auth.uid() = user_id));


create policy "Users can update own subscriptions"
on "public"."subscriptions"
as permissive
for update
to public
using ((auth.uid() = user_id));


create policy "Users can view own subscriptions"
on "public"."subscriptions"
as permissive
for select
to public
using ((auth.uid() = user_id));


create policy "Service role can manage summaries"
on "public"."summaries"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete summaries in their projects"
on "public"."summaries"
as permissive
for delete
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can insert summaries in their projects"
on "public"."summaries"
as permissive
for insert
to public
with check ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can update summaries in their projects"
on "public"."summaries"
as permissive
for update
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Users can view summaries in their projects"
on "public"."summaries"
as permissive
for select
to public
using ((project_id IN ( SELECT projects.id
   FROM projects
  WHERE (projects.created_by = auth.uid()))));


create policy "Service role can manage sync tracking"
on "public"."sync_tracking"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete own sync tracking"
on "public"."sync_tracking"
as permissive
for delete
to public
using ((auth.uid() = user_id));


create policy "Users can insert own sync tracking"
on "public"."sync_tracking"
as permissive
for insert
to public
with check ((auth.uid() = user_id));


create policy "Users can update own sync tracking"
on "public"."sync_tracking"
as permissive
for update
to public
using ((auth.uid() = user_id));


create policy "Users can view own sync tracking"
on "public"."sync_tracking"
as permissive
for select
to public
using ((auth.uid() = user_id));


create policy "Service role can manage tags"
on "public"."tags"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can delete own tags"
on "public"."tags"
as permissive
for delete
to public
using ((auth.uid() = created_by));


create policy "Users can insert own tags"
on "public"."tags"
as permissive
for insert
to public
with check ((auth.uid() = created_by));


create policy "Users can update own tags"
on "public"."tags"
as permissive
for update
to public
using ((auth.uid() = created_by));


create policy "Users can view own tags"
on "public"."tags"
as permissive
for select
to public
using ((auth.uid() = created_by));


create policy "Service role can manage users"
on "public"."users"
as permissive
for all
to public
using ((auth.role() = 'service_role'::text));


create policy "Users can update own user record"
on "public"."users"
as permissive
for update
to public
using ((auth.uid() = id));


create policy "Users can view own user record"
on "public"."users"
as permissive
for select
to public
using ((auth.uid() = id));


CREATE TRIGGER trg_update_chat_messages_activity BEFORE INSERT OR UPDATE ON public.chat_messages FOR EACH ROW EXECUTE FUNCTION update_chat_messages_activity();

CREATE TRIGGER trg_update_chat_sessions_activity BEFORE UPDATE ON public.chat_sessions FOR EACH ROW EXECUTE FUNCTION update_chat_sessions_activity();

CREATE TRIGGER trg_update_drive_file_watches_updated_at BEFORE UPDATE ON public.drive_file_watches FOR EACH ROW EXECUTE FUNCTION update_drive_file_watches_updated_at();

CREATE TRIGGER trg_update_next_poll_time BEFORE UPDATE ON public.meetings FOR EACH ROW WHEN ((old.bot_status IS DISTINCT FROM new.bot_status)) EXECUTE FUNCTION update_next_poll_time();

CREATE TRIGGER trg_update_subscriptions_updated_at BEFORE UPDATE ON public.subscriptions FOR EACH ROW EXECUTE FUNCTION update_subscriptions_updated_at();

CREATE TRIGGER trg_update_username_set_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION update_username_set_at();


