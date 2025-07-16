from django.contrib import admin
from .models import AreaEstrategica, Entidad, AreaOrganizacional, TipoIndicador, TipoResultado, ObjetivoEstrategico
from .models import Operacion, Indicador, AccionEstrategica, ProgramacionFisica, TasaEficacia, ProgramacionTasaEficacia


admin.site.register(AreaEstrategica)
admin.site.register(Entidad)
admin.site.register(AreaOrganizacional)
admin.site.register(TipoIndicador)
admin.site.register(TipoResultado)
admin.site.register(ObjetivoEstrategico)
admin.site.register(Operacion)
admin.site.register(Indicador)

admin.site.register(AccionEstrategica)
admin.site.register(ProgramacionFisica)

admin.site.register(TasaEficacia)
admin.site.register(ProgramacionTasaEficacia)

    