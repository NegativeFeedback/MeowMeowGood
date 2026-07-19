from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Guess, Poll


def reveal_poll(poll: Poll, actual_rating: Decimal) -> Poll:
    """Locks the poll with the subject's real rating and scores all guesses."""
    with transaction.atomic():
        poll = Poll.objects.select_for_update().get(pk=poll.pk)
        if poll.is_closed:
            return poll

        poll.actual_rating = actual_rating
        poll.closed_at = timezone.now()
        poll.full_clean()
        poll.save()

        guesses = list(poll.guesses.all())
        if guesses:
            min_distance = min(abs(g.value - actual_rating) for g in guesses)
            winner_ids = [g.pk for g in guesses if abs(g.value - actual_rating) == min_distance]
            Guess.objects.filter(pk__in=winner_ids).update(is_winner=True)

        return poll
