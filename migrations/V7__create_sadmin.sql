INSERT INTO users (
    id, 
    first_name, 
    last_name, 
    email, 
    password, 
    is_super_admin,
    created_ts,
    updated_ts,
    last_login_ts 
) 
VALUES (
    123456,
    'Super',
    'Admin',
    'supervadmin@slt.com',
    '$argon2id$v=19$m=65536,t=3,p=4$j5N+Y9+n1MiUYtj28fev/g$abUF5Fr7sN5Mm3iMTZtwbG5EGQhleR0V5EKr953JC+4',
    TRUE, 
    NOW(), 
    NOW(),
    NOW() 
);