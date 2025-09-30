from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from cis import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),  
    path("reportes/cumplimiento/", views.ReporteCumplimientoView.as_view(), name="reporte_cumplimiento"),
    
    path("areas/", views.AreaOrganizacionalListView.as_view(), name="area_org_list"),
    path("areas/nuevo/", views.AreaOrganizacionalCreateView.as_view(), name="area_org_create"),
    path("areas/<int:pk>/editar/", views.AreaOrganizacionalUpdateView.as_view(), name="area_org_update"),
    path("areas/<int:pk>/eliminar/", views.AreaOrganizacionalDeleteView.as_view(), name="area_org_delete"),
    
    path("indicadores/", views.IndicadorListView.as_view(), name="indicador_list"),
    path("indicadores/nuevo/", views.IndicadorCreateView.as_view(), name="indicador_create"),
    path("indicadores/<int:pk>/editar/", views.IndicadorUpdateView.as_view(), name="indicador_update"),
    path("indicadores/<int:pk>/eliminar/", views.IndicadorDeleteView.as_view(), name="indicador_delete"),
    
    
    path("series/", views.SerieIndicadorListView.as_view(), name="serie_list"),
    path("series/nuevo/", views.SerieIndicadorCreateView.as_view(), name="serie_create"),
    path("series/<int:pk>/editar/", views.SerieIndicadorUpdateView.as_view(), name="serie_update"),
    path("series/<int:pk>/eliminar/", views.SerieIndicadorDeleteView.as_view(), name="serie_delete"),

    # editor masivo por indicador
    path("indicadores/<int:indicador_id>/series/editar/", views.SerieIndicadorBulkEditView.as_view(), name="serie_bulk_edit"),
    
    path("areas-estrategicas/", views.AreaEstrategicaListView.as_view(), name="area_estrategica_list"),
    path("areas-estrategicas/nueva/", views.AreaEstrategicaCreateView.as_view(), name="area_estrategica_create"),
    path("areas-estrategicas/<int:pk>/editar/", views.AreaEstrategicaUpdateView.as_view(), name="area_estrategica_update"),
    path("areas-estrategicas/<int:pk>/eliminar/", views.AreaEstrategicaDeleteView.as_view(), name="area_estrategica_delete"),
    
    path("objetivos/", views.ObjetivoListView.as_view(), name="objetivo_list"),
    path("objetivos/nuevo/", views.ObjetivoCreateView.as_view(), name="objetivo_create"),
    path("objetivos/<int:pk>/editar/", views.ObjetivoUpdateView.as_view(), name="objetivo_update"),
    path("objetivos/<int:pk>/eliminar/", views.ObjetivoDeleteView.as_view(), name="objetivo_delete"),
    
    
    path("acciones/", views.AccionListView.as_view(), name="accion_list"),
    path("acciones/nueva/", views.AccionCreateView.as_view(), name="accion_create"),
    path("acciones/<int:pk>/editar/", views.AccionUpdateView.as_view(), name="accion_update"),
    path("acciones/<int:pk>/eliminar/", views.AccionDeleteView.as_view(), name="accion_delete"),
    
    
    path("operaciones/", views.OperacionListView.as_view(), name="operacion_list"),
    path("operaciones/nueva/", views.OperacionCreateView.as_view(), name="operacion_create"),
    path("operaciones/<int:pk>/editar/", views.OperacionUpdateView.as_view(), name="operacion_update"),
    path("operaciones/<int:pk>/eliminar/", views.OperacionDeleteView.as_view(), name="operacion_delete"),

    path("fuentes/", views.FuenteListView.as_view(), name="fuente_list"),
    path("fuentes/nueva/", views.FuenteCreateView.as_view(), name="fuente_create"),
    path("fuentes/<int:pk>/editar/", views.FuenteUpdateView.as_view(), name="fuente_update"),
    path("fuentes/<int:pk>/eliminar/", views.FuenteDeleteView.as_view(), name="fuente_delete"),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
