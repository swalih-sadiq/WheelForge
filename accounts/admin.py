from django.contrib import admin
from .models import User 

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_blocked', 'is_staff', 'is_active')
    ordering = ('-created_at', )

    search_fields = ('email',)

    list_filter = ('is_active', 'is_blocked')

    # hide admin/staff users from admin list + searc
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_staff=False, is_superuser=False)
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        queryset = queryset.filter(
            is_staff=False,
            is_superuser=False
        )
        return queryset, use_distinct
    
    # prevent editing admin users via direct URL
    def has_change_permission(self, request, obj=None):
        if obj and (obj.is_staff or obj.is_superuser):
            return False
        return super().has_change_permission(request, obj)
    
    # prevent deleting admin users
    def has_delete_permission(self, request, obj=None):
        if obj and (obj.is_staff or obj.is_superuser):
            return False
        return super().has_delete_permission(request, obj)