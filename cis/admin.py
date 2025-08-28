# planificacion/admin.py
from django.contrib import admin
from .models import *

class SerieInline(admin.TabularInline):
    model = SerieIndicador
    extra = 0

@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ("nombre","tipo","unidad","operacion","anio_linea_base","linea_base","anio_meta","meta_valor")
    list_filter = ("tipo","unidad","operacion__accion__objetivo","operacion__accion__objetivo__area_org")
    search_fields = ("nombre","operacion__descripcion","operacion__codigo","codigo")
    inlines = [SerieInline]

admin.site.register([Entidad, AreaOrganizacional, AreaEstrategica, ObjetivoEstrategico,
                     AccionEstrategica, Operacion, FuenteInformacion, SerieIndicador])
