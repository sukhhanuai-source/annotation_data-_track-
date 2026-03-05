from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.core.validators import RegexValidator

# Country Table
class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# Data Table
class Data(models.Model):
    name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ['-created_at']


# Dashboard URLs Table
class DashboardURL(models.Model):
    name = models.CharField(max_length=100, unique=True)
    url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Custom User Model
class CustomUser(models.Model):
    USER_TYPE_CHOICES = (
        ('worker', 'Worker'),
        ('admin', 'Admin'),
    )

    django_user = models.OneToOneField(DjangoUser, on_delete=models.CASCADE, related_name='custom_profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='worker')
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')]
    )
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    data = models.ForeignKey(Data, on_delete=models.SET_NULL, null=True, blank=True, related_name='workers')
    dashboard_url = models.ForeignKey(DashboardURL, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_verified = models.BooleanField(default=False, help_text='Admin verification status')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.django_user.username} ({self.user_type})"

    class Meta:
        ordering = ['-created_at']
