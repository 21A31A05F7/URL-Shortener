from flask import Flask, request, redirect, render_template
import random, string
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Create a function to generate a short URL code
def generate_short_url(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Initialize SQLite DB to store URLs
def init_db():
    conn = sqlite3.connect('urls.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS urls
                    (id INTEGER PRIMARY KEY,
                     original_url TEXT,
                     short_url TEXT,
                     expiration_time DATETIME)''')
    conn.close()

# Route to display form for URL input
@app.route('/')
def index():
    return render_template('index.html')  # This will render the HTML file above

@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form['url']
    expiration = request.form['expiration']
    
    # Handle expiration logic
    expiration_time = None if expiration == 'forever' else datetime.now() + timedelta(days=int(expiration))
    
    short_url = generate_short_url()

    # Insert URL into the database
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO urls (original_url, short_url, expiration_time) VALUES (?, ?, ?)",
                   (original_url, short_url, expiration_time))
    conn.commit()
    conn.close()

    # Render with the new short URL
    return render_template('index.html', short_url=f"http://localhost:5000/{short_url}")

# Redirect to original URL when short URL is accessed
@app.route('/<short_url>')
def redirect_url(short_url):
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute("SELECT original_url, expiration_time FROM urls WHERE short_url=?", (short_url,))
    result = cursor.fetchone()
    
    if result:
        original_url, expiration_time = result
        
        # Check if expiration_time is None (meaning no expiration)
        if expiration_time:
            # Try parsing the expiration time, including microseconds
            try:
                expiration_time = datetime.strptime(expiration_time, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                # Fallback in case there are no microseconds in the string
                expiration_time = datetime.strptime(expiration_time, "%Y-%m-%d %H:%M:%S")
            
            if expiration_time < datetime.now():
                return "This short URL has expired."
        
        return redirect(original_url)
    else:
        return "Short URL not found."

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
