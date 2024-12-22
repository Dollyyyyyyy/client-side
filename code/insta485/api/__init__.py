"""Insta485 REST API."""

from insta485.api.posts import get_post_detail
from insta485.api.posts import get_posts
from insta485.api.resources import get_resources
from insta485.api.likes import post_like
from insta485.api.likes import delete_like
from insta485.api.comments import post_comment
from insta485.api.comments import delete_comment

from insta485.api.test import posts_test
from insta485.api.test import likes_test
from insta485.api.test import comments_test
