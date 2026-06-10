from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserSession


@receiver(post_save, sender=User)
def create_user_session(sender, instance, created, **kwargs):
    """Create a UserSession when a new user is created"""
    if created:
        UserSession.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_session(sender, instance, **kwargs):
    """Save user session when user is saved"""
    instance.dermacare_session.save()
