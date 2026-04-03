-- Migration 007: Auth & Medical Reports Pipeline

-- 1. Add role column to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS role TEXT CHECK (role IN ('patient', 'doctor')) DEFAULT 'patient';

-- 2. Create doctor_patient_mapping
CREATE TABLE IF NOT EXISTS doctor_patient_mapping (
    doctor_id UUID REFERENCES users(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (doctor_id, patient_id)
);

-- 3. Create structured_reports
CREATE TABLE IF NOT EXISTS structured_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    report_id UUID, -- Not strictly a foreign key to medical_reports to avoid circular dependencies if it's external, but we'll leave it as UUID.
    file_url TEXT NOT NULL,
    extracted_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctor_patient_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE structured_reports ENABLE ROW LEVEL SECURITY;

-- Note: In a production system, all tables linked to a user would be scoped here,
-- but mapping just the required ones according to the person 1 guidelines.

-- 5. RLS Policies

-- For users table:
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON users FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Doctors can view mapped patients profiles"
    ON users FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM doctor_patient_mapping dpm
            WHERE dpm.doctor_id = auth.uid() AND dpm.patient_id = users.id
        )
    );

-- For doctor_patient_mapping:
CREATE POLICY "Doctors can view their patients"
    ON doctor_patient_mapping FOR SELECT
    USING (doctor_id = auth.uid());
    
CREATE POLICY "Patients can view their doctors"
    ON doctor_patient_mapping FOR SELECT
    USING (patient_id = auth.uid());

-- For structured_reports:
CREATE POLICY "Users can view their own structured_reports"
    ON structured_reports FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Doctors can view structured_reports of their mapped patients"
    ON structured_reports FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM doctor_patient_mapping dpm
            WHERE dpm.doctor_id = auth.uid() AND dpm.patient_id = structured_reports.user_id
        )
    );

-- The backend API (fastapi) will insert using a Service Role Key, 
-- or we can provide an INSERT check for standard clients:
CREATE POLICY "Users can insert their own structured_reports"
    ON structured_reports FOR INSERT
    WITH CHECK (auth.uid() = user_id);
