-- ============================================================
-- create_admin_user.sql
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================================
-- STEP 1: First sign up normally in your app with your desired
--         admin email (this creates the Clerk user).
--         Then find your Clerk User ID from:
--         https://dashboard.clerk.com → Users → click your user
--
-- STEP 2: Replace the values below and run this SQL
-- ============================================================

-- Option A: INSERT a brand-new admin user
INSERT INTO users (
    clerk_user_id,
    email,
    full_name,
    role,
    status,
    created_at,
    updated_at
)
VALUES (
    'user_REPLACE_WITH_YOUR_CLERK_ID',   -- ← paste your Clerk user_xxx ID here
    'admin@sbuniversity.edu',             -- ← your admin email
    'Super Admin',                        -- ← display name
    'admin',
    'active',
    now(),
    now()
)
ON CONFLICT (clerk_user_id) DO UPDATE
    SET role   = 'admin',
        status = 'active';

-- Option B: Promote an EXISTING user to admin (user already signed up)
-- Just replace the email below:
-- UPDATE users
-- SET role = 'admin'
-- WHERE email = 'your-email@example.com';

-- Verify the result:
SELECT id, clerk_user_id, email, full_name, role, status, created_at
FROM users
WHERE role = 'admin';
