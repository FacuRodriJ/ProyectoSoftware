import uuid
from django.db import models
from django_softdelete.models import SoftDeleteModel, SoftDeleteManager
from PIL import Image
from django.conf import settings
from django.contrib.auth import get_user_model


class Club(SoftDeleteModel):
    nombre = models.CharField(max_length=255, verbose_name='Nombre')
    localidad = models.ForeignKey('parameters.Localidad', on_delete=models.PROTECT)
    direccion = models.CharField(max_length=255, verbose_name='Dirección')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def logo_directory_path(self, filename):
        """Método para obtener la ruta de la imagen del logo del club."""
        return 'img/club_logo/{0}/{1}'.format(self.id, filename)

    logo = models.ImageField(upload_to=logo_directory_path, null=True, blank=True, verbose_name='Logo')

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        """Método save() sobrescrito para redimensionar la imagen."""
        super().save(*args, **kwargs)
        try:
            img = Image.open(self.logo.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.logo.path)
        except Exception as e:
            print(e)

    def get_logo(self):
        """Método para obtener la imagen de perfil del usuario."""
        try:
            return self.logo.url
        except Exception as e:
            print(e)
            return settings.STATIC_URL + 'img/empty.svg'

    class Meta:
        unique_together = ('localidad', 'direccion')
        verbose_name = 'Club'
        verbose_name_plural = "Clubes"
        ordering = ['id']


class Cancha(models.Model):
    numero = models.SmallIntegerField(verbose_name='Número')
    deporte = models.ForeignKey('parameters.Deporte', on_delete=models.PROTECT)
    superficie = models.ForeignKey('parameters.Superficie', on_delete=models.PROTECT)
    techado = models.BooleanField(default=False, verbose_name='¿Es techada?')
    iluminacion = models.BooleanField(default=False, verbose_name='Iluminación')
    precio = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='Precio por hora')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Cancha {0} - {1}'.format(self.numero, self.deporte)

    class Meta:
        unique_together = ('numero', 'deporte')
        verbose_name = 'Cancha'
        verbose_name_plural = "Canchas"


class Socio(SoftDeleteModel):
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    categoria = models.ForeignKey('parameters.SocioCategoria', on_delete=models.PROTECT)
    localidad = models.ForeignKey('parameters.Localidad', on_delete=models.PROTECT)
    direccion = models.CharField(max_length=255, verbose_name='Dirección')
    is_inscripto = models.BooleanField(default=False, verbose_name='¿Está inscripto?')
    estado = models.ForeignKey('parameters.SocioEstado', on_delete=models.PROTECT, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
