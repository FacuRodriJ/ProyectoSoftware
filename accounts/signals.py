from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Funcion para crear un perfil de usuario cuando se crea un usuario."""
    Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """Funcion para guardar el perfil de usuario cuando se guarda un usuario."""
    instance.profile.save()
