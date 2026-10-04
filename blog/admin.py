from django.contrib import admin
from django.db.models import Count

from .models import Category, Comment, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "post_count"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_posts=Count("posts"))

    @admin.display(description="Posts", ordering="_posts")
    def post_count(self, obj):
        return obj._posts


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    search_fields = ["name"]


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ["name", "email", "body", "approved", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status", "published_at", "author"]
    list_filter = ["status", "category", "tags", "published_at"]
    list_editable = ["status"]
    search_fields = ["title", "excerpt", "body"]
    prepopulated_fields = {"slug": ["title"]}
    filter_horizontal = ["tags"]
    date_hierarchy = "published_at"
    autocomplete_fields = ["category"]
    inlines = [CommentInline]
    actions = ["make_published", "make_draft"]

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Publish selected posts")
    def make_published(self, request, queryset):
        updated = queryset.update(status=Post.Status.PUBLISHED)
        self.message_user(request, f"{updated} post(s) published.")

    @admin.action(description="Move selected posts to draft")
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f"{updated} post(s) moved to draft.")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["name", "post", "short_body", "approved", "created_at"]
    list_filter = ["approved", "created_at"]
    list_editable = ["approved"]
    search_fields = ["name", "email", "body"]
    actions = ["approve", "unapprove"]

    @admin.display(description="Comment")
    def short_body(self, obj):
        return obj.body if len(obj.body) <= 60 else obj.body[:57] + "…"

    @admin.action(description="Approve selected comments")
    def approve(self, request, queryset):
        self.message_user(request, f"{queryset.update(approved=True)} comment(s) approved.")

    @admin.action(description="Unapprove selected comments")
    def unapprove(self, request, queryset):
        self.message_user(request, f"{queryset.update(approved=False)} comment(s) hidden.")
