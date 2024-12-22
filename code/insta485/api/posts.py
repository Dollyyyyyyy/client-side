"""REST API for likes."""
import flask
import insta485
from insta485.api.auth import requires_auth
import insta485.model


@insta485.app.route('/api/v1/posts/')
@requires_auth
def get_posts():
    """Retrieve a list of posts based on query parameters."""
    # if "username" not in flask.session:
    #       return flask.redirect(flask.url_for('login'))

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

    page = flask.request.args.get("page", default=0, type=int)
    if page < 0:
        flask.abort(400)

    context = {}

    query = (
        "SELECT postid FROM posts WHERE postid <= {} AND owner IN ({}) "
        "ORDER BY postid DESC LIMIT {} OFFSET {}".format(
            postid_lte,
            ','.join('?' for _ in post_owners),
            size,
            page * size
        )
    )
    cur = connection.execute(query, post_owners)
    results = cur.fetchall()
    if len(results) == size:
        context["next"] = (
            "/api/v1/posts/?size=" + str(size) +
            "&page=" + str(page + 1) +
            "&postid_lte=" + str(postid_lte)
        )
    else:
        context["next"] = ""
    for result in results:
        result["url"] = "/api/v1/posts/" + str(result["postid"]) + "/"
    context["results"] = results
    context["url"] = (
        flask.request.path +
        (
            '?' + flask.request.query_string.decode()
            if flask.request.query_string else ''
        )
    )
    return flask.jsonify(**context)


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/')
@requires_auth
def get_post_detail(postid_url_slug):
    """Retrieve detailed information for a specific post."""
    # if "username" not in flask.session:
    #       return flask.redirect(flask.url_for('login'))
    logname = flask.session["username"]

    # Connect to database
    connection = insta485.model.get_db()

    query = "SELECT * FROM posts WHERE postid = ?"
    cur = connection.execute(query, (postid_url_slug, ))
    check = cur.fetchone()
    if check is None:
        flask.abort(404)

    context = {}

    # insert comments
    query = "SELECT commentid, owner, text FROM comments WHERE postid = ?"
    cur = connection.execute(query, (postid_url_slug, ))
    comments = cur.fetchall()
    for comment in comments:
        if logname == comment["owner"]:
            comment["lognameOwnsThis"] = True
        else:
            comment["lognameOwnsThis"] = False
        comment["ownerShowUrl"] = "/users/" + comment["owner"] + "/"
        comment["url"] = "/api/v1/comments/" + str(comment["commentid"]) + "/"
    context["comments"] = comments
    context["comments_url"] = "/api/v1/comments/?postid=" + \
        str(postid_url_slug)

    # insert owner, img_url and timestamp into context
    query = "SELECT * FROM posts WHERE postid = ?"
    cur = connection.execute(query, (postid_url_slug, ))
    curr_post = cur.fetchone()

    context["created"] = curr_post["created"]
    context["imgUrl"] = "/uploads/" + curr_post["filename"]

    # insert likes into context
    likes = {}
    query = "SELECT COUNT(*) FROM LIKES WHERE postid = ?"
    cur = connection.execute(query, (postid_url_slug, ))
    count = cur.fetchone()
    likes["numLikes"] = count["COUNT(*)"]

    query = "SELECT * FROM likes WHERE owner = ? AND postid = ?"
    cur = connection.execute(query, (logname, postid_url_slug, ))
    count = cur.fetchone()
    if count is None:
        likes["lognameLikesThis"] = False
        likes["url"] = None
    else:
        likes["lognameLikesThis"] = True
        likes["url"] = "/api/v1/likes/" + str(count["likeid"]) + "/"

    context["likes"] = likes

    context["owner"] = curr_post["owner"]

    # insert owner_img_url
    query = "SELECT * FROM users WHERE username = ?"
    cur = connection.execute(query, (curr_post['owner'], ))
    post_owner = cur.fetchone()
    context["ownerImgUrl"] = "/uploads/" + post_owner["filename"]

    context["ownerShowUrl"] = "/users/" + curr_post["owner"] + "/"
    context["postShowUrl"] = "/posts/" + str(postid_url_slug) + "/"
    context["postid"] = postid_url_slug
    context["url"] = "/api/v1/posts/" + str(postid_url_slug) + "/"

    return flask.jsonify(**context)
