from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model

from .models import Guess, Poll
from .widgets import CatRatingWidget

User = get_user_model()


class PollForm(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("username"),
        label="Who is this poll about?",
    )

    class Meta:
        model = Poll
        fields = ["subject", "item_name", "category", "image"]
        labels = {
            "item_name": "What are they rating?",
            "category": "Category (optional)",
            "image": "Reaction picture (optional)",
        }


class GuessForm(forms.ModelForm):
    class Meta:
        model = Guess
        fields = ["value"]
        labels = {"value": "Your guess"}
        widgets = {"value": CatRatingWidget(attrs={"aria-label": "Your guess"})}


class RevealForm(forms.Form):
    actual_rating = forms.DecimalField(
        min_value=Decimal("1.00"),
        max_value=Decimal("5.00"),
        max_digits=3,
        decimal_places=2,
        label="Your real rating",
        widget=CatRatingWidget(attrs={"aria-label": "Your real rating"}),
    )
