import sqlite3
import logging
import sys
import os

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Configure logging
loglevel = os.getenv("LOGLEVEL", "DEBUG").upper()
loglevel = (
    getattr(logging, loglevel)
    if loglevel in ["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING",]
    else logging.DEBUG
)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.ERROR)

handlers = [stderr_handler, stdout_handler]

# Config log at the DEBUG level and handlers
logging.basicConfig(level=loglevel, 
    format='%(levelname)s:%(name)s:[%(asctime)s], %(message)s', 
    handlers=handlers)

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the connection_count
app.config['DB_CONN_COUNTER'] = 0

# Define the main route of the web application 
@app.route('/')
def index():
    app.config['DB_CONN_COUNTER'] = app.config['DB_CONN_COUNTER'] + 1
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    app.config['DB_CONN_COUNTER'] = app.config['DB_CONN_COUNTER'] + 1
    post = get_post(post_id)
    if post is None:
      app.logger.error('Non-existed article is accessed')
      return render_template('404.html'), 404
    else:
      app.logger.info('Article %r retrieved!', post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About page is retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    app.config['DB_CONN_COUNTER'] = app.config['DB_CONN_COUNTER'] + 1
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info('Article "' + title + '" is created!')

            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthz():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    return response

@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()
    connection.close()

    response = app.response_class(
            response=json.dumps({"db_connection_count": app.config['DB_CONN_COUNTER'], "post_count": post_count[0]}),
            status=200,
            mimetype='application/json'
    )
    return response

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
