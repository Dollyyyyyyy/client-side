"""REST API for likes."""
import flask
from flask import request
import insta485
from insta485.api.auth import requires_auth
import insta485.model as model
import sys


@insta485.app.route('/api/v1/likes/', methods=['POST'])
@requires_auth
def post_like():
    """Handle POST request to create a like for a post."""
    # if "username" not in flask.session:
    #     return flask.redirect(flask.url_for('login'))

    logname = flask.session["username"]

    # extract the postid from query
    post_id = request.args.get('postid')

    # check if the query parameter is provided
    if post_id is None:
        flask.abort(400)

    # connect to the db
    connection = model.get_db()

    # check if the postid is out of range, if so, return 404
    cur = connection.execute("SELECT postid FROM posts WHERE postid = ?",
                             (post_id, ))

    post_exist = cur.fetchone()

    if post_exist is None:
        print("ww")
        flask.abort(404)

    # check if the like already exists
    cur = connection.execute(
        "SELECT likeid FROM likes WHERE owner = ? AND postid = ?",
        (logname, post_id)
    )

    like_exist = cur.fetchone()

    # case when the like already exists
    if like_exist:
        like_id = like_exist['likeid']

        return flask.jsonify({
            "likeid": like_id,
            "url": f"/api/v1/likes/{like_id}/"
        }), 200
    # case when the like does not already exist, we need to create one
    else:
        connection.execute("INSERT INTO likes (owner, postid) VALUES(?, ?)",
                           (logname, post_id))

        like_id = connection.execute(
            "SELECT likeid FROM likes WHERE owner =? and postid =?",
            (logname,
             post_id)).fetchone()['likeid']

        return flask.jsonify({
            "likeid": like_id,
            "url": f"/api/v1/likes/{like_id}/"
        }), 201


@insta485.app.route('/api/v1/likes/<likeid>/', methods=["DELETE"])
@requires_auth
def delete_like(likeid):
    """Handle DELETE request to remove a like from a post."""
    # if "username" not in flask.session:
    #     return flask.redirect(flask.url_for('login'))
    logname = flask.session["username"]

    # Connect to database
    connection = insta485.model.get_db()

    # check if likeid exists
    query = "SELECT * FROM likes WHERE likeid = ?"
    cur = connection.execute(query, (likeid, ))
    check = cur.fetchone()
    if check is None:
        flask.abort(404)

    # check if logname owns the like
    if check["owner"] != logname:
        flask.abort(403)

    query = "DELETE FROM likes WHERE likeid = ?"
    connection.execute(query, (likeid, ))

    return '', 204
