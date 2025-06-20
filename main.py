from flask import Flask, render_template, url_for, request, redirect # Added request, redirect

app = Flask(__name__)

# In-memory database for blog posts
posts = [
    {
        'id': 1,
        'title': 'First Post',
        'content': 'This is the content of the first post.'
    },
    {
        'id': 2,
        'title': 'Second Post',
        'content': 'This is some more content for the second post.'
    }
]
next_id = 3 # Next id to assign to a new post

@app.route('/')
def index(): # Renamed from hello_world
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def get_post(post_id):
    post = next((post for post in posts if post['id'] == post_id), None)
    if post:
        return render_template('post.html', post=post)
    return "Post Not Found", 404

@app.route('/add', methods=['GET', 'POST'])
def add_post():
    global next_id # Declare next_id as global to modify it
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = {
            'id': next_id,
            'title': title,
            'content': content
        }
        posts.append(new_post)
        next_id += 1
        return redirect(url_for('index'))
    return render_template('add_post.html')

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return "Post Not Found", 404

    if request.method == 'POST':
        post['title'] = request.form['title']
        post['content'] = request.form['content']
        return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:post_id>') # Could also specify methods=['POST'] for safety
def delete_post(post_id):
    global posts # Declare posts as global because we are modifying it (re-assigning filter result)
    original_length = len(posts)
    posts = [post for post in posts if post['id'] != post_id]
    # Optionally: check if len(posts) changed to confirm deletion or if post_id was not found.
    # For now, we just redirect. If post_id didn't exist, list remains unchanged.
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
