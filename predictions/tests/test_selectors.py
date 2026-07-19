from django.contrib.auth import get_user_model
from django.test import TestCase

from predictions.models import Poll
from predictions.selectors import leaderboard
from predictions.services import reveal_poll

User = get_user_model()


class LeaderboardTests(TestCase):
    def setUp(self):
        self.zach = User.objects.create_user("zach")
        self.sam = User.objects.create_user("sam")
        self.alice = User.objects.create_user("alice")
        self.bob = User.objects.create_user("bob")

    def _poll(self, subject, creator):
        return Poll.objects.create(subject=subject, creator=creator, item_name="Item")

    def test_wins_and_win_rate(self):
        poll1 = self._poll(self.zach, self.zach)
        poll1.guesses.create(guesser=self.alice, value=4)
        poll1.guesses.create(guesser=self.bob, value=1)
        reveal_poll(poll1, actual_rating=5)  # alice wins

        poll2 = self._poll(self.zach, self.zach)
        poll2.guesses.create(guesser=self.alice, value=1)
        poll2.guesses.create(guesser=self.bob, value=3)
        reveal_poll(poll2, actual_rating=3)  # bob wins

        rows = {row.username: row for row in leaderboard()}
        self.assertEqual(rows["alice"].wins, 1)
        self.assertEqual(rows["alice"].guesses_total, 2)
        self.assertAlmostEqual(rows["alice"].win_rate, 0.5)
        self.assertEqual(rows["bob"].wins, 1)
        self.assertEqual(rows["bob"].guesses_total, 2)

    def test_tie_counts_as_win_for_both(self):
        poll = self._poll(self.zach, self.zach)
        poll.guesses.create(guesser=self.alice, value=3)
        poll.guesses.create(guesser=self.bob, value=5)
        reveal_poll(poll, actual_rating=4)  # tie: both off by 1

        rows = {row.username: row for row in leaderboard()}
        self.assertEqual(rows["alice"].wins, 1)
        self.assertEqual(rows["bob"].wins, 1)

    def test_per_subject_leaderboard_is_scoped(self):
        poll_about_zach = self._poll(self.zach, self.zach)
        poll_about_zach.guesses.create(guesser=self.alice, value=5)
        reveal_poll(poll_about_zach, actual_rating=5)

        poll_about_sam = self._poll(self.sam, self.sam)
        poll_about_sam.guesses.create(guesser=self.alice, value=1)
        reveal_poll(poll_about_sam, actual_rating=5)

        zach_rows = {row.username: row for row in leaderboard(subject=self.zach)}
        self.assertEqual(zach_rows["alice"].guesses_total, 1)
        self.assertEqual(zach_rows["alice"].wins, 1)

    def test_zero_guess_poll_excluded_from_leaderboard(self):
        poll = self._poll(self.zach, self.zach)
        reveal_poll(poll, actual_rating=3)
        self.assertEqual(list(leaderboard()), [])

    def test_open_polls_excluded_from_leaderboard(self):
        poll = self._poll(self.zach, self.zach)
        poll.guesses.create(guesser=self.alice, value=3)
        rows = {row.username: row for row in leaderboard()}
        self.assertNotIn("alice", rows)
