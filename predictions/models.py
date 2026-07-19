from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

RATING_VALIDATORS = [MinValueValidator(Decimal("1.00")), MaxValueValidator(Decimal("5.00"))]


class Poll(models.Model):
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="polls_about_me",
        help_text="The person whose real rating is being predicted.",
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="polls_created",
    )
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="poll_images/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    actual_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=RATING_VALIDATORS,
        help_text="Set once, by the subject, at reveal time. Null while open.",
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.item_name} (subject: {self.subject})"

    @property
    def is_closed(self) -> bool:
        return self.actual_rating is not None

    def get_absolute_url(self):
        return reverse("predictions:poll_detail", args=[self.pk])


class Guess(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="guesses")
    guesser = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guesses"
    )
    value = models.DecimalField(max_digits=3, decimal_places=2, validators=RATING_VALIDATORS)
    created_at = models.DateTimeField(auto_now_add=True)
    is_winner = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["poll", "guesser"], name="unique_guess_per_poll_per_user"),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.guesser}: {self.value} on {self.poll_id}"

    def clean(self):
        if self.poll_id and self.guesser_id == self.poll.subject_id:
            raise ValidationError("The subject of a poll cannot guess on their own poll.")
        if self.poll_id and self.poll.is_closed:
            raise ValidationError("This poll is closed; guesses can no longer be submitted.")

    @property
    def distance(self):
        if self.poll.actual_rating is None:
            return None
        return abs(self.value - self.poll.actual_rating)
