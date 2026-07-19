from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

admin.site.register(User, UserAdmin)

admin.site.site_header = "MeowMeowBeenz Administration"
admin.site.site_title = "MeowMeowBeenz Admin"
admin.site.index_title = "MeowMeowBeenz"
