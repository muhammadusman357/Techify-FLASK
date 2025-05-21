import sqlite3
from datetime import datetime

# Connect to the SQLite database
conn = sqlite3.connect('D:\kaam\Project_zero\Project_zero\instance\your_database.db')  # Replace with your SQLite database file path
cursor = conn.cursor()

# SQL queries to insert vendors with additional details
insert_vendors = [
    ("AMD", "support@amd.com", "+1-408-749-4000", "Santa Clara, CA, USA", datetime.utcnow()),
    ("Intel", "support@intel.com", "+1-800-628-8686", "Santa Clara, CA, USA", datetime.utcnow()),
    ("Nvidia", "support@nvidia.com", "+1-408-486-2000", "Santa Clara, CA, USA", datetime.utcnow()),
    ("ASUS", "support@asus.com", "+1-812-282-2787", "Taipei, Taiwan", datetime.utcnow()),
    ("Corsair", "support@corsair.com", "+1-888-222-4346", "Fremont, CA, USA", datetime.utcnow()),
    ("MSI", "support@msi.com", "+1-626-271-1004", "New Taipei City, Taiwan", datetime.utcnow()),
    ("Gigabyte", "support@gigabyte.com", "+1-626-854-9338", "New Taipei City, Taiwan", datetime.utcnow()),
    ("Kingston", "support@kingston.com", "+1-714-435-2600", "Fountain Valley, CA, USA", datetime.utcnow()),
    ("Samsung", "support@samsung.com", "+1-800-726-7864", "Seoul, South Korea", datetime.utcnow()),
    ("Western Digital", "support@wd.com", "+1-800-275-4932", "San Jose, CA, USA", datetime.utcnow()),
    ("Seagate", "support@seagate.com", "+1-800-732-4283", "Cupertino, CA, USA", datetime.utcnow()),
    ("Cooler Master", "support@coolermaster.com", "+1-888-624-5099", "Taipei, Taiwan", datetime.utcnow()),
    ("Logitech", "support@logitech.com", "+1-646-454-3200", "Lausanne, Switzerland", datetime.utcnow()),
    ("Razer", "support@razer.com", "+1-855-872-5233", "Irvine, CA, USA", datetime.utcnow()),
    ("Dell", "support@dell.com", "+1-800-624-9897", "Round Rock, TX, USA", datetime.utcnow())
]

# Insert query with additional columns
insert_query = """
INSERT INTO vendors (name, contact_email, phone_number, address, created_at)
VALUES (?, ?, ?, ?, ?)
"""

# Execute the insert queries
cursor.executemany(insert_query, insert_vendors)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Vendors added successfully!")
