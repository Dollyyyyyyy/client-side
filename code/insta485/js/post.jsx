import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
// import './Post.css';
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";
import PostBar from "./postbar"; // Import the PostBar component

dayjs.extend(relativeTime);
dayjs.extend(utc);

export default function Post({ url }) {
  const [imgUrl, setImgUrl] = useState("");
  const [owner, setOwner] = useState("");
  const [ownerImgUrl, setOwnerImgUrl] = useState("");
  const [ownerShowUrl, setOwnerShowUrl] = useState("");
  const [postShowUrl, setPostShowUrl] = useState("");
  const [postId, setPostId] = useState(null);
  const [numLikes, setNumLikes] = useState(0);
  const [likesUrl, setLikesUrl] = useState("");
  const [lognameLikesThis, setLognameLikesThis] = useState(false);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState("");
  const [created, setCreated] = useState("");

  useEffect(() => {
    let ignoreStaleRequest = false;

    // Call REST API to get the post's information
    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        if (!ignoreStaleRequest) {
          setImgUrl(data.imgUrl);
          setOwner(data.owner);
          setOwnerImgUrl(data.ownerImgUrl);
          setOwnerShowUrl(data.ownerShowUrl);
          setPostShowUrl(data.postShowUrl);
          setPostId(data.postid);
          setCreated(data.created); // Set created timestamp

          // set likes data
          setNumLikes(data.likes.numLikes);
          setLognameLikesThis(data.likes.lognameLikesThis);
          setLikesUrl(data.likes.url);

          // set comments data
          setComments(data.comments);

          setLoading(false);
        }
      })
      .catch((error) => {
        console.log(error);
        setLoading(false);
      });

    return () => {
      ignoreStaleRequest = true;
    };
  }, [url]);

  // handler for like
  const handleLike = () => {
    //  unlike since the owner already liked this
    if (lognameLikesThis) {
      fetch(likesUrl, { method: "DELETE", credentials: "same-origin" }).then(
        () => {
          setNumLikes(numLikes - 1);
          setLognameLikesThis(false);
          setLikesUrl(null); // Clear likesUrl after unliking
        },
      );

      //  like, since the owner haven't liked this
    } else {
      fetch(`/api/v1/likes/?postid=${postId}`, {
        method: "POST",
        credentials: "same-origin",
      })
        .then((response) => response.json())
        .then((data) => {
          setNumLikes(numLikes + 1);
          setLognameLikesThis(true);
          setLikesUrl(data.url);
        })
        .catch((error) => console.error("Error liking post:", error));
    }
  };

  // Handle submit comment
  const handleSubmitComment = (e) => {
    e.preventDefault();

    if (newComment.trim() === "") {
      console.error("Comment cannot be empty.");
      return;
    }

    fetch(`/api/v1/comments/?postid=${postId}`, {
      method: "POST",
      credentials: "same-origin",
      body: JSON.stringify({ text: newComment }),
      headers: { "Content-Type": "application/json" }, // Specify content type
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to post comment");
        }
        return response.json();
      })
      .then((newCommentData) => {
        setComments([...comments, newCommentData]);
        setNewComment("");
      })
      .catch((error) => {
        console.error("Error posting comment:", error);
      });
  };

  const handleDoubleClick = () => {
    if (lognameLikesThis) {
      return;
    }
    fetch(`/api/v1/likes/?postid=${postId}`, {
      credentials: "same-origin",
      method: "POST",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to double click and like");
        }
        return response.json();
      })
      .then((data) => {
        setNumLikes(numLikes + 1);
        setLognameLikesThis(!lognameLikesThis);
        setLikesUrl(data.url);
      });
  };

  const handleDeleteComment = (commentId) => {
    fetch(`/api/v1/comments/${commentId}/`, {
      method: "DELETE",
      credentials: "same-origin",
    })
      .then(() => {
        setComments(
          comments.filter((comment) => comment.commentid !== commentId),
        );
      })
      .catch((error) => console.error("Error deleting comment:", error));
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  const renderLikesText = () =>
    numLikes === 1 ? `${numLikes} like` : `${numLikes} likes`;

  const renderHumanReadableTime = () => dayjs.utc(created).local().fromNow();

  return (
    <div className="post" onClick={handleDoubleClick}>
      {/* Use PostBar for the post header */}
      <PostBar
        ownerUrl={ownerShowUrl}
        ownerImgUrl={ownerImgUrl}
        owner={owner}
        postShowUrl={postShowUrl}
        created={renderHumanReadableTime()}
      />

      <img src={imgUrl} alt="post_image" className="post-pic" />

      {/* Like button */}
      <div className="like-section">
        <button
          type="button"
          data-testid="like-unlike-button"
          onClick={handleLike}
        >
          {lognameLikesThis ? "Unlike" : "Like"}
        </button>
        <span>{renderLikesText()}</span>
      </div>

      {/* Comments section */}
      <div className="comments">
        {comments.map((comment) => (
          <div key={comment.commentid} className="comment">
            <p data-testid="comment-text">
              <a href={comment.ownerShowUrl}>
                <strong>{comment.owner}</strong>
              </a>
              : {comment.text}
            </p>
            {comment.lognameOwnsThis && (
              <button
                type="button"
                data-testid="delete-comment-button"
                onClick={() => handleDeleteComment(comment.commentid)}
              >
                Delete
              </button>
            )}
          </div>
        ))}

        {/* Comment submission form */}
        <form data-testid="comment-form" onSubmit={handleSubmitComment}>
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment"
          />
        </form>
      </div>
    </div>
  );
}

Post.propTypes = {
  url: PropTypes.string.isRequired,
};
