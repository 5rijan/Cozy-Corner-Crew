import os
import features
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




# Allow HTTP for development (disable in production)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'EFEWFEWFEW' 
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://srijanchaudhary:Srijan2003%40@localhost/cozycorner'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    
    # relationship to Board
    boards = db.relationship('Board', backref='user', lazy=True, cascade="all, delete-orphan")
    
    #  relationship to Collection
    collections = db.relationship('Collection', backref='user', lazy=True, cascade="all, delete-orphan")
    
    __table_args__ = (
        db.UniqueConstraint('auth_id', 'provider', name='unique_auth_id_provider'),
    )
    
    def __repr__(self):
        return f'<User {self.name} via {self.provider}>'

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
    client_id='305111169551-lf1lchu3cle3chuaj27ut19jj0rshd32.apps.googleusercontent.com',
    client_secret='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',
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


@app.route('/')
def home():
    try:
        if google.authorized or github.authorized or facebook.authorized:
            return redirect(url_for('dashboard'))
    except TokenExpiredError:
        # Token has expired, ask the user to log in again
        session.clear()  
        flash("Session expired. Please log in again.", category="error")
        return render_template('index.html', error="Session expired. Please log in again.")
    except MismatchingStateError:
        # CSRF state mismatch, possibly from a tampered request
        session.clear()  
        flash("Authentication failed due to CSRF state mismatch.", category="error")
        return render_template('index.html', error="Authentication failed due to CSRF state mismatch.")
    except Exception as e:
        # Handle other potential errors
        if 'too many redirects' in str(e).lower():
            session.clear()  
            flash("Too many redirects occurred. Please log in again.", category="error")
            return redirect(url_for('home')) 
        else:
            flash(f"An unexpected error occurred: {str(e)}", category="error")
            return render_template('index.html', error="An unexpected error occurred. Please try again.")

    return render_template('index.html')


# Process Route 
@app.route('/process', methods=['POST'])
def process_url():
    data = request.get_json()
    url = data.get('url')
    domain_name = url.replace('https://', '').replace('http://', '').split('/')[0]

    # Check if user is in session
    insession = False
    user_name = None
    users_authid = None
    provider = None

    if google.authorized:
        insession = True
        resp = google.get("/oauth2/v2/userinfo")
        user_info = resp.json()
        users_authid = user_info.get('id')
        user_name = user_info.get('name')
        provider = 'google'

    elif github.authorized:
        insession = True
        resp = github.get("/user")
        user_info = resp.json()
        users_authid = user_info.get('id')
        user_name = user_info.get('login') 
        provider = 'github'

    elif facebook.authorized:
        insession = True
        resp = facebook.get("/me?fields=id,name,email")
        user_info = resp.json()
        users_authid = user_info.get('id')
        user_name = user_info.get('name')
        provider = 'facebook'

    user = User.query.filter_by(auth_id=users_authid, provider=provider).first()
    user_id = user.id if user else None

    return redirect(url_for('board', site=domain_name, insession=insession, user_name=user_name, users_authid=users_authid, user_id=user_id))


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


@app.route('/dashboard')
def dashboard():
    provider = None
    user_info = None

    try:
        # Determine which provider is authorized
        if google.authorized:
            provider = 'google'
            resp = google.get("/oauth2/v2/userinfo")
            if not resp.ok:
                flash("Failed to fetch user info from Google.", category="error")
                return redirect(url_for('home'))
            user_info = resp.json()
        elif github.authorized:
            provider = 'github'
            resp = github.get("/user")
            if not resp.ok:
                flash("Failed to fetch user info from GitHub.", category="error")
                return redirect(url_for('home'))
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
                flash("Failed to fetch user info from Facebook.", category="error")
                return redirect(url_for('home'))
            user_info = resp.json()
        
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", category="error")
        return redirect(url_for('home'))

    if not provider or not user_info:
        flash("Authentication failed. Please log in again.", category="error")
        return redirect(url_for('home'))

    # Extract user details based on provider
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
            db.session.commit()
            user = new_user
        
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
                print(folder_name)
                folder_path = os.path.join('static', 'database', folder_name)
                print(folder_path)
                base_url = request.host_url
                # Fetch screenshot
                screenshot_path = os.path.join(folder_path, 'screenshot.png')
                screenshot_url = urljoin(base_url, f'{folder_path}/screenshot.png') if os.path.exists(screenshot_path) else None
                
                # Fetch color JSONs
                json_files = [json_file for json_file in os.listdir(os.path.join(folder_path, 'color')) if json_file.endswith('.json')]
                json_urls = [urljoin(base_url, f'{folder_path}/color/{json_file}') for json_file in json_files]

                # Append board data with feature URLs
                boards_data.append({
                    'name': board.name,
                    'website_name': board.website_name,
                    'last_modified': board.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'screenshot': screenshot_url,
                    'color_json': json_urls,
                    'id':board.id
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
                        'screenshot': screenshot_url,
                        'last_modified': board.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
                        'id':board.id
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
        user_name=user.name, 
        email=user.email, 
        user_id=user.id,
        auth=auth_id,
        boards=boards_data,
        collections=collections_data  
    )


# Logout Route
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

    # Create a new board instance
    new_board = Board(user_id=user_id, name=board_name, website_name=website_name)

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



if __name__ == "__main__":
    app.run()


