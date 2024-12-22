"""REST API for resource."""
import flask
import insta485
from insta485.api.auth import requires_auth
import insta485.model


@insta485.app.route('/api/v1/posts/test/')
def posts_test():
    """Test the posts API endpoints."""
    print("\n########## testing api/v1/post/ ##########")
    logname = flask.session["username"]

    # Connect to database
    connection = insta485.model.get_db()

    query = "SELECT username2 FROM following WHERE username1 = ?;"
    cur = connection.execute(query, (logname, ))
    post_owners = [dic["username2"] for dic in cur.fetchall()]
    post_owners.append(logname)

    query = "SELECT MAX(postid) FROM posts WHERE owner IN ({})".format(
        ','.join('?' for _ in post_owners))
    cur = connection.execute(query, post_owners)
    maxid = cur.fetchone()["MAX(postid)"]
    postid_lte = flask.request.args.get("postid_lte", default=maxid, type=int)
    print(f"postid_lte = {postid_lte}")

    size = flask.request.args.get("size", default=10, type=int)
    if size <= 0:
        flask.abort(400)
    print(f"size = {size}")

    page = flask.request.args.get("page", default=0, type=int)
    if page < 0:
        flask.abort(400)
    print(f"page = {page}")

    context = {}

    query = (
        "SELECT postid FROM posts "
        "WHERE postid <= {} AND owner IN ({}) "
        "ORDER BY postid DESC "
        "LIMIT {} OFFSET {}"
    ).format(
        postid_lte,
        ','.join('?' for _ in post_owners),
        size,
        page * size
    )
    cur = connection.execute(query, post_owners)
    results = cur.fetchall()

    print(results)

    print(flask.request.relative_url)

    print("########## finished testing ##########\n")
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/likes/test/', methods=["POST"])
def likes_test():
    """Test the likes API endpoints."""
    print("\n########## testing api/v1/post/ ##########")
    logname = flask.session["username"]

    # Connect to database
    connection = insta485.model.get_db()
    postid = flask.request.args.get("postid")
    # check if postid is in the range
    query = "SELECT * FROM posts WHERE postid = ?"
    cur = connection.execute(query, (postid, ))
    check = cur.fetchone()
    if check is None:
        flask.abort(404)

    context = {}
    # see if logname has already liked the post
    query = "SELECT * FROM likes WHERE owner = ? AND postid = ?"
    cur = connection.execute(query, (logname, postid, ))
    result = cur.fetchone()
    if result is not None:
        likeid = result["likeid"]
        context["likeid"] = likeid
        context["url"] = "/api/v1/likes/" + str(likeid) + "/"
        return flask.jsonify(**context)

    else:
        query = (
            "INSERT INTO likes('owner', postid) "
            "VALUES (?, ?) "
            "RETURNING likeid"
        )
        cur = connection.execute(query, (logname, postid, ))
        likeid = cur.fetchone()["likeid"]
        context["likeid"] = likeid
        context["url"] = "/api/v1/likes/" + str(likeid) + "/"
        return flask.jsonify(**context), 201

    print("########## finished testing ##########\n")


@insta485.app.route('/api/v1/comments/test/', methods=["POST"])
def comments_test():
    """Test the comments API endpoints."""
    print("\n########## testing api/v1/post/ ##########")
    logname = flask.session["username"]

    # Connect to database
    connection = insta485.model.get_db()
    postid = flask.request.args.get("postid")
    # check if postid is in the range
    check = flask.request.get_json()
    print(type(check))
    return '', 204

    print("########## finished testing ##########\n")
