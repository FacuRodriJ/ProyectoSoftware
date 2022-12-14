from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


# PARÁMETROS DEL SISTEMA
# Parámetros para socios y miembros
class Parentesco(models.Model):
    """
    Modelo para almacenar los parentescos de los miembros de la familia.
    """
    nombre = models.CharField(max_length=50, verbose_name=_('Nombre'))

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _('Parentesco')
        verbose_name_plural = _('Parentescos')


# Parámetros para perfiles de usuario
class Sexo(models.Model):
    """Modelo para almacenar los sexos de los usuarios."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name=_('Nombre'))

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _('Sexo')
        verbose_name_plural = _('Sexos')


# Parámetros de localización
class Pais(models.Model):
    """Modelo para almacenar los países."""
    nombre = models.CharField(max_length=100, unique=True, verbose_name=_('Nombre'))

    def __str__(self):
        return self.nombre

    def clean(self):
        super(Pais, self).clean()
        # El nombre del país comienza con mayúscula.
        self.nombre = self.nombre.capitalize()
        # El nombre del país no debe contener números.
        if any(char.isdigit() for char in self.nombre):
            raise ValidationError(_('El nombre del país no debe contener números.'))
        # El nombre del país no debe contener dobles espacios.
        if '  ' in self.nombre:
            raise ValidationError(_('El nombre del país no debe contener dobles espacios.'))
        # Si tiene espacios en blanco al principio o al final, se eliminan.
        self.nombre = self.nombre.strip()

    class Meta:
        verbose_name = _('País')
        verbose_name_plural = _('Países')


class Provincia(models.Model):
    """Modelo para almacenar las provincias."""
    nombre = models.CharField(max_length=100, verbose_name=_('Nombre'))
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT, verbose_name=_('País'))

    def __str__(self):
        return self.nombre

    def clean(self):
        super(Provincia, self).clean()
        # El nombre de la provincia comienza con mayúscula.
        self.nombre = self.nombre.capitalize()
        # El nombre de la provincia no debe contener números.
        if any(char.isdigit() for char in self.nombre):
            raise ValidationError(_('El nombre de la provincia no debe contener números.'))
        # El nombre de la provincia no debe contener dobles espacios.
        if '  ' in self.nombre:
            raise ValidationError(_('El nombre de la provincia no debe contener dobles espacios.'))
        # Si tiene espacios en blanco al principio o al final, se eliminan.
        self.nombre = self.nombre.strip()

    class Meta:
        unique_together = ('nombre', 'pais')
        verbose_name = _('Provincia')
        verbose_name_plural = _('Provincias')


class Localidad(models.Model):
    """Modelo para almacenar las localidades."""
    nombre = models.CharField(max_length=255, verbose_name=_('Nombre'))
    provincia = models.ForeignKey(Provincia, on_delete=models.PROTECT, verbose_name=_('Provincia'))
    pais = models.ForeignKey(Pais, on_delete=models.PROTECT, verbose_name=_('Pais'))

    def __str__(self):
        return self.nombre + ', ' + self.provincia.nombre + ', ' + self.pais.nombre

    def clean(self):
        super(Localidad, self).clean()
        # El nombre de la localidad comienza con mayúscula.
        self.nombre = self.nombre.capitalize()
        # El nombre de la localidad no debe contener números.
        if any(char.isdigit() for char in self.nombre):
            raise ValidationError(_('El nombre de la localidad no debe contener números.'))
        # El nombre de la localidad no debe contener dobles espacios.
        if '  ' in self.nombre:
            raise ValidationError(_('El nombre de la localidad no debe contener dobles espacios.'))
        # Si tiene espacios en blanco al principio o al final, se eliminan.
        self.nombre = self.nombre.strip()

    class Meta:
        unique_together = ('nombre', 'provincia', 'pais')
        verbose_name = _('Localidad')
        verbose_name_plural = _('Localidades')
