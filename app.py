from flask import Flask, render_template, url_for, request, redirect ,session, flash, jsonify
from authlib.integrations.flask_client import OAuth

from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail
from flask_mail import Message as MailMessage
from datetime import datetime
import smtplib
import os
import json
from sqlalchemy.orm import joinedload  # Import joinedload here
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from flask import flash
import cloudinary
import cloudinary.uploader
import cloudinary.api
from sqlalchemy import func
from random import randint
import logging
from dotenv import load_dotenv

logging.basicConfig(filename='logs/test_log.log', level=logging.INFO)

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Define allowed extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



options = ["Dashboard","Products","Orders","Customers","Reviews", "Settings", "Extras","ManageAdmins","CPUS"]

#Create database model
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# General Config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS') == 'True'

# Upload Config
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH'))

# Flask-Mail Config
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')




db = SQLAlchemy(app)
mail = Mail(app)
migrate = Migrate(app, db)

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Temporary in-memory dictionary for storing reset codes
reset_codes = {}

oauth = OAuth(app)

# Load client_secret.json
with open('client_secret.json') as f:
    google_secrets = json.load(f)['web']

google = oauth.register(
    name='google',
    client_id=google_secrets['client_id'],
    client_secret=google_secrets['client_secret'],
    access_token_url=google_secrets['token_uri'],
    authorize_url=google_secrets['auth_uri'],
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
    },
)
    

# 3. Products Table
class Product(db.Model):
    __tablename__ = 'products'

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    cost_price = db.Column(db.Float, nullable=True)  # Added to match schema
    price = db.Column(db.Float, nullable=False)  # Renamed from 'price' to match schema
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.vendor_id'), nullable=False)  # Change 'vendor' to 'vendors'

    images = db.relationship('ProductImage', backref='product_ref', lazy=True)  
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    reviews = db.relationship('Review', backref='product', lazy=True)
    
class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    # No need for a backref in this case

class Admin(db.Model):
    __tablename__ = 'admins'
    
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed password
    role = db.Column(db.String(50), nullable=False)  # 'superadmin', 'product_manager', etc.
    super_admin_id = db.Column(db.Integer, db.ForeignKey('admins.admin_id'), nullable=True)  # Reference to super admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date_of_birth = db.Column(db.Date, nullable=True)  # Added to match schema
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=True)  # e.g., 'Male', 'Female', 'Other'
    contact = db.Column(db.String(15), nullable=True)  # Store contact number
    profile_pic = db.Column(db.String(255), nullable=True)  # URL to profile picture
    bio = db.Column(db.Text, nullable=True)  # Added to match schema

    __table_args__ = (
        CheckConstraint("role IN ('superadmin', 'product_manager')", name='check_admin_role'),  # Removed extra roles
    )

    # Relationship to manage sub-admins
    sub_admins = db.relationship('Admin', backref=db.backref('super_admin', remote_side=[admin_id]), lazy=True)



class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone_number = db.Column(db.String(50))
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date_of_birth = db.Column(db.Date, nullable=True)  # Added to match schema
    gender = db.Column(db.String(10), nullable=True)  # Added to match schema
    

    # Relationships remain the same (orders, reviews, etc.)
    orders = db.relationship('Order', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)
    wishlist = db.relationship('Wishlist', backref='user', lazy=True)
    cart = db.relationship('Cart', backref='user', lazy=True)
    
# 8. Cart Table
class Cart(db.Model):
    __tablename__ = 'carts'
    
    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Foreign key to users

    # Relationship to cart items
    items = db.relationship('CartItem', backref=db.backref('cart', lazy=True), lazy='dynamic')

class CartItem(db.Model):

    __tablename__ = 'cart_items'

    cart_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.cart_id'), nullable=False)  # Foreign key to users
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)  # Foreign key to products
    quantity = db.Column(db.Integer, nullable=False)  # Quantity of the product in the cart
    added_at = db.Column(db.DateTime, default=datetime.utcnow)  # When the product was added to the cart

    # Relationships
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))



    # 7. Wishlist Table
class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    
    wishlist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Foreign key to users

    # Relationship with wishlist_items (many-to-many relationship with products)
    items = db.relationship('WishlistItem', backref=db.backref('wishlist', lazy=True), lazy='dynamic')


    # Wishlist Association Table for Many-to-Many

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_items'
    
    wishlist_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlists.wishlist_id'), nullable=False)  # Add this line
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)  # Foreign key to products
    added_at = db.Column(db.DateTime, default=datetime.utcnow)  # When the product was added to the wishlist


class Address(db.Model):
    __tablename__ = 'addresses'
    
    address_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Foreign key to users table
    street = db.Column(db.String(255), nullable=False)  # Street address
    city = db.Column(db.String(100), nullable=False)  # City name
    state = db.Column(db.String(100), nullable=False)  # State name
    country = db.Column(db.String(100), nullable=False)  # Country name
    postal_code = db.Column(db.String(20), nullable=False)  # Postal/ZIP code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of creation

    # Relationship (optional) to easily access the user associated with this address
    user = db.relationship('User', backref=db.backref('addresses', lazy=True))

class Chat(db.Model):
    __tablename__ = 'chats'
    
    chat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Foreign key to users
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.admin_id'), nullable=True)  # Foreign key to admins
    status = db.Column(db.Enum('seen', 'unseen', 'open',name='chat_status'), nullable=True)  # Status of the chat
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Chat creation timestamp
    closed_at = db.Column(db.DateTime, nullable=True)  # Chat closed timestamp

    # Relationships for easier access
    user = db.relationship('User', backref=db.backref('chats', lazy=True))
    admin = db.relationship('Admin', backref=db.backref('chats', lazy=True))

class Message(db.Model):
    __tablename__ = 'messages'
    
    message_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.chat_id'), nullable=False)  # Foreign key to chats
    sender_id = db.Column(db.Integer, nullable=False)  # Refers to either user_id or admin_id
    sender_type = db.Column(db.Enum('user', 'admin', name='sender_type'), nullable=False)  # Indicates sender type
    message_text = db.Column(db.Text, nullable=False)  # Message content
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of the message

    # Relationship for easier access to chat
    chat = db.relationship('Chat', backref=db.backref('messages', lazy=True))


# 2. Category Table
class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    products = db.relationship('Product', backref='category', lazy=True)


# 4. Orders Table
class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'), nullable=False)  # Added as per schema
    billing_address_id = db.Column(db.Integer, db.ForeignKey('addresses.address_id'), nullable=False)  # Added as per schema

    order_items = db.relationship('OrderItem', backref='order', lazy=True)

# 4. Order-Items Table
class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    return_requested = db.Column(db.Boolean, default=False)  # Added as per schema

    
    


# 6. Reviews Table
class Review(db.Model):
    __tablename__ = 'reviews'
    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Adding the CheckConstraint for rating validation
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name='check_rating_range'),
    )

class Payment(db.Model):
    __tablename__ = 'payments'
    
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)  # Foreign key to orders
    amount = db.Column(db.Float, nullable=False)  # Amount paid
    payment_method = db.Column(db.String(50), nullable=False)  # Payment method (e.g., 'credit_card', 'paypal')
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)  # Unique transaction ID
    status = db.Column(db.String(20), default='completed')  # Payment status, default is 'completed'
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of the payment

    # Relationship to the order
    order = db.relationship('Order', backref=db.backref('payments', lazy=True))






# 8. Vendor Table
class Vendor(db.Model):
    __tablename__ = 'vendors'
    vendor_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(100))
    phone_number = db.Column(db.String(50))
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Products
    products = db.relationship('Product', backref='vendor', lazy=True)

class SalesSummary(db.Model):
    __tablename__ = 'sales_summary'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    total_sales = db.Column(db.Float, nullable=True, default=0.0)
    total_expenses = db.Column(db.Float, nullable=True, default=0.0)
    total_income = db.Column(db.Float, nullable=True, default=0.0)
    number_of_orders = db.Column(db.Integer, nullable=True, default=0)
    items_sold = db.Column(db.Integer, nullable=True, default=0)

    # Foreign keys for related tables
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.vendor_id'), nullable=True)

    # Relationships
    product = db.relationship('Product', backref='sales_summary', lazy=True)
    vendor = db.relationship('Vendor', backref='sales_summary', lazy=True)
    order = db.relationship('Order', backref='sales_summary', lazy=True)

    def __repr__(self):
        return f'<SalesSummary {self.id} for Product {self.product_id} on {self.date}>'

class ReturnRequest(db.Model):
    __tablename__ = 'return_requests'
    
    return_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Foreign key to users
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.order_item_id'), nullable=False)  # Foreign key to order_items
    reason = db.Column(db.String(255), nullable=False)  # Reason for the return request
    status = db.Column(db.String(20), default='pending')  # Status of the return request, default is 'pending'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When the return request was created
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # When the return request was last updated
    refund_amount = db.Column(db.Float, nullable=True)  # Amount to be refunded (nullable)

    # Relationships
    order_item = db.relationship('OrderItem', backref=db.backref('return_requests', lazy=True))
    user = db.relationship('User', backref=db.backref('return_requests', lazy=True))

    
    
SIZE_KEYWORDS = [
    "VRAM",          # Graphics Cards
    "Memory",        # RAM
    "Storage",       # SSDs, HDDs
    "Screen Size",   # Monitors, Laptops
    "Power",         # Power Supplies (Wattage)
    "Dimensions",    # Cases, Heatsinks
    "Speed",         # CPUs, Network Cards
    "Cores/Threads", # CPUs
    "Refresh Rate",  # Monitors
    "Battery Capacity",  # Laptops, UPS
    "Weight",        # Accessories, laptops
    "Fan Size",      # Case fans
    "Cable Length",  # HDMI, USB, Ethernet cables
    "Button Count",  # Mice, Game Controllers
    "Key Count",     # Keyboards
    "Connectivity Range",  # Bluetooth devices
    "RPM",           # Hard Drives
    "Ports",         # USB hubs
    "Resolution",    # Monitors
    "Latency",       # RAM or Networking devices
]

def create_sales_summary(product_id, vendor_id, total_sales, total_expenses, total_income, number_of_orders, items_sold):
    sales_summary = SalesSummary(
        date=datetime.utcnow(),
        total_sales=total_sales,
        total_expenses=total_expenses,
        total_income=total_income,
        number_of_orders=number_of_orders,
        items_sold=items_sold,
        product_id=product_id,
        vendor_id=vendor_id
    )

    db.session.add(sales_summary)
    db.session.commit()

def create_triggers():
    with app.app_context():
        # Get a raw SQLite connection
        connection = db.engine.raw_connection()
        cursor = connection.cursor()

        # Drop existing triggers if they exist
        cursor.execute("DROP TRIGGER IF EXISTS after_order_insert;")
        cursor.execute("DROP TRIGGER IF EXISTS after_order_item_insert;")

        # Create triggers for sales summary updates
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_order_insert
        AFTER INSERT ON orders
        BEGIN
            INSERT INTO sales_summary (date, total_sales, total_expenses, total_income, number_of_orders, items_sold)
            SELECT DATE('now'), NEW.total_price, 0, NEW.total_price, 1, 0
            WHERE NOT EXISTS (SELECT 1 FROM sales_summary WHERE date = DATE('now'));

            UPDATE sales_summary
            SET total_sales = total_sales + NEW.total_price,
                total_income = total_sales - total_expenses,
                number_of_orders = number_of_orders + 1
            WHERE date = DATE('now');
        END;
        """)

        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_order_item_insert
        AFTER INSERT ON order_items
        BEGIN
            -- Ensure the sales summary row for today exists
            INSERT INTO sales_summary (date, total_sales, total_expenses, total_income, number_of_orders, items_sold)
            SELECT DATE('now'), 0, 0, 0, 0, 0
            WHERE NOT EXISTS (SELECT 1 FROM sales_summary WHERE date = DATE('now'));

            -- Update sales summary for today's date without calculating total_expenses
            UPDATE sales_summary
            SET items_sold = items_sold + NEW.quantity,
                total_income = total_sales - total_expenses
            WHERE date = DATE('now');
        END;
        """)

        # Add any additional triggers here if needed
        connection.commit()
        cursor.close()
        connection.close()

# Flag to track if the triggers have already been created
triggers_created = False

@app.before_request
def setup():
    global triggers_created
    if not triggers_created:
        db.create_all()  # Ensure tables exist
        create_triggers()  # Create triggers
        triggers_created = True  # Mark as created

from sqlalchemy import func


"""@app.route('/best_sellers/<category_name>', methods=['GET'])
def best_sellers(category_name):
    # Fetch the category
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        return jsonify({"success": False, "message": "Category not found"}), 404

    # Query best-selling products for this category
    best_selling = (
    db.session.query(Product)
    .filter(Product.category_id == category.category_id)
    .order_by(Product.created_at.desc())  # Order by creation date (or any other desired field)
    .all()
    )


    # Format the results for JSON response
    products = [
        {
            "id": product.product_id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "avg_rating": sum([review.rating for review in product.reviews]) / len(product.reviews)
            if product.reviews else None,
            "image_urls": [image.image_url for image in product.images]
        }
        for product, _ in best_selling
    ]

    return jsonify({"success": True, "products": products})"""

@app.route('/get_product_details/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        product_details = {
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'image_url': product.images[0].image_url if product.images else None
        }
        return jsonify({'product': product_details})
    return jsonify({'message': 'Product not found'}), 404

def truncate_text(text, word_limit=20):
    """Truncate text to a specified number of words."""
    if not text:
        return ''
    words = text.split()
    return ' '.join(words[:word_limit]) + ('...' if len(words) > word_limit else '')



@app.route('/sa')
def sampl():
    selected = "sampl"
    return render_template('sampl.html', selected=selected)
@app.route('/api/products', methods=['GET'])
def get_products2():
    search_query = request.args.get('q', '')
    products_query = Product.query

    if search_query:
        products_query = products_query.filter(Product.name.ilike(f"%{search_query}%"))
            
      
    products = products_query.all()
    # Generate a truncated description with up to 20 words
    
    result = []
    for product in products:
        truncated_description = truncate_text(product.description, 20) 
        truncated_name = truncate_text(product.name, 10) 
        images = [image.image_url for image in product.images]
        result.append({
            'id': product.product_id,
            'name': truncated_name,
            'stock': product.stock,
            'description': truncated_description,
            'price': product.price,
            'image_url': images[0] if images else 'https://via.placeholder.com/50',
        })

    return jsonify(result)










from sqlalchemy.orm import aliased


app.route('/search', methods=['GET'])
def search2():
    query = request.args.get('query', '')  # Get the search query from the request
    if not query:
        return jsonify(products=[])

    # Search products and categories using SQLAlchemy ORM
    products = db.session.query(Product).join(Category).filter(
        (Product.name.ilike(f'%{query}%')) |
        (Category.name.ilike(f'%{query}%'))
    ).all()

    # Prepare the products to return in the response
    product_list = [{
        'id': product.product_id,
        'name': product.name,
        'image_url': product.images[0].image_url if product.images else None  # Assume first image
    } for product in products]

    return jsonify(products=product_list)





@app.route('/<string:category_name>', methods=['GET'])
def show_category_products(category_name):
    category_name = category_name.lower()
    category = Category.query.filter(func.lower(Category.name) == category_name).first()

    if not category:
        return "Category not found", 404

    # Fetch all available filter data for the category
    all_products = Product.query.filter_by(category_id=category.category_id).all()
    all_vendors = {product.vendor.name for product in all_products if product.vendor}
    all_filters = {}

    for product in all_products:
        for keyword in SIZE_KEYWORDS:
            import re
            pattern = rf"{keyword}:\s*([\w./-]+)"
            match = re.search(pattern, product.description, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if keyword not in all_filters:
                    all_filters[keyword] = set()
                all_filters[keyword].add(value)

    all_filters = {key: sorted(values) for key, values in all_filters.items()}

    # Apply sorting and filtering to the displayed products
    sort_option = request.args.get('sort', 'alphabetically_az')  # Default to 'alphabetically_az'
    products_query = Product.query.filter_by(category_id=category.category_id)

    # Apply sorting logic
    if sort_option == 'price_low_to_high':
        products_query = products_query.order_by(Product.price.asc())
    elif sort_option == 'price_high_to_low':
        products_query = products_query.order_by(Product.price.desc())
    elif sort_option == 'alphabetically_az':
        products_query = products_query.order_by(Product.name.asc())
    elif sort_option == 'alphabetically_za':
        products_query = products_query.order_by(Product.name.desc())
    elif sort_option == 'best_selling':
        products_query = (
            products_query
            .join(OrderItem, OrderItem.product_id == Product.product_id)  # Join with OrderItem table
            .group_by(Product.product_id)  # Group by product to aggregate sales
            .order_by(func.sum(OrderItem.quantity).desc())  # Order by total quantity sold
        )

    elif sort_option == 'date_old_to_new':
        products_query = products_query.order_by(Product.created_at.asc())
    elif sort_option == 'date_new_to_old':
        products_query = products_query.order_by(Product.created_at.desc())

    # Apply filters
    in_stock = request.args.get('in_stock')
    if in_stock == 'true':
        products_query = products_query.filter(Product.stock > 0)
    elif in_stock == 'false':
        products_query = products_query.filter(Product.stock == 0)

    """min_price = request.args.get('min_price', type=float, default=0)
    max_price = db.session.query(func.max(Product.price)).filter_by(category_id=category.category_id).scalar() or 0"""
    
    """min_price = request.args.get('min_price', default=0, type=float)
    max_price = request.args.get('max_price', default=None, type=float)

    # If max_price is not provided, fetch the maximum price from the database
    if max_price is None:
        max_price = db.session.query(func.max(Product.price)).filter_by(category_id=category.category_id).scalar() or 0

    # Apply the price range filter
    products_query = products_query.filter(Product.price >= min_price, Product.price <= max_price)
    products_query = products_query.filter(Product.price >= min_price, Product.price <= max_price)"""

    # Fetch the actual min and max price for the category
    category_min_price = db.session.query(func.min(Product.price)).filter_by(category_id=category.category_id).scalar() or 0
    category_max_price = db.session.query(func.max(Product.price)).filter_by(category_id=category.category_id).scalar() or 0

    # Get user-selected price range or default to the category's min and max price
    selected_min_price = request.args.get('min_price', default=category_min_price, type=float)
    selected_max_price = request.args.get('max_price', default=category_max_price, type=float)

    #Apply the selected price range filter
    products_query = products_query.filter(Product.price >= selected_min_price, Product.price <= selected_max_price)


    selected_vendors = request.args.getlist('vendor')
    if selected_vendors:
        products_query = products_query.filter(Product.vendor.has(Vendor.name.in_(selected_vendors)))

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = products_query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    # Prepare products for display
    products_with_images = []
    product_count = len(products)
    for product in products:
        images = ProductImage.query.filter_by(product_id=product.product_id).limit(2).all()
        image_urls = [image.image_url for image in images] if images else ["https://via.placeholder.com/200"]

        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.product_id == product.product_id)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating is not None else None

        products_with_images.append({
            'id': product.product_id,
            'name': product.name,
            'description': product.description,
            'stock': product.stock,
            'price': product.price,
            'image_urls': image_urls,
            'avg_rating': avg_rating,
            'vendor_name': product.vendor.name if product.vendor else "Unknown Vendor"
        })
        
    product_count = len(products)
    return render_template(
        'display_products.html',
        products=products_with_images,
        filters=all_filters,
        vendors=sorted(all_vendors),
        selected=category_name,
        category_min_price=category_min_price,
        category_max_price=category_max_price,
        selected_min_price=selected_min_price,
        selected_max_price=selected_max_price,
        page=page,
        total_pages=pagination.pages,
        sort_option=sort_option,
        product_count = product_count
    )



"""
@app.route('/cart')
def cart():
    selected = "Analytics"
    return render_template('cart.html', selected=selected)"""







from datetime import timedelta

@app.route('/analytics')
def analytics():
    selected = "analytics"
    # Get the last 30 days of sales data
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    # Query Sales Summary Data for the last 30 days
    sales_data = SalesSummary.query.filter(SalesSummary.date >= start_date).order_by(SalesSummary.date).all()

    # Extract data for the graph and handle None values
    dates = [sale.date.strftime('%Y-%m-%d') for sale in sales_data]
    sales = [sale.total_sales if sale.total_sales is not None else 0 for sale in sales_data]
    expenses = [sale.total_expenses if sale.total_expenses is not None else 0 for sale in sales_data]
    income = [sale.total_income if sale.total_income is not None else 0 for sale in sales_data]
    orders = [sale.number_of_orders if sale.number_of_orders is not None else 0 for sale in sales_data]
    total_orders = sum(orders)
    avg_orders_per_day = total_orders / len(sales_data) if sales_data else 0
    # You can calculate additional metrics (like number of items sold, profit margin, etc.) here if needed
    return render_template('/admin/a-dashboard/analytics.html', selected=selected, dates=dates, sales=sales, expenses=expenses, income=income, orders=orders,total_orders=total_orders, avg_orders_per_day=avg_orders_per_day)


from flask import request  # Make sure to import request

@app.route('/products')
def products():
    selected = "Products"
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    criteria = request.args.get('criteria', 'name')  # Default to 'username'

    # Base query
    query = Product.query.outerjoin(Product.images)

    # Filter admins by search criteria and query if it exists
    if search_query:
        if criteria == "name":
            query = query.filter(Product.name.ilike(f'%{search_query}%'))
        elif criteria == "category":
            query = query.filter(Product.category.ilike(f'%{search_query}%'))
        

    # Pagination
    per_page = 8
    productdata = query.paginate(page=page, per_page=per_page, error_out=False)

    

    # Debug: Print product names and image URLs
    for product in productdata.items:
        print(f"Product ID: {product.product_id}, Product Name: {product.name}")
        for image in product.images:
            # Normalize URL to use forward slashes
            image_url = image.image_url.replace('\\', '/')
            print(f"  Image URL: {image_url}")

    return render_template('/admin/a-dashboard/products.html', productdata=productdata, selected=selected)



@app.route('/home-base')
def homebase():
    
    selected = "Home"
    return render_template('home-base.html', selected=selected)

@app.route('/')
def home():
    error_statement = " "
    
    username = session.get('username')
    user_id = session.get('user_id')
    selected = "Techify"

    vendors = Vendor.query.all()
    
    # Prepare vendor data to include their logo paths (assuming vendor logos are in static/images/vendors)
    vendor_data = [
        {"name": vendor.name, "logo": f"images/vendors/{vendor.name.lower().replace(' ', '_')}.png"}
        for vendor in vendors
    ]


    # Query to fetch products with images (adjust according to your needs)
    slider = Product.query.join(Category, Product.category_id == Category.category_id) \
        .filter(Category.name.in_(["Laptops", "Prebuild PCs"]), Product.price > 400000) \
        .limit(8).all()
    products = Product.query.join(SalesSummary, SalesSummary.product_id == Product.product_id)\
                                      .group_by(Product.product_id)\
                                      .order_by(func.sum(SalesSummary.total_sales).desc())
    # Prepare the product data with images and ratings
    products_with_images = []
    for product in products:
        images = ProductImage.query.filter_by(product_id=product.product_id).limit(2).all()
        image_urls = [image.image_url for image in images] if images else ["https://via.placeholder.com/200"]

        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.product_id == product.product_id)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating is not None else None
        products_with_images.append({
            'id': product.product_id,
            'name': product.name,
            'description': product.description,
            'stock': product.stock,
            'price': product.price,
            'image_urls': image_urls,
            'avg_rating': avg_rating,
            
        })
    categories = [category.name for category in Category.query.order_by(Category.name).all()]


    # Fetching images related to the products
    product_images = {product.product_id: [image.image_url for image in product.images] for product in slider}

    return render_template('home.html',username=username,categories=categories ,products=products_with_images, selected=selected, slider=slider, product_images=product_images, vendors=vendor_data,error_statement=error_statement)


@app.route('/userlogin', methods=['POST', 'GET'])
def userlogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
            # Store the username in the session
            session['username'] = user.username
            session['user_id'] = user.user_id
            
            # Redirect to the home page
            return redirect(url_for('home'))
        else:
            flash("Incorrect username or password.", 'error')
            return redirect(url_for('userlogin'))
    return render_template("userlogin.html")

@app.route('/validate_username', methods=['GET'])
def validate_username():
    username = request.args.get('username')
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'exists': True})
    return jsonify({'exists': False})


@app.route('/validate_email', methods=['GET'])
def validate_email():
    email = request.args.get('email')
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'exists': True})
    return jsonify({'exists': False})


@app.route('/validate_dob', methods=['GET'])
def validate_dob():
    dob = request.args.get('dob')
    try:
        datetime.strptime(dob, '%Y-%m-%d')
        return jsonify({'valid': True})
    except ValueError:
        return jsonify({'valid': False})
    
@app.route('/send_mail', methods=['GET'])
def send_mail():
    # Send the email
    email = request.args.get('email')
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        username=existing_user.username
    else:
        username=email
    msg = MailMessage(
        subject='Welcome to Our Site!',
        recipients=[email],
        html=render_template('news_email.html', username=username)
        )

    try:
        mail.send(msg)
        return jsonify({'valid': True})
    except Exception as e:
        return jsonify({'valid': False})
        


# Route for signup
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        gender = request.form['gender']
        dob = request.form['dob']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        confpassword =request.form['confpassword']
        # Validate and convert dob to date format
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
        except ValueError:
            error_message4 = '* Invalid date format. Please enter in YYYY-MM-DD format.'
            return render_template('signup.html',email=email,username=username, error_message4=error_message4)
        
        # Check if username or email already exists
        existing_username = User.query.filter(User.username == username).first()
        existing_email = User.query.filter(User.email == email).first()
        if existing_email and existing_username:
            error_message2 = "* An account with this email address already exists"
            error_message3 = "* Username already taken."
            return render_template('signup.html',email=email,username=username, error_message2=error_message2, error_message3=error_message3)
        elif existing_email:
            error_message2 = "An account with this email address already exists"
            logging.info(f"An account with this email address {email} already exists time: {datetime.now()}")
            return render_template('signup.html',email=email,username=username, error_message2=error_message2)
        elif existing_username:
            error_message3 = "Username already taken."
            return render_template('signup.html',email=email,username=username, error_message3=error_message3)

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create a new user object with the hashed password
        new_user = User(username=username, email=email,first_name=first_name,last_name=last_name, password=hashed_password, gender=gender, date_of_birth=dob_date)
        try:
            db.session.add(new_user)
            db.session.commit()
            logging.info(f"Login success for user {email} at {datetime.now()}")
            flash("User account created successfully!", 'success')
            session['username'] = new_user.username
            session['user_id'] = new_user.user_id
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating the account: {e}', 'error')
            return redirect(url_for('signup'))

        # Separate block for email
        try:
            msg = MailMessage(
                subject='Welcome to Our Site!',
                recipients=[email],
                html=render_template('login_email.html', username=username)
            )
            mail.send(msg)  # Send the email

            return redirect('/')
        except Exception as e:
            flash(f'An error occurred while sending the welcome email: {e}', 'error')
            return redirect(url_for('signup'))

           


    return render_template('signup.html')


@app.route('/forgotPassword',methods=['POST','GET'])

def forgotPassword():
    if request.method=='POST':
        user_email = request.form.get('email')
        
        # Check if the user exists in the database
        user = User.query.filter_by(email=user_email).first()
        
        if user:
            # Generate a 6-digit reset code
            reset_code = str(randint(100000, 999999))
            reset_codes[user_email] = reset_code
            # Store the reset code in the database (or in memory, but it's safer in the DB)
            #user.reset_code = reset_code  # Make sure your User model has this field
            #db.session.commit()

            # Separate block for email
            try:
                msg = MailMessage(
                    subject='Password Reset Code',
                    recipients=[user_email],
                    html=render_template('reset_code_email.html', reset_code=reset_code)
                )
                mail.send(msg)  # Send the email
                logging.info(f"A reset code has been sent to your email {user_email} at {datetime.now()}")
                flash('A reset code has been sent to your email.', 'success')
            except Exception as e:
                flash(f'An error occurred while sending the welcome email: {e}', 'error')
            
            return redirect(url_for('resetLink', user_email=user_email))
        else:
            flash('Email not found.', 'error')
            return redirect(url_for('forgotPassword'))
    else:
        return render_template('forgotPassword.html')





@app.route('/resetLink', methods=['POST', 'GET'])
def resetLink():
    if request.method == 'POST':
        user_email = request.args.get('user_email')  # Get the email from query parameters
        user_code = request.form.get('reset_code')

        # Check if the code matches
        if user_email in reset_codes and reset_codes[user_email] == user_code:
            flash('Code verified. You can now reset your password.', 'success')
            # Remove the reset code after successful verification
            del reset_codes[user_email]
            return redirect(url_for('resetPassword', user_email=user_email))
        else:
            flash('Invalid or expired code. Please try again.', 'error')
            return redirect(url_for('resetLink', user_email=user_email))
    else:
        return render_template('resetLink.html')  # Ensure a valid response is returned here


@app.route('/resetPassword', methods=['POST', 'GET'])
def resetPassword():

    if request.method == 'POST':
        user_email = request.args.get('user_email')  # Retrieve the email from query parameters
        new_password = request.form.get('password')
        # Fetch the user record from the database

        user = User.query.filter_by(email=user_email).first()
        if user:
            try:
                # Hash the new password and update the user record
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                user.password=hashed_password
                db.session.commit()
                flash('Password reset successful.', 'success')
                return redirect(url_for('userlogin'))  
            except Exception as e:
                flash('An error occurred while updating the password. Please try again.', 'error')
                db.session.rollback()  # Rollback in case of an error
                return redirect(url_for('resetPassword', user_email=user_email))
        else:
            flash('User not found. Please check the email and try again.', 'error')
            return redirect(url_for('resetPassword', user_email=user_email))

    # Handle GET request
    #if not user_email:
    #    flash('Missing user email. Please try again.', 'error')
    #    return redirect(url_for('resetLink'))  # Redirect to the reset link page if email is missing
    else:
        return render_template('resetPassword.html')

# admin-pages
@app.route('/news_email')
def news_email():
    selected = "news_email"
    return render_template('news_email.html', selected=selected)

# admin-pages
@app.route('/login_email')
def login_email():
    selected = "login_email"
    return render_template('login_email.html', selected=selected)



# admin-pages
@app.route('/dashboard', methods=['GET'])
def dashboard():
    admin_id = session.get('admin_id')  # Assume admin_id is stored in session
    if not admin_id:
        return "Admin not logged in", 401


    # Fetch admin data (optional, if needed)
    admin = Admin.query.get(admin_id)
    if not admin:
        return "Admin not found", 404

    # Aliases for shipping and billing addresses
    shipping_address = aliased(Address)
    billing_address = aliased(Address)

    # Fetch the six most recent orders for all users
    query = (
        db.session.query(
            Order,
            User.first_name.label("user_first_name"),
            User.last_name.label("user_last_name"),
            shipping_address.street.label("shipping_street"),
            shipping_address.city.label("shipping_city"),
            shipping_address.state.label("shipping_state"),
            shipping_address.country.label("shipping_country"),
            shipping_address.postal_code.label("shipping_postal_code"),
            billing_address.street.label("billing_street"),
            billing_address.city.label("billing_city"),
            billing_address.state.label("billing_state"),
            billing_address.country.label("billing_country"),
            billing_address.postal_code.label("billing_postal_code"),
        )
        .join(User, User.user_id == Order.user_id)  # Join with User table to fetch user details
        .join(shipping_address, Order.shipping_address_id == shipping_address.address_id)
        .join(billing_address, Order.billing_address_id == billing_address.address_id)
        .order_by(Order.created_at.desc())  # Order by most recent
        .limit(6)  # Limit to the 6 most recent orders
    )

    recent_orders = query.all()

    current_date = datetime.utcnow().strftime('%Y-%m-%d')  # Format as YYYY-MM-DD


    from sqlalchemy import func

    # Query to get the total expenses, total income, and total sales
    result = db.session.query(
        func.sum(SalesSummary.total_expenses).label('total_expenses'),
        func.sum(SalesSummary.total_income).label('total_income'),
        func.sum(SalesSummary.total_sales).label('total_sales')
    ).first()

    # Store the results as integers in an array
    summary = [
        int(result.total_expenses or 0), 
        int(result.total_income or 0), 
        int(result.total_sales or 0)
    ]


    selected = "dashboard"
    return render_template('/admin/a-dashboard/dashboard.html',
                           selected=selected,summary=summary, current_date=current_date, recent_orders=recent_orders, admin=admin)



@app.route('/reviews', methods=['GET'])
def reviews():
    selected = "Reviews"
    
    # Get pagination and search parameters from the URL
    page = request.args.get('page', 1, type=int)
    per_page = 8
    search = request.args.get('search', '')
    criteria = request.args.get('criteria', 'username')
    
    # Modify the query to explicitly select the required columns
    if criteria == 'username':
        query = db.session.query(
            Review.review_id, Review.review_text, Review.rating, Review.created_at,
            User.username, Product.name.label('product_name')
        ).join(User).join(Product).filter(Review.user_id == User.user_id)
    elif criteria == 'product_name':
        query = db.session.query(
            Review.review_id, Review.review_text, Review.rating, Review.created_at,
            User.username, Product.name.label('product_name')
        ).join(User).join(Product)
    
    # Pagination for reviews
    reviewdata = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('/admin/a-dashboard/reviews.html', selected=selected, reviewdata=reviewdata)






@app.route('/stock')
def stock():
    selected = "Stock"
    
    return render_template('/admin/a-dashboard/stock.html', selected=selected)



@app.route('/customers')
def customers():
    selected = "Customers"
    return render_template('/admin/a-dashboard/customers.html', selected=selected)



@app.route('/settings')
def settings():
    selected = "Settings"
    return render_template('/admin/a-dashboard/settings.html', selected=selected)

@app.route('/extras')
def extras():
    selected = "Extras"
    return render_template('/admin/a-dashboard/extras.html', selected=selected)



@app.route('/reports')
def reports():
    selected = "Reports"
    return render_template('/admin/a-dashboard/reports.html', selected=selected)

@app.route('/profile')
def profile():
    selected = "Profile"
    return render_template('/admin/a-dashboard/profile.html', selected=selected)

"""@app.route('/CPUS')
def CPUS():
    selected = "CPUS"
    return render_template('CPUS.html',selected=selected)"""





"""@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    # Fetch the product details from the database
    product = Product.query.get_or_404(product_id)

    # Ensure product exists and fetch all associated images
    image_urls = []
    if product.images:
        image_urls = [image.image_url for image in product.images]

    description_lines = product.description.strip().split('\n')
    # Pass both 'product' and 'image_urls' to the template
    return render_template('product_details.html', product=product, image_urls=image_urls, description_lines = description_lines)"""



from sqlalchemy import func

@app.route('/get-products', methods=['GET'])
def get_products():
    categories = request.args.getlist('categories')  # Get list of categories
    page = request.args.get('page', type=int, default=1)  # Default to page 1
    per_page = 3  # Number of products per page

    # Query products filtered by category
    products_query = (
        db.session.query(Product, db.func.avg(Review.rating).label('avg_rating'))
        .join(Category, Product.category_id == Category.category_id)
        .outerjoin(Review, Product.product_id == Review.product_id)
        .filter(Category.name.in_(categories))  # Filter products by category
        .group_by(Product.product_id)
        .paginate(page=page, per_page=per_page)
    )

    products = []
    for product, avg_rating in products_query.items:
        image_urls = [image.image_url for image in product.images[:2]]

        products.append({
            'id': product.product_id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'category': product.category.name,
            'image_urls': image_urls,
            'avg_rating': round(avg_rating, 1) if avg_rating else None,
        })

    return jsonify({
        'products': products,
        'total_pages': products_query.pages,
        'current_page': products_query.page,
    })










@app.route('/get-reviews/<int:product_id>', methods=['GET'])
def get_reviews(product_id):
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of reviews per page

    # Query reviews for the product with user details, ordered by created_at in descending order
    reviews_query = (
        db.session.query(Review, User)
        .join(User, Review.user_id == User.user_id)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    # Construct the response
    reviews = [
        {
            'username': f"{review_user.first_name} {review_user.last_name}" if review_user.first_name and review_user.last_name else review_user.username,
            'review_text': review.review_text,
            'rating': review.rating,
            'created_at': review.created_at.strftime('%Y-%m-%d'),
        }
        for review, review_user in reviews_query.items
    ]

    # Return paginated data
    return jsonify({
        'reviews': reviews,
        'total_pages': reviews_query.pages,
        'current_page': reviews_query.page,
    })







@app.route('/product_details/<int:product_id>')
def product_details(product_id):
    # Fetch product details by product_id
    product = Product.query.get_or_404(product_id)
    
    category = Category.query.filter(product.category_id == Category.category_id).first()
    vendor = Vendor.query.filter(product.vendor_id == Vendor.vendor_id).first()
    if not category:
        return "Category not found", 404

    
    avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.product_id == product.product_id)
            .scalar()
        )
    # Fetch reviews along with associated user data
    reviews = Review.query.filter(product.product_id==Review.product_id).all()
    # Fetch all reviews for a product along with associated user data (including multiple reviews from the same user)
    #reviews = db.session.query(User.username, Review.review_text, Review.rating, Review.created_at).join(Review).filter(Review.product_id == product.product_id).all()


    
     # This array will have all reviews with user data
    review_counts = {
        rating: Review.query.filter(Review.product_id == product.product_id, Review.rating == rating).count()
        for rating in range(1, 6)
    }
    review_count_all = Review.query.filter(Review.product_id == product.product_id).count()
    description_lines = product.description.strip().split('\n')
    # Fetch associated images
    #images = ProductImage.query.filter_by(product_id=product_id).all()
    product_images = ProductImage.query.filter_by(product_id=product_id).all()
    image_urls = [image.image_url for image in product_images]

    
    
    product_data = {
        'id' : product.product_id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'category': category.name,
        'vendor': vendor.name,
        'created_at': product.created_at.strftime("%B %d, %Y"),
        'avg_rating': avg_rating,
        'review_counts': review_counts,
        'review_count_all': review_count_all
    }

    return render_template('product_details.html',reviews=reviews, product=product_data , description_lines = description_lines, image_urls = image_urls)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    # Retrieve the product by its ID from the database
    product = Product.query.get_or_404(product_id)
    
    # Delete related images manually if necessary
    for image in product.images:
        db.session.delete(image)  # Delete related images
    
    db.session.delete(product)  # Delete the product
    db.session.commit()  # Commit the transaction to the database
    
    # Redirect back to the products page
    return redirect(url_for('products'))


"""@app.route('/delete_admin/<int:admin_id>')
def delete_admin(admin_id):
    current_admin_id = session.get('admin_id')  # Get the logged-in admin ID from the session
    admin_to_delete = Admin.query.get_or_404(admin_id)
     # Prevent deleting the superadmin
    if admin_to_delete.role == 'superadmin':
        flash("Cannot delete the superadmin.")
        return redirect(url_for('manage_admins'))
    
    # Prevent the superadmin from deleting themselves
    if admin_to_delete.admin_id == current_admin_id:
        flash("You cannot delete your own account.")
        return redirect(url_for('manage_admins'))  

    db.session.delete(admin_to_delete)
    db.session.commit()
    flash("Admin deleted successfully!")
    return redirect(url_for('manage_admins'))"""

@app.route('/toggle_wishlist', methods=['POST'])
def toggle_wishlist():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    product_id = request.json.get('product_id')

    if not product_id:
        return jsonify({'error': 'No product ID provided'}), 400

    # Fetch or create the user's wishlist
    wishlist = Wishlist.query.filter_by(user_id=user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.session.add(wishlist)
        db.session.commit()

    # Check if the product is in the wishlist
    wishlist_item = WishlistItem.query.filter_by(wishlist_id=wishlist.wishlist_id, product_id=product_id).first()

    if wishlist_item:
        # Remove from wishlist if it exists
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({'message': 'Product removed from wishlist', 'in_wishlist': False}), 200

    # Add to wishlist if not present
    new_item = WishlistItem(wishlist_id=wishlist.wishlist_id, product_id=product_id, added_at=datetime.utcnow())
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Product added to wishlist', 'in_wishlist': True}), 200


@app.route('/check_wishlist', methods=['GET'])
def check_wishlist():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    wishlist = Wishlist.query.filter_by(user_id=user_id).first()

    if not wishlist:
        return jsonify({'products': []}), 200

    # Return a list of product IDs in the wishlist
    product_ids = [item.product_id for item in wishlist.items]
    return jsonify({'products': product_ids}), 200





"""@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    product_id = request.json.get('product_id')

    if not product_id:
        return jsonify({'error': 'No product ID provided'}), 400

    # Fetch or create the user's wishlist
    wishlist = Wishlist.query.filter_by(user_id=user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.session.add(wishlist)
        db.session.commit()

    # Check if product is already in wishlist
    wishlist_item = WishlistItem.query.filter_by(wishlist_id=wishlist.wishlist_id, product_id=product_id).first()
    if wishlist_item:
        return jsonify({'message': 'Product already in wishlist'}), 200

    # Add product to wishlist
    new_item = WishlistItem(wishlist_id=wishlist.wishlist_id, product_id=product_id, added_at=datetime.utcnow())
    db.session.add(new_item)
    db.session.commit()

    return jsonify({'message': 'Product added to wishlist'}), 200"""
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/categories', methods=['GET'])
@cache.cached(timeout=3600)  # Cache for 1 hour
def get_categories():
    categories = [category.name for category in Category.query.order_by(Category.name).all()]
    return jsonify(categories)

@app.route('/test')
def test():
    selected = "test"
    return render_template('test.html', selected=selected)


# Fetch categories
@app.route('/fetch_categories', methods=['GET'])
def fetch_categories():
    categories = Category.query.all()
    return jsonify([{"id": category.category_id, "name": category.name} for category in categories])

# Fetch vendors by category
@app.route('/fetch_vendors/<int:category_id>', methods=['GET'])
def fetch_vendors(category_id):
    vendors = Vendor.query.join(Product).filter(Product.category_id == category_id).distinct(Vendor.vendor_id).all()
    return jsonify([{"id": vendor.vendor_id, "name": vendor.name} for vendor in vendors])

# Fetch products by vendor and category
@app.route('/fetch_products/<int:vendor_id>/<int:category_id>', methods=['GET'])
def fetch_products(vendor_id, category_id):
    products = Product.query.filter_by(vendor_id=vendor_id, category_id=category_id).all()
    return jsonify([{
        "id": product.product_id,
        "name": product.name,
        "stock": product.stock,
        "price": product.cost_price,
        "image_url": product.images[0].image_url if product.images else "/path/to/default.jpg"
    } for product in products])

# Restock products and record expenses
@app.route('/restock_products', methods=['POST'])
def restock_products():
    data = request.json
    products = data.get("products", [])
    
    if not products:
        return jsonify({"error": "No products provided"}), 400
    
    total_expense = 0.0
    for item in products:
        product_id = item.get("id")
        quantity = item.get("quantity", 0)
        
        # Fetch product and update stock
        product = Product.query.get(product_id)
        if not product:
            continue  # Skip if product not found
        product.stock += quantity
        total_expense += quantity * (product.cost_price or 0.0)  # Use cost price for expense
        
        # Update last updated timestamp
        product.last_updated = datetime.utcnow()
        db.session.add(product)
    
    # Update SalesSummary
    sales_summary = SalesSummary.query.filter_by(date=datetime.utcnow().date()).first()
    if not sales_summary:
        sales_summary = SalesSummary(date=datetime.utcnow().date(), total_expenses=0.0)
    
    sales_summary.total_expenses += total_expense
    sales_summary.total_income = (sales_summary.total_sales or 0.0) - (sales_summary.total_expenses or 0.0)
    db.session.add(sales_summary)
    
    # Commit changes to database
    db.session.commit()
    
    return jsonify({"message": "Products restocked successfully", "total_expense": total_expense})

@app.route('/addproduct', methods=['GET', 'POST'])
def addproduct():
    selected = "Add-Product"
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        print(1)
        # Clean the price input
        price_str = request.form['price'].replace(',', '')  # Remove commas
        try:
            price = float(price_str)
        except ValueError:
            return "Invalid price format", 400
        
        cost_price_str = request.form['cost_price'].replace(',', '')  # Remove commas
        try:
            cost_price = float(cost_price_str)
        except ValueError:
            return "Invalid price format", 400
        
        stock = request.form['stock']
        category_name = request.form['category']
        vendor_name = request.form['vendor']
        
        # Update vendor_id based on the selected vendor from the form
        vendor_id = request.form['vendor']
        if vendor_id:
            vendor = Vendor.query.filter_by(vendor_id=vendor_id).first()
            if vendor:
                vendor_id = vendor.vendor_id

        # Update category_id based on the selected category from the form
        category_id = request.form['category']
        if category_id:
            category = Category.query.filter_by(category_id=category_id).first()
            if category:
                category_id = category.category_id

        vendor_id = vendor.vendor_id
        
        # Create a new product
        new_product = Product(
            name=name,
            description=description,
            price=price,
            cost_price=cost_price,
            stock=stock,
            category_id=category_id,
            vendor_id=vendor_id,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

        try:
            # Add product to the database first
            db.session.add(new_product)
            db.session.commit()

            # Handle image uploads to Cloudinary
            if 'image' in request.files:
                files = request.files.getlist('image')

                for file in files:
                    if file and file.filename != '':
                        upload_result = cloudinary.uploader.upload(file)
                        image_url = upload_result.get('secure_url')

                        new_image = ProductImage(
                            product_id=new_product.product_id,
                            image_url=image_url
                        )
                        db.session.add(new_image)

                db.session.commit()
            logging.info(f"Product added Successfull\nProduct name: {name}\nDescription: {description}\nPrice: {price}\nStock: {stock}\n")
            return redirect(url_for('products'))

        except IntegrityError as ie:
            db.session.rollback()
            return f"IntegrityError: {str(ie)}"

        except Exception as e:
            db.session.rollback()
            return f"Exception: {str(e)}"

    # GET request logic remains the same
    vendors = Vendor.query.all()
    categories = Category.query.all()
    return render_template('/admin/a-dashboard/addproduct.html', selected=selected,vendors=vendors, categories=categories)

@app.route('/updateproduct/<int:product_id>', methods=['GET', 'POST'])
def updateproduct(product_id):
    selected = "Products"
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # Update basic product information
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.description = request.form['description']
        product.cost_price = float(request.form['cost_price'])

        # Update vendor_id based on the selected vendor from the form
        vendor_id = request.form['vendor']
        if vendor_id:
            vendor = Vendor.query.filter_by(vendor_id=vendor_id).first()
            if vendor:
                product.vendor_id = vendor.vendor_id

        # Update category_id based on the selected category from the form
        category_id = request.form['category']
        if category_id:
            category = Category.query.filter_by(category_id=category_id).first()
            if category:
                product.category_id = category.category_id

        # Handle image deletion
        images_to_keep = request.form.getlist('keep_image[]')
        for image in product.images[:]:  # Use [:] to create a copy of the list
            if str(image.id) not in images_to_keep:
                # Remove image from Cloudinary
                cloudinary_id = image.image_url.split('/')[-1].split('.')[0]
                cloudinary.uploader.destroy(cloudinary_id)

                # Remove image from the database
                product.images.remove(image)
                db.session.delete(image)

        # Handle new image uploads
        if 'image' in request.files:
            files = request.files.getlist('image')
            for file in files:
                if file and allowed_file(file.filename):
                    # Upload the image to Cloudinary
                    upload_result = cloudinary.uploader.upload(file)
                    image_url = upload_result.get('secure_url')

                    # Create a new ProductImage entry
                    new_image = ProductImage(product_id=product.product_id, image_url=image_url)
                    db.session.add(new_image)

        try:
            db.session.commit()
            logging.info(f"Product updated Successfull\nProduct name: {product.name}\nDescription: {product.description}\nPrice: {product.price}\nStock: {product.stock}\n")
            flash("Product updated successfully!")
        except IntegrityError:
            db.session.rollback()
            flash("Error updating product. Please try again.")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}")

        return redirect(url_for('products', selected=selected))

    # GET request logic remains the same
    vendors = Vendor.query.all()
    categories = Category.query.all()
    return render_template('/admin/a-dashboard/updateproduct.html', product=product, selected=selected, vendors=vendors, categories=categories)

    



@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if email or password is empty
        if not email or not password:
            error_statement = "All fields are required!"
            logging.info(f"All fields are required! at {datetime.now()}")
            return render_template("/admin/a-dashboard/login.html", error_statement=error_statement)

        # Fetch the admin from the database using the email
        admin = Admin.query.filter_by(email=email).first()

        # If admin is not found, or password is incorrect
        if not admin or not password:# Assuming passwords are hashed
            error_statement = "Invalid email or password!"
            logging.info(f"Invalid email or password! at {datetime.now()}")
            return render_template("/admin/a-dashboard/login.html", error_statement=error_statement)

        

        if not admin or not bcrypt.checkpw(password.encode('utf-8'), admin.password.encode('utf-8')):
            flash("Invalid email or password!", "error")
            logging.info(f"Invalid email or password! at {datetime.now()}")
            return render_template("/admin/a-dashboard/login.html")

        # Store admin info in session
        session['admin_id'] = admin.admin_id
        session['admin_role'] = admin.role
        session['admin_username'] = admin.username

        # Redirect based on role
        role_redirects = {
            'superadmin': 'dashboard',
            'product_manager': 'products',
            'order_support': 'orders',
            'analyst': 'analytics'
        }
        logging.info(f"Admin logged in successfully of email {email} at {datetime.now()}")
        return redirect(url_for(role_redirects.get(admin.role, 'login')))

    # If it's a GET request, render the login page
    logging.info(f"Admin logged in successfully at {datetime.now()}")
    return render_template('/admin/a-dashboard/login.html')



@app.route('/manage_admins')
def manage_admins():
    selected = "Manage-Admins"
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    criteria = request.args.get('criteria', 'username')  # Default to 'username'

    # Base query
    query = Admin.query

    # Filter admins by search criteria and query if it exists
    if search_query:
        if criteria == "username":
            query = query.filter(Admin.username.ilike(f'%{search_query}%'))
        elif criteria == "email":
            query = query.filter(Admin.email.ilike(f'%{search_query}%'))
        elif criteria == "role":
            query = query.filter(Admin.role.ilike(f'%{search_query}%'))

    # Pagination
    admins_per_page = 8
    paginated_admins = query.paginate(page=page, per_page=admins_per_page, error_out=False)

    if not paginated_admins.items and page != 1:
        return redirect(url_for('manage_admins', page=1, search=search_query, criteria=criteria))

    return render_template('/admin/a-dashboard/manage_admins.html',
                           admins=paginated_admins.items,
                           selected=selected,
                           page=paginated_admins.page,
                           total_pages=paginated_admins.pages)





@app.route('/check_username_exists', methods=['GET'])
def check_username_exists():
    username = request.args.get('username')
    # Check if username exists in your database (pseudo-code here)
    exists = Admin.query.filter_by(username=username).first() is not None
    return jsonify({"exists": exists})


@app.route('/check_email_exists', methods=['GET'])
def check_email_exists():
    email = request.args.get('email', '')
    exists = Admin.query.filter_by(email=email).first() is not None
    return jsonify({'exists': exists})


@app.route('/add_admin', methods=['GET', 'POST'])
def add_admin():
    selected = "Add-Admin"
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']  # User entered password
        role = request.form['role']
        gender = request.form['gender']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        confpassword = request.form['confpassword']

        # Prevent adding another superadmin
        if role == 'superadmin':
            existing_superadmin = Admin.query.filter_by(role='superadmin').first()
            if existing_superadmin:
                error_message4 = "A superadmin already exists. Cannot add another superadmin."
                return render_template('/admin/a-dashboard/add_admin.html', selected=selected, error_message4=error_message4)

        if password != confpassword:
            mismatch_error = "Password does not match"
            return render_template('/admin/a-dashboard/add_admin.html', selected=selected, mismatch_error=mismatch_error)

        # Check if the email already exists in the database
        existing_admin = Admin.query.filter_by(email=email).first()
        existing_username = Admin.query.filter_by(username=username).first()

        if existing_admin and existing_username:
            error_message2 = "An account with this email address already exists"
            error_message3 = "Username already taken."
            return render_template('/admin/a-dashboard/add_admin.html', email=email, username=username, selected=selected, error_message2=error_message2, error_message3=error_message3)
        elif existing_admin:
            error_message2 = "An account with this email address already exists"
            return render_template('/admin/a-dashboard/add_admin.html', email=email, username=username, selected=selected, error_message2=error_message2)
        elif existing_username:
            error_message3 = "Username already taken."
            return render_template('/admin/a-dashboard/add_admin.html', email=email, username=username, selected=selected, error_message3=error_message3)

        # Hash the password before saving it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # If the role is not superadmin, assign the super_admin_id from the existing superadmin
        if role != 'superadmin':
            super_admin = Admin.query.filter_by(role='superadmin').first()  # Get the superadmin
            super_admin_id = super_admin.admin_id if super_admin else None  # Get superadmin's admin_id or set to None
        else:
            super_admin_id = None  # Superadmin does not have a super_admin_id

        # Create a new admin with hashed password and super_admin_id
        new_admin = Admin(username=username, email=email, password=hashed_password, role=role, 
                          first_name=first_name, last_name=last_name, gender=gender, super_admin_id=super_admin_id)
        db.session.add(new_admin)
        db.session.commit()

        flash("Admin added successfully!")
        return redirect(url_for('manage_admins'))
    
    return render_template('/admin/a-dashboard/add_admin.html', selected=selected, options=options)

# Route to delete an admin
@app.route('/delete_admin/<int:admin_id>')
def delete_admin(admin_id):
    current_admin_id = session.get('admin_id')  # Get the logged-in admin ID from the session
    admin_to_delete = Admin.query.get_or_404(admin_id)
     # Prevent deleting the superadmin
    if admin_to_delete.role == 'superadmin':
        flash("Cannot delete the superadmin.")
        return redirect(url_for('manage_admins'))
    
    # Prevent the superadmin from deleting themselves
    if admin_to_delete.admin_id == current_admin_id:
        flash("You cannot delete your own account.")
        return redirect(url_for('manage_admins'))  

    db.session.delete(admin_to_delete)
    db.session.commit()
    flash("Admin deleted successfully!")
    return redirect(url_for('manage_admins'))



# Route to edit an admin
@app.route('/edit_admin/<int:admin_id>', methods=['GET', 'POST'])
def edit_admin(admin_id):
    admin = Admin.query.get_or_404(admin_id)
    selected = "ManageAdmins"
    
    if request.method == 'POST':
        admin.username = request.form['username']
        admin.email = request.form['email']
        admin.role = request.form['role']
        admin.gender = request.form['gender']
        admin.first_name = request.form['first_name']
        admin.last_name = request.form['last_name']
        password = request.form['password']  # You should hash this
        confpassword = request.form['confpassword']
        currentpassword = request.form['currentpassword']
        if currentpassword:
            if currentpassword!=admin.password and password!=confpassword:
                mismatch_error2="Current password is incorrect"
                mismatch_error="Pasword doesnot match"
                return render_template('/admin/a-dashboard/edit_admin.html',admin=admin, selected=selected, confpassword=confpassword, mismatch_error2=mismatch_error2, mismatch_error=mismatch_error)
            elif currentpassword!=admin.password:
                mismatch_error2="Current password is incorrect"
                return render_template('/admin/a-dashboard/edit_admin.html',admin=admin, selected=selected, confpassword=confpassword, mismatch_error2=mismatch_error2)
            elif password!=confpassword:
                mismatch_error="Pasword doesnot match"
                return render_template('/admin/a-dashboard/edit_admin.html',admin=admin, selected=selected, confpassword=confpassword, mismatch_error=mismatch_error)


            # Hash the new password before saving it
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin.password = hashed_password
        
        db.session.commit()
        flash("Admin details updated successfully!")
        return redirect(url_for('manage_admins'))

    return render_template('/admin/a-dashboard/edit_admin.html', admin=admin, selected=selected)

@app.route('/cart')
def cart():
    user_id = session.get('user_id')
    if user_id:
        # Fetch the cart for the logged-in user
        cart = Cart.query.filter_by(user_id=user_id).first()
        if cart:
            cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
            items = []
            subtotal = 0
            total_items = sum(cart_item.quantity for cart_item in cart_items)
            
            for cart_item in cart_items:
                product = Product.query.get(cart_item.product_id)
                items.append({
                    'name': product.name,
                    'image_url': product.images[0].image_url if product.images else None,
                    'quantity': cart_item.quantity,
                    'price': product.price,
                    'product_id': product.product_id
                })
                subtotal += product.price * cart_item.quantity
                

            # Return the data as JSON
            return jsonify({"items": items, "subtotal": subtotal, "total_items":total_items})
        else:
            # Return an empty cart if no cart exists
            return jsonify({"items": [], "subtotal": 0})
    else:
        return redirect('/userlogin')

@app.route('/remove_item/<int:product_id>', methods=['POST'])
def remove_item(product_id):
    user_id = session.get('user_id')
    if user_id:
        # Get the user's cart
        cart = Cart.query.filter_by(user_id=user_id).first()
        
        if cart:
            # Find the cart item to remove
            cart_item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=product_id).first()
            
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()

                # Get updated cart items and subtotal after removal
                cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
                items = []
                subtotal = 0
                for cart_item in cart_items:
                    product = Product.query.get(cart_item.product_id)
                    items.append({
                        'name': product.name,
                        'image_url': product.images[0].image_url if product.images else None,
                        'quantity': cart_item.quantity,
                        'price': product.price,
                        'product_id': product.product_id
                    })
                    subtotal += product.price * cart_item.quantity
                total_items = sum(item.quantity for item in cart_items)    

                return jsonify({
                    "success": True,
                    "items": items,
                    "subtotal": subtotal,
                    "total_items": total_items
                })
        
        return jsonify({"success": False, "message": "Item not found or already removed."})
    return jsonify({"success": False, "message": "User not logged in."})



@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({"message": "You must be logged in to add items to the cart."}), 401

    user_id = session['user_id']
    product_id = request.json.get('product_id')

    # Validate quantity
    try:
        quantity = int(request.json.get('quantity', 1))  # Default to 1
        if quantity <= 0:
            return jsonify({"message": "Quantity must be greater than 0"}), 400
    except ValueError:
        return jsonify({"message": "Invalid quantity"}), 400

    # Check if product exists
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    # Check stock availability
    if product.stock < quantity:
        return jsonify({"message": f"Only {product.stock} units available"}), 400

    # Get or create the user's cart
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

    # Check if the product is already in the cart
    existing_item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=product_id).first()

    if existing_item:
        # Update quantity, ensuring it doesn't exceed stock
        if existing_item.quantity + quantity > product.stock:
            return jsonify({
                "message": f"Cannot add more than {product.stock - existing_item.quantity} units"
            }), 400
        existing_item.quantity += quantity
    else:
        # Add new item to the cart
        new_item = CartItem(cart_id=cart.cart_id, product_id=product_id, quantity=quantity)
        db.session.add(new_item)

    db.session.commit()

    # Get updated cart items and subtotal
    cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
    items = []
    subtotal = 0
    total_items = 0
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        items.append({
            'name': product.name,
            'image_url': product.images[0].image_url if product.images else None,
            'quantity': cart_item.quantity,
            'price': product.price,
            'product_id': product.product_id
        })
        subtotal += product.price * cart_item.quantity
        total_items += cart_item.quantity

    return jsonify({
        "message": "Item added to cart successfully!",
        "items": items,
        "subtotal": subtotal,
        "total_items": total_items
    })


@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    if 'user_id' not in session:
        return jsonify({"message": "You must be logged in to update the cart."}), 401

    user_id = session['user_id']
    product_id = request.json.get('product_id')
    try:
        quantity = int(request.json.get('quantity', 1))  # Ensure it's an integer
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid quantity"}), 400

    if not product_id:
        return jsonify({"message": "Product ID is required"}), 400

    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({"message": "Cart not found"}), 404

    cart_item = CartItem.query.filter_by(cart_id=cart.cart_id, product_id=product_id).first()
    if not cart_item:
        return jsonify({"message": "Item not found in cart"}), 404

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    if quantity > product.stock:
        return jsonify({"message": f"Only {product.stock} units available in stock."}), 400

    cart_item.quantity = quantity
    db.session.commit()
    total_items = sum(item.quantity for item in CartItem.query.filter_by(cart_id=cart.cart_id).all())
    # Recalculate subtotal
    cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
    subtotal = sum(Product.query.get(item.product_id).price * item.quantity for item in cart_items)

    return jsonify({
        "updated_quantity": cart_item.quantity,
        "subtotal": subtotal,
        "total_items": total_items
    })


"""@app.route('/checkout', methods=['GET'])
def checkout():
    user_id = session.get('user_id')  # Ensure the user is logged in
    if not user_id:
        return redirect('/userlogin')
    return render_template('checkout.html')  # Your checkout page template


@app.route('/checkout_summary', methods=['GET'])
def checkout_summary():
    user_id = session.get('user_id')  # Get the logged-in user's ID from session
    if not user_id:
        return redirect('/userlogin')

    # Fetch the user's cart
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({"items": [], "subtotal": 0, "shipping_fee": 0, "tax": 0, "total": 0})

    # Fetch cart items and their related product details
    cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
    items = []
    subtotal = 0

    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        if not product:
            continue
        item_total = product.price * cart_item.quantity
        items.append({
            'name': product.name,
            'image_url': product.images[0].image_url if product.images else None,
            'quantity': cart_item.quantity,
            'price': product.price,
            'item_total': item_total
        })
        subtotal += item_total

    # Calculate additional fees
    shipping_fee = 20.00  # Flat fee for simplicity
    tax = round(subtotal * 0.02, 2)  # 2% tax rate
    total = round(subtotal + tax + shipping_fee, 2)

    # Return the order summary data
    return jsonify({
        "items": items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "tax": tax,
        "total": total
    })"""

@app.route('/new_checkout', methods=['GET'])
def new_checkout():
    user_id = session.get('user_id')  # Ensure the user is logged in
    if not user_id:
        return redirect('/userlogin')

    # Fetch user's details
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return redirect('/userlogin')

    # Fetch user's saved addresses
    addresses = Address.query.filter_by(user_id=user_id).all()
    address_list = [{
        'address_id': address.address_id,
        'street': address.street,
        'city': address.city,
        'state': address.state,
        'postal_code': address.postal_code,
        'country': address.country
    } for address in addresses]

    return render_template('new_checkout.html', user=user, addresses=address_list, phone_number=user.phone_number)


@app.route('/get_order_summary', methods=['GET'])
def get_order_summary():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    # Fetch cart items
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({
            "items": [],
            "subtotal": 0,
            "shipping_fee": 0,
            "tax": 0,
            "total": 0
        })

    cart_items = CartItem.query.filter_by(cart_id=cart.cart_id).all()
    items = []
    subtotal = 0

    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        if not product:
            continue
        item_total = product.price * cart_item.quantity
        items.append({
            'name': product.name,
            'image_url': product.images[0].image_url if product.images else '/default_image.png',
            'quantity': cart_item.quantity,
            'price': product.price,
            'item_total': item_total
        })
        subtotal += item_total

    # Calculate shipping fee, tax, and total
    shipping_fee = 20.00  # Flat shipping fee
    tax = round(subtotal * 0.02, 2)  # 2% tax
    total = round(subtotal + shipping_fee + tax, 2)
    logging.info(f"items: {items} | subtotal: {subtotal} | shipping_fee: {shipping_fee} | tax: {tax} | total: {total}")
    return jsonify({
        "items": items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "tax": tax,
        "total": total
    })


@app.route('/confirm_order_details', methods=['GET'])
def confirm_order_details():
    order_details = session.get('personal_info')
    if not order_details:
        return jsonify({'error': 'No order details found'}), 400
    return jsonify(order_details)


@app.route('/save_personal_info', methods=['POST'])
def save_personal_info():
    session['personal_info'] = request.json
    return jsonify({'status': 'success'})

@app.route('/save_payment_info', methods=['POST'])
def save_payment_info():
    session['payment_info'] = request.json
    return jsonify({'status': 'success'})


import os
import sqlite3
@app.route('/place_order', methods=['POST'])
def place_order():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    try:
        # Connect to the database and set timeout
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the relative path
        db_path = os.path.join(base_dir, 'instance', 'your_database.db')
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout = 3000;")  # Set timeout for lock contention
        cursor = conn.cursor()

        # Start an exclusive transaction to prevent concurrent writes
        cursor.execute("BEGIN IMMEDIATE;")

                # Retrieve form data
        # Function to check if an address exists
        def get_existing_address_id(address):
            cursor.execute("""
                SELECT address_id
                FROM addresses
                WHERE user_id = ? AND street = ? AND city = ? AND state = ? AND postal_code = ? AND country = ?
            """, (user_id, address['street'], address['city'], address['state'], address['postal_code'], address['country']))
            result = cursor.fetchone()
            return result[0] if result else None

        # Function to insert an address if it does not exist
        def insert_address(address):
            existing_address_id = get_existing_address_id(address)
            if existing_address_id:
                return existing_address_id
            cursor.execute("""
                INSERT INTO addresses (user_id, street, city, state, postal_code, country, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (user_id, address['street'], address['city'], 
                address['state'], address['postal_code'], 
                address['country']))
            return cursor.lastrowid

        # Retrieve form data
        shipping_address = {
            'street': request.form['street'],
            'city': request.form['city'],
            'state': request.form['state'],
            'postal_code': request.form['postal_code'],
            'country': request.form['country']
        }

        if 'sameAsShipping' in request.form and request.form['sameAsShipping'] == 'true':
            billing_address = shipping_address
        else:
            billing_address = {
                'street': request.form['billing_street'],
                'city': request.form['billing_city'],
                'state': request.form['billing_state'],
                'postal_code': request.form['billing_postal_code'],
                'country': request.form['billing_country']
            }

        payment_method = request.form['payment_method']

        # Insert shipping and billing addresses if they do not exist
        shipping_address_id = insert_address(shipping_address)
        billing_address_id = shipping_address_id if shipping_address == billing_address else insert_address(billing_address)

        # Fetch cart items and ensure stock availability
        cursor.execute("""
            SELECT ci.product_id, ci.quantity, p.price, p.stock
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.product_id
            WHERE ci.cart_id = (SELECT cart_id FROM carts WHERE user_id = ?)
        """, (user_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            raise ValueError("Cart is empty.")

        subtotal = 0
        for product_id, quantity, price, stock in cart_items:
            if quantity > stock:
                raise ValueError(f"Insufficient stock for product_id {product_id}. Available: {stock}.")
            subtotal += quantity * price

        shipping_fee = 20.00
        tax = round(subtotal * 0.02, 2)
        total_price = round(subtotal + shipping_fee + tax, 2)

        # Insert order
        cursor.execute("""
            INSERT INTO orders (user_id, total_price, status, created_at, shipping_address_id, billing_address_id)
            VALUES (?, ?, 'pending', datetime('now'), ?, ?)
        """, (user_id, total_price, shipping_address_id, billing_address_id))
        order_id = cursor.lastrowid

        # Insert order items and atomically update product stock
        for product_id, quantity, price, stock in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase)
                VALUES (?, ?, ?, ?)
            """, (order_id, product_id, quantity, price))

            # Atomically update stock
            cursor.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE product_id = ? AND stock >= ?
            """, (quantity, product_id, quantity))

            # Ensure stock update was successful
            if cursor.rowcount == 0:
                raise ValueError(f"Stock conflict for product_id {product_id}.")

        # Insert payment record
        transaction_id = f"{payment_method.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        cursor.execute("""
            INSERT INTO payments (order_id, amount, payment_method, transaction_id, status, payment_date)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (order_id, total_price, payment_method, transaction_id,
              "Completed" if payment_method != "cash_on_delivery" else "Pending"))

        # Clear the cart
        cursor.execute("""
            DELETE FROM cart_items
            WHERE cart_id = (SELECT cart_id FROM carts WHERE user_id = ?)
        """, (user_id,))
        cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))

        # Commit the transaction
        conn.commit()

        user = User.query.filter(User.user_id == user_id).first()


        cursor.execute("""
            SELECT 
                oi.product_id, 
                p.name, 
                p.price, 
                oi.quantity, 
                (oi.quantity * p.price) AS total, 
                pi.image_url
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN product_images pi ON p.product_id = pi.product_id
            WHERE oi.order_id = ?
            GROUP BY oi.product_id
        """, (order_id,))
        ordered_products = cursor.fetchall()

        # Construct the products list for email data
        email_products = [
            {
                'name': product[1],  # p.name
                'quantity': product[3],  # oi.quantity
                'price': product[2],  # p.price
                'total': product[4],  # (oi.quantity * p.price)
                'image_url': product[5] or '/path/to/default-image.jpg'  # pi.image_url or fallback to a default
            }
            for product in ordered_products
        ]

        # Prepare the email data
        emaildata = {
            'order_id': order_id,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'shipping': shipping_address,  # Dictionary with keys: 'street', 'city', 'state', 'postal_code', 'country'
            'billing': billing_address,  # Same structure as shipping
            'products': email_products,  # List of enriched product dictionaries
            'subtotal': subtotal,
            'shipping_fee': shipping_fee,
            'order_total': total_price,
            'tax': tax,  # Add tax to the email data
            'payment_method': payment_method,
            'username': user.username,
        }

        try:
            # Send welcome email
            msg = MailMessage(
                subject=f'Order Confirmation - {order_id}',
                recipients=[user.email],
                html=render_template('receipt.html', **emaildata)
            )

            mail.send(msg)
        except Exception as e2:
            flash(f'An error occurred while sending the welcome email: {e}', 'error')
        logging.info(f"Order placed successfully\n order_id: {order_id}\n cart items: {cart_items}\n")
        return jsonify({'success': 'Order placed successfully', 'order_id': order_id})

    except Exception as e:
        # Rollback the transaction on error
        conn.rollback()
        return jsonify({'error': str(e)}), 400

    finally:
        conn.close()


@app.route('/order_confirmation', methods=['GET'])
def order_confirmation():
    order_details = session.get('order_details')
    
    if not order_details:
        return redirect('/')  # Redirect if no order details found

    return render_template('order_summary.html', order_details=order_details, payment_details={})

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    # Retrieve order details from session
    order_details = session.get('order_details')
    payment_details = session.get('payment_details')

    if not order_details or not payment_details:
        return redirect('/')

    # Save shipping and billing addresses
    shipping_address_entry = Address(
        user_id=user_id,
        **order_details['shipping_address'],
        created_at=datetime.utcnow()
    )
    db.session.add(shipping_address_entry)
    db.session.commit()

    billing_address_entry = Address(
        user_id=user_id,
        **order_details['billing_address'],
        created_at=datetime.utcnow()
    )
    db.session.add(billing_address_entry)
    db.session.commit()

    # Create the order
    new_order = Order(
        user_id=user_id,
        total_price=order_details['total_price'],  # Includes shipping fee and tax
        status='pending',
        created_at=datetime.utcnow(),
        shipping_address_id=shipping_address_entry.address_id,
        billing_address_id=billing_address_entry.address_id
    )
    db.session.add(new_order)
    db.session.commit()

    # Add order items
    for item in order_details['items']:
        order_item = OrderItem(
            order_id=new_order.order_id,
            product_id=Product.query.filter_by(name=item['name']).first().product_id,
            quantity=item['quantity'],
            price_at_purchase=item['price']
        )
        db.session.add(order_item)

        # Update product stock
        product = Product.query.filter_by(name=item['name']).first()
        product.stock -= item['quantity']
    db.session.commit()

    # Generate payment transaction ID
    transaction_id = f"{payment_details['payment_method'].upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    payment_details.update({
        "transaction_id": transaction_id,
        "status": "Completed" if payment_details['payment_method'] != "cash_on_delivery" else "Pending"
    })

    # Save payment information
    payment_entry = Payment(
        order_id=new_order.order_id,
        amount=order_details['total_price'],  # Includes shipping fee and tax
        payment_method=payment_details['payment_method'],
        transaction_id=transaction_id,
        status=payment_details['status'],
        payment_date=datetime.utcnow()
    )
    db.session.add(payment_entry)
    db.session.commit()

    # Clear cart and session
    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart:
        CartItem.query.filter_by(cart_id=cart.cart_id).delete()
        db.session.delete(cart)
    db.session.commit()

    session.pop('order_details', None)
    session.pop('payment_details', None)

    return render_template('order_success.html')


@app.route('/order_success')
def order_success():
    order_id = request.args.get('order_id')
    # Query database to fetch order details if needed
    return render_template('order_success.html', order_id=order_id)






        ########################################################################################################################
        ########################################################################################################################
        ################################################################ NEW CHANGES ###########################################
        ########################################################################################################################
        ########################################################################################################################

@app.route('/orders')
def orders():
    selected = "Orders"
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    criteria = request.args.get('criteria', 'status')  # Default to 'status'

    #Base query
    #query = Order.query.outerjoin(Order.order_items)
     # Aliases for shipping and billing addresses
    shipping_address = aliased(Address)
    billing_address = aliased(Address)

    # Base query with aliased joins
    query = (
    db.session.query(
        Order,
        shipping_address.street.label("shipping_street"),
        shipping_address.city.label("shipping_city"),
        shipping_address.state.label("shipping_state"),
        shipping_address.country.label("shipping_country"),
        shipping_address.postal_code.label("shipping_postal_code"),
        billing_address.street.label("billing_street"),
        billing_address.city.label("billing_city"),
        billing_address.state.label("billing_state"),
        billing_address.country.label("billing_country"),
        billing_address.postal_code.label("billing_postal_code"),
    )
    .join(shipping_address, Order.shipping_address_id == shipping_address.address_id)
    .join(billing_address, Order.billing_address_id == billing_address.address_id)
)
    # Filter orders by search criteria and query if it exists
    if search_query:
        if criteria == "status":
            query = query.filter(Order.status.ilike(f'%{search_query}%'))
        elif criteria == "user_id":
            query = query.filter(Order.user_id == int(search_query))
        elif criteria == "order_id":
            query = query.filter(Order.order_id == int(search_query))
            
    query = query.order_by(Order.created_at.desc())
    # Pagination
    per_page = 8
    orderdata = query.paginate(page=page, per_page=per_page, error_out=False)

    # Debug: Print order details
    '''for order in orderdata.items:
        print(f"Order ID: {order.order_id}, Status: {order.status}, Total Price: {order.total_price}")
        for item in order.order_items:
            print(f"  Product ID: {item.product_id}, Quantity: {item.quantity}, Price at Purchase: {item.price_at_purchase}")
'''
    return render_template('/admin/a-dashboard/orders.html', orderdata=orderdata, selected=selected)



@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    data = request.get_json()
    new_status = data.get('status')

    try:
        # Update the status in the database
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'})

        order.status = new_status
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})



@app.route('/admincategories')
def admincategories():
    selected = "Categories"
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    criteria = request.args.get('criteria', 'name')  # Default to 'name'

    # Base query
    query = Category.query

    # Filter categories by search criteria if it exists
    if search_query:
        if criteria == "name":
            query = query.filter(Category.name.ilike(f'%{search_query}%'))
        elif criteria == "description":
            query = query.filter(Category.description.ilike(f'%{search_query}%'))

    # Pagination
    per_page = 8
    categorydata = query.paginate(page=page, per_page=per_page, error_out=False)

    # Debug: Print category details
    for category in categorydata.items:
        print(f"Category ID: {category.category_id}, Name: {category.name}, Description: {category.description}")

    return render_template('/admin/a-dashboard/categories.html', categorydata=categorydata, selected=selected)


@app.route('/addcategory', methods=['GET', 'POST'])
def addcategory():
    selected = "Add-Category"

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        # Validate input
        if not name or not description:
            return "Name and description are required", 400

        # Check if the category already exists
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            return "Category with this name already exists", 400

        # Create a new category
        new_category = Category(
            name=name,
            description=description
        )

        try:
            # Add the new category to the database
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('admincategories'))  # Redirect to the categories list
        except IntegrityError as ie:
            db.session.rollback()
            return f"IntegrityError: {str(ie)}"
        except Exception as e:
            db.session.rollback()
            return f"Exception: {str(e)}"

    return render_template('/admin/a-dashboard/addcategory.html', selected=selected)


@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    # Retrieve the product by its ID from the database
    category = Category.query.get_or_404(category_id)
    
    # Delete related images manually if necessary
    
    db.session.delete(category)  # Delete the product
    db.session.commit()  # Commit the transaction to the database
    
    # Redirect back to the products page
    return redirect(url_for('admincategories'))


@app.route('/updatecategory/<int:category_id>', methods=['GET', 'POST'])
def updatecategory(category_id):
    selected = "Categories"
    category = Category.query.get_or_404(category_id)  # Fetch the category or return 404

    if request.method == 'POST':
        # Get the form data
        name = request.form.get('name')
        description = request.form.get('description')

        # Validation: Check if the name is empty
        if not name:
            return jsonify({
                "status": "error",
                "message": "Category name cannot be empty."
            }), 400

        # Check for duplicate category name
        existing_category = Category.query.filter(
            Category.name == name,
            Category.category_id != category_id
        ).first()
        if existing_category:
            return jsonify({
                "status": "error",
                "message": "A category with this name already exists."
            }), 400

        try:
            # Update category details
            category.name = name
            category.description = description
            db.session.commit()

            # Return success response
            return jsonify({
                "status": "success",
                "message": "Category updated successfully.",
                "category": {
                    "category_id": category.category_id,
                    "name": category.name,
                    "description": category.description
                }
            })

        except IntegrityError:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Database error occurred. Please try again."
            }), 500

        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }), 500

    # Render the update form for GET requests
    return render_template('/admin/a-dashboard/updatecategory.html', category=category, selected=selected)


@app.route('/vendors')
def vendors():
    selected = "Vendors"
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    criteria = request.args.get('criteria', 'name')  # Default to 'name'

    # Base query
    query = Vendor.query

    # Filter vendors by search criteria if it exists
    if search_query:
        if criteria == "name":
            query = query.filter(Vendor.name.ilike(f'%{search_query}%'))
        elif criteria == "contact_email":
            query = query.filter(Vendor.contact_email.ilike(f'%{search_query}%'))
        elif criteria == "phone_number":
            query = query.filter(Vendor.phone_number.ilike(f'%{search_query}%'))
        elif criteria == "address":
            query = query.filter(Vendor.address.ilike(f'%{search_query}%'))

    # Pagination
    per_page = 8
    vendordata = query.paginate(page=page, per_page=per_page, error_out=False)

    # Debug: Print vendor details
    for vendor in vendordata.items:
        print(f"Vendor ID: {vendor.vendor_id}, Name: {vendor.name}, Email: {vendor.contact_email}, Phone: {vendor.phone_number}, Address: {vendor.address}")

    return render_template('/admin/a-dashboard/vendors.html', vendordata=vendordata, selected=selected)


@app.route('/addvendor', methods=['GET', 'POST'])
def addvendor():
    selected = "Add-Vendor"

    if request.method == 'POST':
        # Use the correct field names as per the HTML
        name = request.form.get('name')
        contact_email = request.form.get('contact_email')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')

        # Validate input
        if not name or not contact_email or not phone_number or not address:
            return "All fields are required", 400
        
        if not phone_number.isdigit() or len(phone_number) != 11:
            return jsonify({
                "status": "error",
                "message": "Phone number must be exactly 11 digits and numeric."
            }), 400
        
        # Check if the vendor already exists
        existing_vendor = Vendor.query.filter_by(name=name).first()
        if existing_vendor:
            return "Vendor with this name already exists", 400

        # Create a new vendor
        new_vendor = Vendor(
            name=name,
            contact_email=contact_email,
            phone_number=phone_number,
            address=address
        )

        try:
            # Add the new vendor to the database
            db.session.add(new_vendor)
            db.session.commit()
            return redirect(url_for('vendors'))  # Redirect to the vendors list
        except IntegrityError as ie:
            db.session.rollback()
            return f"IntegrityError: {str(ie)}"
        except Exception as e:
            db.session.rollback()
            return f"Exception: {str(e)}"

    return render_template('/admin/a-dashboard/addvendor.html', selected=selected)


@app.route('/delete_vendor/<int:vendor_id>', methods=['POST'])
def delete_vendor(vendor_id):
    # Retrieve the vendor by its ID from the database
    vendor = Vendor.query.get_or_404(vendor_id)
    
    try:
        db.session.delete(vendor)  # Delete the vendor
        db.session.commit()  # Commit the transaction to the database
        return redirect(url_for('vendors'))
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"
    

@app.route('/updatevendor/<int:vendor_id>', methods=['GET', 'POST']) 
def updatevendor(vendor_id):
    selected = "Vendors"
    vendor = Vendor.query.get_or_404(vendor_id)

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        contact_email = request.form.get('contact_email')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')

        # Validation: Check if the name is empty
        if not name:
            return jsonify({
                "status": "error",
                "message": "Vendor name cannot be empty."
            }), 400

        # Validate phone number
        if not phone_number.isdigit() or len(phone_number) != 11:
            return jsonify({
                "status": "error",
                "message": "Phone number must be exactly 11 digits and numeric."
            }), 400

        # Check for duplicate vendor
        existing_vendor = Vendor.query.filter(Vendor.name == name, Vendor.vendor_id != vendor_id).first()
        if existing_vendor:
            return jsonify({
                "status": "error",
                "message": "A vendor with this name already exists."
            }), 400

        # Update vendor details
        vendor.name = name
        vendor.contact_email = contact_email
        vendor.phone_number = phone_number
        vendor.address = address
        db.session.commit()

        return redirect(url_for('vendors'))  # Redirect to the vendors page

    return render_template('/admin/a-dashboard/updatevendor.html', vendor=vendor, selected=selected)




@app.context_processor
def inject_user():
    return {'username': session.get('username')}


@app.route('/user-settings', methods=['GET'])
def user_settings():
    user_id = session.get('user_id')  # Assume user_id is stored in session
    if not user_id:
        return "User not logged in", 401

    # Fetch user data
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    # Fetch wishlist items with product details using a join
    wishlist_items = db.session.query(
        WishlistItem,
        Product
    ).join(Product, WishlistItem.product_id == Product.product_id).join(
        Wishlist, WishlistItem.wishlist_id == Wishlist.wishlist_id
    ).filter(Wishlist.user_id == user_id).all()

    # Fetch order history
    orders = Order.query.filter_by(user_id=user_id).options(
        joinedload(Order.order_items).joinedload(OrderItem.product)
    ).all()

    return render_template(
        'user-settings.html',
        user=user,
        wishlist_items=wishlist_items,
        orders=orders
    )

@app.route('/customer-dashboard-base', methods=['GET'])
def userdashboardbase():
    selected="dashboard"
    
    return render_template('/customer/c-dashboard/user-dashboard-base.html',selected=selected)

@app.route('/customer-info', methods=['GET', 'POST'])
def customerinfo():
    user_id = session.get('user_id')  # Assume user_id is stored in session
    if not user_id:
        return "User not logged in", 401

    user = User.query.get_or_404(user_id)
    selected = "User Details"
    
    if request.method == 'POST':
        # Collect form data
        user.username = request.form['username']
        user.email = request.form['email']
        user.gender = request.form['gender']
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.phone_number = request.form['phone_number']
        current_password = request.form['currentpassword']
        new_password = request.form['password']
        confirm_password = request.form['confpassword']
        session['username'] = user.username
        if user:
            first_name = user.first_name if user.first_name else " "
            last_name = user.last_name if user.last_name else " "
            session['fullname'] = first_name + " " + last_name
        else:
            session['fullname'] = "Unknown"  # Handle case where user does not exist
        if current_password:
            # Validate current password
            if not bcrypt.checkpw(current_password.encode('utf-8'), user.password):
                mismatch_error2 = "Current password is incorrect."
                return render_template(
                    '/customer/c-dashboard/user-details.html',
                    user=user,
                    selected=selected,
                    mismatch_error2=mismatch_error2
                )

            # Check if new passwords match
            if new_password != confirm_password:
                mismatch_error = "Passwords do not match."
                return render_template(
                    '/customer/c-dashboard/user-details.html',
                    user=user,
                    selected=selected,
                    mismatch_error=mismatch_error
                )

            # Hash and save the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user.password = hashed_password.decode('utf-8')
        db.session.commit()
        flash("User details updated successfully!")
        logging.info(f"User details updated successfully! {datetime.now()}")
        return redirect(url_for('customerinfo'))

    return render_template('/customer/c-dashboard/user-details.html', user=user, selected=selected)



@app.route('/wishlist', methods=['GET'])
def wishlist():
    selected = "wishlist"
    user_id = session.get('user_id')  # Assume user_id is stored in session
    if not user_id:
        return "User not logged in", 401

    # Subquery to get the first image for each product
    first_image_subquery = db.session.query(
        ProductImage.product_id, 
        db.func.min(ProductImage.id).label('first_image_id')
    ).group_by(ProductImage.product_id).subquery()

    # Join WishlistItem, Product, and the first image of each product
    wishlist_items = db.session.query(
        WishlistItem,
        Product,
        ProductImage
    ).join(
        Wishlist, Wishlist.wishlist_id == WishlistItem.wishlist_id
    ).join(
        Product, Product.product_id == WishlistItem.product_id
    ).outerjoin(
        first_image_subquery, Product.product_id == first_image_subquery.c.product_id
    ).outerjoin(
        ProductImage, ProductImage.id == first_image_subquery.c.first_image_id
    ).filter(
        Wishlist.user_id == user_id
    ).all()

    return render_template('/customer/c-dashboard/user-wishlist.html', selected=selected, wishlist_items=wishlist_items)



@app.route('/delete_wishlist_item/<int:product_id>', methods=['POST'])
def delete_wishlist_item(product_id):
    user_id = session.get('user_id')  # Get user_id from session
    if not user_id:
        return "User not logged in", 401

    # Fetch the wishlist item by joining Wishlist and WishlistItem
    wishlist_item = db.session.query(WishlistItem).join(Wishlist).filter(
        Wishlist.user_id == user_id,
        WishlistItem.product_id == product_id
    ).first()

    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        return '', 200
    return 'Item not found', 404



from datetime import datetime
@app.route('/customer-dashboard', methods=['GET'])
def userdashboard():
    user_id = session.get('user_id')  # Assume user_id is stored in session
    if not user_id:
        return "User not logged in", 401
    
    # Fetch user data
    user = User.query.get(user_id)
    if user:
            first_name = user.first_name if user.first_name else " "
            last_name = user.last_name if user.last_name else " "
            session['fullname'] = first_name + " " + last_name
    else:
            session['fullname'] = "Unknown"  # Handle case where user does not exist
    if not user:
        return "User not found", 404
    
    # Aliases for shipping and billing addresses
    shipping_address = aliased(Address)
    billing_address = aliased(Address)

    # Fetch the six most recent orders for the user
    query = (
        db.session.query(
            Order,
            shipping_address.street.label("shipping_street"),
            shipping_address.city.label("shipping_city"),
            shipping_address.state.label("shipping_state"),
            shipping_address.country.label("shipping_country"),
            shipping_address.postal_code.label("shipping_postal_code"),
            billing_address.street.label("billing_street"),
            billing_address.city.label("billing_city"),
            billing_address.state.label("billing_state"),
            billing_address.country.label("billing_country"),
            billing_address.postal_code.label("billing_postal_code"),
        )
        .join(shipping_address, Order.shipping_address_id == shipping_address.address_id)
        .join(billing_address, Order.billing_address_id == billing_address.address_id)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())  # Order by most recent
        .limit(6)  # Limit to the 6 most recent orders
    )

    recent_orders = query.all()

    current_date = datetime.utcnow().strftime('%Y-%m-%d')  # Format as YYYY-MM-DD

    selected="dashboard"
    return render_template('/customer/c-dashboard/user-dashboard.html'
                           ,selected=selected,current_date=current_date,recent_orders=recent_orders,user=user)

@app.route('/customer-orders', methods=['GET'])
def customerorders():
    selected="Orders"
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    page = request.args.get('page', 1, type=int)
    per_page = 8

    shipping_address = aliased(Address)
    billing_address = aliased(Address)

    base_query = db.session.query(
        Order,
        shipping_address.street.label("shipping_street"),
        shipping_address.city.label("shipping_city"),
        shipping_address.state.label("shipping_state"),
        shipping_address.country.label("shipping_country"),
        shipping_address.postal_code.label("shipping_postal_code"),
        billing_address.street.label("billing_street"),
        billing_address.city.label("billing_city"),
        billing_address.state.label("billing_state"),
        billing_address.country.label("billing_country"),
        billing_address.postal_code.label("billing_postal_code"),
    ).join(
        shipping_address, Order.shipping_address_id == shipping_address.address_id
    ).join(
        billing_address, Order.billing_address_id == billing_address.address_id
    ).filter(
        Order.user_id == user_id
    )

    orderdata = base_query.paginate(page=page, per_page=per_page, error_out=False)
    order_pending = base_query.filter(Order.status.in_(['pending', 'Pending'])).all()
    order_delivered = base_query.filter(Order.status.in_(['completed', 'Completed'])).all()
    order_shipped= base_query.filter(Order.status.in_(['shipped','Shipped'])).all

    # Render the template with the order data
    return render_template('/customer/c-dashboard/user-dashboard-orders.html',orderdata=orderdata,
        order_pending=order_pending,
        order_delivered=order_delivered,
        selected= selected
        #order_shipped=order_shipped
        )




@app.route('/my_reviews', methods=['GET'])
def my_reviews():
    selected = "Reviews"
    user_id = session.get('user_id')  # Safely fetch user_id from session
    if not user_id:
        return redirect('/login')  # Redirect to login if the user is not authenticated

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 8

    # Join `products`, `orders`, and `order_items` on relevant keys
    
    query = (
    db.session.query(
        Review.review_id,
        Review.rating.label('product_review'),
        Review.review_text.label('product_review_text'),
        Product.product_id,
        Product.name.label('product_name'),
        Product.description.label('product_description'),
    )
    .join(Product, Review.product_id == Product.product_id)  # Join Review with Product
    .filter(Review.user_id == session.get('user_id'))  # Filter by the logged-in user
)
    orderdata = query.paginate(page=page, per_page=per_page, error_out=False)

    
    query2 = (
        db.session.query(
            OrderItem.order_item_id,
            OrderItem.quantity,
            OrderItem.order_id,
            OrderItem.price_at_purchase,
            Order.status,
            Product.product_id,  # Include the product_id here
            Product.name.label('product_name'),
            Product.description.label('product_description'),
            ProductImage.image_url.label('product_image')
        )
        .join(Order, Order.order_id == OrderItem.order_id)
        .join(Product, Product.product_id == OrderItem.product_id)
        .outerjoin(ProductImage, ProductImage.product_id == Product.product_id)
        .outerjoin(Review, Review.product_id == Product.product_id)
        .filter(Order.user_id == user_id)  # Filter by the logged-in user's ID
        .filter(Review.user_id == None)  # Exclude items that already have a review by the user
        .filter(Order.status.in_(['completed', 'Completed']))
        .group_by(OrderItem.order_item_id) 
    )
    return render_template('/customer/c-dashboard/my_reviews.html',selected=selected, orderdata=orderdata, orderdata2=query2)


@app.route('/add_reviews/<int:product_id>', methods=['GET', 'POST'])
def add_reviews(product_id):
    selected = "Reviews"
    user_id = session.get('user_id')  # Ensure the user is logged in.
    if not user_id:
        return redirect('/login')  # Redirect to login page if not authenticated

    message = None  # Initialize a message variable to pass to the template

    if request.method == 'POST':
        # Retrieve form data
        review_text = request.form.get('review_text')
        rating = request.form.get('rating')

        # Validate form inputs
        if not review_text or not rating:
            message = "All fields are required."
        else:
            try:
                # Ensure the product exists
                product = db.session.query(Product).filter_by(product_id=product_id).first()
                if not product:
                    message = "Invalid product ID."
                else:
                    # Save review to the database
                    new_review = Review(
                        user_id=user_id,
                        product_id=product_id,
                        rating=int(rating),
                        review_text=review_text,
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(new_review)
                    db.session.commit()

                    # Redirect to 'my_reviews' page on success
                    return redirect(url_for('my_reviews'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error submitting review: {e}")
                message = "An error occurred while submitting your review."

    # Render the form with an optional error/success message
    return render_template(
        '/customer/c-dashboard/add_reviews.html',
        selected=selected,
        product_id=product_id,
        message=message
    )




@app.route('/customer-items', methods=['GET'])
def customeritems():
    selected = "Received-Orders"
    user_id = session.get('user_id')  # Fetch user_id from session

    if not user_id:
        # Redirect to login if user not found
        return redirect('/login')

    # Define the SQL query to get returnable items along with request status
    query = """
        SELECT 
            oi.order_item_id, 
            p.name AS product_name, 
            pi.image_url AS product_image, 
            oi.price_at_purchase, 
            julianday('now') - julianday(o.created_at) AS days_since_received,
            rr.return_id IS NOT NULL AS already_requested
        FROM 
            order_items oi
        INNER JOIN 
            orders o ON oi.order_id = o.order_id
        INNER JOIN 
            products p ON oi.product_id = p.product_id
        LEFT JOIN 
            product_images pi ON p.product_id = pi.product_id
        LEFT JOIN 
            return_requests rr ON oi.order_item_id = rr.order_item_id AND rr.user_id = ?
        WHERE 
            o.user_id = ? AND 
            o.status = 'Completed' AND 
            julianday('now') - julianday(o.created_at) <= 7
    """

    # Connect to the database
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'instance', 'your_database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Use Row factory for dict-like access
    cursor = conn.cursor()

    try:
        # Execute the query with the user_id
        cursor.execute(query, (user_id, user_id))
        rows = cursor.fetchall()
        # Prepare the list of eligible items
        eligible_items = [
            {
                'order_item_id': row['order_item_id'],
                'product_name': row['product_name'],
                'product_image': row['product_image'],
                'price': row['price_at_purchase'],
                'days_remaining': 7 - int(row['days_since_received']),
                'already_requested': bool(row['already_requested']),  # Check if return request exists
            }
            for row in rows
        ]

    finally:
        conn.close()

    # Render the template with the eligible items
    return render_template('/customer/c-dashboard/user-items-received.html', items=eligible_items, selected=selected)

@app.route('/order_details/<int:order_id>', methods=['GET'])
def order_details(order_id):
    selected="Orders"
    # Ensure the user is logged in
    if 'user_id' not in session:
        return render_template('error.html', message="User not logged in"), 401

    user_id = session['user_id']

    # Fetch the order and items from the database
    order = db.session.query(Order).filter_by(order_id=order_id, user_id=user_id).first()
    if not order:
        return render_template('error.html', message="Order not found or access denied"), 404

    # Retrieve the order items and build the structure
    order_items = [
        {
            "product_name": item.product_name,
            "quantity": item.quantity,
            "price_at_purchase": item.price_at_purchase,
        }
        for item in db.session.query(
            OrderItem.quantity,
            OrderItem.price_at_purchase,
            Product.name.label("product_name")
        )
        .join(Product, Product.product_id == OrderItem.product_id)
        .filter(OrderItem.order_id == order_id)
        .all()
    ]

    # Construct the order details dictionary
    order_details = {
        "order_id": order.order_id,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": order.total_price,
        "status": order.status,
        "order_items": order_items,  # Renamed from `items` to `order_items`
    }


    
    # Pass the dictionary to the template
    return render_template('/customer/c-dashboard/user-order-details.html',selected=selected, order_details=order_details)

@app.route('/admin_order_details/<int:order_id>', methods=['GET'])
def order_detailsa(order_id):
    selected="Orders"
    # Ensure the user is logged in
    if 'user_id' not in session:
        return render_template('error.html', message="User not logged in"), 401

    user_id = session['user_id']

    # Fetch the order and items from the database
    order = db.session.query(Order).filter_by(order_id=order_id).first()
    if not order:
        return render_template('error.html', message="Order not found or access denied"), 404

    # Retrieve the order items and build the structure
    order_items = [
        {
            "product_name": item.product_name,
            "quantity": item.quantity,
            "price_at_purchase": item.price_at_purchase,
        }
        for item in db.session.query(
            OrderItem.quantity,
            OrderItem.price_at_purchase,
            Product.name.label("product_name")
        )
        .join(Product, Product.product_id == OrderItem.product_id)
        .filter(OrderItem.order_id == order_id)
        .all()
    ]

    # Construct the order details dictionary
    order_details = {
        "order_id": order.order_id,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": order.total_price,
        "status": order.status,
        "order_items": order_items,  # Renamed from `items` to `order_items`
    }


    
    # Pass the dictionary to the template
    return render_template('/admin/a-dashboard/admin-order-details.html',selected=selected, order_details=order_details)




@app.route('/add_address', methods=['POST'])
def add_address():
    

    if 'user_id' not in session:
        return render_template('error.html', message="User not logged in"), 401

    user_id = session['user_id']

    street = request.form['street']
    city = request.form['city']
    state = request.form['state']
    country = request.form['country']
    postal_code = request.form['postal_code']
    

    new_address = Address(
        user_id=user_id,
        street=street,
        city=city,
        state=state,
        country=country,
        postal_code=postal_code
    )
    db.session.add(new_address)
    db.session.commit()

    flash('Address added successfully!', 'success')
    return redirect(url_for('customer_address'))

@app.route('/address/<int:address_id>/edit', methods=['GET'])
def edit_address(address_id):
    address = Address.query.get_or_404(address_id)
    # Return the address details as JSON for the frontend to populate the form
    return jsonify({
        'address_id': address.address_id,
        'street': address.street,
        'city': address.city,
        'state': address.state,
        'country': address.country,
        'postal_code': address.postal_code
    })

@app.route('/update_address', methods=['POST'])
def update_address():
    address_id = request.form['address_id']
    address = Address.query.get_or_404(address_id)

    address.street = request.form['street']
    address.city = request.form['city']
    address.state = request.form['state']
    address.country = request.form['country']
    address.postal_code = request.form['postal_code']

    db.session.commit()

    flash('Address updated successfully!', 'success')
    return redirect(url_for('customer_address'))

@app.route('/address/<int:address_id>/delete', methods=['GET'])
def delete_address(address_id):
    address = Address.query.get_or_404(address_id)
    db.session.delete(address)
    db.session.commit()

    flash('Address deleted successfully!', 'success')
    return redirect(url_for('customer_address'))

@app.route('/customer_address', methods=['GET'])
def customer_address():
    if 'user_id' not in session:
        return render_template('error.html', message="User not logged in"), 401

    user_id = session['user_id']
    selected="Adresses"
    # Get the currently logged-in user
     # Assuming `current_user` is available and represents the logged-in user

    # Query to fetch all addresses of the user
    addresses = Address.query.filter_by(user_id=user_id).all()

    # Pass the addresses to the template
    return render_template('/customer/c-dashboard/user-address.html', addresses=addresses,selected=selected)




#--------------------------------------------------------- chat start ------------------------------------------
# Messages
@app.route('/messages')
def messages():
    page = request.args.get('page', 1, type=int)  # Get current page number
    per_page = 10  # Set items per page

    # Replace this query with your actual ORM query
    chat_query = (
        db.session.query(Chat, User.username)
        .join(User, Chat.user_id == User.user_id)  # Join with User table
        .order_by(Chat.closed_at.desc().nullslast())  # Order by recent messages
    )

    # Paginate the joined query
    chat_rooms = chat_query.paginate(page=page, per_page=per_page)

    selected = "Messages"
    return render_template('/admin/a-dashboard/messages.html', chat_rooms=chat_rooms, selected=selected)

@app.route("/get_chat_room", methods=["POST"])
def get_chat_room():
    user_id = session['user_id']

    # Check if a chat room exists for the user
    chat_room = Chat.query.filter_by(user_id=user_id).first()
    if not chat_room:
        # Create a new chat room
        chat_room = Chat(user_id=user_id,status='seen')
        db.session.add(chat_room)
        db.session.commit()

    return jsonify({"chat_room_id": chat_room.chat_id, "user_id":user_id})

@app.route("/save_message", methods=["POST"])
def save_message():
    data = request.get_json()

    # Validate the data
    chat_room_id = data.get("chat_room_id")
    sender_type = data.get("sender_type")  # 'user' or 'admin'
    message = data.get("message")
    sender_id=data.get("user_id")

    if not chat_room_id or not sender_type or not message:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    try:
        # Save the message in the database
        new_message = Message(chat_id=chat_room_id, sender_type=sender_type, sender_id=sender_id, message_text=message)
        db.session.add(new_message)
        db.session.commit()

        chat_room = Chat.query.get(chat_room_id)
        if chat_room:
            chat_room.closed_at = datetime.utcnow()  # Update to current time
            chat_room.status='unseen'
            db.session.commit()

        return jsonify({"success": True, "message_id": new_message.message_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    


@app.route("/get_messages", methods=["GET"])
def get_messages():
    user_id = session['user_id']  # Get the user ID from the session
    chat_room = Chat.query.filter_by(user_id=user_id).first()
    closed_at = request.args.get("closed_at")  # Fetch the last timestamp

    if not chat_room:
        return jsonify({"success": False, "error": "No chat room found"}), 404

    query = Message.query.filter_by(chat_id=chat_room.chat_id).order_by(Message.timestamp)

    if closed_at:
        query = query.filter(Message.timestamp > closed_at)  # Fetch only new messages

    messages = query.all()
    messages_data = [
        {
            "message": msg.message_text,
            "sender_type": msg.sender_type,
            "timestamp": msg.timestamp.isoformat(),
        }
        for msg in messages
    ]

    return jsonify({"success": True, "messages": messages_data})



@app.route("/get_all_chat_rooms", methods=["GET"])
def get_all_chat_rooms():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page
    rooms = Chat.query.all()
    data = [{"chat_room_id": room.chat_id, "user_id": room.user_id} for room in rooms]
    return jsonify({"rooms": data})

@app.route("/get_adminmessages", methods=["GET"])
def get_adminmessages():
    chat_id = request.args.get("chat_id", type=int)
    closed_at = request.args.get("closed_at")  # Timestamp of the last message seen by the client

    if not chat_id:
        return jsonify({"success": False, "error": "Room ID is required"}), 400

    query = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp)
    
    if closed_at:
        query = query.filter(Message.timestamp > closed_at)
    
    chat = Chat.query.get(chat_id)
    chat.status = 'seen'
    db.session.commit()
    messages = query.all()

    messages_data = [
        {
            "message": msg.message_text,
            "sender_type": msg.sender_type,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ]

    return jsonify({"success": True, "messages": messages_data})


@app.route("/send_message", methods=["POST"])
def save_adminmessage():
    data = request.get_json()

    admin_id = session.get("admin_id")
    chat_room_id = data.get("room_id")
    sender_type = 'admin'
    message = data.get("message_text")

    if not chat_room_id or not sender_type or not message:
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    try:
        new_message = Message(
            chat_id=chat_room_id,
            sender_type=sender_type,
            sender_id=admin_id,
            message_text=message
        )
        db.session.add(new_message)
        db.session.commit()

        return jsonify({"success": True, "message_id": new_message.message_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
#---------------------------------------------------chat end ----------------------------------------------------


@app.route('/submit_return_request/<int:order_item_id>', methods=['GET', 'POST'])
def submit_return_request(order_item_id):
    order_item = OrderItem.query.get_or_404(order_item_id)
    user_id = session['user_id']  # Fetch user_id from session

    # Check if the order item belongs to the logged-in user
    if order_item.order.user_id != user_id:
        flash("Unauthorized access to this order item.", "danger")
        return redirect(url_for('returnable_items'))

    if request.method == 'POST':
        reason = request.form['reason']
        return_request = ReturnRequest(
            user_id=user_id,
            order_item_id=order_item_id,
            reason=reason,
            status='pending',
            created_at=datetime.utcnow(),
        )
        db.session.add(return_request)
        db.session.commit()
        flash('Return request submitted successfully.', 'success')
        return redirect(url_for('view_return_requests'))

    return render_template('/customer/c-dashboard/submit_return_request.html', item=order_item)

@app.route('/view_return_requests')
def view_return_requests():
    selected = "view_return_requests"
    user_id = session['user_id']  # Fetch user_id from session
    return_requests = ReturnRequest.query.options(joinedload(ReturnRequest.order_item)).filter_by(user_id=user_id).all()

    requests_data = [{
        'product_name': req.order_item.product.name,
        'product_image': req.order_item.product.images[0].image_url if req.order_item.product.images else None,
        'price': req.order_item.price_at_purchase,
        'reason': req.reason,
        'status': req.status,
        'requested_at': req.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for req in return_requests]

    return render_template('/customer/c-dashboard/view_return_requests.html', return_requests=requests_data,selected=selected)










@app.route('/update-user', methods=['POST'])
def update_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Update fields
    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.phone_number = request.form.get('phone_number', user.phone_number)

    db.session.commit()
    return jsonify({'success': 'User updated successfully'})



import secrets

@app.route('/login/google')
def google_login():
    # Generate a random nonce
    nonce = secrets.token_urlsafe()
    session['nonce'] = nonce

    # Redirect to Google's authorization endpoint
    print(url_for('google_authorize', _external=True))
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri, nonce=nonce)
    
    

@app.route('/login/callback')
def google_authorize():
    token = google.authorize_access_token()

    # Retrieve the nonce from the session
    nonce = session.get('nonce')
    if not nonce:
        flash('Invalid login attempt.', 'error')
        return redirect(url_for('userlogin'))

    # Parse the ID token with the nonce
    user_info = google.parse_id_token(token, nonce=nonce)
    if not user_info:
        flash('Failed to fetch user information from Google.', 'error')
        return redirect(url_for('userlogin'))

    # Extract user data from Google response
    email = user_info.get('email')
    first_name = user_info.get('given_name')
    last_name = user_info.get('family_name')
    username1 = email.split('@')[0]  # Generate a username from email

    # Check if the user exists in the database
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create a new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username1,
            password=bcrypt.hashpw(username1.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Encode hashed password as a string
        )
        db.session.add(user)
        db.session.commit()

        try:
            # Send welcome email
            msg = MailMessage(
                subject='Welcome to Our Site!',
                recipients=[email],
                html=render_template('login_email_google.html', username=user.username)
            )
            mail.send(msg)
        except Exception as e:
            flash(f'An error occurred while sending the welcome email: {e}', 'error')

        # Log the user in
        session['user_id'] = user.user_id
        session['username'] = user.username
        return redirect(url_for('home'))

    # Log the user in
    session['user_id'] = user.user_id
    session['username'] = user.username
    return redirect(url_for('home'))





@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('userlogin'))







if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
