from django.contrib import admin
from django_adelaidex.lti.models import User

class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('password',)
    list_display = ('username', 'first_name', 'is_staff',)
    list_filter = ('is_staff', 'is_active',)

admin.site.register(User, UserAdmin)
