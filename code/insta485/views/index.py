"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
import insta485
import arrow
import pathlib
import uuid
import hashlib

from insta485.api.auth import requires_auth
import insta485.model


@insta485.app.route('/')
def show_index():
    """Display / route."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    # Connect to database
    connection = insta485.model.get_db()
    logname = flask.session["username"]
    print("ssssss", logname)
    # Query database

    # find all post owners
    query = "SELECT username2 FROM following WHERE username1 = ?;"
    cur = connection.execute(query, (logname, ))
    post_owners = [dic["username2"] for dic in cur.fetchall()]
    post_owners.append(logname)

    posts = []
    # for each post owner, append all one's post into posts
    for post_owner in post_owners:
        # first find all posts the post_owner owns:
        query = "SELECT postid FROM posts WHERE owner = ?;"
        cur = connection.execute(query, (post_owner, ))
        post_ids = [dic["postid"] for dic in cur.fetchall()]
        # construct one post at a time
        for post_id in post_ids:
            post = {"postid": post_id}
            post["owner"] = post_owner

            query = "SELECT filename FROM users WHERE username = ?;"
            cur = connection.execute(query, (post_owner, ))
            filename = cur.fetchone()["filename"]
            owner_img_url = "/uploads/" + filename
            post["owner_img_url"] = owner_img_url

            query = "SELECT filename, created FROM posts WHERE postid = ?;"
            cur = connection.execute(query, (post_id, ))
            info = cur.fetchone()
            img_url = "/uploads/" + info["filename"]
            timestamp = arrow.get(
                info["created"],
                'YYYY-MM-DD HH:mm:ss').humanize()
            post["img_url"] = img_url
            post["timestamp"] = timestamp

            query = "SELECT owner, text FROM comments WHERE postid = ?;"
            cur = connection.execute(query, (post_id, ))
            comments = cur.fetchall()
            post["comments"] = comments

            query = "SELECT * FROM likes WHERE postid = ?;"
            cur = connection.execute(query, (post_id, ))
            like_list = cur.fetchall()
            post["likes"] = len(like_list)

            query = "SELECT likeid FROM likes WHERE owner = ? AND postid = ?;"
            cur = connection.execute(query, (logname, post_id, ))
            if cur.fetchone() is None:
                post["is_liked"] = False
            else:
                post["is_liked"] = True

            posts.append(post)

    # Add database info to context
    context = {"logname": logname, "posts": posts}
    return flask.render_template("index.html", **context)


@insta485.app.route('/uploads/<filename>')
@requires_auth
def download_file(filename):
    """doc_string."""
    if "username" not in flask.session:
        flask.abort(403)
    return flask.send_from_directory(
        insta485.app.config['UPLOAD_FOLDER'], filename, as_attachment=True
    )


@insta485.app.route('/users/<user_url_slug>/')
@requires_auth
def users(user_url_slug):
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    # Connect to database
    connection = insta485.model.get_db()

    # insert logname and username into context
    context = {"logname": logname, "username": user_url_slug}

    # insert user_img_url into context
    # insert owner_img_url
    query = "SELECT * FROM users WHERE username = ?"
    cur = connection.execute(query, (user_url_slug, ))
    user = cur.fetchone()
    if user is None:
        flask.abort(404)
    context["user_img_url"] = "/uploads/" + user["filename"]

    # insert fullname into context
    query = "SELECT * FROM users WHERE username = ?"
    cur = connection.execute(query, (user_url_slug, ))
    curr_user = cur.fetchone()
    context["fullname"] = curr_user["fullname"]

    # insert logname_follows_username into context
    query = "SELECT * FROM following WHERE username1 = ? AND username2 = ?"
    cur = connection.execute(query, (logname, user_url_slug, ))
    curr_following = cur.fetchall()
    if len(curr_following) == 0:
        context["logname_follows_username"] = False
    else:
        context["logname_follows_username"] = True

    # insert following into context
    query = "SELECT * FROM following WHERE username1 = ?"
    cur = connection.execute(query, (user_url_slug, ))
    curr_followings = cur.fetchall()
    context["following"] = len(curr_followings)

    # insert followers into context
    query = "SELECT * FROM following WHERE username2 = ?"
    cur = connection.execute(query, (user_url_slug, ))
    curr_follower = cur.fetchall()
    context["followers"] = len(curr_follower)

    # insert total_posts and posts into context
    query = "SELECT postid, filename FROM posts WHERE owner = ?"
    cur = connection.execute(query, (user_url_slug, ))
    curr_posts = cur.fetchall()
    context["total_posts"] = len(curr_posts)
    for post in curr_posts:
        post["img_url"] = "/uploads/" + post.pop("filename")
    context["posts"] = curr_posts

    return flask.render_template("users.html", **context)


@insta485.app.route('/users/<user_url_slug>/followers/')
@requires_auth
def followers(user_url_slug):
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    connection = insta485.model.get_db()

    username = user_url_slug

    query = "SELECT username1 FROM following WHERE username2 = ?;"
    cur = connection.execute(query, (username, ))
    follower_list = cur.fetchall()

    followers = []
    for follower in follower_list:
        follower_dic = {"username": follower['username1']}

        query = "SELECT filename FROM users WHERE username = ?"
        cur = connection.execute(query, (follower['username1'], ))
        user_img_url = '/uploads/' + cur.fetchone()['filename']
        follower_dic['user_img_url'] = user_img_url

        query = (
            "SELECT * FROM following WHERE username1 = ? "
            "AND username2 = ?;"
        )
        cur = connection.execute(query, (logname, follower['username1'], ))
        if cur.fetchone() is None:
            follower_dic['logname_follows_username'] = False
        else:
            follower_dic['logname_follows_username'] = True

        followers.append(follower_dic)

    context = {
        "logname": logname,
        "username": username,
        "followers": followers}
    return flask.render_template("followers.html", **context)


@insta485.app.route('/users/<user_url_slug>/following/')
@requires_auth
def following(user_url_slug):
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    connection = insta485.model.get_db()

    username = user_url_slug

    query = "SELECT username2 FROM following WHERE username1 = ?;"
    cur = connection.execute(query, (username, ))
    following_list = cur.fetchall()

    followings = []
    for following in following_list:
        following_dic = {"username": following['username2']}

        query = "SELECT filename FROM users WHERE username = ?"
        cur = connection.execute(query, (following['username2'], ))
        user_img_url = '/uploads/' + cur.fetchone()['filename']
        following_dic['user_img_url'] = user_img_url

        query = (
            "SELECT * FROM following "
            "WHERE username1 = ? AND username2 = ?;"
        )
        cur = connection.execute(query, (logname, following['username2'], ))
        if cur.fetchone() is None:
            following_dic['logname_follows_username'] = False
        else:
            following_dic['logname_follows_username'] = True

        followings.append(following_dic)

    context = {
        "logname": logname,
        "username": username,
        "following": followings}
    return flask.render_template("following.html", **context)


@insta485.app.route('/posts/<postid_url_slug>/')
@requires_auth
def posts(postid_url_slug):
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    # Connect to database
    connection = insta485.model.get_db()

    # insert logname into context
    context = {"logname": logname}

    # insert postid into context
    context["postid"] = postid_url_slug

    # insert owner, img_url and timestamp into context

    query = "SELECT * FROM posts WHERE postid = ?"
    cur = connection.execute(query, (postid_url_slug, ))
    curr_post = cur.fetchone()

    context["owner"] = curr_post["owner"]
    context["img_url"] = "/uploads/" + curr_post["filename"]
    context["timestamp"] = arrow.get(
        curr_post["created"],
        'YYYY-MM-DD HH:mm:ss').humanize()

    # insert is_liked into context
    query = "SELECT COUNT(*) FROM likes WHERE owner = ? AND postid = ?"
    cur = connection.execute(query, (logname, postid_url_slug), )
    count = cur.fetchall()
    if count[0]['COUNT(*)'] != 0:
        context["is_liked"] = True
    else:
        context["is_liked"] = False

    # insert owner_img_url
    query = "SELECT * FROM users WHERE username=?"
    cur = connection.execute(query, (curr_post['owner'], ))
    post_owner = cur.fetchall()
    context["owner_img_url"] = "/uploads/" + post_owner[0]["filename"]

    # insert likes
    query = "SELECT * FROM likes WHERE postid = ?"
    cur = connection.execute(query, (postid_url_slug, ))
    likes = cur.fetchall()
    context["likes"] = len(likes)

    # insert comments
    query = "SELECT commentid, owner, text FROM comments WHERE postid = ?"
    cur = connection.execute(query, (postid_url_slug, ))
    comments = cur.fetchall()
    context["comments"] = comments

    return flask.render_template("posts.html", **context)


@insta485.app.route('/explore/')
@requires_auth
def explore():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    connection = insta485.model.get_db()

    # insert logname into context
    context = {"logname": logname}

    # insert not_following into context
    # first figure out who is followed by logname
    query = "SELECT username2 FROM following WHERE username1 = ?"
    cur = connection.execute(query, (logname, ))
    curr_followings = cur.fetchall()

    # construct a list of curr_followings
    curr_following_list = [logname]
    for entree in curr_followings:
        curr_following_list.append(entree["username2"])

    # construct query and find not_following
    query = (
        "SELECT username, filename FROM users "
        "WHERE username NOT IN ({})"
    ).format(
        ','.join('?' for _ in curr_following_list)
    )

    cur = connection.execute(query, curr_following_list)
    not_following = cur.fetchall()

    for entree in not_following:
        entree["user_img_url"] = "/uploads/" + entree.pop("filename")

    context["not_following"] = not_following
    return flask.render_template("explore.html", **context)


@insta485.app.route('/accounts/login/')
def login():
    """doc_string."""
    if "username" in flask.session:
        return show_index()

    return flask.render_template("login.html")


@insta485.app.route('/accounts/create/')
def create():
    """doc_string."""
    if "username" in flask.session:
        return edit()

    return flask.render_template("signup.html")


@insta485.app.route('/accounts/delete/')
@requires_auth
def delete():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    context = {"logname": logname}
    return flask.render_template("delete.html", **context)


@insta485.app.route('/accounts/edit/')
@requires_auth
def edit():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    context = {"logname": logname}

    connection = insta485.model.get_db()
    # insert user_img_url
    query = "SELECT * FROM users WHERE username = ?"
    cur = connection.execute(query, (logname, ))
    user = cur.fetchone()
    context["user_img_url"] = "/uploads/" + user["filename"]

    return flask.render_template("edit.html", **context)


@insta485.app.route('/accounts/password/')
@requires_auth
def password():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]

    context = {"logname": logname}
    return flask.render_template("password.html", **context)

# # need further implementation
# @insta485.app.route('/accounts/auth/')
# def auth():
#     """doc_string."""
#     if "username" not in flask.session:
#         flask.abort(403)
#     return "200"


@insta485.app.route('/likes/', methods=['POST'])
@requires_auth
def likes():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    connection = insta485.model.get_db()

    post_id = flask.request.form['postid']
    if flask.request.form['operation'] == 'like':
        query = "SELECT * FROM likes WHERE owner = ? AND postid = ?;"
        cur = connection.execute(query, (logname, post_id, ))
        temp = cur.fetchone()
        if temp is not None:
            flask.abort(409)

        query = "INSERT INTO likes(`owner`, postid) VALUES(?, ?);"
    else:
        query = "SELECT * FROM likes WHERE owner = ? AND postid = ?;"
        cur = connection.execute(query, (logname, post_id, ))
        temp = cur.fetchone()
        if temp is None:
            flask.abort(409)
        query = "DELETE FROM likes WHERE owner=? AND postid=?"

    connection.execute(query, (logname, post_id, ))
    return flask.redirect(flask.request.args.get("target", "/"))


@insta485.app.route('/comments/', methods=['POST'])
@requires_auth
def comments():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]

    connection = insta485.model.get_db()

    if flask.request.form['operation'] == 'create':
        text = flask.request.form["text"]
        if not text:
            flask.abort(400)
        query = (
            "INSERT INTO comments(`owner`, postid, `text`) "
            "VALUES(?, ?, ?);"
        )
        connection.execute(
            query, (logname, flask.request.form['postid'], text, ))
    else:
        query = "SELECT owner FROM comments WHERE commentid = ?;"
        cur = connection.execute(query, (flask.request.form['commentid'], ))
        owner = cur.fetchone()
        if owner['owner'] != logname:
            flask.abort(403)
        query = "DELETE FROM comments WHERE commentid = ?"
        connection.execute(query, (flask.request.form['commentid'], ))

    return flask.redirect(flask.request.args.get("target", "/"))

# end of implementation


@insta485.app.route('/following/', methods=['POST'])
@requires_auth
def follow_unfollow():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    connection = insta485.model.get_db()

    username = flask.request.form['username']
    if flask.request.form['operation'] == 'follow':
        query = (
            "SELECT * FROM following WHERE username1 = ? "
            "AND username2 = ?;"
        )

        cur = connection.execute(query, (logname, username, ))
        if cur.fetchone() is not None:
            flask.abort(409)
        query = "INSERT INTO following (username1, username2) VALUES (?, ?);"
    else:
        query = (
            "SELECT * FROM following "
            "WHERE username1 = ? AND username2 = ?;"
        )
        cur = connection.execute(query, (logname, username, ))
        if cur.fetchone() is None:
            flask.abort(409)
        query = "DELETE FROM following WHERE username1 = ? AND username2 = ?;"

    connection.execute(query, (logname, username, ))
    return flask.redirect(flask.request.args.get("target", "/"))


@insta485.app.route('/posts/', methods=['POST'])
@requires_auth
def post_op():
    """doc_string."""
    if "username" not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]
    # Connect to database
    connection = insta485.model.get_db()

    if flask.request.form["operation"] == "delete":
        query = "SELECT filename, owner FROM posts WHERE postid=?"
        cur = connection.execute(query, (flask.request.form['postid'], ))
        curr_dic = cur.fetchone()

        if curr_dic["owner"] != logname:
            flask.abort(403)

        curr_filename = curr_dic["filename"]
        pathlib.Path(
            str(insta485.app.config['UPLOAD_FOLDER']) + "/" + curr_filename
        ).unlink()
        query = "DELETE FROM posts WHERE postid=?"
        connection.execute(query, (flask.request.form['postid'], ))
    else:
        fileobj = flask.request.files["file"]

        fileobj.seek(0)
        fileobj.read(1)
        if fileobj.tell() == 0:
            flask.abort(400)
        fileobj.seek(0)

        filename = fileobj.filename

        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = insta485.app.config["UPLOAD_FOLDER"] / uuid_basename
        fileobj.save(path)

        query = "INSERT INTO posts (`filename`, `owner`) VALUES (?, ?)"
        connection.execute(query, (uuid_basename, logname, ))

    return flask.redirect(flask.request.args.get(
        "target", flask.url_for('users', user_url_slug=logname)))


@insta485.app.route('/accounts/logout/', methods=['POST'])
def logout():
    """doc_string."""
    flask.session.pop("username", None)
    return flask.redirect(flask.url_for('login'))


@insta485.app.route('/accounts/', methods=['POST'])
def accounts():
    """doc_string."""
    connection = insta485.model.get_db()

    operation = flask.request.form["operation"]
    if operation == "login":
        username = flask.request.form["username"]
        password = flask.request.form["password"]

        query = "SELECT password FROM users WHERE username = ?;"
        cur = connection.execute(query, (username, ))
        password_db = cur.fetchone()
        if not password_db:
            flask.abort(403)

        password_db = password_db['password']

        algorithm, salt, _ = password_db.split("$")

        hash_obj = hashlib.new(algorithm)
        password_salted = salt + password
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_entered = "$".join([algorithm, salt, password_hash])

        if password_db != password_entered:
            flask.abort(403)

        flask.session["username"] = username

    elif operation == "create":
        username = flask.request.form["username"]
        password = flask.request.form["password"]
        fullname = flask.request.form["fullname"]
        email = flask.request.form["email"]
        file = flask.request.files["file"]

        if (
            not username or not password or
            not fullname or not email or
            file.filename == ''
        ):
            flask.abort(400)

        query = "SELECT * FROM users WHERE username = ?;"
        cur = connection.execute(query, (username, ))
        if cur.fetchone():
            flask.abort(409)

        stem = uuid.uuid4().hex
        suffix = pathlib.Path(file.filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        path = insta485.app.config['UPLOAD_FOLDER'] / uuid_basename
        file.save(path)

        algorithm = 'sha512'
        salt = uuid.uuid4().hex
        hash_obj = hashlib.new(algorithm)
        password_salted = salt + password
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])

        query = (
            "INSERT INTO users(username, fullname, email, `filename`, "
            "`password`) VALUES (?, ?, ?, ?, ?)"
        )

        connection.execute(
            query,
            (username,
             fullname,
             email,
             uuid_basename,
             password_db_string,
             ))

        flask.session["username"] = username

    elif operation == "delete":
        if "username" not in flask.session:
            return flask.redirect(flask.url_for('login'))

        logname = flask.session["username"]
        # delete user profile picture
        query = "SELECT filename FROM users WHERE username = ?;"
        cur = connection.execute(query, (logname, ))
        filename = cur.fetchone()['filename']
        file = pathlib.Path(insta485.app.config['UPLOAD_FOLDER']) / filename
        file.unlink()

        # delete user post picture
        query = "SELECT filename FROM posts WHERE owner = ?;"
        cur = connection.execute(query, (logname, ))
        filenames = [filename['filename'] for filename in cur.fetchall()]

        for filename in filenames:
            file = pathlib.Path(
                insta485.app.config['UPLOAD_FOLDER']) / filename
            file.unlink()

        # delete user info in the database
        query = "DELETE FROM users WHERE username = ?;"
        connection.execute(query, (logname, ))

        flask.session.pop("username", None)

    elif operation == "edit_account":
        if "username" not in flask.session:
            return flask.redirect(flask.url_for('login'))

        logname = flask.session["username"]
        fullname = flask.request.form["fullname"]
        email = flask.request.form["email"]
        file = flask.request.files["file"]

        if not fullname or not email:
            flask.abort(400)

        query = "UPDATE users SET fullname = ?, email = ? WHERE username = ?;"
        connection.execute(query, (fullname, email, logname, ))

        if file.filename != '':
            stem = uuid.uuid4().hex
            suffix = pathlib.Path(file.filename).suffix.lower()
            uuid_basename = f"{stem}{suffix}"
            path = insta485.app.config['UPLOAD_FOLDER'] / uuid_basename
            file.save(path)

            query = "SELECT filename FROM users WHERE username = ?;"
            cur = connection.execute(query, (logname, ))
            old_filename = cur.fetchone()['filename']
            old_file = pathlib.Path(
                insta485.app.config['UPLOAD_FOLDER']) / old_filename
            old_file.unlink()

            query = "UPDATE users SET filename = ? WHERE username = ?;"
            connection.execute(query, (uuid_basename, logname, ))

    elif operation == "update_password":
        if "username" not in flask.session:
            return flask.redirect(flask.url_for('login'))

        logname = flask.session["username"]
        password = flask.request.form["password"]
        new_password1 = flask.request.form["new_password1"]
        new_password2 = flask.request.form["new_password2"]
        if not password or not new_password1 or not new_password2:
            flask.abort(400)

        query = "SELECT password FROM users WHERE username = ?;"
        cur = connection.execute(query, (logname, ))
        logname_password = cur.fetchone()['password']

        algorithm, salt, _ = logname_password.split("$")

        hash_obj = hashlib.new(algorithm)
        password_salted = salt + password
        hash_obj.update(password_salted.encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        password_db_string = "$".join([algorithm, salt, password_hash])

        if logname_password != password_db_string:
            flask.abort(403)

        if new_password1 != new_password2:
            flask.abort(401)

        algorithm = 'sha512'
        salt = uuid.uuid4().hex
        hash_obj = hashlib.new(algorithm)
        new_password_salted = salt + new_password1
        hash_obj.update(new_password_salted.encode('utf-8'))
        new_password_hash = hash_obj.hexdigest()
        new_password_db_string = "$".join([algorithm, salt, new_password_hash])

        query = "UPDATE users SET password = ? WHERE username = ?;"
        connection.execute(query, (new_password_db_string, logname, ))

    return flask.redirect(flask.request.args.get("target", "/"))
