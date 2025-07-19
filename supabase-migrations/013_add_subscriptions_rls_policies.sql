-- Add Row Level Security policies for subscriptions table
-- This migration ensures users can only access their own subscriptions

-- Enable Row Level Security on subscriptions table
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Create comprehensive RLS policies for subscriptions table
CREATE POLICY "Users can view own subscriptions" ON subscriptions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own subscriptions" ON subscriptions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own subscriptions" ON subscriptions
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own subscriptions" ON subscriptions
  FOR DELETE USING (auth.uid() = user_id);

-- Service role policy for backend operations (more restrictive than ALL)
CREATE POLICY "Service role can manage subscriptions" ON subscriptions
  FOR ALL USING (auth.role() = 'service_role');

-- Note: The following indexes already exist in the remote schema:
-- - idx_subscriptions_user_id (for RLS performance)
-- - idx_subscriptions_status (for status filtering)
-- - idx_subscriptions_provider_external (for payment provider lookups)

-- Create index for tier filtering (common query pattern)
CREATE INDEX IF NOT EXISTS idx_subscriptions_tier ON subscriptions(tier);

-- Create index for period date filtering (useful for subscription management)
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_dates ON subscriptions(current_period_start, current_period_end);

-- Create index for external customer lookups (payment processing)
CREATE INDEX IF NOT EXISTS idx_subscriptions_external_customer ON subscriptions(external_customer_id) WHERE external_customer_id IS NOT NULL;

-- Create trigger for automatic updated_at timestamp updates
CREATE OR REPLACE FUNCTION update_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_subscriptions_updated_at
BEFORE UPDATE ON subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_subscriptions_updated_at();

-- Additional optional indexes for specific query patterns
-- Index for date range queries (created_at)
CREATE INDEX IF NOT EXISTS idx_subscriptions_created_at ON subscriptions(created_at);

-- Index for finding expiring subscriptions (active subscriptions ending soon)
CREATE INDEX IF NOT EXISTS idx_subscriptions_expiring ON subscriptions(current_period_end) WHERE status = 'active';

-- Index for payment method lookups
CREATE INDEX IF NOT EXISTS idx_subscriptions_payment_method ON subscriptions(payment_method_id) WHERE payment_method_id IS NOT NULL;

-- Additional constraints for data integrity
-- Ensure one active subscription per user (business rule)
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_one_active_per_user 
ON subscriptions(user_id) WHERE status = 'active';

-- Ensure external subscription IDs are unique per provider
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscriptions_external_unique 
ON subscriptions(payment_provider, external_subscription_id) 
WHERE external_subscription_id IS NOT NULL; 