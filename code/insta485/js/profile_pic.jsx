import React from "react";
import PropTypes from "prop-types";

// The parameter of this function is an object with a string called url inside it.
// url is a prop for the Post component.
export default function ProfilePic({ ownerUrl, ownerImgUrl, owner }) {
  /* Display image and post owner of a single post */

  // Render post image and post owner
  return (
    <a href={ownerUrl}>
      <img src={ownerImgUrl} alt={owner} className="profile_pic" />
    </a>
  );
}

ProfilePic.propTypes = {
  ownerUrl: PropTypes.string.isRequired,
  ownerImgUrl: PropTypes.string.isRequired,
  owner: PropTypes.string.isRequired,
};
