from django import forms
from django.db import IntegrityError
from django.contrib.admin.widgets import AdminFileWidget
from django.core.exceptions import ValidationError

from socios.models import Estado, Categoria, Socio
from parameters.models import Parentesco


class SelectEstadoForm(forms.Form):
    """
    Formulario para elegir un estado de socio.
    """
    estado = forms.ModelChoiceField(required=True,
                                    queryset=Estado.objects.all(),
                                    widget=forms.Select(attrs={'class': 'form-control select2'}))


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

    def __init__(self, *args, **kwargs):
        super(SocioForm, self).__init__(*args, **kwargs)
        self.fields['persona'].queryset = self.fields['persona'].queryset.filter(socio=None, miembro=None)

    # Validar si el socio que se quiere crear ya existe y está eliminado
    def clean(self):
        super(SocioForm, self).clean()
        try:
            socio = Socio.global_objects.get(persona_id=self.cleaned_data['persona'])
            if socio.is_deleted:
                raise ValidationError('El socio {} ya existe. Pero se encuentra eliminado.'.format(socio))
        except Socio.DoesNotExist:
            pass

    class Meta:
        model = Socio
        fields = ['persona', 'categoria', 'estado']
        widgets = {
            'persona': forms.Select(attrs={'class': 'form-control select2'}),
            'categoria': forms.Select(attrs={'class': 'form-control select2'}),
            'estado': forms.Select(attrs={'class': 'form-control select2'}),
        }
