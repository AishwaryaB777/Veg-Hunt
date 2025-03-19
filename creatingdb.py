import os
import sqlite3

# Define paths to the databases in the "instance" folder
basedir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(basedir, "instance")
users_db_path = os.path.join(instance_dir, "users.db")
reviews_db_path = os.path.join(instance_dir, "reviews.db")

# Ensure the instance folder exists
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)
    print(f"Created instance directory at: {instance_dir}")

# Delete the existing databases if they exist
if os.path.exists(users_db_path):
    os.remove(users_db_path)
    print("Deleted existing users.db")
else:
    print("users.db not found, skipping deletion.")

if os.path.exists(reviews_db_path):
    os.remove(reviews_db_path)
    print("Deleted existing reviews.db")
else:
    print("reviews.db not found, skipping deletion.")

# Create a new users.db and its table
conn_users = sqlite3.connect(users_db_path)
cursor_users = conn_users.cursor()
cursor_users.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")
conn_users.commit()
conn_users.close()
print("Created new users.db with the users table.")

# Create a new reviews.db and its table
conn_reviews = sqlite3.connect(reviews_db_path)
cursor_reviews = conn_reviews.cursor()
cursor_reviews.execute("""
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_name TEXT NOT NULL,
        author TEXT NOT NULL,
        text TEXT NOT NULL,
        rating INTEGER NOT NULL,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn_reviews.commit()
conn_reviews.close()
print("Created new reviews.db with the reviews table.")
