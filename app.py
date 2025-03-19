from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from restaurant_reviews import get_restaurants  # Import restaurant reviews logic
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Updated DB URI to point to the 'instance' folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'reviews.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key
db = SQLAlchemy(app)

GOOGLE_PLACES_API_KEY = "AIzaSyCfT5lgVhG5shvwQG1cPrtaQvoKE_CUHtY"  # Replace with your actual API key

# Updated Review Model with restaurant_name field
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_name = db.Column(db.String(200), nullable=False)  # New field to associate review with a restaurant
    author = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

# Initialize DB inside the app context
with app.app_context():
    db.create_all()

# Initialize SQLite for users
def init_db():
    users_db_path = os.path.join(basedir, 'instance', 'users.db')
    conn = sqlite3.connect(users_db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))  # Redirect to login page immediately

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect(os.path.join(basedir, 'instance', 'users.db'))
        c = conn.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed_password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            conn.close()
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect(os.path.join(basedir, 'instance', 'users.db'))
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password!', 'error')
            
    return render_template('login.html')

@app.route('/home')
@login_required
def home():
    # Fetch vegetarian restaurants near Ernakulam (latitude, longitude)
    restaurants = get_restaurants(location="9.9816,76.2999", radius=5000, keyword="vegetarian")
    return render_template('home.html', username=session.get('username'), restaurants=restaurants)

@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '').strip()
    if not query:
        flash("Please enter a search term", "error")
        return redirect(url_for('home'))

    print(f"Searching for: {query}")  # Debugging line

    restaurants = get_restaurants(location="9.9816,76.2999", radius=5000, keyword=query)
    
    if not restaurants:
        flash("No restaurants found for your search.", "warning")

    return render_template('home.html', restaurants=restaurants)

@app.route('/restaurant/<restaurant_name>')
@login_required
def restaurant_detail(restaurant_name):
    # Find the restaurant from the list
    restaurants = get_restaurants(location="9.9816,76.2999", radius=5000, keyword="vegetarian")
    restaurant = next((r for r in restaurants if r["name"] == restaurant_name), None)

    if not restaurant:
        flash("Restaurant not found.", "error")
        return redirect(url_for('home'))

    # Fetch reviews only for the specified restaurant
    reviews = Review.query.filter_by(restaurant_name=restaurant_name).order_by(Review.id.desc()).all()

    return render_template('restaurant.html', restaurant=restaurant, reviews=reviews)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    flash(' ', 'success')
    return redirect(url_for('login'))

### 📌 **Comment API**
@app.route('/api/comments', methods=['POST'])
def add_comment():
    data = request.get_json()
    # Check for required keys: content and restaurant
    if not data or "content" not in data or "restaurant" not in data:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    # Use the rating provided in the request (default to 3 if not provided)
    rating = data.get("rating", 3)

    new_review = Review(
        restaurant_name=data["restaurant"],  # Associate the review with a restaurant
        author=session.get('username', 'Anonymous'),
        text=data["content"],
        rating=rating,  # Use the user-selected rating
        upvotes=0,
        downvotes=0
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify({
        "success": True,
        "comment": {
            "id": new_review.id,
            "restaurant": new_review.restaurant_name,
            "author": new_review.author,
            "text": new_review.text,
            "rating": new_review.rating,
            "upvotes": new_review.upvotes,
            "downvotes": new_review.downvotes
        }
    })


@app.route('/api/comments/<int:comment_id>/vote', methods=['POST'])
def vote_comment(comment_id):
    review = Review.query.get(comment_id)
    if not review:
        return jsonify({"success": False, "error": "Comment not found"}), 404

    # Get user's vote history from session (per user basis)
    user_votes = session.get('user_votes', {})

    data = request.get_json()
    vote_type = data.get("voteType")

    # Check if the user has already voted on this review
    previous_vote = user_votes.get(str(comment_id))

    if previous_vote == vote_type:
        # If clicking the same vote again, remove it
        if vote_type == "upvote":
            review.upvotes -= 1
        elif vote_type == "downvote":
            review.downvotes -= 1
        user_votes.pop(str(comment_id))  # Remove vote from session
    else:
        # If switching votes, adjust the counts
        if previous_vote == "upvote":
            review.upvotes -= 1
        elif previous_vote == "downvote":
            review.downvotes -= 1

        # Apply new vote
        if vote_type == "upvote":
            review.upvotes += 1
        elif vote_type == "downvote":
            review.downvotes += 1
        
        user_votes[str(comment_id)] = vote_type  # Save new vote in session

    # Save changes
    session['user_votes'] = user_votes
    db.session.commit()

    return jsonify({
        "success": True,
        "upvotes": review.upvotes,
        "downvotes": review.downvotes
    })

@app.route('/api/comments', methods=['GET'])
def get_comments():
    reviews = Review.query.order_by(Review.id.desc()).all()
    return jsonify([
        {
            "id": review.id,
            "restaurant": review.restaurant_name,
            "author": review.author,
            "text": review.text,
            "rating": review.rating,
            "upvotes": review.upvotes,
            "downvotes": review.downvotes
        } for review in reviews
    ])

if __name__ == '__main__':
    with app.app_context():
        init_db()  # Initialize user database
    app.run(debug=True)
