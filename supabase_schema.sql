-- ================================================
--  GYM MANAGEMENT - SUPABASE SCHEMA
-- ================================================

-- ADMINS
CREATE TABLE admins (
    id         BIGSERIAL PRIMARY KEY,
    username   VARCHAR(50) UNIQUE NOT NULL,
    email      VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name  VARCHAR(100) NOT NULL,
    phone      VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- GYM SETTINGS
CREATE TABLE gym_settings (
    id          BIGSERIAL PRIMARY KEY,
    gym_name    VARCHAR(100) DEFAULT 'PowerFit Gym',
    gym_logo    VARCHAR(255),
    gym_address TEXT,
    gym_phone   VARCHAR(20),
    gym_email   VARCHAR(100),
    gym_website VARCHAR(100),
    theme       VARCHAR(20) DEFAULT 'dark',
    currency    VARCHAR(10) DEFAULT '₹',
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- TRAINERS
CREATE TABLE trainers (
    id               BIGSERIAL PRIMARY KEY,
    full_name        VARCHAR(100) NOT NULL,
    email            VARCHAR(100) UNIQUE,
    phone            VARCHAR(20),
    specialization   VARCHAR(100),
    experience_years INT DEFAULT 0,
    photo            VARCHAR(255),
    bio              TEXT,
    salary           DECIMAL(10,2) DEFAULT 0,
    status           VARCHAR(20) DEFAULT 'active',
    join_date        DATE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- MEMBERSHIP PLANS
CREATE TABLE membership_plans (
    id               BIGSERIAL PRIMARY KEY,
    plan_name        VARCHAR(100) NOT NULL,
    duration_months  INT NOT NULL,
    price            DECIMAL(10,2) NOT NULL,
    description      TEXT,
    features         TEXT,
    status           VARCHAR(20) DEFAULT 'active',
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- MEMBERS
CREATE TABLE members (
    id                 BIGSERIAL PRIMARY KEY,
    member_id          VARCHAR(20) UNIQUE NOT NULL,
    full_name          VARCHAR(100) NOT NULL,
    phone              VARCHAR(20) NOT NULL,
    email              VARCHAR(100),
    password_hash      VARCHAR(255),
    address            TEXT,
    date_of_birth      DATE,
    gender             VARCHAR(10),
    photo              VARCHAR(255),
    membership_plan_id BIGINT REFERENCES membership_plans(id) ON DELETE SET NULL,
    trainer_id         BIGINT REFERENCES trainers(id) ON DELETE SET NULL,
    join_date          DATE NOT NULL,
    expiry_date        DATE NOT NULL,
    status             VARCHAR(20) DEFAULT 'active',
    blood_group        VARCHAR(10),
    emergency_contact  VARCHAR(20),
    notes              TEXT,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- PAYMENTS
CREATE TABLE payments (
    id              BIGSERIAL PRIMARY KEY,
    invoice_number  VARCHAR(30) UNIQUE,
    member_id       BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    plan_id         BIGINT REFERENCES membership_plans(id) ON DELETE SET NULL,
    amount          DECIMAL(10,2) NOT NULL,
    payment_mode    VARCHAR(20) NOT NULL,
    payment_status  VARCHAR(20) DEFAULT 'completed',
    payment_date    DATE NOT NULL,
    remarks         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ATTENDANCE
CREATE TABLE attendance (
    id              BIGSERIAL PRIMARY KEY,
    member_id       BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in_time   TIME,
    check_out_time  TIME,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(member_id, attendance_date)
);

-- COMPLAINTS
CREATE TABLE complaints (
    id          BIGSERIAL PRIMARY KEY,
    member_id   BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    subject     VARCHAR(200) NOT NULL,
    message     TEXT NOT NULL,
    category    VARCHAR(50),
    status      VARCHAR(20) DEFAULT 'open',
    admin_reply TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- MESSAGES
CREATE TABLE messages (
    id         BIGSERIAL PRIMARY KEY,
    member_id  BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    to_type    VARCHAR(20) DEFAULT 'gym',
    trainer_id BIGINT REFERENCES trainers(id) ON DELETE SET NULL,
    subject    VARCHAR(200) NOT NULL,
    message    TEXT NOT NULL,
    status     VARCHAR(20) DEFAULT 'sent',
    reply      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ANNOUNCEMENTS
CREATE TABLE announcements (
    id         BIGSERIAL PRIMARY KEY,
    title      VARCHAR(200) NOT NULL,
    message    TEXT NOT NULL,
    priority   VARCHAR(20) DEFAULT 'info',
    created_by BIGINT NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ANNOUNCEMENT READS
CREATE TABLE announcement_reads (
    id              BIGSERIAL PRIMARY KEY,
    announcement_id BIGINT NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,
    member_id       BIGINT NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    read_at         TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(announcement_id, member_id)
);

-- ================================================
-- SEED DATA
-- ================================================

-- Default admin (password: admin123)
INSERT INTO admins (username, email, password_hash, full_name, phone) VALUES
('admin', 'admin@powerfit.com', 'scrypt:32768:8:1$9gQeqX1U7wFfTyIW$ec62d56035c5dd587529e77329229348d83d46e12d4f50b8218ae23d8c0f36951edecda83a73fb21a34bb94ee9183363e287d965a73e344c65a033fc52545a9e', 'Super Admin', '+91-9999999999')
ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- Default gym settings
INSERT INTO gym_settings (gym_name, gym_address, gym_phone, gym_email, gym_website) VALUES
('PowerFit Gym', '123 Fitness Street, Mumbai', '+91-9000000000', 'info@powerfit.com', 'www.powerfit.com');

-- Membership plans
INSERT INTO membership_plans (plan_name, duration_months, price, description, features) VALUES
('Monthly Basic',      1,  999.00,  'Starter plan',              'Gym Access,Locker Room,Basic Equipment'),
('Quarterly Standard', 3,  2499.00, 'Best value',                'Gym Access,Locker Room,All Equipment,1 PT Session'),
('Half Yearly Pro',    6,  4499.00, 'Comprehensive package',     'Gym Access,All Equipment,4 PT Sessions,Diet Plan'),
('Annual Elite',       12, 7999.00, 'Ultimate fitness experience','Unlimited Access,All Equipment,12 PT Sessions,Diet Plan,Sauna');

-- Trainers
INSERT INTO trainers (full_name, email, phone, specialization, experience_years, salary, join_date) VALUES
('Arjun Sharma', 'arjun@powerfit.com', '+91-9111111111', 'Strength & Conditioning', 8, 35000, '2020-01-15'),
('Priya Patel',  'priya@powerfit.com', '+91-9222222222', 'Yoga & Flexibility',       6, 30000, '2021-03-10'),
('Vikram Singh', 'vikram@powerfit.com','+91-9333333333', 'Cardio & Weight Loss',    10, 40000, '2019-06-20');
