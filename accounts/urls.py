from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.user_list, name="user_list"),
    path("<int:user_id>/impersonate/", views.impersonate_start, name="impersonate_start"),
    path("stop-impersonating/", views.impersonate_stop, name="impersonate_stop"),
]
