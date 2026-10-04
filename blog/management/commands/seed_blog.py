"""Populate the database with demo categories, tags, posts and comments.

Usage:
    python manage.py seed_blog            # add demo content (idempotent)
    python manage.py seed_blog --reset    # delete existing blog content first
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from blog.models import Category, Comment, Post, Tag

CATEGORIES = {
    "Frontend": "HTML, CSS, JavaScript and React — everything that runs in the browser.",
    "Backend": "APIs, databases and the server side of web applications.",
    "Design": "Layout, typography and building interfaces people enjoy using.",
    "Career": "Freelancing, learning and working with clients.",
}

POSTS = [
    ("Why Semantic HTML Still Matters", "Frontend", ["html", "accessibility"],
     "Semantic HTML is the foundation of an accessible, search-friendly website. Elements such as header, nav, main and article describe the meaning of content, not just how it looks.\n\nScreen readers rely on these landmarks to let people jump straight to what they need. Search engines use them to understand the structure of a page.\n\nBefore reaching for another div, ask whether a more meaningful element already exists. Most of the time, it does."),
    ("A Practical Guide to CSS Grid Layouts", "Frontend", ["css", "layout"],
     "CSS Grid makes two-dimensional layouts straightforward. With grid-template-columns and the repeat() function you can describe an entire page structure in a few lines.\n\nThe auto-fit keyword combined with minmax() creates responsive card grids without a single media query.\n\nUse Grid for the overall page and Flexbox for alignment inside components — the two work best together."),
    ("Designing REST APIs That Are Easy to Use", "Backend", ["api", "django", "node"],
     "A good API is predictable. Use plural nouns for resources, HTTP verbs for actions and consistent status codes for results.\n\nReturn helpful validation errors that point to the exact field that failed, so client developers can show useful messages.\n\nFinally, document every endpoint with an example request and response. Future you will be grateful."),
    ("Getting Started with Django Class-Based Views", "Backend", ["django", "python"],
     "Class-based views remove a lot of repetition from Django projects. ListView and DetailView handle querying, pagination and template rendering for you.\n\nOverride get_queryset to filter results and get_context_data to add extra variables to the template.\n\nWhen a view becomes hard to follow, a plain function-based view is still a perfectly good choice."),
    ("Choosing a Colour Palette for Your Next Website", "Design", ["design", "css"],
     "Start with one primary colour that reflects the brand, then add a neutral scale for text, borders and backgrounds.\n\nCheck contrast ratios early. Beautiful colours are not useful if people cannot read the text on top of them.\n\nStore your palette as CSS custom properties so a theme change is a single edit."),
    ("Typography Basics for Developers", "Design", ["design", "typography"],
     "Comfortable reading starts with a line length of roughly 60 to 75 characters and a generous line height.\n\nLimit yourself to two typefaces: one for headings and one for body text. Hierarchy comes from size and weight, not from more fonts.\n\nUse relative units so text scales with the user's browser settings."),
    ("React State: When to Lift It Up", "Frontend", ["react", "javascript"],
     "When two components need the same data, move that state to their closest common parent and pass it down as props.\n\nIf you find yourself passing props through many layers, React context or a small store can help.\n\nKeep state as local as possible by default. It makes components easier to reason about and to test."),
    ("Securing Node.js APIs: A Checklist", "Backend", ["node", "security", "api"],
     "Validate every input on the server, even when the frontend already does. Never trust data coming from the client.\n\nHash passwords with a slow algorithm such as bcrypt, keep secrets in environment variables and set sensible CORS rules.\n\nAdd rate limiting to authentication endpoints and keep dependencies up to date."),
    ("How to Write a Clear Project Proposal", "Career", ["freelancing", "communication"],
     "A clear proposal restates the client's problem in your own words, so both sides know you understood it.\n\nBreak the work into milestones with deliverables, and be explicit about what is not included.\n\nShort, specific proposals are easier to say yes to than long generic ones."),
    ("Learning by Building Real Projects", "Career", ["learning"],
     "Tutorials are a great start, but real understanding comes from building something end to end and fixing the problems along the way.\n\nPick a small project you would actually use. Ship it, then improve it.\n\nReading official documentation and other people's open-source code fills in the gaps that tutorials skip."),
    ("Making Forms Accessible", "Frontend", ["accessibility", "html"],
     "Every input needs a visible label connected with the for attribute. Placeholders are not a replacement for labels.\n\nShow error messages next to the field they describe and connect them with aria-describedby.\n\nMake sure the whole form can be completed using only the keyboard."),
    ("Pagination Patterns for Content Sites", "Backend", ["django", "performance"],
     "Offset pagination with page numbers is simple and works well for blogs and catalogues.\n\nFor very large or fast-changing datasets, cursor-based pagination avoids skipped or duplicated items.\n\nWhichever you choose, keep URLs shareable so readers can bookmark a page."),
    ("Dark Mode Without the Flash", "Design", ["css", "javascript"],
     "Read the saved theme before the first paint with a tiny inline script, then apply it as a data attribute on the html element.\n\nDefine colours as custom properties for each theme so components never hard-code a colour.\n\nRespect prefers-color-scheme as the default when the user has not chosen a theme."),
    ("Draft: Notes on Deployment Pipelines", "Backend", ["deployment"],
     "This post is still a draft and is only visible to staff in preview mode."),
]

COMMENTS = [
    ("Sara", "sara@example.com", "Really clear explanation, thanks for sharing!", True),
    ("Daniel", "daniel@example.com", "I've been doing this the hard way for years. Great tips.", True),
    ("Lina", "lina@example.com", "Could you write a follow-up with more examples?", True),
    ("Marco", "marco@example.com", "This comment is waiting for moderation.", False),
]


class Command(BaseCommand):
    help = "Seed the blog with demo categories, tags, posts and comments."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing posts, categories, tags and comments first.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write("Existing blog content removed.")

        User = get_user_model()
        author, created = User.objects.get_or_create(username="inkwell", defaults={"first_name": "Inkwell", "last_name": "Editor"})
        if created:
            author.set_unusable_password()
            author.save()

        cats = {name: Category.objects.get_or_create(name=name, defaults={"description": desc})[0] for name, desc in CATEGORIES.items()}
        now = timezone.now()
        new_posts = 0
        for i, (title, cat, tags, body) in enumerate(POSTS):
            is_draft = title.startswith("Draft:")
            post, made = Post.objects.get_or_create(
                title=title.removeprefix("Draft: "),
                defaults={
                    "author": author,
                    "category": cats[cat],
                    "body": body,
                    "status": Post.Status.DRAFT if is_draft else Post.Status.PUBLISHED,
                    "published_at": now - timedelta(days=3 * (len(POSTS) - i), hours=i),
                },
            )
            if not made:
                continue
            new_posts += 1
            post.tags.set([Tag.objects.get_or_create(name=t)[0] for t in tags])
            if not is_draft and i % 3 != 1:
                for name, email, text, approved in COMMENTS[: 2 + i % 3]:
                    Comment.objects.create(post=post, name=name, email=email, body=text, approved=approved)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {Category.objects.count()} categories, {Tag.objects.count()} tags, "
            f"{Post.objects.count()} posts ({new_posts} new), {Comment.objects.count()} comments "
            f"({Comment.objects.filter(approved=False).count()} awaiting moderation)."
        ))
