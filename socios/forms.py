from django import forms
from django.contrib.admin.widgets import AdminFileWidget
from django.core.exceptions import ValidationError

from accounts.models import User
from parameters.models import Parentesco
from socios.models import Categoria, Socio, SolicitudSocio, CuotaSocial


class SelectCategoriaForm(forms.Form):
    """
    Formulario para elegir una categoria de socio.
    """
    categoria = forms.ModelChoiceField(required=True,
                                       queryset=Categoria.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-control select2'}))


class SelectParentescoForm(forms.Form):
    """
    Formulario para elegir un parentesco.
    """
    parentesco = forms.ModelChoiceField(required=True,
                                        queryset=Parentesco.objects.all(),
                                        widget=forms.Select(attrs={'class': 'form-control select2'}))


class SocioForm(forms.ModelForm):
    """
    Formulario para crear un socio.
    """
    fecha_ingreso = forms.DateField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
                'placeholder': 'Fecha de ingreso',
                'class': 'form-control  datetimepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_fecha_ingreso',
            }
        ))
    socio_titular = forms.ModelChoiceField(required=False,
                                           queryset=Socio.global_objects.all().filter(socio_titular__isnull=True),
                                           widget=forms.Select(attrs={'class': 'form-control select2'}))

    class Meta:
        model = Socio
        fields = ['persona', 'categoria', 'socio_titular', 'parentesco', 'fecha_ingreso']
        widgets = {
            'persona': forms.Select(attrs={'class': 'form-control select2'}),
            'categoria': forms.Select(attrs={'class': 'form-control select2'}),
            'parentesco': forms.Select(attrs={'class': 'form-control select2'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control datepicker'}),
        }


class SolicitudForm(forms.ModelForm):
    """
    Formulario para crear una solicitud de socio.
    """
    dni = forms.CharField(max_length=8,
                          required=True,
                          widget=forms.TextInput(attrs={'placeholder': 'DNI',
                                                        'class': 'form-control',
                                                        }))
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={'placeholder': 'Email',
                                                            'class': 'form-control',
                                                            }))
    sexo = forms.Select(attrs={'class': 'form-control select2'})
    nombre = forms.CharField(max_length=100,
                             required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'Nombre',
                                                           'class': 'form-control',
                                                           }))
    apellido = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'Apellido',
                                                             'class': 'form-control',
                                                             }))
    fecha_nacimiento = forms.DateField(required=True,
                                       widget=forms.DateInput(
                                           format='%d/%m/%Y',
                                           attrs={
                                               'autocomplete': 'off',
                                               'placeholder': 'Fecha de nacimiento',
                                               'class': 'form-control  datetimepicker-input',
                                               'data-toggle': 'datetimepicker',
                                               'data-target': '#id_fecha_nacimiento',
                                           }
                                       ))
    imagen = forms.ImageField(required=True, widget=AdminFileWidget, label='Foto carnet')

    def clean(self):
        super(SolicitudForm, self).clean()
        dni = self.cleaned_data['dni']
        try:
            solicitud = SolicitudSocio.objects.get(dni=dni)
            raise ValidationError('Ya existe una solicitud enviada con el DNI ingresado. '
                                  'Estado de solicitud: {}'.format(solicitud.get_estado()))
        except SolicitudSocio.DoesNotExist:
            pass
        try:
            Socio.global_objects.get(persona__dni=dni)
            raise ValidationError('Ya existe un socio con el DNI ingresado. Por favor, verifique los datos ingresados.')
        except Socio.DoesNotExist:
            pass
        email = self.cleaned_data['email']
        try:
            User.global_objects.get(email=email)
            raise ValidationError('Ya existe un usuario con el email ingresado. '
                                  'Por favor, verifique los datos ingresados.')
        except User.DoesNotExist:
            pass

    class Meta:
        model = SolicitudSocio
        fields = ['nombre', 'apellido', 'dni', 'email', 'sexo', 'fecha_nacimiento', 'imagen', 'categoria']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control select2'}),
        }


class CuotaSocialForm(forms.ModelForm):
    """
    Formulario para crear una cuota social.
    """
    con_vencimiento = forms.BooleanField(required=False,
                                         widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    meses = forms.MultipleChoiceField(required=True,
                                      choices=CuotaSocial.MESES,
                                      widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '12'}))

    class Meta:
        model = CuotaSocial
        fields = ['persona', 'periodo_anio', 'cargo_extra', 'observaciones']
        widgets = {
            'persona': forms.HiddenInput(),
            # 'periodo_mes': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '12'}),
            'periodo_anio': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'cargo_extra': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
