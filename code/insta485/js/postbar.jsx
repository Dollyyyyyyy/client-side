import React from "react";
import PropTypes from "prop-types";
import ProfilePic from "./profile_pic";

// The parameter of this function is an object with a string called url inside it.
// url is a prop for the Post component.
export default function PostBar({
  ownerUrl,
  ownerImgUrl,
  owner,
  postShowUrl,
  created,
}) {
  /* Display image and post owner of a single post */

  // Render post image and post owner
  return (
    <div className="post_bar">
      <ProfilePic ownerUrl={ownerUrl} ownerImgUrl={ownerImgUrl} owner={owner} />
      <div className="owner_name">
        <a href={ownerUrl}>{owner}</a>
      </div>
      <div className="timestamp" style={{ marginLeft: "auto" }}>
        <a href={postShowUrl}>{created}</a>
      </div>
    </div>
  );
}

PostBar.propTypes = {
  ownerUrl: PropTypes.string.isRequired,
  ownerImgUrl: PropTypes.string.isRequired,
  owner: PropTypes.string.isRequired,
  postShowUrl: PropTypes.string.isRequired,
  created: PropTypes.string.isRequired,
};
