from django.contrib import admin
from .models import CustomUser, Country, Data, DashboardURL


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'user_type', 'get_email', 'country', 'data', 'is_verified', 'created_at']
    list_filter = ['user_type', 'country', 'is_verified', 'created_at']
    search_fields = ['django_user__username', 'django_user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Info', {'fields': ('django_user', 'phone_number')}),
        ('Account Details', {'fields': ('user_type', 'is_verified')}),
        ('Assignments', {'fields': ('country', 'data', 'dashboard_url')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_username(self, obj):
        return obj.django_user.username
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.django_user.email
    get_email.short_description = 'Email'


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(Data)
class DataAdmin(admin.ModelAdmin):
    list_display = ['name', 'data_type', 'created_at']
    list_filter = ['data_type', 'created_at']
    search_fields = ['name', 'data_type']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DashboardURL)
class DashboardURLAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'created_at']
    search_fields = ['name', 'url']
    readonly_fields = ['created_at']
