from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from predictions.models import Guess, Poll

User = get_user_model()


class GuessConstraintTests(TestCase):
    def setUp(self):
        self.subject = User.objects.create_user("subject")
        self.creator = User.objects.create_user("creator")
        self.guesser = User.objects.create_user("guesser")
        self.poll = Poll.objects.create(subject=self.subject, creator=self.creator, item_name="A Beer")

    def test_subject_cannot_guess_on_own_poll(self):
        guess = Guess(poll=self.poll, guesser=self.subject, value=3)
        with self.assertRaises(ValidationError):
            guess.clean()

    def test_guess_rejected_after_close(self):
        self.poll.actual_rating = 4
        self.poll.save()
        guess = Guess(poll=self.poll, guesser=self.guesser, value=3)
        with self.assertRaises(ValidationError):
            guess.clean()

    def test_one_guess_per_user_per_poll(self):
        Guess.objects.create(poll=self.poll, guesser=self.guesser, value=3)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Guess.objects.create(poll=self.poll, guesser=self.guesser, value=5)

    def test_is_closed_derived_from_actual_rating(self):
        self.assertFalse(self.poll.is_closed)
        self.poll.actual_rating = 2
        self.assertTrue(self.poll.is_closed)

    def test_guess_supports_two_decimal_places(self):
        guess = Guess.objects.create(poll=self.poll, guesser=self.guesser, value=Decimal("4.25"))
        guess.refresh_from_db()
        self.assertEqual(guess.value, Decimal("4.25"))

    def test_distance_is_computed_to_two_decimal_places(self):
        self.poll.actual_rating = Decimal("4.30")
        self.poll.save()
        guess = Guess.objects.create(poll=self.poll, guesser=self.guesser, value=Decimal("4.05"))
        self.assertEqual(guess.distance, Decimal("0.25"))
