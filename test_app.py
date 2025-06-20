import os
import tempfile
import pytest
import io # Added for io.BytesIO
from main import app as flask_app # Assuming your Flask app instance is named 'app' in main.py
from werkzeug.datastructures import FileStorage

# Pytest fixtures
@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    # Set up a temporary directory for uploads during tests
    # Create a unique temp directory for each test run using mkdtemp
    temp_dir = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = temp_dir
    app.config['TESTING'] = True

    # Ensure the in-memory posts list is reset for each test
    import main
    main.posts = []
    main.next_id = 1

    client = app.test_client()
    yield client

    # Teardown: clean up the temporary directory and its contents
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER'], topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(app.config['UPLOAD_FOLDER'])


# Test functions
def test_add_post_with_image(client, app):
    import main # Required to access main.posts and main.next_id
    main.posts = []
    main.next_id = 1

    image_content = b"fake image data"
    image = FileStorage(
        stream=io.BytesIO(image_content),
        filename="test_image.png",
        content_type="image/png"
    )

    data = {
        'title': 'Image Post',
        'content': 'This post has an image.',
        'image': image
    }

    response = client.post('/add', data=data, content_type='multipart/form-data')
    assert response.status_code == 302 # Redirect to index
    assert main.next_id == 2
    assert len(main.posts) == 1
    new_post = main.posts[0]
    assert new_post['title'] == 'Image Post'
    assert new_post['image'] is not None
    assert new_post['image'].endswith('.png')

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], new_post['image'])
    assert os.path.exists(image_path)

    response = client.get(f"/post/{new_post['id']}")
    assert response.status_code == 200
    assert b'<img class="post-image"' in response.data
    assert bytes(new_post['image'], 'utf-8') in response.data

    response = client.get('/')
    assert response.status_code == 200
    assert b'<img class="thumbnail-image"' in response.data
    assert bytes(new_post['image'], 'utf-8') in response.data

    # Clean up not needed here due to fixture teardown logic for UPLOAD_FOLDER contents
    # However, if specific files outside UPLOAD_FOLDER were created, they'd need manual cleanup.

def test_add_post_without_image(client):
    import main
    main.posts = []
    main.next_id = 1

    data = {
        'title': 'No Image Post',
        'content': 'This post has no image.'
    }

    response = client.post('/add', data=data, content_type='multipart/form-data')
    assert response.status_code == 302
    assert len(main.posts) == 1
    new_post = main.posts[0]
    assert new_post['title'] == 'No Image Post'
    assert new_post['image'] is None

def test_edit_post_add_image(client, app):
    import main
    main.posts = []
    main.next_id = 1

    client.post('/add', data={'title': 'Initial Title', 'content': 'Initial content.'}, content_type='multipart/form-data')
    assert len(main.posts) == 1
    post_id = main.posts[0]['id']
    assert main.posts[0]['image'] is None

    image_content = b"another fake image"
    image = FileStorage(
        stream=io.BytesIO(image_content),
        filename="edit_image.jpg",
        content_type="image/jpeg"
    )
    edit_data = {
        'title': 'Updated Title with Image',
        'content': 'Updated content, now with image.',
        'image': image
    }
    response = client.post(f'/edit/{post_id}', data=edit_data, content_type='multipart/form-data')
    assert response.status_code == 302

    edited_post = next(p for p in main.posts if p['id'] == post_id)
    assert edited_post['title'] == 'Updated Title with Image'
    assert edited_post['image'] is not None
    assert edited_post['image'].endswith('.jpg')

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], edited_post['image'])
    assert os.path.exists(image_path)

def test_edit_post_replace_image(client, app):
    import main
    main.posts = []
    main.next_id = 1

    initial_image_content = b"initial image data"
    initial_image_file = FileStorage(
        stream=io.BytesIO(initial_image_content),
        filename="initial.png",
        content_type="image/png"
    )
    client.post('/add', data={'title': 'Post with Image', 'content': 'Content.', 'image': initial_image_file}, content_type='multipart/form-data')
    assert len(main.posts) == 1
    post_id = main.posts[0]['id']
    initial_image_filename = main.posts[0]['image']
    assert initial_image_filename is not None
    initial_image_path = os.path.join(app.config['UPLOAD_FOLDER'], initial_image_filename)
    assert os.path.exists(initial_image_path) # Check initial image saved

    new_image_content = b"new image data"
    new_image_file = FileStorage(
        stream=io.BytesIO(new_image_content),
        filename="replacement.jpg",
        content_type="image/jpeg"
    )
    edit_data = {
        'title': 'Post with Replaced Image',
        'content': 'Content updated.',
        'image': new_image_file
    }
    client.post(f'/edit/{post_id}', data=edit_data, content_type='multipart/form-data')

    edited_post = next(p for p in main.posts if p['id'] == post_id)
    assert edited_post['image'] is not None
    assert edited_post['image'] != initial_image_filename
    assert edited_post['image'].endswith('.jpg')

    new_image_path = os.path.join(app.config['UPLOAD_FOLDER'], edited_post['image'])
    assert os.path.exists(new_image_path)
    assert not os.path.exists(initial_image_path) # Old image should be deleted by edit_post

def test_delete_post_removes_image(client, app):
    import main
    main.posts = []
    main.next_id = 1

    image_content = b"image to be deleted"
    image = FileStorage(
        stream=io.BytesIO(image_content),
        filename="delete_me.png",
        content_type="image/png"
    )
    client.post('/add', data={'title': 'To Delete', 'content': 'Content.', 'image': image}, content_type='multipart/form-data')
    assert len(main.posts) == 1
    post_to_delete = main.posts[0]
    post_id = post_to_delete['id']
    image_filename = post_to_delete['image']
    assert image_filename is not None
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    assert os.path.exists(image_path)

    client.get(f'/delete/{post_id}')
    assert len(main.posts) == 0
    # This assertion will fail if main.py's delete_post doesn't remove the file
    assert not os.path.exists(image_path)
