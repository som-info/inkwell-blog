from io import StringIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Post


class BlogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_blog", verbosity=0, stdout=StringIO())

    def test_home_lists_published_posts_paginated(self):
        res = self.client.get(reverse("blog:post_list"))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context["is_paginated"])
        self.assertEqual(len(res.context["posts"]), 6)
        self.assertNotContains(res, "Notes on Deployment Pipelines")

    def test_second_page(self):
        res = self.client.get(reverse("blog:post_list") + "?page=2")
        self.assertEqual(res.status_code, 200)

    def test_draft_hidden_from_public_but_visible_to_staff(self):
        draft = Post.objects.get(status=Post.Status.DRAFT)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 404)
        staff = get_user_model().objects.create_user("editor", password="x-Strong-pass-1", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(draft.get_absolute_url()).status_code, 200)

    def test_category_and_tag_filters(self):
        res = self.client.get(reverse("blog:category", args=["design"]))
        self.assertTrue(all(p.category.slug == "design" for p in res.context["posts"]))
        res = self.client.get(reverse("blog:tag", args=["django"]))
        self.assertTrue(res.context["posts"])
        self.assertTrue(all(p.tags.filter(slug="django").exists() for p in res.context["posts"]))

    def test_search(self):
        res = self.client.get(reverse("blog:search"), {"q": "grid"})
        titles = [p.title for p in res.context["posts"]]
        self.assertIn("A Practical Guide to CSS Grid Layouts", titles)
        res = self.client.get(reverse("blog:search"), {"q": "zzzzzz"})
        self.assertContains(res, "No posts matched")

    def test_only_approved_comments_are_shown(self):
        post = Post.objects.published().filter(comments__approved=False).first()
        res = self.client.get(post.get_absolute_url())
        self.assertNotContains(res, "waiting for moderation")
        self.assertTrue(all(c.approved for c in res.context["comments"]))

    def test_new_comment_requires_moderation(self):
        post = Post.objects.published().first()
        res = self.client.post(post.get_absolute_url(), {"name": "Eve", "email": "eve@example.com", "body": "Nice article!"})
        self.assertEqual(res.status_code, 302)
        c = Comment.objects.get(name="Eve")
        self.assertFalse(c.approved)
        self.assertNotContains(self.client.get(post.get_absolute_url()), "Nice article!")

    def test_invalid_comment_shows_errors(self):
        post = Post.objects.published().first()
        res = self.client.post(post.get_absolute_url(), {"name": "", "email": "bad", "body": ""})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(Comment.objects.filter(email="bad").exists())

    def test_honeypot_blocks_spam(self):
        post = Post.objects.published().first()
        self.client.post(post.get_absolute_url(), {"name": "Bot", "email": "b@example.com", "body": "Buy now", "website": "http://spam"})
        self.assertFalse(Comment.objects.filter(name="Bot").exists())

    def test_seed_is_idempotent(self):
        before = Post.objects.count()
        call_command("seed_blog", stdout=StringIO())
        self.assertEqual(Post.objects.count(), before)

    def test_404_page(self):
        self.assertEqual(self.client.get("/post/does-not-exist/").status_code, 404)
