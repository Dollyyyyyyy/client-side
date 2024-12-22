"""Authentication-related API endpoints."""
import flask
import insta485
import hashlib
from functools import wraps


def check_auth(username, password):
    """Check if the username and password combination is valid."""
    connection = insta485.model.get_db()

    cur = connection.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    )
    user = cur.fetchone()

    if user is None:
        return False

    stored_password = user["password"]
    algorithm, salt, stored_hash = stored_password.split('$')

    hash_obj = hashlib.new(algorithm)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))

    provided_hash = hash_obj.hexdigest()

    return provided_hash == stored_hash


def unauthorized():
    """Send a 401 response that enables basic auth."""
    return flask.jsonify({"message": "Forbidden", "status_code": 403}), 403


def requires_auth(f):
    """Prompt for authentication if not already authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):

        if "username" in flask.session:
            return f(*args, **kwargs)

        auth = flask.request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return unauthorized()
        flask.session["username"] = auth.username
        return f(*args, **kwargs)
    return decorated


@insta485.app.route('/accounts/auth/')
def check_user_auth():
    """
    Verify if the user is authenticated.

    Return the current user's session information.
    """
    if "username" in flask.session:
        # User is logged in, return the username
        return flask.jsonify({"username": flask.session["username"]}), 200

    # Check if HTTP Basic Authentication is provided
    auth = flask.request.authorization
    if auth and check_auth(auth.username, auth.password):
        # Set session for the authenticated user
        flask.session["username"] = auth.username
        return flask.jsonify({"username": auth.username}), 200

    # If neither return unauthorized
    return unauthorized()
