import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import InfiniteScroll from "react-infinite-scroll-component";
import Post from "./post";

export default function Feed({ feedUrl }) {
  const [posts, setPosts] = useState([]);
  const [nextUrl, setNextUrl] = useState(feedUrl);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Reset posts when feedUrl changes
    setPosts([]);
    setHasMore(true);
    setNextUrl(feedUrl);
    setLoading(true);

    // Fetch initial posts
    fetch(feedUrl, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch posts");
        }
        return response.json();
      })
      .then((data) => {
        setPosts(data.results);
        setNextUrl(data.next);
        setHasMore(!!data.next);
        setLoading(false);
      })
      .catch((error) => {
        console.log(error);
        setLoading(false);
      });
  }, [feedUrl]);

  const loadMorePosts = () => {
    if (!nextUrl) return;

    fetch(nextUrl, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch more posts");
        }
        return response.json();
      })
      .then((data) => {
        setPosts((prevPosts) => [...prevPosts, ...data.results]);
        setNextUrl(data.next);
        setHasMore(!!data.next);
      })
      .catch((error) => {
        console.log(error);
        setHasMore(false);
      });
  };

  if (loading) {
    return <div>Loading posts...</div>;
  }

  return (
    <div className="feed">
      <InfiniteScroll
        dataLength={posts.length}
        next={loadMorePosts}
        hasMore={hasMore}
        loader={<h4>Loading more posts...</h4>}
        endMessage={<p>No more posts to load</p>}
      >
        {posts.map((post) => (
          <Post key={post.postid} url={post.url} />
        ))}
      </InfiniteScroll>
    </div>
  );
}

Feed.propTypes = {
  feedUrl: PropTypes.string.isRequired,
};
