

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."get_user_by_google_id"("google_user_id" "text") RETURNS TABLE("user_id" "uuid", "email" "text", "name" "text", "picture" "text")
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
  RETURN QUERY
  SELECT 
    gc.user_id,
    gc.google_email,
    gc.google_name,
    gc.google_picture
  FROM google_credentials gc
  WHERE gc.google_user_id = get_user_by_google_id.google_user_id
    AND gc.login_provider = TRUE;
END;
$$;


ALTER FUNCTION "public"."get_user_by_google_id"("google_user_id" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_google_oauth_login"("google_user_id" "text", "google_email" "text", "google_name" "text", "google_picture" "text", "access_token" "text", "refresh_token" "text", "token_type" "text", "expires_at" timestamp with time zone, "scope" "text") RETURNS "uuid"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  user_id UUID;
  existing_user_id UUID;
BEGIN
  -- Check if a user already exists with this Google user ID
  SELECT gc.user_id INTO existing_user_id
  FROM google_credentials gc
  WHERE gc.google_user_id = handle_google_oauth_login.google_user_id
    AND gc.login_provider = TRUE;
  
  IF existing_user_id IS NOT NULL THEN
    -- Update existing credentials
    UPDATE google_credentials
    SET 
      access_token = handle_google_oauth_login.access_token,
      refresh_token = handle_google_oauth_login.refresh_token,
      token_type = handle_google_oauth_login.token_type,
      expires_at = handle_google_oauth_login.expires_at,
      scope = handle_google_oauth_login.scope,
      google_email = handle_google_oauth_login.google_email,
      google_name = handle_google_oauth_login.google_name,
      google_picture = handle_google_oauth_login.google_picture,
      updated_at = NOW()
    WHERE user_id = existing_user_id;
    
    RETURN existing_user_id;
  ELSE
    -- Check if a user exists with this email (for linking existing accounts)
    SELECT id INTO existing_user_id
    FROM auth.users
    WHERE email = handle_google_oauth_login.google_email;
    
    IF existing_user_id IS NOT NULL THEN
      -- Link existing user account to Google OAuth
      INSERT INTO google_credentials (
        user_id,
        google_user_id,
        google_email,
        google_name,
        google_picture,
        access_token,
        refresh_token,
        token_type,
        expires_at,
        scope,
        login_provider,
        login_created_at
      ) VALUES (
        existing_user_id,
        handle_google_oauth_login.google_user_id,
        handle_google_oauth_login.google_email,
        handle_google_oauth_login.google_name,
        handle_google_oauth_login.google_picture,
        handle_google_oauth_login.access_token,
        handle_google_oauth_login.refresh_token,
        handle_google_oauth_login.token_type,
        handle_google_oauth_login.expires_at,
        handle_google_oauth_login.scope,
        TRUE,
        NOW()
      );
      
      RETURN existing_user_id;
    ELSE
      -- Create new user account
      INSERT INTO auth.users (
        email,
        email_confirmed_at,
        raw_user_meta_data
      ) VALUES (
        handle_google_oauth_login.google_email,
        NOW(),
        jsonb_build_object(
          'name', handle_google_oauth_login.google_name,
          'picture', handle_google_oauth_login.google_picture,
          'provider', 'google'
        )
      ) RETURNING id INTO user_id;
      
      -- Insert Google credentials
      INSERT INTO google_credentials (
        user_id,
        google_user_id,
        google_email,
        google_name,
        google_picture,
        access_token,
        refresh_token,
        token_type,
        expires_at,
        scope,
        login_provider,
        login_created_at
      ) VALUES (
        user_id,
        handle_google_oauth_login.google_user_id,
        handle_google_oauth_login.google_email,
        handle_google_oauth_login.google_name,
        handle_google_oauth_login.google_picture,
        handle_google_oauth_login.access_token,
        handle_google_oauth_login.refresh_token,
        handle_google_oauth_login.token_type,
        handle_google_oauth_login.expires_at,
        handle_google_oauth_login.scope,
        TRUE,
        NOW()
      );
      
      RETURN user_id;
    END IF;
  END IF;
END;
$$;


ALTER FUNCTION "public"."handle_google_oauth_login"("google_user_id" "text", "google_email" "text", "google_name" "text", "google_picture" "text", "access_token" "text", "refresh_token" "text", "token_type" "text", "expires_at" timestamp with time zone, "scope" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_new_user"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
begin
  insert into public.users (id, email, name, role, created_at)
  values (
    new.id, 
    new.email, 
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    'user', -- default role
    new.created_at
  );
  return new;
end;
$$;


ALTER FUNCTION "public"."handle_new_user"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_bots_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_bots_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_calendar_webhooks_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_calendar_webhooks_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_meetings_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_meetings_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_timestamp"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
   NEW.updated_at = now();
   RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_timestamp"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."agent_logs" (
    "id" "uuid" NOT NULL,
    "agent_name" "text",
    "input_id" "text",
    "input_type" "text",
    "output" "jsonb",
    "confidence" numeric,
    "notes" "text",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."agent_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."bots" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "name" "text" NOT NULL,
    "description" "text",
    "avatar_url" "text",
    "provider" "text" NOT NULL,
    "provider_bot_id" "text",
    "settings" "jsonb",
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."bots" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."calendar_sync_logs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "sync_type" "text" NOT NULL,
    "status" "text" NOT NULL,
    "events_processed" integer DEFAULT 0,
    "meetings_created" integer DEFAULT 0,
    "meetings_updated" integer DEFAULT 0,
    "meetings_deleted" integer DEFAULT 0,
    "error_message" "text",
    "sync_range_start" timestamp with time zone,
    "sync_range_end" timestamp with time zone,
    "duration_ms" integer,
    "created_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "calendar_sync_logs_status_check" CHECK (("status" = ANY (ARRAY['started'::"text", 'completed'::"text", 'failed'::"text"]))),
    CONSTRAINT "calendar_sync_logs_sync_type_check" CHECK (("sync_type" = ANY (ARRAY['initial'::"text", 'incremental'::"text", 'webhook'::"text", 'manual'::"text"])))
);


ALTER TABLE "public"."calendar_sync_logs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."calendar_webhooks" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "google_calendar_id" "text" DEFAULT 'primary'::"text" NOT NULL,
    "webhook_id" "text",
    "resource_id" "text",
    "expiration_time" timestamp with time zone,
    "sync_token" "text",
    "last_sync_at" timestamp with time zone DEFAULT "now"(),
    "is_active" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."calendar_webhooks" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."chat_messages" (
    "id" "uuid" NOT NULL,
    "session_id" "uuid",
    "role" "text",
    "message" "text",
    "used_chunks" "text"[],
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."chat_messages" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."chat_sessions" (
    "id" "uuid" NOT NULL,
    "user_id" "uuid",
    "project_id" "uuid",
    "started_at" timestamp without time zone DEFAULT "now"(),
    "ended_at" timestamp without time zone,
    "name" character varying(255)
);


ALTER TABLE "public"."chat_sessions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."document_chunks" (
    "id" "uuid" NOT NULL,
    "document_id" "uuid",
    "project_id" "uuid",
    "chunk_index" integer,
    "text" "text",
    "embedding_id" "text",
    "metadata" "jsonb",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."document_chunks" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."document_tags" (
    "id" "uuid" NOT NULL,
    "document_id" "uuid",
    "tag_id" "uuid",
    "applied_by" "uuid",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."document_tags" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."documents" (
    "id" "uuid" NOT NULL,
    "project_id" "uuid",
    "knowledge_space_id" "uuid",
    "source" "text",
    "source_id" "text",
    "title" "text",
    "summary" "text",
    "author" "text",
    "received_at" timestamp without time zone,
    "file_url" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "created_by" "uuid"
);


ALTER TABLE "public"."documents" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."google_credentials" (
    "user_id" "uuid" NOT NULL,
    "access_token" "text",
    "refresh_token" "text",
    "token_type" "text",
    "expires_at" timestamp without time zone,
    "scope" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "google_email" "text",
    "login_provider" boolean DEFAULT false,
    "google_user_id" "text",
    "google_name" "text",
    "google_picture" "text",
    "login_created_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."google_credentials" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."knowledge_spaces" (
    "id" "uuid" NOT NULL,
    "project_id" "uuid",
    "name" "text" NOT NULL,
    "description" "text",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."knowledge_spaces" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."meetings" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "project_id" "uuid",
    "google_calendar_event_id" "text",
    "title" "text" NOT NULL,
    "description" "text",
    "meeting_url" "text",
    "start_time" timestamp with time zone NOT NULL,
    "end_time" timestamp with time zone NOT NULL,
    "attendee_bot_id" "uuid",
    "bot_name" "text" DEFAULT 'Kirit Notetaker'::"text",
    "bot_chat_message" "text" DEFAULT 'Hi, I''m here to transcribe this meeting!'::"text",
    "transcript" "text",
    "transcript_url" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "event_status" "text" DEFAULT 'needsAction'::"text",
    "bot_status" "text" DEFAULT 'pending'::"text",
    CONSTRAINT "meetings_bot_status_check" CHECK (("bot_status" = ANY (ARRAY['pending'::"text", 'bot_scheduled'::"text", 'bot_joined'::"text", 'transcribing'::"text", 'completed'::"text", 'failed'::"text"]))),
    CONSTRAINT "meetings_event_status_check" CHECK (("event_status" = ANY (ARRAY['accepted'::"text", 'declined'::"text", 'tentative'::"text", 'needsAction'::"text"])))
);


ALTER TABLE "public"."meetings" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."projects" (
    "id" "uuid" NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "status" "text",
    "created_by" "uuid",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."projects" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."receipts" (
    "id" "uuid" NOT NULL,
    "project_id" "uuid",
    "vendor" "text",
    "amount" numeric(12,2),
    "date" "date",
    "category" "text",
    "receipt_image_url" "text",
    "document_id" "uuid",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."receipts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."subscriptions" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "tier" "text" DEFAULT 'free'::"text" NOT NULL,
    "sync_days_limit" integer DEFAULT 7 NOT NULL,
    "status" "text" DEFAULT 'active'::"text" NOT NULL,
    "payment_provider" "text",
    "external_subscription_id" "text",
    "external_customer_id" "text",
    "payment_method_id" "text",
    "current_period_start" timestamp without time zone,
    "current_period_end" timestamp without time zone,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "updated_at" timestamp without time zone DEFAULT "now"(),
    CONSTRAINT "subscriptions_status_check" CHECK (("status" = ANY (ARRAY['active'::"text", 'cancelled'::"text", 'expired'::"text"]))),
    CONSTRAINT "subscriptions_tier_check" CHECK (("tier" = ANY (ARRAY['free'::"text", 'pro'::"text", 'enterprise'::"text"])))
);


ALTER TABLE "public"."subscriptions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."summaries" (
    "id" "uuid" NOT NULL,
    "project_id" "uuid",
    "date" "date",
    "summary" "text",
    "alerts" "jsonb",
    "references" "text"[],
    "created_by" "uuid",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."summaries" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."sync_tracking" (
    "user_id" "uuid" NOT NULL,
    "last_sync_timestamp" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"()
);


ALTER TABLE "public"."sync_tracking" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."tags" (
    "id" "uuid" NOT NULL,
    "name" "text",
    "type" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "created_by" "uuid"
);


ALTER TABLE "public"."tags" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."user_api_keys" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "service" "text" NOT NULL,
    "api_key" "text" NOT NULL,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "updated_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."user_api_keys" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" "uuid" NOT NULL,
    "email" "text" NOT NULL,
    "name" "text",
    "role" "text",
    "created_at" timestamp without time zone DEFAULT "now"()
);


ALTER TABLE "public"."users" OWNER TO "postgres";


ALTER TABLE ONLY "public"."agent_logs"
    ADD CONSTRAINT "agent_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."bots"
    ADD CONSTRAINT "bots_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."calendar_sync_logs"
    ADD CONSTRAINT "calendar_sync_logs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."calendar_webhooks"
    ADD CONSTRAINT "calendar_webhooks_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."calendar_webhooks"
    ADD CONSTRAINT "calendar_webhooks_user_id_google_calendar_id_key" UNIQUE ("user_id", "google_calendar_id");



ALTER TABLE ONLY "public"."calendar_webhooks"
    ADD CONSTRAINT "calendar_webhooks_webhook_id_key" UNIQUE ("webhook_id");



ALTER TABLE ONLY "public"."chat_messages"
    ADD CONSTRAINT "chat_messages_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."chat_sessions"
    ADD CONSTRAINT "chat_sessions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_chunks"
    ADD CONSTRAINT "document_chunks_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."document_tags"
    ADD CONSTRAINT "document_tags_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."google_credentials"
    ADD CONSTRAINT "google_credentials_pkey" PRIMARY KEY ("user_id");



ALTER TABLE ONLY "public"."knowledge_spaces"
    ADD CONSTRAINT "knowledge_spaces_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."meetings"
    ADD CONSTRAINT "meetings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."projects"
    ADD CONSTRAINT "projects_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."receipts"
    ADD CONSTRAINT "receipts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."summaries"
    ADD CONSTRAINT "summaries_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sync_tracking"
    ADD CONSTRAINT "sync_tracking_pkey" PRIMARY KEY ("user_id");



ALTER TABLE ONLY "public"."tags"
    ADD CONSTRAINT "tags_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_api_keys"
    ADD CONSTRAINT "user_api_keys_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_api_keys"
    ADD CONSTRAINT "user_api_keys_user_id_service_key" UNIQUE ("user_id", "service");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."users"
    ADD CONSTRAINT "users_pkey" PRIMARY KEY ("id");



CREATE INDEX "idx_bots_is_active" ON "public"."bots" USING "btree" ("is_active");



CREATE INDEX "idx_bots_provider" ON "public"."bots" USING "btree" ("provider");



CREATE INDEX "idx_bots_user_id" ON "public"."bots" USING "btree" ("user_id");



CREATE INDEX "idx_calendar_sync_logs_created_at" ON "public"."calendar_sync_logs" USING "btree" ("created_at");



CREATE INDEX "idx_calendar_sync_logs_user_id" ON "public"."calendar_sync_logs" USING "btree" ("user_id");



CREATE INDEX "idx_calendar_webhooks_active" ON "public"."calendar_webhooks" USING "btree" ("is_active");



CREATE INDEX "idx_calendar_webhooks_user_id" ON "public"."calendar_webhooks" USING "btree" ("user_id");



CREATE INDEX "idx_google_credentials_google_user_id" ON "public"."google_credentials" USING "btree" ("google_user_id");



CREATE INDEX "idx_google_credentials_login_provider" ON "public"."google_credentials" USING "btree" ("login_provider");



CREATE INDEX "idx_meetings_bot_status" ON "public"."meetings" USING "btree" ("bot_status");



CREATE INDEX "idx_meetings_event_status" ON "public"."meetings" USING "btree" ("event_status");



CREATE INDEX "idx_meetings_google_event_id" ON "public"."meetings" USING "btree" ("google_calendar_event_id");



CREATE INDEX "idx_meetings_project_id" ON "public"."meetings" USING "btree" ("project_id");



CREATE INDEX "idx_meetings_start_time" ON "public"."meetings" USING "btree" ("start_time");



CREATE INDEX "idx_meetings_user_id" ON "public"."meetings" USING "btree" ("user_id");



CREATE INDEX "idx_subscriptions_provider_external" ON "public"."subscriptions" USING "btree" ("payment_provider", "external_subscription_id");



CREATE INDEX "idx_subscriptions_status" ON "public"."subscriptions" USING "btree" ("status");



CREATE INDEX "idx_subscriptions_user_id" ON "public"."subscriptions" USING "btree" ("user_id");



CREATE INDEX "idx_sync_tracking_user_id" ON "public"."sync_tracking" USING "btree" ("user_id");



CREATE OR REPLACE TRIGGER "set_timestamp" BEFORE UPDATE ON "public"."user_api_keys" FOR EACH ROW EXECUTE FUNCTION "public"."update_timestamp"();



CREATE OR REPLACE TRIGGER "trg_update_bots_updated_at" BEFORE UPDATE ON "public"."bots" FOR EACH ROW EXECUTE FUNCTION "public"."update_bots_updated_at"();



CREATE OR REPLACE TRIGGER "trg_update_calendar_webhooks_updated_at" BEFORE UPDATE ON "public"."calendar_webhooks" FOR EACH ROW EXECUTE FUNCTION "public"."update_calendar_webhooks_updated_at"();



CREATE OR REPLACE TRIGGER "trg_update_meetings_updated_at" BEFORE UPDATE ON "public"."meetings" FOR EACH ROW EXECUTE FUNCTION "public"."update_meetings_updated_at"();



ALTER TABLE ONLY "public"."bots"
    ADD CONSTRAINT "bots_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."calendar_sync_logs"
    ADD CONSTRAINT "calendar_sync_logs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."calendar_webhooks"
    ADD CONSTRAINT "calendar_webhooks_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."chat_messages"
    ADD CONSTRAINT "chat_messages_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "public"."chat_sessions"("id");



ALTER TABLE ONLY "public"."chat_sessions"
    ADD CONSTRAINT "chat_sessions_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id");



ALTER TABLE ONLY "public"."chat_sessions"
    ADD CONSTRAINT "chat_sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."document_chunks"
    ADD CONSTRAINT "document_chunks_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id");



ALTER TABLE ONLY "public"."document_chunks"
    ADD CONSTRAINT "document_chunks_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id");



ALTER TABLE ONLY "public"."document_tags"
    ADD CONSTRAINT "document_tags_applied_by_fkey" FOREIGN KEY ("applied_by") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."document_tags"
    ADD CONSTRAINT "document_tags_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id");



ALTER TABLE ONLY "public"."document_tags"
    ADD CONSTRAINT "document_tags_tag_id_fkey" FOREIGN KEY ("tag_id") REFERENCES "public"."tags"("id");



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "documents_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "documents_knowledge_space_id_fkey" FOREIGN KEY ("knowledge_space_id") REFERENCES "public"."knowledge_spaces"("id");



ALTER TABLE ONLY "public"."documents"
    ADD CONSTRAINT "documents_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id");



ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "fk_subscriptions_user_id" FOREIGN KEY ("user_id") REFERENCES "public"."google_credentials"("user_id") ON UPDATE CASCADE ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sync_tracking"
    ADD CONSTRAINT "fk_sync_tracking_user_id" FOREIGN KEY ("user_id") REFERENCES "public"."google_credentials"("user_id") ON UPDATE CASCADE ON DELETE CASCADE;



ALTER TABLE ONLY "public"."google_credentials"
    ADD CONSTRAINT "google_credentials_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."knowledge_spaces"
    ADD CONSTRAINT "knowledge_spaces_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id");



ALTER TABLE ONLY "public"."meetings"
    ADD CONSTRAINT "meetings_attendee_bot_id_fkey" FOREIGN KEY ("attendee_bot_id") REFERENCES "public"."bots"("id");



ALTER TABLE ONLY "public"."meetings"
    ADD CONSTRAINT "meetings_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."meetings"
    ADD CONSTRAINT "meetings_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."projects"
    ADD CONSTRAINT "projects_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."receipts"
    ADD CONSTRAINT "receipts_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "public"."documents"("id");



ALTER TABLE ONLY "public"."receipts"
    ADD CONSTRAINT "receipts_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id");



ALTER TABLE ONLY "public"."subscriptions"
    ADD CONSTRAINT "subscriptions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."summaries"
    ADD CONSTRAINT "summaries_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."summaries"
    ADD CONSTRAINT "summaries_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("id");



ALTER TABLE ONLY "public"."sync_tracking"
    ADD CONSTRAINT "sync_tracking_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."tags"
    ADD CONSTRAINT "tags_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");



ALTER TABLE ONLY "public"."user_api_keys"
    ADD CONSTRAINT "user_api_keys_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."users"("id") ON DELETE CASCADE;



CREATE POLICY "Allow user to delete their api keys" ON "public"."user_api_keys" FOR DELETE USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Allow user to insert their api keys" ON "public"."user_api_keys" FOR INSERT WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "Allow user to read their api keys" ON "public"."user_api_keys" FOR SELECT USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Allow user to update their api keys" ON "public"."user_api_keys" FOR UPDATE USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Authenticated users can select own google credentials" ON "public"."google_credentials" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can delete own bots" ON "public"."bots" FOR DELETE USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can delete own google credentials" ON "public"."google_credentials" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can delete own meetings" ON "public"."meetings" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can delete own webhooks" ON "public"."calendar_webhooks" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert document chunks" ON "public"."document_chunks" FOR INSERT WITH CHECK (("project_id" IN ( SELECT "projects"."id"
   FROM "public"."projects"
  WHERE ("projects"."created_by" = "auth"."uid"()))));



CREATE POLICY "Users can insert documents" ON "public"."documents" FOR INSERT WITH CHECK (("project_id" IN ( SELECT "projects"."id"
   FROM "public"."projects"
  WHERE ("projects"."created_by" = "auth"."uid"()))));



CREATE POLICY "Users can insert messages to their own sessions" ON "public"."chat_messages" FOR INSERT WITH CHECK (("session_id" IN ( SELECT "chat_sessions"."id"
   FROM "public"."chat_sessions"
  WHERE ("chat_sessions"."user_id" = "auth"."uid"()))));



CREATE POLICY "Users can insert own bots" ON "public"."bots" FOR INSERT WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can insert own meetings" ON "public"."meetings" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own sync logs" ON "public"."calendar_sync_logs" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert own webhooks" ON "public"."calendar_webhooks" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert projects" ON "public"."projects" FOR INSERT WITH CHECK (("created_by" = "auth"."uid"()));



CREATE POLICY "Users can insert their own chat sessions" ON "public"."chat_sessions" FOR INSERT WITH CHECK (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can read chunks in their projects" ON "public"."document_chunks" FOR SELECT USING (("project_id" IN ( SELECT "projects"."id"
   FROM "public"."projects"
  WHERE ("projects"."created_by" = "auth"."uid"()))));



CREATE POLICY "Users can read documents in their projects" ON "public"."documents" FOR SELECT USING (("project_id" IN ( SELECT "projects"."id"
   FROM "public"."projects"
  WHERE ("projects"."created_by" = "auth"."uid"()))));



CREATE POLICY "Users can read messages from their own sessions" ON "public"."chat_messages" FOR SELECT USING (("session_id" IN ( SELECT "chat_sessions"."id"
   FROM "public"."chat_sessions"
  WHERE ("chat_sessions"."user_id" = "auth"."uid"()))));



CREATE POLICY "Users can read their own chat sessions" ON "public"."chat_sessions" FOR SELECT USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can read their own projects" ON "public"."projects" FOR SELECT USING (("created_by" = "auth"."uid"()));



CREATE POLICY "Users can update own bots" ON "public"."bots" FOR UPDATE USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can update own meetings" ON "public"."meetings" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can update own webhooks" ON "public"."calendar_webhooks" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own bots" ON "public"."bots" FOR SELECT USING (("user_id" = "auth"."uid"()));



CREATE POLICY "Users can view own google credentials" ON "public"."google_credentials" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own meetings" ON "public"."meetings" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own sync logs" ON "public"."calendar_sync_logs" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own webhooks" ON "public"."calendar_webhooks" FOR SELECT USING (("auth"."uid"() = "user_id"));



ALTER TABLE "public"."bots" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."calendar_sync_logs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."calendar_webhooks" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."google_credentials" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."meetings" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_api_keys" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";






ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."chat_messages";



ALTER PUBLICATION "supabase_realtime" ADD TABLE ONLY "public"."chat_sessions";



GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."get_user_by_google_id"("google_user_id" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_user_by_google_id"("google_user_id" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_user_by_google_id"("google_user_id" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_google_oauth_login"("google_user_id" "text", "google_email" "text", "google_name" "text", "google_picture" "text", "access_token" "text", "refresh_token" "text", "token_type" "text", "expires_at" timestamp with time zone, "scope" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."handle_google_oauth_login"("google_user_id" "text", "google_email" "text", "google_name" "text", "google_picture" "text", "access_token" "text", "refresh_token" "text", "token_type" "text", "expires_at" timestamp with time zone, "scope" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_google_oauth_login"("google_user_id" "text", "google_email" "text", "google_name" "text", "google_picture" "text", "access_token" "text", "refresh_token" "text", "token_type" "text", "expires_at" timestamp with time zone, "scope" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_new_user"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_bots_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_bots_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_bots_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_calendar_webhooks_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_calendar_webhooks_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_calendar_webhooks_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_meetings_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_meetings_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_meetings_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_timestamp"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_timestamp"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_timestamp"() TO "service_role";


















GRANT ALL ON TABLE "public"."agent_logs" TO "anon";
GRANT ALL ON TABLE "public"."agent_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."agent_logs" TO "service_role";



GRANT ALL ON TABLE "public"."bots" TO "anon";
GRANT ALL ON TABLE "public"."bots" TO "authenticated";
GRANT ALL ON TABLE "public"."bots" TO "service_role";



GRANT ALL ON TABLE "public"."calendar_sync_logs" TO "anon";
GRANT ALL ON TABLE "public"."calendar_sync_logs" TO "authenticated";
GRANT ALL ON TABLE "public"."calendar_sync_logs" TO "service_role";



GRANT ALL ON TABLE "public"."calendar_webhooks" TO "anon";
GRANT ALL ON TABLE "public"."calendar_webhooks" TO "authenticated";
GRANT ALL ON TABLE "public"."calendar_webhooks" TO "service_role";



GRANT ALL ON TABLE "public"."chat_messages" TO "anon";
GRANT ALL ON TABLE "public"."chat_messages" TO "authenticated";
GRANT ALL ON TABLE "public"."chat_messages" TO "service_role";



GRANT ALL ON TABLE "public"."chat_sessions" TO "anon";
GRANT ALL ON TABLE "public"."chat_sessions" TO "authenticated";
GRANT ALL ON TABLE "public"."chat_sessions" TO "service_role";



GRANT ALL ON TABLE "public"."document_chunks" TO "anon";
GRANT ALL ON TABLE "public"."document_chunks" TO "authenticated";
GRANT ALL ON TABLE "public"."document_chunks" TO "service_role";



GRANT ALL ON TABLE "public"."document_tags" TO "anon";
GRANT ALL ON TABLE "public"."document_tags" TO "authenticated";
GRANT ALL ON TABLE "public"."document_tags" TO "service_role";



GRANT ALL ON TABLE "public"."documents" TO "anon";
GRANT ALL ON TABLE "public"."documents" TO "authenticated";
GRANT ALL ON TABLE "public"."documents" TO "service_role";



GRANT ALL ON TABLE "public"."google_credentials" TO "anon";
GRANT ALL ON TABLE "public"."google_credentials" TO "authenticated";
GRANT ALL ON TABLE "public"."google_credentials" TO "service_role";



GRANT ALL ON TABLE "public"."knowledge_spaces" TO "anon";
GRANT ALL ON TABLE "public"."knowledge_spaces" TO "authenticated";
GRANT ALL ON TABLE "public"."knowledge_spaces" TO "service_role";



GRANT ALL ON TABLE "public"."meetings" TO "anon";
GRANT ALL ON TABLE "public"."meetings" TO "authenticated";
GRANT ALL ON TABLE "public"."meetings" TO "service_role";



GRANT ALL ON TABLE "public"."projects" TO "anon";
GRANT ALL ON TABLE "public"."projects" TO "authenticated";
GRANT ALL ON TABLE "public"."projects" TO "service_role";



GRANT ALL ON TABLE "public"."receipts" TO "anon";
GRANT ALL ON TABLE "public"."receipts" TO "authenticated";
GRANT ALL ON TABLE "public"."receipts" TO "service_role";



GRANT ALL ON TABLE "public"."subscriptions" TO "anon";
GRANT ALL ON TABLE "public"."subscriptions" TO "authenticated";
GRANT ALL ON TABLE "public"."subscriptions" TO "service_role";



GRANT ALL ON TABLE "public"."summaries" TO "anon";
GRANT ALL ON TABLE "public"."summaries" TO "authenticated";
GRANT ALL ON TABLE "public"."summaries" TO "service_role";



GRANT ALL ON TABLE "public"."sync_tracking" TO "anon";
GRANT ALL ON TABLE "public"."sync_tracking" TO "authenticated";
GRANT ALL ON TABLE "public"."sync_tracking" TO "service_role";



GRANT ALL ON TABLE "public"."tags" TO "anon";
GRANT ALL ON TABLE "public"."tags" TO "authenticated";
GRANT ALL ON TABLE "public"."tags" TO "service_role";



GRANT ALL ON TABLE "public"."user_api_keys" TO "anon";
GRANT ALL ON TABLE "public"."user_api_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."user_api_keys" TO "service_role";



GRANT ALL ON TABLE "public"."users" TO "anon";
GRANT ALL ON TABLE "public"."users" TO "authenticated";
GRANT ALL ON TABLE "public"."users" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






























RESET ALL;
