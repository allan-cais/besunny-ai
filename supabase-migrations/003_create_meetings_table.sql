-- Create meetings table for storing calendar events and bot associations
CREATE TABLE IF NOT EXISTS meetings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Who owns this meeting
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- What project it's attached to
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

  -- Google Calendar
  google_calendar_event_id TEXT,

  -- Meeting info
  title TEXT NOT NULL,
  description TEXT,
  meeting_url TEXT,

  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE NOT NULL,

  -- Bot integration (optional)
  attendee_bot_id UUID REFERENCES bots(id),
  bot_name TEXT DEFAULT 'Sunny AI Assistant',
  bot_chat_message TEXT DEFAULT 'Hi, I''m here to transcribe this meeting!',

  -- Transcript storage
  transcript TEXT,
  transcript_url TEXT,

  -- Status lifecycle
  status TEXT DEFAULT 'pending' CHECK (
    status IN (
      'pending',
      'bot_scheduled',
      'bot_joined',
      'transcribing',
      'completed',
      'failed'
    )
  ),

  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own meetings"
  ON meetings FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own meetings"
  ON meetings FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own meetings"
  ON meetings FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own meetings"
  ON meetings FOR DELETE
  USING (auth.uid() = user_id);

CREATE OR REPLACE FUNCTION update_meetings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_meetings_updated_at
BEFORE UPDATE ON meetings
FOR EACH ROW
EXECUTE FUNCTION update_meetings_updated_at();

CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id);
CREATE INDEX IF NOT EXISTS idx_meetings_project_id ON meetings(project_id);
CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_google_event_id ON meetings(google_calendar_event_id);

-- Create bots table for managing transcription bots
CREATE TABLE IF NOT EXISTS bots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Who created/owns this bot
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

  name TEXT NOT NULL,
  description TEXT,
  avatar_url TEXT,

  provider TEXT NOT NULL,         -- 'attendee', 'otter', etc.
  provider_bot_id TEXT,           -- External identifier
  settings JSONB,                 -- Any configuration JSON

  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

ALTER TABLE bots ENABLE ROW LEVEL SECURITY;

-- Users can read their own bots
CREATE POLICY "Users can view own bots"
  ON bots FOR SELECT
  USING (user_id = auth.uid());

-- Users can insert their own bots
CREATE POLICY "Users can insert own bots"
  ON bots FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- Users can update their own bots
CREATE POLICY "Users can update own bots"
  ON bots FOR UPDATE
  USING (user_id = auth.uid());

-- Users can delete their own bots
CREATE POLICY "Users can delete own bots"
  ON bots FOR DELETE
  USING (user_id = auth.uid());

CREATE OR REPLACE FUNCTION update_bots_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_bots_updated_at
BEFORE UPDATE ON bots
FOR EACH ROW
EXECUTE FUNCTION update_bots_updated_at();

CREATE INDEX IF NOT EXISTS idx_bots_user_id ON bots(user_id);
CREATE INDEX IF NOT EXISTS idx_bots_provider ON bots(provider);
CREATE INDEX IF NOT EXISTS idx_bots_is_active ON bots(is_active); 