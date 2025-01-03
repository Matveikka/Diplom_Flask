from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import sqlite3
import re

app = Flask(__name__)

first_request = True


@app.before_request
def before_first_request():
    global first_request
    if first_request:
        init_db()
        first_request = False


def generate_slug(title):
    slug = re.sub(r'[^a-zA-Zа-яА-Я0-9-]', '-', title.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    conn = get_db_connection()
    cursor = conn.cursor()
    original_slug = slug
    count = cursor.execute('SELECT COUNT(*) FROM posts WHERE slug = ?', (slug,)).fetchone()[0]
    i = 1
    while count > 0:
        slug = f"{original_slug}-{i}"
        count = cursor.execute('SELECT COUNT(*) FROM posts WHERE slug = ?', (slug,)).fetchone()[0]
        i += 1
    close_db_connection(conn)
    return slug


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def close_db_connection(conn):
    conn.close()


def init_db():
    conn = get_db_connection()
    conn.execute(
        'CREATE TABLE IF NOT EXISTS posts ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'title TEXT NOT NULL, '
        'rezume TEXT NOT NULL, '
        'info TEXT NOT NULL, '
        'created_at DATETIME DEFAULT CURRENT_TIMESTAMP, '
        'slug TEXT UNIQUE NOT NULL)')
    conn.close()


@app.route('/')
def all_posts():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('home.html', posts=posts)


@app.route('/posts/<slug>', strict_slashes=False)
def get_post(slug):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE slug = ?', (slug,)).fetchone()
    conn.close()
    return render_template('details.html', post=post)


@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        rezume = request.form['rezume']
        info = request.form['info']
        created_at = datetime.now().isoformat()
        slug = generate_slug(title)
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (title, rezume, info, created_at, slug) VALUES (?, ?, ?, ?, ?)',
                     (title, rezume, info, created_at, slug))
        conn.commit()
        conn.close()
        return redirect(url_for('all_posts'))
    return render_template('add_post.html')


@app.post('/posts/<slug>/delete')
def delete_post(slug: str):
    conn = get_db_connection()
    post = conn.execute('SELECT title, info, created_at FROM posts WHERE slug = ? ', (slug,)).fetchone()
    title = post['title']
    conn.execute('DELETE FROM posts WHERE slug = ?', (slug,))
    conn.commit()
    conn.close()
    return redirect(url_for('after_delete', title=title))


@app.get('/posts/deleted/<title>')
def after_delete(title: str):
    return render_template('after_delete.html', title=title)


if __name__ == '__main__':
    app.run(debug=True)
