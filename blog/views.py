from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .forms import CommentForm
from .models import Category, Post, Tag


class PostListView(ListView):
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = settings.BLOG_POSTS_PER_PAGE
    heading = "Latest posts"

    def get_queryset(self):
        return Post.objects.published().select_related("category", "author").prefetch_related("tags")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("heading", self.heading)
        return ctx


class CategoryPostListView(PostListView):
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return super().get_queryset().filter(category=self.category)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(heading=f"Category: {self.category.name}", subheading=self.category.description, active_category=self.category)
        return ctx


class TagPostListView(PostListView):
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        return super().get_queryset().filter(tags=self.tag)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(heading=f"Tagged “{self.tag.name}”", active_tag=self.tag)
        return ctx


class SearchView(PostListView):
    template_name = "blog/search.html"

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()[:100]
        if not self.query:
            return Post.objects.none()
        q = Q()
        for word in self.query.split()[:8]:
            q &= Q(title__icontains=word) | Q(excerpt__icontains=word) | Q(body__icontains=word) | Q(tags__name__icontains=word) | Q(category__name__icontains=word)
        return super().get_queryset().filter(q).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(query=self.query, heading="Search")
        return ctx


class PostDetailView(DetailView):
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        qs = Post.objects.select_related("category", "author").prefetch_related("tags")
        # Staff can preview drafts; everyone else only sees published posts.
        return qs if self.request.user.is_staff else qs.published()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object
        ctx["comments"] = post.comments.filter(approved=True)
        ctx.setdefault("form", CommentForm())
        ctx["related"] = (
            Post.objects.published().filter(category=post.category).exclude(pk=post.pk)[:3] if post.category_id else []
        )
        ctx["previous_post"] = Post.objects.published().filter(published_at__lt=post.published_at).first()
        ctx["next_post"] = Post.objects.published().filter(published_at__gt=post.published_at).order_by("published_at").first()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.approved = False  # every comment is moderated
            comment.save()
            messages.success(request, "Thanks! Your comment was received and will appear once it has been approved.")
            return redirect(self.object.get_absolute_url() + "#comments")
        messages.error(request, "Please correct the errors below.")
        return self.render_to_response(self.get_context_data(form=form), status=400)


def not_found(request, exception):
    return render(request, "404.html", status=404)
