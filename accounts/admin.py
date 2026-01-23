from django.contrib import admin
from .models import User 

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_blocked', 'is_staff', 'is_active')
    ordering = ('-created_at', )