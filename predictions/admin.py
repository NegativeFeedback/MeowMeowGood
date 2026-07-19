from django.contrib import admin

from .models import Guess, Poll


class GuessInline(admin.TabularInline):
    model = Guess
    extra = 0
    readonly_fields = ["guesser", "value", "created_at", "is_winner"]
    can_delete = False


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ["item_name", "subject", "creator", "actual_rating", "is_closed", "created_at"]
    list_filter = ["actual_rating"]
    search_fields = ["item_name", "category"]
    inlines = [GuessInline]


@admin.register(Guess)
class GuessAdmin(admin.ModelAdmin):
    list_display = ["poll", "guesser", "value", "is_winner", "created_at"]
    list_filter = ["is_winner"]
