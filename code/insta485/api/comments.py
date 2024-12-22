"""API endpoints for managing comments in the Insta485 application."""
import flask
import insta485
from insta485.api.auth import requires_auth
import insta485.model


@insta485.app.route('/api/v1/comments/', methods=["POST"])
@requires_auth
def post_comment():
    """Handle POST request to add a comment to a post."""
    # if "username" not in flask.session:
    #     return flask.redirect(flask.url_for('login'))

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
    # read text from the data field
    text = flask.request.get_json()["text"]
    # insert into the database, get corresponding commentid
    query = (
        "INSERT INTO comments ('owner', postid, 'text') "
        "VALUES (?, ?, ?) "
        "RETURNING commentid"
    )
    cur = connection.execute(query, (logname, postid, text, ))
    commentid = cur.fetchone()["commentid"]
    # construct context
    context = {}
    context["commentid"] = commentid
    context["lognameOwnsThis"] = True
    context["owner"] = logname
    context["ownerShowUrl"] = "/users/" + logname + "/"
    context["text"] = text
    context["url"] = "/api/v1/comments/" + str(commentid) + "/"

    return flask.jsonify(**context), 201


@insta485.app.route('/api/v1/comments/<commentid>/', methods=["DELETE"])
@requires_auth
def delete_comment(commentid):
    """Handle DELETE request to remove a comment."""
    # if "username" not in flask.session:
    #     return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]

    # Connect to database
    connection = insta485.model.get_db()

    # check if commentid exists
    query = "SELECT * FROM comments WHERE commentid = ?"
    cur = connection.execute(query, (commentid, ))
    check = cur.fetchone()
    if check is None:
        flask.abort(404)

    # check if logname owns the comment
    if check["owner"] != logname:
        flask.abort(403)

    query = "DELETE FROM comments WHERE commentid = ?"
    connection.execute(query, (commentid, ))

    return '', 204
