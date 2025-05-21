from app import app, db  # Make sure this points to the correct module where your Flask app and db are defined

# Ensure to run this code in a separate Python script or Python shell
with app.app_context():
    db.create_all()  # Indent this line to avoid IndentationError
    print("Database tables created successfully.")
