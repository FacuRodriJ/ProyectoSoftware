from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.forms import model_to_dict
from django_softdelete.models import SoftDeleteModel, SoftDeleteManager

from accounts.models import Persona


class Socio(SoftDeleteModel):
    """
    Modelo de socio.
    """
    persona = models.OneToOneField(Persona, on_delete=models.PROTECT)
    categoria = models.ForeignKey('socios.Categoria', on_delete=models.PROTECT)
    estado = models.ForeignKey('socios.Estado', on_delete=models.PROTECT)

    def __str__(self):
        return self.persona.get_full_name()

    def get_user(self):
        try:
            return self.persona.user
        except ObjectDoesNotExist:
            return None

    def get_related_objects(self):
        """
        Devuelve una lista de objetos relacionados con el socio.
        """
        try:
            miembro = Miembro.global_objects.filter(socio=self)
            # Queryset to list
            miembro = list(miembro)
            return miembro
        except ObjectDoesNotExist:
            return []

    def restore(self, cascade=None):
        # Si el socio tiene Persona eliminada, no puede ser restaurado
        persona = Persona.global_objects.get(pk=self.persona.pk)
        if persona.is_deleted:
            raise ValidationError('No se puede restaurar el socio porque la persona está eliminada.')

        # Si el socio es miembro de un grupo familiar, no puede ser restaurado
        try:
            if not self.persona.miembro.is_deleted:
                raise ValidationError(
                    'No es posible restaurar el socio: '
                    '{} ya es miembro de otro socio.'.format(self.persona.get_full_name()))
        except ObjectDoesNotExist:
            pass
        super(Socio, self).restore(cascade=cascade)

    # TODO: Si el socio tiene deudas pendientes, no puede ser eliminado

    def clean(self):
        super(Socio, self).clean()
        # Socio no puede ser miembro
        try:
            if not self.persona.miembro.is_deleted:
                raise ValidationError(
                    'La persona {} ya es miembro de otro socio.'.format(self.persona.get_full_name()))
        except ObjectDoesNotExist:
            pass

    class Meta:
        verbose_name = 'Socio'
        verbose_name_plural = "Socios"
        ordering = ['id']


class Miembro(SoftDeleteModel):
    """
    Modelo de miembro de familia.
    """
    persona = models.OneToOneField(Persona, on_delete=models.PROTECT)
    socio = models.ForeignKey(Socio, on_delete=models.PROTECT)
    parentesco = models.ForeignKey('parameters.Parentesco', on_delete=models.PROTECT)
    categoria = models.ForeignKey('socios.Categoria', on_delete=models.PROTECT)

    def __str__(self):
        return self.persona.get_full_name()

    def restore(self, cascade=None):
        # Si el miembro es socio, no puede ser restaurado
        try:
            if not self.persona.socio.is_deleted:
                raise ValidationError(
                    'No es posible restaurar el miembro: '
                    '{} ya es socio.'.format(self.persona.get_full_name()))
        except ObjectDoesNotExist:
            super(Miembro, self).restore(cascade=cascade)

    def clean(self):
        # Miembro no puede ser socio
        try:
            if not self.persona.socio.is_deleted:
                raise ValidationError('La persona {} ya es socio.'.format(self.persona.get_full_name()))
        except ObjectDoesNotExist:
            pass
        # Socio y Persona no pueden ser iguales

    class Meta:
        verbose_name = 'Miembro'
        verbose_name_plural = "Miembros"


class Categoria(models.Model):
    """
    Modelo para almacenar las categorías de los socios.
    """
    nombre = models.CharField(max_length=255, verbose_name='Nombre')
    cuota = models.DecimalField(max_digits=10, default=0.10, decimal_places=2, verbose_name='Cuota')
    edad_desde = models.PositiveSmallIntegerField(default=0, verbose_name='Edad desde')
    edad_hasta = models.PositiveSmallIntegerField(default=0, verbose_name='Edad hasta')

    def __str__(self):
        return self.nombre + ' $' + str(self.cuota)

    def clean(self):
        if self.edad_desde > self.edad_hasta:
            raise ValidationError('La edad "desde" debe ser menor que la edad "hasta".')
        if self.edad_desde == self.edad_hasta:
            raise ValidationError('Las edades ingresadas no deben ser iguales.')

    def toJSON(self):
        item = model_to_dict(self)
        return item

    class Meta:
        verbose_name = 'Categoría de socio'
        verbose_name_plural = 'Categorías de socios'


class Estado(models.Model):
    """
    Modelo para almacenar los estados de los socios.
    """
    nombre = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    descripcion = models.CharField(max_length=255, verbose_name='Descripción')
    code = models.CharField(max_length=2, unique=True, verbose_name='Código')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Estado de socio'
        verbose_name_plural = 'Estados de socios'
