import sqlite3
from datetime import datetime

# Connect to the SQLite database
conn = sqlite3.connect('D:\\Study\\DB\\Project\\DB Project files\\AJAXcart\\instance\\your_database.db')

cursor = conn.cursor()

# Generate the superadmin user data
superadmin_username = 'usmanfarooqui357'
superadmin_email = 'usmanfarooqui357@gmail.com'
superadmin_password = 'usman'  # Plain text password (not hashed)
superadmin_role = 'superadmin'  # Superadmin role
superadmin_super_admin_id = None  # No parent super admin, as this is a top-level admin
superadmin_created_at = datetime.utcnow()
superadmin_date_of_birth = '1990-01-01'  # Example date
superadmin_first_name = 'Usman'
superadmin_last_name = 'Farooqui'
superadmin_gender = 'Male'
superadmin_contact = '+1234567890'  # Example contact number
superadmin_profile_pic = 'https://example.com/profiles/usman.jpg'  # Example URL for profile picture
superadmin_bio = 'Super Admin - Can manage the entire application.'

# Insert superadmin user into the database
cursor.execute(
    """INSERT INTO admins 
       (username, email, password, role, super_admin_id, created_at, date_of_birth, first_name, last_name, gender, contact, profile_pic, bio) 
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (superadmin_username, superadmin_email, superadmin_password, superadmin_role, superadmin_super_admin_id, superadmin_created_at, superadmin_date_of_birth, superadmin_first_name, superadmin_last_name, superadmin_gender, superadmin_contact, superadmin_profile_pic, superadmin_bio)
)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Super Admin user added successfully!")
