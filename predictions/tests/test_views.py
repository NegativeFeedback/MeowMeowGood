from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from predictions.models import Guess, Poll

User = get_user_model()


class PollGuessViewTests(TestCase):
    def setUp(self):
        self.subject = User.objects.create_user("subject")
        self.creator = User.objects.create_user("creator")
        self.guesser = User.objects.create_user("guesser")
        self.poll = Poll.objects.create(subject=self.subject, creator=self.creator, item_name="A Beer")

    def test_subject_cannot_guess_via_view(self):
        self.client.force_login(self.subject)
        response = self.client.post(reverse("predictions:poll_guess", args=[self.poll.pk]), {"value": 3})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Guess.objects.filter(poll=self.poll, guesser=self.subject).exists())

    def test_guess_rejected_after_poll_closed(self):
        self.poll.actual_rating = 4
        self.poll.save()
        self.client.force_login(self.guesser)
        response = self.client.post(
            reverse("predictions:poll_guess", args=[self.poll.pk]), {"value": 3}, follow=True
        )
        self.assertFalse(Guess.objects.filter(poll=self.poll, guesser=self.guesser).exists())
        self.assertContains(response, "already closed")

    def test_valid_guess_recorded(self):
        self.client.force_login(self.guesser)
        self.client.post(reverse("predictions:poll_guess", args=[self.poll.pk]), {"value": 3})
        self.assertTrue(Guess.objects.filter(poll=self.poll, guesser=self.guesser, value=3).exists())


class PollRevealViewTests(TestCase):
    def setUp(self):
        self.subject = User.objects.create_user("subject")
        self.creator = User.objects.create_user("creator")
        self.other = User.objects.create_user("other")
        self.poll = Poll.objects.create(subject=self.subject, creator=self.creator, item_name="A Movie")

    def test_only_subject_can_reveal(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("predictions:poll_reveal", args=[self.poll.pk]), {"actual_rating": 4})
        self.assertEqual(response.status_code, 403)
        self.poll.refresh_from_db()
        self.assertFalse(self.poll.is_closed)

    def test_subject_can_reveal(self):
        self.client.force_login(self.subject)
        self.client.post(reverse("predictions:poll_reveal", args=[self.poll.pk]), {"actual_rating": 4})
        self.poll.refresh_from_db()
        self.assertTrue(self.poll.is_closed)
        self.assertEqual(self.poll.actual_rating, 4)


class DashboardViewTests(TestCase):
    def setUp(self):
        self.zach = User.objects.create_user("zach")
        self.sam = User.objects.create_user("sam")

    def test_dashboard_buckets_polls_correctly(self):
        awaiting = Poll.objects.create(subject=self.zach, creator=self.sam, item_name="Awaiting")
        can_guess = Poll.objects.create(subject=self.sam, creator=self.sam, item_name="CanGuess")
        already_guessed = Poll.objects.create(subject=self.sam, creator=self.sam, item_name="AlreadyGuessed")
        Guess.objects.create(poll=already_guessed, guesser=self.zach, value=3)

        self.client.force_login(self.zach)
        response = self.client.get(reverse("predictions:dashboard"))

        self.assertContains(response, "Awaiting")
        self.assertContains(response, "CanGuess")
        self.assertContains(response, "AlreadyGuessed")
        self.assertIn(awaiting, response.context["awaiting_your_answer"])
        self.assertIn(can_guess, response.context["you_can_guess"])
        self.assertIn(already_guessed, response.context["waiting_on_others"])
