from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, ListView

from . import selectors
from .forms import GuessForm, PollForm, RevealForm
from .models import Guess, Poll
from .services import reveal_poll

User = get_user_model()


@login_required
def dashboard(request):
    open_polls = Poll.objects.filter(actual_rating__isnull=True)
    guessed_poll_ids = set(
        Guess.objects.filter(guesser=request.user).values_list("poll_id", flat=True)
    )

    awaiting_your_answer = open_polls.filter(subject=request.user)
    you_can_guess = open_polls.exclude(subject=request.user).exclude(pk__in=guessed_poll_ids)
    waiting_on_others = open_polls.exclude(subject=request.user).filter(pk__in=guessed_poll_ids)

    return render(
        request,
        "predictions/dashboard.html",
        {
            "awaiting_your_answer": awaiting_your_answer,
            "you_can_guess": you_can_guess,
            "waiting_on_others": waiting_on_others,
        },
    )


class PollCreateView(LoginRequiredMixin, CreateView):
    model = Poll
    form_class = PollForm
    template_name = "predictions/poll_form.html"

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


@login_required
def poll_detail(request, pk):
    poll = get_object_or_404(Poll, pk=pk)
    is_subject = poll.subject_id == request.user.id
    my_guess = Guess.objects.filter(poll=poll, guesser=request.user).first()
    can_guess = (not poll.is_closed) and (not is_subject) and (my_guess is None)
    guess_count = poll.guesses.count()

    context = {
        "poll": poll,
        "is_subject": is_subject,
        "my_guess": my_guess,
        "can_guess": can_guess,
        "guess_count": guess_count,
    }

    if can_guess:
        context["guess_form"] = GuessForm()
    if is_subject and not poll.is_closed:
        context["reveal_form"] = RevealForm()
    if poll.is_closed:
        context["guesses"] = poll.guesses.select_related("guesser").all()

    return render(request, "predictions/poll_detail.html", context)


@login_required
def poll_guess(request, pk):
    if request.method != "POST":
        return redirect("predictions:poll_detail", pk=pk)

    poll = get_object_or_404(Poll, pk=pk)

    if poll.subject_id == request.user.id:
        return HttpResponseForbidden("The subject of a poll cannot guess on their own poll.")

    if poll.is_closed:
        messages.error(request, "That poll is already closed.")
        return redirect("predictions:poll_detail", pk=pk)

    if Guess.objects.filter(poll=poll, guesser=request.user).exists():
        messages.info(request, "You've already guessed on this poll.")
        return redirect("predictions:poll_detail", pk=pk)

    form = GuessForm(request.POST)
    if form.is_valid():
        guess = form.save(commit=False)
        guess.poll = poll
        guess.guesser = request.user
        try:
            guess.full_clean()
            guess.save()
            messages.success(request, "Your guess has been recorded.")
        except (ValidationError, IntegrityError):
            messages.error(
                request,
                "Your guess could not be saved — the poll may have just closed, or you may have already guessed.",
            )
    else:
        messages.error(request, "Please enter a rating between 1.00 and 5.00.")

    return redirect("predictions:poll_detail", pk=pk)


@login_required
def poll_reveal(request, pk):
    if request.method != "POST":
        return redirect("predictions:poll_detail", pk=pk)

    poll = get_object_or_404(Poll, pk=pk)

    if poll.subject_id != request.user.id:
        return HttpResponseForbidden("Only the subject of this poll can reveal the answer.")

    if poll.is_closed:
        messages.info(request, "This poll is already closed.")
        return redirect("predictions:poll_detail", pk=pk)

    form = RevealForm(request.POST)
    if form.is_valid():
        reveal_poll(poll, form.cleaned_data["actual_rating"])
        messages.success(request, "Poll closed — results are now visible.")
    else:
        messages.error(request, "Please enter a rating between 1.00 and 5.00.")

    return redirect("predictions:poll_detail", pk=pk)


class HistoryListView(LoginRequiredMixin, ListView):
    model = Poll
    template_name = "predictions/history_list.html"
    context_object_name = "polls"
    paginate_by = 20

    def get_queryset(self):
        return (
            Poll.objects.filter(actual_rating__isnull=False)
            .order_by("-closed_at")
            .select_related("subject", "creator")
            .prefetch_related("guesses__guesser")
        )


@login_required
def leaderboard_overall(request):
    return render(request, "predictions/leaderboard_overall.html", {"rows": selectors.leaderboard()})


@login_required
def leaderboard_subject_index(request):
    subjects = User.objects.filter(
        pk__in=Poll.objects.filter(actual_rating__isnull=False)
        .values_list("subject_id", flat=True)
        .distinct()
    ).order_by("username")
    return render(request, "predictions/leaderboard_subject_index.html", {"subjects": subjects})


@login_required
def leaderboard_subject_detail(request, user_id):
    subject = get_object_or_404(User, pk=user_id)
    return render(
        request,
        "predictions/leaderboard_subject_detail.html",
        {"subject": subject, "rows": selectors.leaderboard(subject=subject)},
    )
