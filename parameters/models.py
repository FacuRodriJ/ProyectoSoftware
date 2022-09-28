from django.db import models
from django.utils.translation import gettext_lazy as _


# PARAMETROS DEL SISTEMA
# Parametros para perfiles de usuario
class Genero(models.Model):
    """Modelo para almacenar los generos de los usuarios."""
    genero = models.CharField(max_length=20, verbose_name=_('Género'))

    class Meta:
        verbose_name = _('Género')
        verbose_name_plural = _('Géneros')

    def __str__(self):
        return self.genero


# Parametros para las canchas
class Deporte(models.Model):
    """Modelo para almacenar los deportes."""
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Deporte')
        verbose_name_plural = _('Deportes')

    def __str__(self):
        return self.nombre


class Superficie(models.Model):
    """Modelo para almacenar las superficies de las canchas."""
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _('Superficie')
        verbose_name_plural = _('Superficies')


# Parametros de localización
class Pais(models.Model):
    """Modelo para almacenar los paises."""
    nombre = models.CharField(max_length=255, unique=True, verbose_name=_('Nombre'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _('Pais')
        verbose_name_plural = _('Paises')


class Provincia(models.Model):
    """Modelo para almacenar las provincias."""
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT, verbose_name=_('Pais'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    def __str__(self):
        return self.nombre

    class Meta:
        unique_together = ('nombre', 'pais')
        verbose_name = _('Provincia')
        verbose_name_plural = _('Provincias')


class Localidad(models.Model):
    """Modelo para almacenar las localidades."""
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT, verbose_name=_('Provincia'))
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT, verbose_name=_('Pais'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    def __str__(self):
        return self.nombre

    class Meta:
        unique_together = ('nombre', 'provincia', 'pais')
        verbose_name = _('Localidad')
        verbose_name_plural = _('Localidades')


# PARAMETROS DE LOS CLUBES
# Parametros para los socios
class SocioCategoria(models.Model):
    """Modelo para almacenar las categorías de los socios."""
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Precio'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _('Categoría de socio')
        verbose_name_plural = _('Categorías de socios')