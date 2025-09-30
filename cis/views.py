from django.shortcuts import render

from django.db.models import Avg, Count, F, Q, Sum, Case, When, Value
from django.db.models.functions import Coalesce
from django.db.models import FloatField
from .models import Indicador, SerieIndicador, AreaOrganizacional



def dashboard(request):
    indicadores = (Indicador.objects
                   .select_related("operacion", "operacion__accion",
                                   "operacion__accion__objetivo",
                                   "operacion__accion__objetivo__area_org"))
    series = SerieIndicador.objects.all()

    total_indicadores = indicadores.count()
    con_ejecucion = indicadores.filter(series__es_programado=False, series__valor__isnull=False).distinct().count()
    sin_programacion = indicadores.exclude(series__es_programado=True).distinct().count()

    # --- Programado vs Ejecutado por año (todo a FloatField) ---
    por_anio = (
        series.values("anio")
        .annotate(
            programado=Coalesce(
                Sum(Case(When(es_programado=True, then=F("valor")), default=Value(0), output_field=FloatField())),
                Value(0.0), output_field=FloatField()
            ),
            ejecutado=Coalesce(
                Sum(Case(When(es_programado=False, then=F("valor")), default=Value(0), output_field=FloatField())),
                Value(0.0), output_field=FloatField()
            ),
        )
        .order_by("anio")
    )

    # --- Distribución por tipo ---
    dist_tipo = (indicadores.values("tipo")
                 .annotate(total=Count("id"))
                 .order_by("tipo"))

    # --- Cumplimiento por indicador y año (todo a FloatField) ---
    ind_anio = (
        series.values("indicador_id", "anio")
        .annotate(
            programado=Coalesce(
                Sum(Case(When(es_programado=True, then=F("valor")), default=Value(0), output_field=FloatField())),
                Value(0.0), output_field=FloatField()
            ),
            ejecutado=Coalesce(
                Sum(Case(When(es_programado=False, then=F("valor")), default=Value(0), output_field=FloatField())),
                Value(0.0), output_field=FloatField()
            ),
        )
        .annotate(
            cumplimiento=Case(
                When(programado__gt=0, then=(Value(100.0, output_field=FloatField()) * F("ejecutado") / F("programado"))),
                default=Value(0.0),
                output_field=FloatField(),
            )
        )
    )

    # --- Avance promedio global ---
    tot_prog = sum(x["programado"] for x in ind_anio)
    tot_ejec = sum(x["ejecutado"] for x in ind_anio)
    avance_promedio = round((tot_ejec / tot_prog) * 100, 2) if tot_prog > 0 else 0.0

    # --- Cumplimiento por área (último año) ---
    ultimo = series.order_by("-anio").values_list("anio", flat=True).first()
    cumplimiento_area = []
    if ultimo:
        ind_ultimo = { (r["indicador_id"], r["anio"]): r for r in ind_anio.filter(anio=ultimo) }

        areas = (AreaOrganizacional.objects
                 .select_related("entidad")
                 .annotate(total_ind=Count("objetivos__acciones__operaciones__indicadores", distinct=True))
                 .order_by("entidad__sigla", "nombre"))

        for area in areas:
            ids_ind_area = (Indicador.objects
                            .filter(operacion__accion__objetivo__area_org=area)
                            .values_list("id", flat=True))
            valores = []
            for ind_id in ids_ind_area:
                row = ind_ultimo.get((ind_id, ultimo))
                if row and row["programado"] > 0:
                    valores.append(row["cumplimiento"])
            prom = round(sum(valores)/len(valores), 2) if valores else 0.0
            cumplimiento_area.append({
                "area_id": area.id,
                "area": f"{area.nombre} ({area.entidad.sigla or area.entidad.nombre})",
                "prom_cumplimiento": prom,
                "total_indicadores": area.total_ind,
            })

    context = dict(
        total_indicadores=total_indicadores,
        con_ejecucion=con_ejecucion,
        sin_programacion=sin_programacion,
        avance_promedio=avance_promedio,
        por_anio=list(por_anio),
        dist_tipo=list(dist_tipo),
        cumplimiento_area=cumplimiento_area,
        ultimo_anio=ultimo,
    )
    return render(request, "dashboard.html", context)
    

from django.views.generic import TemplateView

class ReporteCumplimientoView(TemplateView):
    template_name = "planificacion/reporte_cumplimiento.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        anio = self.request.GET.get("anio")
        # Si viene vacío o no es número, lo ignoramos
        try:
            anio_int = int(anio) if anio else None
        except ValueError:
            anio_int = None

        qs = (
            SerieIndicador.objects
            .values(
                "indicador_id",
                "indicador__nombre",
                "anio",
                "indicador__operacion__codigo",
                "indicador__operacion__accion__objetivo__area_org__nombre",
            )
            .annotate(
                programado=Coalesce(
                    Sum(
                        Case(
                            When(es_programado=True, then=F("valor")),
                            default=Value(0),
                            output_field=FloatField(),   # <- fuerza float
                        )
                    ),
                    Value(0.0),
                    output_field=FloatField(),       # <- fuerza float
                ),
                ejecutado=Coalesce(
                    Sum(
                        Case(
                            When(es_programado=False, then=F("valor")),
                            default=Value(0),
                            output_field=FloatField(),   # <- fuerza float
                        )
                    ),
                    Value(0.0),
                    output_field=FloatField(),       # <- fuerza float
                ),
            )
            .annotate(
                cumplimiento=Case(
                    When(
                        programado__gt=0,
                        then=Value(100.0, output_field=FloatField()) * F("ejecutado") / F("programado"),
                    ),
                    default=Value(0.0),
                    output_field=FloatField(),       # <- fuerza float
                )
            )
            .order_by("anio", "indicador__operacion__codigo", "indicador__nombre")
        )

        if anio_int:
            qs = qs.filter(anio=anio_int)

        ctx["rows"] = list(qs)
        ctx["anio_selected"] = anio_int or ""
        return ctx

# planificacion/views_area_org.py
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import AreaOrganizacional
from .forms import AreaOrganizacionalForm

class AreaOrganizacionalListView(ListView):
    model = AreaOrganizacional
    template_name = "planificacion/area_org_list.html"
    context_object_name = "areas"
    paginate_by = 10

    def get_queryset(self):
        qs = (AreaOrganizacional.objects
              .select_related("entidad")
              .order_by("entidad__sigla", "nombre"))
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(responsable__icontains=q) |
                Q(entidad__nombre__icontains=q) |
                Q(entidad__sigla__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        return ctx


class AreaOrganizacionalCreateView(CreateView):
    model = AreaOrganizacional
    form_class = AreaOrganizacionalForm
    template_name = "planificacion/area_org_form.html"
    success_url = reverse_lazy("area_org_list")

    def form_valid(self, form):
        messages.success(self.request, "Área organizacional creada correctamente.")
        return super().form_valid(form)


class AreaOrganizacionalUpdateView(UpdateView):
    model = AreaOrganizacional
    form_class = AreaOrganizacionalForm
    template_name = "planificacion/area_org_form.html"
    success_url = reverse_lazy("area_org_list")

    def form_valid(self, form):
        messages.success(self.request, "Área organizacional actualizada.")
        return super().form_valid(form)


class AreaOrganizacionalDeleteView(DeleteView):
    model = AreaOrganizacional
    template_name = "planificacion/area_org_confirm_delete.html"
    success_url = reverse_lazy("area_org_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Área organizacional eliminada.")
        return super().delete(request, *args, **kwargs)

# planificacion/views_area_estrategica.py
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import AreaEstrategica
from .forms import AreaEstrategicaForm

class AreaEstrategicaListView(ListView):
    model = AreaEstrategica
    template_name = "planificacion/area_estrategica_list.html"
    context_object_name = "areas_estrategicas"
    paginate_by = 10
    ordering = ["nombre"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        return ctx


class AreaEstrategicaCreateView(CreateView):
    model = AreaEstrategica
    form_class = AreaEstrategicaForm
    template_name = "planificacion/area_estrategica_form.html"
    success_url = reverse_lazy("area_estrategica_list")

    def form_valid(self, form):
        messages.success(self.request, "Área estratégica creada correctamente.")
        return super().form_valid(form)


class AreaEstrategicaUpdateView(UpdateView):
    model = AreaEstrategica
    form_class = AreaEstrategicaForm
    template_name = "planificacion/area_estrategica_form.html"
    success_url = reverse_lazy("area_estrategica_list")

    def form_valid(self, form):
        messages.success(self.request, "Área estratégica actualizada.")
        return super().form_valid(form)


class AreaEstrategicaDeleteView(DeleteView):
    model = AreaEstrategica
    template_name = "planificacion/area_estrategica_confirm_delete.html"
    success_url = reverse_lazy("area_estrategica_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Área estratégica eliminada.")
        return super().delete(request, *args, **kwargs)



# planificacion/views_objetivo.py
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import ObjetivoEstrategico, AreaOrganizacional, AreaEstrategica
from .forms import ObjetivoEstrategicoForm

class ObjetivoListView(ListView):
    model = ObjetivoEstrategico
    template_name = "planificacion/objetivo_list.html"
    context_object_name = "objetivos"
    paginate_by = 10

    def get_queryset(self):
        qs = (ObjetivoEstrategico.objects
              .select_related("area_org", "area_estrategica")
              .order_by("area_org__entidad__sigla", "area_org__nombre", "codigo"))
        q = self.request.GET.get("q", "").strip()
        area_org = self.request.GET.get("area_org", "").strip()
        area_est = self.request.GET.get("area_estrategica", "").strip()

        if q:
            qs = qs.filter(
                Q(codigo__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(area_org__nombre__icontains=q) |
                Q(area_org__entidad__sigla__icontains=q) |
                Q(area_org__entidad__nombre__icontains=q)
            )
        if area_org:
            qs = qs.filter(area_org_id=area_org)
        if area_est:
            qs = qs.filter(area_estrategica_id=area_est)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        ctx["area_org_selected"] = self.request.GET.get("area_org", "")
        ctx["area_est_selected"] = self.request.GET.get("area_estrategica", "")
        ctx["areas_org"] = AreaOrganizacional.objects.select_related("entidad").order_by("entidad__sigla", "nombre")
        ctx["areas_est"] = AreaEstrategica.objects.order_by("nombre")
        return ctx


class ObjetivoCreateView(CreateView):
    model = ObjetivoEstrategico
    form_class = ObjetivoEstrategicoForm
    template_name = "planificacion/objetivo_form.html"
    success_url = reverse_lazy("objetivo_list")

    def get_initial(self):
        initial = super().get_initial()
        # Prefill desde querystring (opcional)
        ao = self.request.GET.get("area_org")
        ae = self.request.GET.get("area_estrategica")
        if ao: initial["area_org"] = ao
        if ae: initial["area_estrategica"] = ae
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Objetivo estratégico creado correctamente.")
        return super().form_valid(form)


class ObjetivoUpdateView(UpdateView):
    model = ObjetivoEstrategico
    form_class = ObjetivoEstrategicoForm
    template_name = "planificacion/objetivo_form.html"
    success_url = reverse_lazy("objetivo_list")

    def form_valid(self, form):
        messages.success(self.request, "Objetivo estratégico actualizado.")
        return super().form_valid(form)


class ObjetivoDeleteView(DeleteView):
    model = ObjetivoEstrategico
    template_name = "planificacion/objetivo_confirm_delete.html"
    success_url = reverse_lazy("objetivo_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Objetivo estratégico eliminado.")
        return super().delete(request, *args, **kwargs)



# planificacion/views_accion.py
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import AccionEstrategica, ObjetivoEstrategico, AreaOrganizacional
from .forms import AccionEstrategicaForm

class AccionListView(ListView):
    model = AccionEstrategica
    template_name = "planificacion/accion_list.html"
    context_object_name = "acciones"
    paginate_by = 10

    def get_queryset(self):
        qs = (AccionEstrategica.objects
              .select_related("objetivo",
                              "objetivo__area_org",
                              "objetivo__area_org__entidad",
                              "objetivo__area_estrategica")
              .order_by("objetivo__area_org__nombre", "objetivo__codigo", "codigo"))
        q = self.request.GET.get("q", "").strip()
        obj = self.request.GET.get("objetivo", "").strip()
        ao = self.request.GET.get("area_org", "").strip()

        if q:
            qs = qs.filter(
                Q(codigo__icontains=q) |
                Q(descripcion__icontains=q) |
                Q(objetivo__descripcion__icontains=q) |
                Q(objetivo__codigo__icontains=q) |
                Q(objetivo__area_org__nombre__icontains=q) |
                Q(objetivo__area_org__entidad__sigla__icontains=q) |
                Q(objetivo__area_org__entidad__nombre__icontains=q)
            )
        if obj:
            qs = qs.filter(objetivo_id=obj)
        if ao:
            qs = qs.filter(objetivo__area_org_id=ao)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        ctx["objetivo_selected"] = self.request.GET.get("objetivo", "")
        ctx["area_org_selected"] = self.request.GET.get("area_org", "")
        ctx["objetivos"] = ObjetivoEstrategico.objects.select_related("area_org").order_by("area_org__nombre", "codigo")
        ctx["areas_org"] = AreaOrganizacional.objects.select_related("entidad").order_by("entidad__sigla", "nombre")
        return ctx


class AccionCreateView(CreateView):
    model = AccionEstrategica
    form_class = AccionEstrategicaForm
    template_name = "planificacion/accion_form.html"
    success_url = reverse_lazy("accion_list")

    def get_initial(self):
        initial = super().get_initial()
        obj = self.request.GET.get("objetivo")
        if obj:
            initial["objetivo"] = obj
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Acción estratégica creada correctamente.")
        return super().form_valid(form)


class AccionUpdateView(UpdateView):
    model = AccionEstrategica
    form_class = AccionEstrategicaForm
    template_name = "planificacion/accion_form.html"
    success_url = reverse_lazy("accion_list")

    def form_valid(self, form):
        messages.success(self.request, "Acción estratégica actualizada.")
        return super().form_valid(form)


class AccionDeleteView(DeleteView):
    model = AccionEstrategica
    template_name = "planificacion/accion_confirm_delete.html"
    success_url = reverse_lazy("accion_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Acción estratégica eliminada.")
        return super().delete(request, *args, **kwargs)


# planificacion/views_operacion.py
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Operacion, AccionEstrategica
from .forms import OperacionForm

class OperacionListView(ListView):
    model = Operacion
    template_name = "planificacion/operacion_list.html"
    context_object_name = "operaciones"
    paginate_by = 10

    def get_queryset(self):
        qs = (Operacion.objects
              .select_related("accion", "accion__objetivo", "accion__objetivo__area_org")
              .order_by("accion__codigo", "codigo"))
        q = self.request.GET.get("q", "").strip()
        accion = self.request.GET.get("accion", "").strip()
        if q:
            qs = qs.filter(Q(codigo__icontains=q) | Q(descripcion__icontains=q) | Q(accion__descripcion__icontains=q))
        if accion:
            qs = qs.filter(accion_id=accion)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["accion_selected"] = self.request.GET.get("accion", "")
        ctx["acciones"] = AccionEstrategica.objects.order_by("codigo")
        return ctx


class OperacionCreateView(CreateView):
    model = Operacion
    form_class = OperacionForm
    template_name = "planificacion/operacion_form.html"
    success_url = reverse_lazy("operacion_list")

    def get_initial(self):
        initial = super().get_initial()
        ac = self.request.GET.get("accion")
        if ac:
            initial["accion"] = ac
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Operación creada correctamente.")
        return super().form_valid(form)


class OperacionUpdateView(UpdateView):
    model = Operacion
    form_class = OperacionForm
    template_name = "planificacion/operacion_form.html"
    success_url = reverse_lazy("operacion_list")

    def form_valid(self, form):
        messages.success(self.request, "Operación actualizada.")
        return super().form_valid(form)


class OperacionDeleteView(DeleteView):
    model = Operacion
    template_name = "planificacion/operacion_confirm_delete.html"
    success_url = reverse_lazy("operacion_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Operación eliminada.")
        return super().delete(request, *args, **kwargs)


# planificacion/views_fuente.py
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import FuenteInformacion
from .forms import FuenteInformacionForm

class FuenteListView(ListView):
    model = FuenteInformacion
    template_name = "planificacion/fuente_list.html"
    context_object_name = "fuentes"
    ordering = ["nombre"]

class FuenteCreateView(CreateView):
    model = FuenteInformacion
    form_class = FuenteInformacionForm
    template_name = "planificacion/fuente_form.html"
    success_url = reverse_lazy("fuente_list")

    def form_valid(self, form):
        messages.success(self.request, "Fuente creada correctamente.")
        return super().form_valid(form)

class FuenteUpdateView(UpdateView):
    model = FuenteInformacion
    form_class = FuenteInformacionForm
    template_name = "planificacion/fuente_form.html"
    success_url = reverse_lazy("fuente_list")

    def form_valid(self, form):
        messages.success(self.request, "Fuente actualizada.")
        return super().form_valid(form)

class FuenteDeleteView(DeleteView):
    model = FuenteInformacion
    template_name = "planificacion/fuente_confirm_delete.html"
    success_url = reverse_lazy("fuente_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Fuente eliminada.")
        return super().delete(request, *args, **kwargs)


# planificacion/views_indicador.py
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Indicador, Operacion, TipoIndicador, UnidadMedida
from .forms import IndicadorForm

class IndicadorListView(ListView):
    model = Indicador
    template_name = "planificacion/indicador_list.html"
    context_object_name = "indicadores"
    paginate_by = 10

    def get_queryset(self):
        qs = (Indicador.objects
              .select_related("operacion", "operacion__accion", "operacion__accion__objetivo",
                              "operacion__accion__objetivo__area_org")
              .prefetch_related("fuentes")
              .order_by("operacion__codigo", "nombre"))
        q = self.request.GET.get("q", "").strip()
        op = self.request.GET.get("op", "").strip()
        tipo = self.request.GET.get("tipo", "").strip()
        unidad = self.request.GET.get("unidad", "").strip()

        if q:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(codigo__icontains=q) |
                Q(operacion__descripcion__icontains=q) |
                Q(operacion__codigo__icontains=q)
            )
        if op:
            qs = qs.filter(operacion_id=op)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if unidad:
            qs = qs.filter(unidad=unidad)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        ctx["op_selected"] = self.request.GET.get("op", "")
        ctx["tipo_selected"] = self.request.GET.get("tipo", "")
        ctx["unidad_selected"] = self.request.GET.get("unidad", "")
        ctx["operaciones"] = Operacion.objects.all().order_by("codigo")
        ctx["tipos"] = TipoIndicador.choices
        ctx["unidades"] = UnidadMedida.choices
        return ctx


class IndicadorCreateView(CreateView):
    model = Indicador
    form_class = IndicadorForm
    template_name = "planificacion/indicador_form.html"
    success_url = reverse_lazy("indicador_list")

    def form_valid(self, form):
        messages.success(self.request, "Indicador creado correctamente.")
        return super().form_valid(form)


class IndicadorUpdateView(UpdateView):
    model = Indicador
    form_class = IndicadorForm
    template_name = "planificacion/indicador_form.html"
    success_url = reverse_lazy("indicador_list")

    def form_valid(self, form):
        messages.success(self.request, "Indicador actualizado.")
        return super().form_valid(form)


class IndicadorDeleteView(DeleteView):
    model = Indicador
    template_name = "planificacion/indicador_confirm_delete.html"
    success_url = reverse_lazy("indicador_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Indicador eliminado.")
        return super().delete(request, *args, **kwargs)




# planificacion/views_serie.py
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View

from .models import SerieIndicador, Indicador
from .forms import SerieIndicadorForm, SerieIndicadorFormSet

class SerieIndicadorListView(ListView):
    model = SerieIndicador
    template_name = "planificacion/serie_list.html"
    context_object_name = "series"
    paginate_by = 12

    def get_queryset(self):
        qs = (SerieIndicador.objects
              .select_related("indicador", "indicador__operacion")
              .order_by("indicador__operacion__codigo", "indicador__nombre", "anio", "-es_programado"))
        q = self.request.GET.get("q", "").strip()
        ind = self.request.GET.get("indicador", "").strip()
        anio = self.request.GET.get("anio", "").strip()
        tipo = self.request.GET.get("tipo", "").strip()  # "prog" o "ejec"

        if q:
            qs = qs.filter(
                Q(indicador__nombre__icontains=q) |
                Q(indicador__codigo__icontains=q) |
                Q(indicador__operacion__codigo__icontains=q) |
                Q(nota__icontains=q)
            )
        if ind:
            qs = qs.filter(indicador_id=ind)
        if anio:
            qs = qs.filter(anio=anio)
        if tipo == "prog":
            qs = qs.filter(es_programado=True)
        elif tipo == "ejec":
            qs = qs.filter(es_programado=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        ctx["indicador_selected"] = self.request.GET.get("indicador", "")
        ctx["anio_selected"] = self.request.GET.get("anio", "")
        ctx["tipo_selected"] = self.request.GET.get("tipo", "")
        ctx["indicadores"] = Indicador.objects.all().order_by("operacion__codigo", "nombre")
        return ctx


class SerieIndicadorCreateView(CreateView):
    model = SerieIndicador
    form_class = SerieIndicadorForm
    template_name = "planificacion/serie_form.html"
    success_url = reverse_lazy("serie_list")

    def get_initial(self):
        initial = super().get_initial()
        ind = self.request.GET.get("indicador")
        if ind:
            initial["indicador"] = ind
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Serie creada correctamente.")
        return super().form_valid(form)


class SerieIndicadorUpdateView(UpdateView):
    model = SerieIndicador
    form_class = SerieIndicadorForm
    template_name = "planificacion/serie_form.html"
    success_url = reverse_lazy("serie_list")

    def form_valid(self, form):
        messages.success(self.request, "Serie actualizada.")
        return super().form_valid(form)


class SerieIndicadorDeleteView(DeleteView):
    model = SerieIndicador
    template_name = "planificacion/serie_confirm_delete.html"
    success_url = reverse_lazy("serie_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Serie eliminada.")
        return super().delete(request, *args, **kwargs)


# ---------- Editor masivo por Indicador ----------
class SerieIndicadorBulkEditView(View):
    template_name = "planificacion/serie_bulk_edit.html"

    def get(self, request, indicador_id):
        indicador = get_object_or_404(Indicador, pk=indicador_id)
        qs = SerieIndicador.objects.filter(indicador=indicador).order_by("anio", "-es_programado")
        formset = SerieIndicadorFormSet(queryset=qs)
        return render(request, self.template_name, {"indicador": indicador, "formset": formset})

    def post(self, request, indicador_id):
        indicador = get_object_or_404(Indicador, pk=indicador_id)
        qs = SerieIndicador.objects.filter(indicador=indicador).order_by("anio", "-es_programado")
        formset = SerieIndicadorFormSet(request.POST, queryset=qs)

        if formset.is_valid():
            # aseguramos indicador en cada form guardado (por si el usuario manipula el DOM)
            instances = formset.save(commit=False)
            ids_a_conservar = []
            for inst in instances:
                inst.indicador = indicador
                inst.save()
                ids_a_conservar.append(inst.pk)
            # eliminar los marcados
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, "Series actualizadas correctamente.")
            return redirect("serie_bulk_edit", indicador_id=indicador.pk)
        else:
            messages.error(request, "Hay errores en el formulario.")
            return render(request, self.template_name, {"indicador": indicador, "formset": formset})
