-- Migration: Extend User Preferences for Dual-Mode Executive Dashboard
-- Version: 2025-09-08-v2
-- Purpose: Add dual-mode fields to existing user_preferences table (not create duplicate)

-- Add new columns to existing user_preferences table for dual-mode support
ALTER TABLE user_preferences ADD COLUMN IF NOT EXISTS
    preferred_period INT DEFAULT 3 COMMENT 'Preferred period length in weeks for executive dashboard',
    preferred_mode VARCHAR(20) DEFAULT 'average' COMMENT 'Preferred view mode: average or period',
    last_custom_period INT NULL COMMENT 'Last custom period entered by user';

-- Update existing user preferences with default dual-mode values
UPDATE user_preferences 
SET 
    preferred_period = 3,
    preferred_mode = 'average',
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = 'default_user';