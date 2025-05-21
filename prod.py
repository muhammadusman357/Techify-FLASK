from app import app, db  # Adjust as necessary
from sqlalchemy import text

with app.app_context():
    # Establish a connection
    with db.engine.connect() as connection:
        try:
            # Execute the raw SQL command to add the column
            
            connection.execute(text("ALTER TABLE products RENAME COLUMN vendor TO vendor_id;"))
            print("Column 'vendor' added successfully.")
        except Exception as e:
            print("Error occurred:", e)
