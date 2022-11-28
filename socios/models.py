import locale
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.forms import model_to_dict
from django.utils.translation import gettext_lazy as _
from django_softdelete.models import SoftDeleteModel
from simple_history.models import HistoricalRecords

from accounts.models import PersonaAbstract
from parameters.models import Socios

locale.setlocale(locale.LC_ALL, 'es_AR.UTF-8')


class Socio(SoftDeleteModel):
    """
    Modelo de socio.
    """
    persona = models.OneToOneField('accounts.Persona', on_delete=models.PROTECT)
    categoria = models.ForeignKey('socios.Categoria', on_delete=models.PROTECT)
    fecha_ingreso = models.DateField(default=datetime.now)
    socio_titular = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    parentesco = models.ForeignKey('parameters.Parentesco', on_delete=models.PROTECT, null=True, blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.persona.__str__()

    def es_titular(self):
        return True if self.socio_titular_id is None else False

    def get_estado(self):
        return 'Activo' if self.is_deleted is False else 'Inactivo'

    def get_miembros(self):
        return Socio.global_objects.filter(socio_titular=self)

    def get_parentesco(self):
        return 'Titular' if self.es_titular() else self.parentesco

    def get_tipo(self):
        return 'Titular' if self.es_titular() else 'Miembro'

    def get_user(self):
        try:
            return self.persona.user
        except ObjectDoesNotExist:
            return None

    def get_related_objects(self):
        if self.es_titular():
            return self.get_miembros()
        return []

    def get_antiguedad(self):
        # Si supera el año, mostrar en años, si no en meses
        if (datetime.now().year - self.fecha_ingreso.year) > 0:
            return '{} años'.format(datetime.now().year - self.fecha_ingreso.year)
        else:
            return '{} meses'.format(datetime.now().month - self.fecha_ingreso.month)

    def toJSON(self):
        item = model_to_dict(self)
        item['__str__'] = self.__str__()
        return item

    def clean(self):
        # Un socio no puede ser miembro de otro miembro
        if not self.es_titular():
            if not self.socio_titular.es_titular():
                raise ValidationError(_('Un socio no puede ser miembro de otro miembro.'))
        # Un socio titular no puede ser menor de 16 años
        if self.es_titular():
            edad_minima_titular = Socios.objects.get(club_id=1).edad_minima_socio_titular
            if self.persona.get_edad() < edad_minima_titular:
                raise ValidationError(_('Un socio titular no puede ser menor de {} años.'.format(edad_minima_titular)))

    class Meta:
        verbose_name = 'Socio'
        verbose_name_plural = "Socios"
        ordering = ['id']
        constraints = [
            # Validar que el socio titular no sea el mismo socio
            models.CheckConstraint(
                check=~models.Q(socio_titular=models.F('id')),
                name='socio_titular_distinto_socio',
                violation_error_message='Un socio no puede ser su propio titular.'
            ),
            # Validar si socio_titular es nulo, parentesco también lo es y viceversa
            models.CheckConstraint(
                check=((models.Q(socio_titular__isnull=True) & models.Q(parentesco__isnull=True))
                       | (models.Q(socio_titular__isnull=False) & models.Q(parentesco__isnull=False))),
                name='socio_titular_parentesco',
                violation_error_message='Si socio_titular es nulo, parentesco también debe serlo y viceversa.'
            ),
        ]


class Categoria(models.Model):
    """
    Modelo para almacenar las categorías de los socios.
    """
    nombre = models.CharField(max_length=255, verbose_name='Nombre')
    cuota = models.DecimalField(max_digits=10, default=0, decimal_places=2, verbose_name='Cuota')
    edad_desde = models.PositiveSmallIntegerField(default=0, verbose_name='Edad desde')
    edad_hasta = models.PositiveSmallIntegerField(default=0, verbose_name='Edad hasta')
    se_factura = models.BooleanField(default=True, verbose_name='¿Se factura?')

    def __str__(self):
        return self.nombre + ' $' + str(self.cuota)

    def sin_categoria(self):
        return self.objects.get(cuota=0, edad_desde=0, edad_hasta=0, se_factura=False)

    def clean(self):
        if self.edad_desde > self.edad_hasta:
            raise ValidationError('La edad "desde" debe ser menor que la edad "hasta".')
        if self.edad_desde == self.edad_hasta:
            raise ValidationError('Las edades ingresadas no deben ser iguales.')

    def toJSON(self):
        item = model_to_dict(self)
        item['__str__'] = self.__str__()
        return item

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        constraints = [
            # Cuota debe ser mayor o igual a 0
            models.CheckConstraint(
                check=models.Q(cuota__gte=0),
                name='cuota_mayor_igual_cero',
                violation_error_message='La cuota debe ser mayor o igual a 0.'
            ),
            # Si cuota es 0, se_factura debe ser False
            models.CheckConstraint(
                check=~(models.Q(cuota=0) & models.Q(se_factura=True)),
                name='cuota_se_factura',
                violation_error_message='Si el precio de la cuota es $0, no se debe incluir en el '
                                        'detalle de la facturación.'
            ),
        ]


class SolicitudSocio(PersonaAbstract):
    """
    Modelo para almacenar las solicitudes de socios.
    """
    dni = models.CharField(max_length=8, verbose_name='DNI')
    email = models.EmailField(max_length=255, verbose_name='Email')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name='Categoría')
    is_aprobado = models.BooleanField(default=False, verbose_name='Aprobado')

    def get_estado(self):
        if self.is_aprobado:
            return 'Aprobado'
        elif self.is_deleted:
            return 'Rechazado'
        return 'Pendiente'

    def toJSON(self):
        item = model_to_dict(self, exclude=['imagen', 'sexo', 'is_aprobado', 'is_deleted', 'deleted_at'])
        item['estado'] = self.get_estado()
        item['categoria'] = self.categoria.toJSON()
        item['edad'] = self.get_edad()
        item['sexo'] = self.sexo.nombre
        item['imagen'] = self.get_imagen()
        return item

    def clean(self):
        super(SolicitudSocio, self).clean()
        # Fecha de nacimiento no puede ser mayor a la fecha actual
        if self.fecha_nacimiento > datetime.now().date():
            raise ValidationError('La fecha de nacimiento no puede ser mayor a la fecha actual.')

    class Meta:
        verbose_name = 'Solicitud de socio'
        verbose_name_plural = 'Solicitudes de socios'
        constraints = [
            # Validar que el DNI solo contenga números, tenga al menos 7 dígitos y no comience con 0.
            models.CheckConstraint(check=models.Q(dni__regex=r'^[1-9][0-9]{6,}$'),
                                   name='solicitud_dni_valido',
                                   violation_error_message=_(
                                       'DNI: El DNI debe contener solo números, '
                                       'tener al menos 7 dígitos y no comenzar con 0.')),
            # Validar que el nombre y el apellido solo contengan letras y espacios.
            models.CheckConstraint(check=models.Q(nombre__regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$'),
                                   name='solicitud_nombre_valido',
                                   violation_error_message=_(
                                       'Nombre: El nombre solo puede contener letras y espacios.')),
            models.CheckConstraint(check=models.Q(apellido__regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$'),
                                   name='solicitud_apellido_valido',
                                   violation_error_message=_(
                                       'Apellido: El apellido solo puede contener letras y espacios.')),
        ]


class CuotaSocial(SoftDeleteModel):
    """
    Modelo para almacenar las cuotas sociales.
    """
    persona = models.ForeignKey('accounts.Persona', on_delete=models.PROTECT, verbose_name='Persona')
    nombre_completo = models.CharField(max_length=255, verbose_name='Nombre completo')
    fecha_emision = models.DateTimeField(default=datetime.now, verbose_name='Fecha de emisión')
    fecha_vencimiento = models.DateTimeField(verbose_name='Fecha de vencimiento')
    fecha_pago = models.DateTimeField(verbose_name='Fecha de pago', null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Total')
    cargo_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Cargo extra')
    history = HistoricalRecords()

    def is_pagada(self):
        return True if self.fecha_pago else False

    def get_estado(self):
        if self.is_pagada():
            return 'Pagada'
        elif self.is_deleted:
            return 'Anulada'
        return 'Pendiente'

    def get_fecha_emision(self):
        return self.fecha_emision.strftime('%d/%m/%Y')

    def get_fecha_vencimiento(self):
        return self.fecha_vencimiento.strftime('%d/%m/%Y')

    def get_fecha_pago(self):
        return self.fecha_pago.strftime('%d/%m/%Y') if self.fecha_pago else None

    def get_periodo(self):
        # MM en letras (Ej: 01 -> Enero) y AAAA en español
        return self.fecha_emision.strftime('%B %Y').capitalize()

    def get_subtotal(self):
        return self.total - self.cargo_extra

    def get_motivo_anulacion(self):
        # Obtener reason change en django_simple_history
        motivo = self.history.filter(is_deleted=True).first().history_change_reason
        return motivo if motivo else 'No especificado'

    def get_related_objects(self):
        return self.detallecuotasocial_set.all()

    def toJSON(self):
        item = model_to_dict(self)
        item['persona'] = self.persona.toJSON()
        item['fecha_emision'] = self.fecha_emision.strftime('%d/%m/%Y %H:%M')
        item['fecha_vencimiento'] = self.fecha_vencimiento.strftime('%d/%m/%Y %H:%M')
        item['fecha_pago'] = self.fecha_pago.strftime('%d/%m/%Y %H:%M') if self.fecha_pago else None
        return item

    def clean(self):
        super(CuotaSocial, self).clean()
        # Fecha de pago no puede ser menor a la fecha de emisión.
        if self.fecha_pago is not None:
            if self.fecha_pago < self.fecha_emision:
                raise ValidationError({'fecha_pago': _('La fecha de pago no puede ser menor a la fecha de emisión.')})

    class Meta:
        verbose_name = 'Cuota social'
        verbose_name_plural = 'Cuotas sociales'
        constraints = [
            # Validar que el total sea mayor o igual a 0.
            models.CheckConstraint(check=models.Q(total__gte=0),
                                   name='cuota_social_total_valido',
                                   violation_error_message=_(
                                       'Total: El total debe ser mayor o igual a 0.')),
            # Validar que el cargo extra sea mayor o igual a 0.
            models.CheckConstraint(check=models.Q(cargo_extra__gte=0),
                                   name='cuota_social_cargo_extra_valido',
                                   violation_error_message=_(
                                       'Cargo extra: El cargo extra debe ser mayor o igual a 0.')),
            # Validar que Fecha de vencimiento no puede ser menor a la fecha de emisión.
            models.CheckConstraint(check=models.Q(fecha_vencimiento__gte=models.F('fecha_emision')),
                                   name='cuota_social_fecha_vencimiento_valido',
                                   violation_error_message=_(
                                       'Fecha de vencimiento: La fecha de vencimiento no puede '
                                       'ser menor a la fecha de emisión.')),

        ]


class DetalleCuotaSocial(SoftDeleteModel):
    """
    Modelo para almacenar los detalles de las cuotas sociales.
    """
    cuota_social = models.ForeignKey('socios.CuotaSocial', on_delete=models.PROTECT, verbose_name='Cuota social')
    socio = models.ForeignKey('socios.Socio', on_delete=models.PROTECT, verbose_name='Socio')
    nombre_completo = models.CharField(max_length=100, verbose_name='Nombre completo')
    categoria = models.CharField(max_length=50, verbose_name='Categoría')
    cuota = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Cuota')
    cargo_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Cargo extra')
    total_parcial = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total parcial')

    def toJSON(self):
        item = model_to_dict(self)
        item['cuota_social'] = self.cuota_social.toJSON()
        item['socio'] = self.socio.toJSON()
        return item

    def clean(self):
        super(DetalleCuotaSocial, self).clean()
        if self.cuota_social.fecha_pago:
            raise ValidationError('No se puede modificar un detalle de cuota social que ya ha sido pagada.')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.cuota = self.socio.categoria.cuota
        self.total_parcial = self.cuota + self.cargo_extra
        super(DetalleCuotaSocial, self).save(force_insert, force_update, using, update_fields)

    class Meta:
        verbose_name = 'Detalle de cuota social'
        verbose_name_plural = 'Detalles de cuotas sociales'
        constraints = [
            # Validar que la cuota sea mayor o igual a 0.
            models.CheckConstraint(check=models.Q(cuota__gte=0),
                                   name='detalle_cuota_social_cuota_valida',
                                   violation_error_message=_(
                                       'Cuota: La cuota debe ser mayor o igual a 0.')),
            # Validar que el cargo extra sea mayor o igual a 0.
            models.CheckConstraint(check=models.Q(cargo_extra__gte=0),
                                   name='detalle_cuota_social_cargo_extra_valido',
                                   violation_error_message=_(
                                       'Cargo extra: El cargo extra debe ser mayor o igual a 0.')),
            # Validar que el total parcial sea mayor o igual a 0.
            models.CheckConstraint(check=models.Q(total_parcial__gte=0),
                                   name='detalle_cuota_social_total_parcial_valido',
                                   violation_error_message=_(
                                       'Total parcial: El total parcial debe ser mayor o igual a 0.')),
        ]
