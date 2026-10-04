from django.db.models import Count, Q

from .models import Category, Post, Tag


def sidebar(request):
    """Categories, popular tags and recent posts for the sidebar (skipped for the admin)."""
    if request.path.startswith("/admin/"):
        return {}
    published = Q(posts__status=Post.Status.PUBLISHED)
    return {
        "sidebar_categories": Category.objects.annotate(num_posts=Count("posts", filter=published)).filter(num_posts__gt=0),
        "sidebar_tags": Tag.objects.annotate(num_posts=Count("posts", filter=published)).filter(num_posts__gt=0).order_by("-num_posts", "name")[:15],
        "sidebar_recent": Post.objects.published().only("title", "slug", "published_at")[:5],
    }
