from django.urls import path

from . import views

app_name = "predictions"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("polls/new/", views.PollCreateView.as_view(), name="poll_create"),
    path("polls/<int:pk>/", views.poll_detail, name="poll_detail"),
    path("polls/<int:pk>/guess/", views.poll_guess, name="poll_guess"),
    path("polls/<int:pk>/reveal/", views.poll_reveal, name="poll_reveal"),
    path("history/", views.HistoryListView.as_view(), name="history"),
    path("leaderboard/", views.leaderboard_overall, name="leaderboard_overall"),
    path("leaderboard/subjects/", views.leaderboard_subject_index, name="leaderboard_subject_index"),
    path("leaderboard/subjects/<int:user_id>/", views.leaderboard_subject_detail, name="leaderboard_subject_detail"),
]
