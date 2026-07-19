from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from predictions.models import Guess, Poll
from predictions.services import reveal_poll

User = get_user_model()


class RevealPollTests(TestCase):
    def setUp(self):
        self.subject = User.objects.create_user("subject")
        self.creator = User.objects.create_user("creator")
        self.poll = Poll.objects.create(subject=self.subject, creator=self.creator, item_name="A Movie")

    def test_reveal_closes_poll_and_marks_single_winner(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        Guess.objects.create(poll=self.poll, guesser=alice, value=4)
        Guess.objects.create(poll=self.poll, guesser=bob, value=2)

        reveal_poll(self.poll, actual_rating=5)

        self.poll.refresh_from_db()
        self.assertTrue(self.poll.is_closed)
        self.assertEqual(self.poll.actual_rating, 5)
        self.assertTrue(Guess.objects.get(guesser=alice).is_winner)
        self.assertFalse(Guess.objects.get(guesser=bob).is_winner)

    def test_reveal_marks_all_tied_guessers_as_winners(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        Guess.objects.create(poll=self.poll, guesser=alice, value=3)
        Guess.objects.create(poll=self.poll, guesser=bob, value=5)

        reveal_poll(self.poll, actual_rating=4)

        self.assertTrue(Guess.objects.get(guesser=alice).is_winner)
        self.assertTrue(Guess.objects.get(guesser=bob).is_winner)

    def test_reveal_with_zero_guesses_does_not_error(self):
        reveal_poll(self.poll, actual_rating=3)
        self.poll.refresh_from_db()
        self.assertTrue(self.poll.is_closed)

    def test_reveal_is_idempotent(self):
        reveal_poll(self.poll, actual_rating=3)
        reveal_poll(self.poll, actual_rating=5)
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.actual_rating, 3)

    def test_reveal_picks_closest_decimal_guess(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        Guess.objects.create(poll=self.poll, guesser=alice, value=Decimal("4.10"))
        Guess.objects.create(poll=self.poll, guesser=bob, value=Decimal("4.30"))

        reveal_poll(self.poll, actual_rating=Decimal("4.15"))

        self.assertTrue(Guess.objects.get(guesser=alice).is_winner)
        self.assertFalse(Guess.objects.get(guesser=bob).is_winner)
