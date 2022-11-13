from django.urls import path

from socios.views.socio.views import *
from socios.views.solicitud.views import *

urlpatterns = [
    # Socios
    path('socios/', SocioListView.as_view(), name='socio-listado'),
    path('socios/<int:pk>/', SocioDetailView.as_view(), name='socio-detalle'),
    path('socios/<int:pk>/editar/', SocioUpdateView.as_view(), name='socio-editar'),
    path('socios/<int:pk>/eliminar/', socio_delete, name='socio-eliminar'),
    path('socios/<int:pk>/restaurar/', socio_restore, name='socio-restaurar'),

    # Solicitud de asociación
    path('solicitud/', SolicitudView.as_view(), name='solicitud-crear'),
    path('solicitud/listado/', SolicitudListView.as_view(), name='solicitud-listado'),
]
