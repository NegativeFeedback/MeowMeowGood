from functools import wraps

from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

User = get_user_model()

MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"


def superuser_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_superuser:
            return HttpResponseForbidden("Superuser access required.")
        return view(request, *args, **kwargs)

    return wrapper


@superuser_required
def user_list(request):
    return render(request, "accounts/user_list.html", {"users": User.objects.order_by("username")})


@superuser_required
def impersonate_start(request, user_id):
    if request.method != "POST":
        return redirect("accounts:user_list")

    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        return redirect("predictions:dashboard")

    original_id = request.user.pk
    login(request, target, backend=MODEL_BACKEND)
    request.session["impersonator_id"] = original_id
    return redirect("predictions:dashboard")


def impersonate_stop(request):
    if request.method != "POST":
        return redirect("predictions:dashboard")

    original_id = request.session.get("impersonator_id")
    if not original_id:
        return redirect("predictions:dashboard")

    original_user = get_object_or_404(User, pk=original_id)
    login(request, original_user, backend=MODEL_BACKEND)
    return redirect("predictions:dashboard")
