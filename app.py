import os
import features
import stripe
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError, MismatchingStateError
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import urljoin
from urllib.parse import urlparse
from datetime import datetime
from flask import jsonify
from functools import wraps




# Allow HTTP for development (disable in production)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'EFEWFEWFEW' 
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'database url here'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
stripe.api_key = 'stripe key here'


# Initialize Session and SQLAlchemy
Session(app)
db = SQLAlchemy(app)




# ============================
# Association Table
# ============================

# Association Table for Collection and Board
collection_boards = db.Table(
    'collection_boards',
    db.Column('collection_id', db.Integer, db.ForeignKey('collections.id'), primary_key=True),
    db.Column('board_id', db.Integer, db.ForeignKey('boards.id'), primary_key=True)
)



# ============================
# User Model
# ============================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    
    # relationship to Boards
    boards = db.relationship('Board', backref='user', lazy=True, cascade="all, delete-orphan")
    
    # relationship to Collections
    collections = db.relationship('Collection', backref='user', lazy=True, cascade="all, delete-orphan")
    
    # relationship to Subscriptions
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade="all, delete-orphan")
    
    __table_args__ = (
        db.UniqueConstraint('auth_id', 'provider', name='unique_auth_id_provider'),
    )

    def __repr__(self):
        return f'<User {self.name} via {self.provider}>'


# ============================
# Subscription Model
# ============================

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)  
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to Payments
    payments = db.relationship('Payment', backref='subscription', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Subscription {self.plan} for User {self.user_id} - Status {self.status}>'


# ============================
# Payment Model
# ============================

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='USD')  
    status = db.Column(db.String(50), nullable=False)  
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transaction_id = db.Column(db.String(255), nullable=True) 
    
    def __repr__(self):
        return f'<Payment {self.amount} {self.currency} for Subscription {self.subscription_id} - Status {self.status}>'


# ============================
# Board Model
# ============================

class Board(db.Model):
    __tablename__ = 'boards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    website_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to Collection via association table
    collections = db.relationship(
        'Collection',
        secondary=collection_boards,
        backref=db.backref('boards', lazy='dynamic')
    )
    
    def __repr__(self):
        return f'<Board {self.name} by User {self.user_id}>'

# ============================
# Collection Model
# ============================

class Collection(db.Model):
    __tablename__ = 'collections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Collection {self.name} by User {self.user_id}>'




# Create the database tables
with app.app_context():
    db.create_all()

# Google OAuth Blueprint
google_blueprint = make_google_blueprint(
    client_id='google client id here',
    client_secret='client secret code here',
    redirect_to='dashboard',
    scope=[
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'openid'
    ]
)
app.register_blueprint(google_blueprint, url_prefix='/google-login')

# GitHub OAuth Blueprint
github_blueprint = make_github_blueprint(
    client_id='YOUR_GITHUB_CLIENT_ID',         # Replace with your GitHub Client ID
    client_secret='YOUR_GITHUB_CLIENT_SECRET', # Replace with your GitHub Client Secret
    redirect_to='dashboard',
    scope='user:email'
)
app.register_blueprint(github_blueprint, url_prefix='/github-login')

# Facebook OAuth Blueprint
facebook_blueprint = make_facebook_blueprint(
    client_id='YOUR_FACEBOOK_APP_ID',         # Replace with your Facebook App ID
    client_secret='YOUR_FACEBOOK_APP_SECRET', # Replace with your Facebook App Secret
    redirect_to='dashboard',
    scope=[
        'email',
        'public_profile'
    ]
)
app.register_blueprint(facebook_blueprint, url_prefix='/facebook-login')



# auth.py (Create a separate file for authentication utilities)

def check_authorization():
    """
    Central function to check if the user is authorized via any provider.
    Returns a tuple (is_authenticated, user_info, provider).
    """
    user_info = None
    provider = None

    try:
        if google.authorized:
            provider = 'google'
            resp = google.get("/oauth2/v2/userinfo")
            if not resp.ok:
                return False, None, None
            user_info = resp.json()
        elif github.authorized:
            provider = 'github'
            resp = github.get("/user")
            if not resp.ok:
                return False, None, None
            user_info = resp.json()
            if not user_info.get('email'):
                emails_resp = github.get("/user/emails")
                if emails_resp.ok:
                    emails = emails_resp.json()
                    primary_emails = [email['email'] for email in emails if email['primary'] and email['verified']]
                    if primary_emails:
                        user_info['email'] = primary_emails[0]
        elif facebook.authorized:
            provider = 'facebook'
            resp = facebook.get("/me?fields=id,name,email")
            if not resp.ok:
                return False, None, None
            user_info = resp.json()

        if user_info:
            return True, user_info, provider
        else:
            return False, None, None

    except Exception as e:
        flash(f"Authentication error: {str(e)}", category="error")
        return False, None, None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' in session and 'provider' in session:
            user_info = session['user_info']
            provider = session['provider']
            return f(user_info=user_info, provider=provider, *args, **kwargs)
        
        is_authenticated, user_info, provider = check_authorization()
        if not is_authenticated:
            flash("Please log in to access this page.", category="warning")
            return redirect(url_for('home'))
        
        # Store in session
        session['user_info'] = user_info
        session['provider'] = provider

        return f(user_info=user_info, provider=provider, *args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    """
    Home route that either shows the login page or redirects authenticated users to the dashboard.
    """
    is_authenticated, user_info, provider = check_authorization()
    if is_authenticated:
        return redirect(url_for('dashboard'))
    
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_url():
    data = request.get_json()
    url = data.get('url')

    # Validate URL input
    if not url:
        flash("No URL provided.", category="error")
        return redirect(url_for('home'))

    # Extract the domain name from the URL
    domain_name = url.replace('https://', '').replace('http://', '').split('/')[0]

    # Initialize default values for unauthenticated users
    insession = False
    user_name = None
    users_authid = None
    user_id = None
    provider = None

    # Check if the user is authenticated via any provider in session
    if 'user_info' in session and 'provider' in session:
        insession = True
        user_info = session['user_info']
        provider = session['provider']
        users_authid = user_info.get('id')
        user_name = user_info.get('name')
    else:
        # Check authorization from providers
        try:
            if google.authorized:
                provider = 'google'
                resp = google.get("/oauth2/v2/userinfo")
                if resp.ok:
                    user_info = resp.json()
                    insession = True
                    users_authid = user_info.get('id')
                    user_name = user_info.get('name')
                else:
                    raise TokenExpiredError()  # Handle expired token

            elif github.authorized:
                provider = 'github'
                resp = github.get("/user")
                if resp.ok:
                    user_info = resp.json()
                    insession = True
                    users_authid = user_info.get('id')
                    user_name = user_info.get('login')
                else:
                    raise TokenExpiredError()  # Handle expired token

            elif facebook.authorized:
                provider = 'facebook'
                resp = facebook.get("/me?fields=id,name,email")
                if resp.ok:
                    user_info = resp.json()
                    insession = True
                    users_authid = user_info.get('id')
                    user_name = user_info.get('name')
                else:
                    raise TokenExpiredError()  # Handle expired token

        except TokenExpiredError:
            flash("Your session has expired. Please log in again.", category="warning")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Authentication error: {str(e)}", category="error")
            return redirect(url_for('home'))

    # Fetch the user from the database if they are authenticated
    if insession and users_authid:
        try:
            user = User.query.filter_by(auth_id=users_authid, provider=provider).first()
            if user:
                user_id = user.id
            else:
                flash("Authenticated user not found in the database.", category="error")
                return redirect(url_for('home'))
        except SQLAlchemyError as e:
            flash(f"Database error occurred: {str(e)}", category="error")
            return redirect(url_for('home'))

    # Redirect to the board processing route, with or without user-specific data
    return redirect(url_for('board', 
                            site=domain_name, 
                            insession=insession, 
                            user_name=user_name, 
                            users_authid=users_authid, 
                            user_id=user_id))


@app.route('/<site>')
def board(site):
    user_name = request.args.get('user_name', None)
    users_authid = request.args.get('users_authid', None)
    user_id = request.args.get('user_id', None)

    # Fetch collections for the user
    collections = Collection.query.filter_by(user_id=user_id).all()

    return render_template(
        'board.html',
        user_name=user_name,
        users_authid=users_authid,
        site_name=site,
        user_id=user_id,
        collections=collections  # Pass collections to the template
    )


@app.route('/get-features', methods=['POST'])
def load_features():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify(success=False, message="No URL provided"), 400

    # Parse the URL and create a safe folder name
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = "http://" + url
        parsed_url = urlparse(url)

    folder_name = (
        parsed_url.netloc.replace(".", "_") + parsed_url.path.replace("/", "_")
    )
    folder_name = folder_name.strip("_")  # Remove leading/trailing underscores

    # Define the folder path
    folder_path = os.path.join('static', 'database', folder_name)

    # Check if the directory exists
    if os.path.exists(folder_path):
        # Load data from existing directory
        base_url = request.host_url
        images = [img for img in os.listdir(os.path.join(folder_path, 'fonts')) if img.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        font_image_urls = [urljoin(base_url, f'static/database/{folder_name}/fonts/{img}') for img in images]  
        
        screenshot_path = os.path.join(folder_path, 'screenshot.png')
        screenshot_url = urljoin(base_url, f'static/database/{folder_name}/screenshot.png') if os.path.exists(screenshot_path) else None
        
        json_files = [json_file for json_file in os.listdir(os.path.join(folder_path, 'color')) if json_file.endswith('.json')]
        json_urls = [urljoin(base_url, f'static/database/{folder_name}/color/{json_file}') for json_file in json_files]
        
        response_data = {
            'success': True,
            'folder_path': folder_path,
            'fontimages': font_image_urls,
            'screenshot': screenshot_url,
            'color_json': json_urls
        }
        
        return jsonify(response_data)
    
    try:
        # If the directory doesn't exist, call features.features
        folder_path = features.features(url)          
        base_url = request.host_url  
        images = [img for img in os.listdir(os.path.join(folder_path, 'fonts')) if img.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        font_image_urls = [urljoin(base_url, f'static/database/{folder_name}/fonts/{img}') for img in images]  
        
        screenshot_path = os.path.join(folder_path, 'screenshot.png')
        screenshot_url = urljoin(base_url, f'static/database/{folder_name}/screenshot.png') if os.path.exists(screenshot_path) else None
        
        json_files = [json_file for json_file in os.listdir(os.path.join(folder_path, 'color')) if json_file.endswith('.json')]
        json_urls = [urljoin(base_url, f'static/database/{folder_name}/color/{json_file}') for json_file in json_files]
        
        response_data = {
            'success': True,
            'folder_path': folder_path,
            'fontimages': font_image_urls,
            'screenshot': screenshot_url,
            'color_json': json_urls
        }
        
        return jsonify(response_data)
        
    except ValueError as e:
        return jsonify(success=False, message=str(e)), 400 
    except Exception as e:
        return jsonify(success=False, message="An unexpected error occurred: " + str(e)), 500


# Pricing Route 
@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


def get_board_screenshot_url(board):
    try:
        url = board.website_name
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = "http://" + url
            parsed_url = urlparse(url)

        folder_name = (
            parsed_url.netloc.replace(".", "_") + parsed_url.path.replace("/", "_")
        )
        folder_name = folder_name.strip("_")  # Remove leading/trailing underscores
        folder_path = os.path.join('static', 'database', folder_name)
        base_url = request.host_url

        screenshot_path = os.path.join(folder_path, 'screenshot.png')
        return urljoin(base_url, f'{folder_path}/screenshot.png') if os.path.exists(screenshot_path) else None
    except Exception as e:
        return None


@app.route('/dashboard')
@login_required
def dashboard(user_info, provider):
    """
    Dashboard route accessible only to authenticated users.
    Handles user data and displays dashboards and collections.
    """
    auth_id = user_info.get('id')
    name = user_info.get('name') or user_info.get('login')  # GitHub uses 'login' for username
    email = user_info.get('email')

    try:
        # Check if the user already exists in the database
        user = User.query.filter_by(auth_id=auth_id, provider=provider).first()
        if not user:
            # If the user is new, add them to the database
            new_user = User(auth_id=auth_id, provider=provider, name=name, email=email)
            db.session.add(new_user)
            db.session.commit()  # Commit to get the new user's ID
            user = new_user

            # Automatically create a "normal" subscription for the new user
            normal_subscription = Subscription(user_id=user.id, plan='normal', status='active', start_date=datetime.utcnow())
            db.session.add(normal_subscription)
            db.session.commit()  

        # Check if the user has a premium subscription
        subscription = Subscription.query.filter_by(user_id=user.id, status='active').first()
        user_type = subscription.plan if subscription else 'free'

        # Fetch the user's boards and collections
        boards = Board.query.filter_by(user_id=user.id).all()
        collections = Collection.query.filter_by(user_id=user.id).all()

        boards_data = []
        for board in boards:
            try:
                # Fetch related features for each board (fonts, screenshot, colors)
                url = board.website_name
                parsed_url = urlparse(url)
                if not parsed_url.scheme:
                    url = "http://" + url
                    parsed_url = urlparse(url)

                folder_name = (
                    parsed_url.netloc.replace(".", "_") + parsed_url.path.replace("/", "_")
                )

                folder_name = folder_name.strip("_")  # Remove leading/trailing underscores
                folder_path = os.path.join('static', 'database', folder_name)
                base_url = request.host_url
                # Fetch screenshot
                screenshot_path = os.path.join(folder_path, 'screenshot.png')
                screenshot_url = urljoin(base_url, f'{folder_path}/screenshot.png') if os.path.exists(screenshot_path) else None
                
                # Fetch color JSONs
                color_folder = os.path.join(folder_path, 'color')
                if os.path.exists(color_folder):
                    json_files = [json_file for json_file in os.listdir(color_folder) if json_file.endswith('.json')]
                    json_urls = [urljoin(base_url, f'{folder_path}/color/{json_file}') for json_file in json_files]
                else:
                    json_urls = []

                # Append board data with feature URLs
                boards_data.append({
                    'name': board.name,
                    'website_name': board.website_name,
                    'last_modified': board.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'screenshot': screenshot_url,
                    'color_json': json_urls,
                    'id': board.id
                })

            except Exception as e:
                # Handle cases where features could not be fetched
                boards_data.append({
                    'name': board.name,
                    'website_name': board.website_name,
                    'last_modified': board.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'error': f"Could not fetch features for this board: {str(e)}"
                })

        # Fetch collections and associated boards
        collections_data = [
            {
                'id': collection.id,  
                'name': collection.name,
                'last_modified': collection.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
                'boards': [
                    {
                        'name': board.name,
                        'website_name': board.website_name,
                        'screenshot': get_board_screenshot_url(board),  # Fetch screenshot for each board
                        'last_modified': board.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
                        'id': board.id
                    }
                    for board in collection.boards  
                ]
            }
            for collection in collections
        ]


    except SQLAlchemyError as e:
        db.session.rollback()
        flash("Failed to fetch boards or collections from the database.", category="error")
        return redirect(url_for('home'))

    return render_template(
        'dashboard.html', 
        user_name=name, 
        email=email, 
        user_id=user.id,
        auth=auth_id,
        boards=boards_data,
        collections=collections_data,
        user_type=user_type  
    )


@app.route('/logout')
def logout():
    try:
        # Revoke tokens from OAuth providers
        if google.authorized:
            token = google.token.get("access_token")
            if token:
                resp = google.post(
                    "https://accounts.google.com/o/oauth2/revoke",
                    params={'token': token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
                if resp.ok:
                    del google.token  # Delete OAuth token from the session
                else:
                    flash("Failed to revoke Google token.", category="error")
        
        if github.authorized:
            # GitHub does not provide a token revocation endpoint by default
            del github.token  # Delete OAuth token from the session
        
        if facebook.authorized:
            # Facebook token revocation
            access_token = facebook.token.get('access_token')
            if access_token:
                resp = facebook.get(f"/me/permissions?access_token={access_token}")
                if resp.ok:
                    data = resp.json()
                    for permission in data.get('data', []):
                        facebook.delete(
                            f"/me/permissions/{permission['permission']}",
                            params={'access_token': access_token}
                        )
                    del facebook.token  # Delete OAuth token from the session
                else:
                    flash("Failed to revoke Facebook token.", category="error")
    except Exception as e:
        flash(f"An unexpected error occurred during logout: {str(e)}", category="error")

    # Clear the entire session to remove all session data
    session.clear()

    flash("You have been logged out.", category="success")
    return redirect(url_for('home'))


# Route to create a new collection
@app.route('/create-collection', methods=['POST'])
def create_collection():
    try:
        data = request.json
        collection_name = data.get('name')
        user_id = data.get('user_id') 
        print(collection_name,user_id)

        # Validate input
        if not collection_name:
            return jsonify({'error': 'Collection name is required'}), 400

        # Create the new collection
        new_collection = Collection(name=collection_name, user_id=user_id)
        db.session.add(new_collection)
        db.session.commit()

        return jsonify({'message': 'Collection created successfully', 'collection': {
            'id': new_collection.id,
            'name': new_collection.name,
            'last_modified': new_collection.last_modified
        }}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@app.route('/save_board', methods=['POST'])
def save_board():
    data = request.get_json()
    board_name = data.get('name')
    collection_ids = data.get('collections')
    website_name = data.get('websiteName')  
    user_id = data.get('userId')

    user = User.query.get(user_id)
    subscription = Subscription.query.filter_by(user_id=user_id).first()

    if not user or not subscription:
        return jsonify({"message": "User or subscription not found."}), 404

    if subscription.plan == 'premium':
        return save_board_process(user, board_name, collection_ids, website_name)
    
    # For normal subscription users, check if they already have 5 or more boards
    if subscription.plan == 'normal':
        board_count = len(user.boards)
        if board_count >= 5:
            return jsonify({"message": "Board limit reached for normal subscription."}), 403
    return save_board_process(user, board_name, collection_ids, website_name)


# Helper function to handle the board-saving process
def save_board_process(user, board_name, collection_ids, website_name):
    new_board = Board(user_id=user.id, name=board_name, website_name=website_name)
    
    # Add the new board to the session
    db.session.add(new_board)
    
    try:
        # Commit to save the board
        db.session.commit()

        # Associate selected collections with the new board
        for collection_id in collection_ids:
            collection = Collection.query.get(collection_id)
            if collection:
                new_board.collections.append(collection)

        # Commit associations
        db.session.commit()
        return jsonify({"message": "Board saved successfully."}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error saving board: {e}")
        return jsonify({"message": "Failed to save the board."}), 500


@app.route('/update_board/<int:board_id>', methods=['POST'])
def update_board(board_id):
    data = request.get_json()
    new_name = data.get('name')
    
    board = Board.query.get(board_id)
    if board:
        board.name = new_name
        db.session.commit()  
        return jsonify({"message": "Board updated successfully!"}), 200
    else:
        return jsonify({"error": "Board not found."}), 404


@app.route('/edit-collection', methods=['POST'])
def edit_collection():
    data = request.get_json()
    collection_id = data.get('collection_id')
    new_name = data.get('new_name')

    if not collection_id or not new_name:
        return jsonify({'error': 'Invalid data'}), 400
    collection = Collection.query.get(collection_id)

    if not collection:
        return jsonify({'error': 'Collection not found'}), 404

    try:
        collection.name = new_name
        collection.last_modified = datetime.utcnow()

        db.session.commit()

        return jsonify({'message': 'Collection updated successfully'}), 200

    except Exception as e:
        db.session.rollback()  
        return jsonify({'error': str(e)}), 500




@app.route('/delete_board/<int:board_id>', methods=['POST'])
def delete_board(board_id):
    try:
        # Find the board by its ID
        board = Board.query.get(board_id)
        
        if not board:
            return jsonify({"error": "Board not found"}), 404
        
        # Remove the board from the collection_boards association table
        db.session.execute(collection_boards.delete().where(collection_boards.c.board_id == board_id))
        
        # Delete the board itself
        db.session.delete(board)
        db.session.commit()
        
        return jsonify({"message": "Board deleted successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    


@app.route('/delete-collection', methods=['POST'])
def delete_collection():
    data = request.get_json()
    collection_id = data.get('collection_id')

    # Validate input
    if not collection_id:
        return jsonify({'error': 'Invalid collection ID'}), 400

    try:
        # Fetch the collection by ID
        collection = Collection.query.get(collection_id)

        if not collection:
            return jsonify({'error': 'Collection not found'}), 404

        # Delete all entries from the association table related to this collection
        db.session.execute(collection_boards.delete().where(collection_boards.c.collection_id == collection_id))

        # Delete the collection itself
        db.session.delete(collection)

        # Commit the changes to the database
        db.session.commit()

        return jsonify({'message': 'Collection deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({'error': str(e)}), 500



@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()  # Get JSON data from the request
        user_id = data.get('user_id')  # Extract user_id

        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400  # Bad Request

        user = User.query.get(user_id)  # Fetch the user by user_id
        if not user:
            return jsonify({'error': 'User not found'}), 404  # Not Found

        # Replace with your actual price ID for a subscription
        price_id = 'price_1Q7GlhHKtnqJhgmNpr4mnjVL'  # Use the actual price ID you created for subscriptions

        # Create a checkout session for Stripe with subscription mode
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,  # Use the subscription price ID
                'quantity': 1,
            }],
            mode='subscription',  # Set mode to subscription
            customer_email=user.email,  # Prefill the user email
            success_url=url_for('payment_success', user_id=user.id, _external=True),
            cancel_url=url_for('payment_failed', _external=True),
        )

        return jsonify({'url': session.url})  # Return the URL as JSON

    except Exception as e:
        # Log the error for debugging
        app.logger.error('Error occurred while creating checkout session: %s', str(e))
        return jsonify({'error': str(e)}), 500  # Internal Server Error


@app.route('/payment-success')
def payment_success():
    user_id = request.args.get('user_id')  

    # Fetch the user based on user_id
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('dashboard'))

    # Find the user's current subscription
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if not subscription:
        flash('No subscription found for the user. Please contact support.', 'error')
        return redirect(url_for('dashboard'))

    # Update the subscription plan to 'premium'
    subscription.plan = 'premium'
    subscription.status = 'active'  

    try:
        db.session.commit()  
        flash('Payment successful! You are now a Premium member.', 'success')
    except Exception as e:
        db.session.rollback() 
        flash(f'Error updating subscription: {str(e)}', 'error')

    return redirect(url_for('home'))



@app.route('/payment-failed')
def payment_failed():
    flash('Payment failed or was cancelled. Please try again.', 'error')
    return redirect(url_for('dashboard'))


endpoint_secret = 'whsec_9ce5a2080e8fefb0b6273d9d48d356d0d4ca6a424ea17dc1f1fd0cce5d02fdaf'

# webhook endpoint
@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    event = None

    try:
        # Verify the event using the Stripe library
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        app.logger.info("Webhook event verified: %s", event['type']) 
    except ValueError as e:
        app.logger.error("Invalid payload: %s", str(e))
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        app.logger.error("Invalid signature: %s", str(e))
        return jsonify({'error': str(e)}), 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']  
        handle_checkout_session(session)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']  
        handle_successful_payment(invoice)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_failed_payment(invoice)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_ended(subscription)


    return jsonify({'status': 'success'}), 200


def handle_checkout_session(session):
    user_id = session.get('client_reference_id')  
    subscription_id = session.get('subscription')  
    
    app.logger.info("Checkout session completed for user ID: %s, subscription ID: %s", user_id, subscription_id)
    user = User.query.get(user_id)
    if user:
        new_subscription = Subscription(
            user_id=user.id,
            plan='premium',
            status='active',
            start_date=datetime.utcnow(),
            end_date=None 
        )
        db.session.add(new_subscription)
        db.session.commit()
        app.logger.info("Subscription created for user ID: %s", user_id)
    else:
        app.logger.error("User not found for ID: %s", user_id)


def handle_successful_payment(invoice):
    subscription_id = invoice.get('subscription')
    amount_paid = invoice.get('amount_paid') / 100 
    transaction_id = invoice.get('payment_intent')

    app.logger.info("Payment succeeded for subscription ID: %s, amount: %s", subscription_id, amount_paid)

    subscription = Subscription.query.filter_by(subscription_id=subscription_id).first()
    if subscription:
        new_payment = Payment(
            subscription_id=subscription.id,
            amount=amount_paid,
            currency='usd',
            status='succeeded',
            payment_date=datetime.utcnow(),
            transaction_id=transaction_id
        )
        db.session.add(new_payment)
        db.session.commit()
        app.logger.info("Payment recorded for subscription ID: %s", subscription_id)
    else:
        app.logger.error("Subscription not found for ID: %s", subscription_id)


def handle_failed_payment(invoice):
    subscription_id = invoice.get('subscription')
    
    app.logger.warning("Payment failed for subscription ID: %s", subscription_id)

    subscription = Subscription.query.filter_by(subscription_id=subscription_id).first()
    if subscription:
        subscription.status = 'past_due'
        db.session.commit()
        app.logger.info("Subscription marked as past due for subscription ID: %s", subscription_id)
    else:
        app.logger.error("Subscription not found for ID: %s", subscription_id)


def handle_subscription_ended(subscription):
    subscription_id = subscription.get('id')
    
    app.logger.info("Subscription ended for subscription ID: %s", subscription_id)

    subscription_record = Subscription.query.filter_by(subscription_id=subscription_id).first()
    if subscription_record:
        subscription_record.status = 'canceled'
        subscription_record.end_date = datetime.utcnow()
        db.session.commit()
        app.logger.info("Subscription canceled for ID: %s", subscription_id)
    else:
        app.logger.error("Subscription not found for ID: %s", subscription_id)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)  
