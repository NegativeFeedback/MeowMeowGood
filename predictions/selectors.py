from django.contrib.auth import get_user_model
from django.db.models import Count, F, FloatField, Q
from django.db.models.functions import Cast


def leaderboard(subject=None):
    """
    Users annotated with guesses_total, wins, and win_rate across closed polls,
    optionally restricted to polls about a specific subject user.
    """
    closed = Q(guesses__poll__actual_rating__isnull=False)
    won = Q(guesses__is_winner=True)
    if subject is not None:
        closed &= Q(guesses__poll__subject=subject)
        won &= Q(guesses__poll__subject=subject)

    return (
        get_user_model()
        .objects.annotate(
            guesses_total=Count("guesses", filter=closed),
            wins=Count("guesses", filter=won),
        )
        .filter(guesses_total__gt=0)
        .annotate(
            win_rate=Cast(F("wins"), FloatField()) / Cast(F("guesses_total"), FloatField()),
        )
        .order_by("-wins", "-win_rate", "username")
    )
