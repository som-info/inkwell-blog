from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class SlugMixin(models.Model):
    """Fills `slug` from `name`/`title` when left blank."""

    slug_source = "name"

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(getattr(self, self.slug_source))[:200] or "item"
            slug, n = base, 2
            while type(self).objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Category(SlugMixin):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("blog:category", args=[self.slug])


class Tag(SlugMixin):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("blog:tag", args=[self.slug])


class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())


class Post(SlugMixin):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    slug_source = "title"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="posts")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    excerpt = models.CharField(max_length=300, blank=True, help_text="Short summary shown in lists. Generated from the body if empty.")
    body = models.TextField(help_text="Plain text. Separate paragraphs with a blank line.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PublishedQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at"]
        indexes = [models.Index(fields=["status", "-published_at"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.excerpt:
            text = " ".join(self.body.split())
            self.excerpt = text if len(text) <= 200 else text[:197].rsplit(" ", 1)[0].rstrip(".,;:!?") + "…"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[self.slug])

    @property
    def reading_time(self):
        return max(1, round(len(self.body.split()) / 200))


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=80)
    email = models.EmailField(help_text="Never shown publicly.")
    body = models.TextField(max_length=2000)
    approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.name} on {self.post}"
