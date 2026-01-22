from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone 
from datetime import timedelta 


# Create your models here.

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=10, blank=True, null=True)
    auth_provider = models.CharField(max_length=20, default='email')
    is_blocked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
class OTPVerification(models.Model):
    PURPOSE_CHOICES = (
        ('signup', 'Signup'),
        ('forgot_password', 'Forgot Password'),
        ('email_change', 'Email Change'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    is_verified = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at 
    
    @staticmethod
    def get_expiry_time():
        return timezone.now() + timedelta(minutes=5)
    
    def __str__(self):
        return f'{self.user.email} - {self.purpose}'