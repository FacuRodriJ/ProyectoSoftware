import json
import six
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import EmailMessage
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.template.loader import render_to_string, get_template
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView

from socios.models import Socio, Miembro, Categoria, Estado
from socios.forms import SocioForm, SelectCategoriaForm, SelectEstadoForm, SelectParentescoForm
from core.models import Club
from accounts.forms import *
from accounts.decorators import admin_required


class SocioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """ Vista para listar los socios """
    model = Socio
    template_name = 'socio/list.html'
    context_object_name = 'socios'
    permission_required = 'socios.view_socio'

    def get_queryset(self):
        return Socio.global_objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Socios'
        # TODO: Agregar lista de Miembros
        return context


class SocioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """ Vista para crear un socio """
    model = Socio
    form_class = SocioForm
    template_name = 'socio/create.html'
    permission_required = 'socios.add_socio'
    success_url = reverse_lazy('socio-listado')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Socio'
        context['action'] = 'add'
        context['persona_form'] = PersonaFormAdmin()
        return context

    def post(self, request, *args, **kwargs):
        data = {}
        try:
            action = request.POST['action']
            if action == 'add':
                # Si la accion es agregar, se crea un nuevo socio
                form = self.form_class(request.POST)
                if form.is_valid():
                    with transaction.atomic():
                        socio = Socio()
                        socio.persona = form.cleaned_data['persona']
                        socio.categoria = form.cleaned_data['categoria']
                        socio.estado = form.cleaned_data['estado']
                        socio.save()
                        messages.success(request, 'Socio creado correctamente')
                else:
                    data['error'] = form.errors
            elif action == 'get_categoria':
                # Si la accion es get_categoria, se obtiene las categorias que puede tener el socio
                data = []
                # Obtener la edad de la Persona
                persona_id = request.POST['persona']
                edad = Persona.objects.get(pk=persona_id).get_edad()
                # Obtener las categorias que corresponden a la edad
                categorias = Categoria.objects.filter(edad_desde__lte=edad,
                                                      edad_hasta__gte=edad)
                for categoria in categorias:
                    item = categoria.toJSON()
                    data.append(item)
            elif action == 'create_persona':
                # Si la accion es create_persona, se crea una nueva persona
                persona_form = PersonaFormAdmin(request.POST, request.FILES)
                if persona_form.is_valid():
                    with transaction.atomic():
                        persona = persona_form.save(commit=False)
                        persona.club = Club.objects.get(pk=1)
                        persona.save()
                        data = persona.toJSON()
                        # Agregar mensaje de exito a data
                        data['tags'] = 'success'
                        data['message'] = 'Persona creada correctamente'
                else:
                    data['error'] = persona_form.errors
            else:
                data['error'] = 'Ha ocurrido un error, intente nuevamente'
        except Exception as e:
            data['error'] = str(e)
        return JsonResponse(data, safe=False)


class SocioDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """ Vista para mostrar un socio """
    model = Socio
    template_name = 'socio/detail.html'
    context_object_name = 'socio'
    permission_required = 'socios.view_socio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle de Socio'
        context['miembros'] = Miembro.objects.filter(socio=self.get_object())
        return context


@login_required
@admin_required
def socio_update_view(request, pk):
    """
    Vista para actualizar un socio
    """
    socio = get_object_or_404(Socio, pk=pk)
    if request.method == 'POST':
        estado_form = SelectEstadoForm(request.POST)
        categoria_form = SelectCategoriaForm(request.POST)
        persona_form = PersonaFormAdmin(request.POST, request.FILES, instance=socio.persona)
        if socio.get_user() is not None:  # Si tiene usuario
            user_form = UpdateUserFormAdmin(request.POST, instance=socio.persona.user)
            if persona_form.is_valid() and estado_form.is_valid() and user_form.is_valid() and categoria_form.is_valid():
                # Actualizar la persona
                persona_form.save()
                # Actualizar el socio
                socio.categoria_id = categoria_form['categoria'].value()
                socio.estado_id = estado_form['estado'].value()
                socio.save()
                # Actualizar el usuario
                user_form.save()
                # TODO: Enviar email de actualización de datos

                messages.success(request, 'Socio actualizado correctamente')
                return redirect('socio-detalle', pk=socio.pk)
        else:  # Si no tiene usuario asociado
            user_form = SimpleCreateUserForm(request.POST)
            if persona_form.is_valid() and estado_form.is_valid() and categoria_form.is_valid():
                # Actualizar la persona
                persona = persona_form.save()
                # Obtener la categoría
                categoria = categoria_form['categoria'].value()
                # Actualizar el socio
                socio.categoria_id = categoria
                socio.estado_id = estado_form['estado'].value()
                socio.save()
                # Si se decidió crearle un usuario al socio, se lo asigna a la persona y se envía un email
                if user_form['add_user'].value():
                    if user_form.is_valid():
                        user = User()
                        user.persona = persona
                        user.email = user_form.clean_email()
                        user.username = persona.dni
                        user.set_password(User.objects.make_random_password())
                        # Enviar email con los datos de acceso
                        current_site = get_current_site(request)
                        mail_subject = 'Bienvenido a %s' % current_site.name
                        message = render_to_string('email/socio_creado_email.html', {
                            'user': user,
                            'domain': current_site.domain,
                            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                            'token': PasswordResetTokenGenerator().make_token(user),
                            'protocol': 'https' if request.is_secure() else 'http',
                        })
                        to_email = user.email
                        email = EmailMessage(mail_subject, message, to=[to_email])
                        email.send()
                        user.save()
                        messages.success(request, 'Socio y Usuario actualizado correctamente')
                        return redirect('socio-detalle', pk=socio.pk)
                messages.success(request, 'Socio actualizado correctamente')
                return redirect('socio-detalle', pk=socio.pk)
    else:
        estado_form = SelectEstadoForm(initial={'estado': socio.estado.pk})
        persona_form = PersonaFormAdmin(instance=socio.persona)
        categoria_form = SelectCategoriaForm(initial={'categoria': socio.categoria.pk})
        if socio.get_user() is not None:
            user_form = UpdateUserFormAdmin(instance=socio.get_user())
        else:
            user_form = SimpleCreateUserForm()

    context = {
        'title': 'Actualizar socio',
        'action': 'update',
        'estado_form': estado_form,
        'user_form': user_form,
        'persona_form': persona_form,
        'categoria_form': categoria_form,
        'socio': socio,
    }
    return render(request, 'socio_update.html', context)


@login_required
@admin_required
def socio_delete(request, pk):
    """
    Eliminar un socio
    """
    socio = get_object_or_404(Socio, pk=pk)
    socio.delete(cascade=True)
    messages.success(request, 'Socio eliminado correctamente')
    return redirect('socio-listado')


@login_required
@admin_required
def socio_restore(request, pk):
    """
    Restaurar un socio eliminado
    """
    socio = Socio.deleted_objects.get(pk=pk)
    try:
        if not socio.get_related_objects():
            socio.restore()
            messages.success(request, 'Socio restaurado correctamente')
        else:
            socio.restore(cascade=True)
            messages.success(request, 'Socio y miembros restaurado correctamente')
    # Capturar el ValidationError si el socio ya existe
    except ValidationError as e:
        messages.error(request, e.message)
    return redirect('socio-listado')


@login_required
@admin_required
def miembro_create_view(request, pk):
    """
    Vista para crear un miembro
    """
    socio = get_object_or_404(Socio, pk=pk)
    if request.method == 'POST':
        persona_form = PersonaFormAdmin(request.POST, request.FILES)
        categoria_form = SelectCategoriaForm(request.POST)
        parentesco_form = SelectParentescoForm(request.POST)
        if persona_form.is_valid() and categoria_form.is_valid() and parentesco_form.is_valid():
            # Crear la persona
            persona = persona_form.save(commit=False)
            persona.club = socio.persona.club
            miembro = Miembro(persona=persona, socio=socio)
            miembro.parentesco_id = parentesco_form['parentesco'].value()
            miembro.categoria_id = categoria_form['categoria'].value()
            persona.save()
            miembro.save()
            messages.success(request, 'Miembro creado correctamente')
            # Redirigir a la vista de detalle del socio con el pk del socio y el miembro
            return redirect('miembro-detalle', miembro_pk=miembro.pk)
    else:
        persona_form = PersonaFormAdmin()
        categoria_form = SelectCategoriaForm()
        parentesco_form = SelectParentescoForm()
    context = {
        'title': 'Crear miembro',
        'action': 'create',
        'persona_form': persona_form,
        'categoria_form': categoria_form,
        'parentesco_form': parentesco_form,
    }
    return render(request, 'miembro_create.html', context)


@login_required
@admin_required
def miembro_detail_view(request, miembro_pk):
    """
    Vista para ver los detalles de un miembro
    """
    miembro = get_object_or_404(Miembro, pk=miembro_pk)
    socio = miembro.socio
    context = {
        'title': 'Miembro',
        'socio': socio,
        'miembro': miembro,
    }
    return render(request, 'miembro_detail.html', context)


@login_required
@admin_required
def miembro_update_view(request, miembro_pk):
    """
    Vista para actualizar un miembro
    """
    miembro = get_object_or_404(Miembro, pk=miembro_pk)
    socio = miembro.socio
    if request.method == 'POST':
        persona_form = PersonaFormAdmin(request.POST, request.FILES, instance=miembro.persona)
        categoria_form = SelectCategoriaForm(request.POST)
        parentesco_form = SelectParentescoForm(request.POST)
        if persona_form.is_valid() and categoria_form.is_valid() and parentesco_form.is_valid():
            # Actualizar la persona
            persona = persona_form.save()
            # Actualizar el miembro
            miembro.parentesco_id = parentesco_form['parentesco'].value()
            miembro.categoria_id = categoria_form['categoria'].value()
            miembro.save()
            messages.success(request, 'Miembro actualizado correctamente')
            return redirect('miembro-detalle', miembro_pk=miembro.pk)
    else:
        persona_form = PersonaFormAdmin(instance=miembro.persona)
        categoria_form = SelectCategoriaForm(initial={'categoria': miembro.categoria.pk})
        parentesco_form = SelectParentescoForm(initial={'parentesco': miembro.parentesco.pk})
    context = {
        'title': 'Actualizar miembro',
        'action': 'update',
        'persona_form': persona_form,
        'categoria_form': categoria_form,
        'parentesco_form': parentesco_form,
        'socio': socio,
        'miembro': miembro,
    }
    return render(request, 'miembro_update.html', context)
