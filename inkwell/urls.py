from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Inkwell administration"
admin.site.site_title = "Inkwell admin"
admin.site.index_title = "Content & moderation"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("blog.urls")),
]

handler404 = "blog.views.not_found"
