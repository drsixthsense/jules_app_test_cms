from flask import Flask, render_template, url_for, request, redirect # Added request, redirect
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

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

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
        image_filename = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_filename = filename
        new_post = {
            'id': next_id,
            'title': title,
            'content': content,
            'image': image_filename
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
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '':
                # Optional: Delete old image
                if post.get('image'):
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], post['image'])
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post['image'] = filename
            # If no new image is uploaded but 'image' field is present,
            # it means the user might have cleared the file input.
            # We keep the old image in this case, unless explicitly handled otherwise.
        return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:post_id>') # Could also specify methods=['POST'] for safety
def delete_post(post_id):
    global posts # Declare posts as global because we are modifying it
    post_to_delete = next((p for p in posts if p['id'] == post_id), None)

    if post_to_delete:
        if post_to_delete.get('image'): # Check if 'image' key exists and is not None/empty
            image_filename = post_to_delete['image']
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError as e:
                    # Log the error or handle it appropriately
                    print(f"Error deleting image {image_path}: {e}")

    posts = [post for post in posts if post['id'] != post_id]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
