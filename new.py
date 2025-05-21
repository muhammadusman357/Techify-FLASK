import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect(r'D:\Study\DB\Project\DB Project files\AJAXcart-mine-final\AJAXcart-mine-final\instance\your_database.db')
cursor = conn.cursor()

# Disable foreign key checks (optional, if needed)
#cursor.execute("PRAGMA foreign_keys = OFF;")

# Check if another superadmin already exists
cursor.execute("SELECT admin_id FROM admins WHERE role = 'superadmin'")
existing_superadmin = cursor.fetchone()

if existing_superadmin:
    print("Error: A superadmin already exists. Cannot assign another superadmin.")
else:
    # Update the role to 'superadmin' for the specified username
    cursor.execute("""
        UPDATE admins 
        SET role = 'superadmin'
        WHERE username = 'usmanfarooqui357'
    """)

    # Check if the update was successful
    if cursor.rowcount == 0:
        print("Error: No admin found with the username 'usmanfarooqui357'.")
    else:
        print("The role has been successfully updated to 'superadmin'.")

# Enable foreign key checks again (if previously disabled)
#cursor.execute("PRAGMA foreign_keys = ON;")

# Commit changes
conn.commit()

# Close the connection
conn.close()
