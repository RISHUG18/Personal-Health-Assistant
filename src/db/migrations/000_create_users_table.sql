-- Migration 000: Users Table
-- Creates the core users table that will be referenced by other tables.
-- This migration should be applied FIRST before any other migrations.

-- ── 1. Enable uuid-ossp extension (safe no-op if already active) ─────────────

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 2. Create users table ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT        UNIQUE NOT NULL,
    full_name       TEXT        NOT NULL,
    phone           TEXT,
    date_of_birth   DATE,
    gender          TEXT        CHECK (gender IN ('male', 'female', 'other')),

    -- Address information
    address_line1   TEXT,
    address_line2   TEXT,
    city            TEXT,
    state           TEXT,
    postal_code     TEXT,
    country         TEXT        DEFAULT 'India',

    -- Medical information
    blood_group     TEXT        CHECK (blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    height_cm       NUMERIC,
    weight_kg       NUMERIC,

    -- Account metadata
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at   TIMESTAMP WITH TIME ZONE,
    is_active       BOOLEAN     DEFAULT TRUE
);

COMMENT ON TABLE users IS
'Core users table storing user profile information, contact details, and basic medical data.';

COMMENT ON COLUMN users.email IS
'Primary email address for the user. Must be unique.';

COMMENT ON COLUMN users.blood_group IS
'Blood group in standard notation (A+, A-, B+, B-, AB+, AB-, O+, O-).';

COMMENT ON COLUMN users.is_active IS
'Flag to soft-delete users without removing their data.';

-- ── 3. Create indexes for efficient lookups ───────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ── 4. Create updated_at trigger ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
