import psycopg2

print("Granting permissions on adk_sessions.sessions table to sre_user...")

try:
    # Connect as postgres user to grant permissions
    conn = psycopg2.connect(
        host="34.9.74.83",
        port=5432,
        database="adk_sessions",
        user="postgres",
        password="Azure@123456"
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Grant all necessary permissions
    print("\n1. Granting SELECT, INSERT, UPDATE, DELETE on sessions table...")
    cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE sessions TO sre_user;")
    print("   ✓ Granted")
    
    # Grant usage on sequences if they exist
    print("\n2. Checking for sequences...")
    cur.execute("""
        SELECT sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_schema = 'public' 
        AND sequence_name LIKE 'sessions%';
    """)
    sequences = cur.fetchall()
    if sequences:
        for seq in sequences:
            print(f"   Granting USAGE on {seq[0]}...")
            cur.execute(f"GRANT USAGE, SELECT ON SEQUENCE {seq[0]} TO sre_user;")
        print("   ✓ Sequence permissions granted")
    else:
        print("   No sequences found")
    
    # Verify permissions
    print("\n3. Verifying permissions...")
    cur.execute("""
        SELECT privilege_type 
        FROM information_schema.role_table_grants 
        WHERE table_name = 'sessions' 
        AND grantee = 'sre_user'
        ORDER BY privilege_type;
    """)
    privileges = cur.fetchall()
    if privileges:
        print(f"   ✓ sre_user has privileges: {[p[0] for p in privileges]}")
    else:
        print("   ✗ No privileges found!")
    
    cur.close()
    conn.close()
    print("\n✓ All permissions granted successfully!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nNote: If connection fails, ensure postgres user password is correct")
    print("      or run this SQL manually as a superuser:")
    print("\n      GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE sessions TO sre_user;")
