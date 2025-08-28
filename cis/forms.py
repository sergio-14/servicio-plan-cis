# planificacion/forms.py
from django import forms
from .models import AreaOrganizacional, Entidad

class AreaOrganizacionalForm(forms.ModelForm):
    class Meta:
        model = AreaOrganizacional
        fields = ["entidad", "nombre", "responsable"]
        widgets = {
            "entidad": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del área"}),
            "responsable": forms.TextInput(attrs={"class": "form-control", "placeholder": "Responsable (opcional)"}),
        }
        help_texts = {
            "nombre": "Ej.: Carrera de Ingeniería de Sistemas",
            "responsable": "Nombre de la persona responsable (si aplica)",
        }

# planificacion/forms.py
from django import forms
from .models import AreaEstrategica

class AreaEstrategicaForm(forms.ModelForm):
    class Meta:
        model = AreaEstrategica
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej.: Educación, Innovación, etc."
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Breve descripción (opcional)"
            }),
        }

# planificacion/forms.py
from django import forms
from .models import ObjetivoEstrategico, AreaOrganizacional, AreaEstrategica

class ObjetivoEstrategicoForm(forms.ModelForm):
    class Meta:
        model = ObjetivoEstrategico
        fields = ["area_org", "area_estrategica", "codigo", "descripcion"]
        widgets = {
            "area_org": forms.Select(attrs={"class": "form-select"}),
            "area_estrategica": forms.Select(attrs={"class": "form-select"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej.: 1, 2, OBJ-01 (opcional)"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Describe el objetivo…"}),
        }
        help_texts = {
            "area_org": "Área organizacional propietaria del objetivo.",
            "area_estrategica": "Opcional; relaciona con un área estratégica.",
            "codigo": "Opcional, pero si lo usas debe ser único dentro del área organizacional.",
        }

    def clean(self):
        cleaned = super().clean()
        area_org = cleaned.get("area_org")
        codigo = (cleaned.get("codigo") or "").strip()
        # Normaliza código (evita espacios/sensibilidad de mayúsculas)
        if codigo:
            cleaned["codigo"] = codigo

        # Enforce unicidad (area_org, codigo) cuando hay código
        if area_org and codigo:
            qs = ObjetivoEstrategico.objects.filter(area_org=area_org, codigo__iexact=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("codigo", "Ya existe un objetivo con ese código en esta área organizacional.")
        return cleaned



# planificacion/forms.py
from django import forms
from .models import AccionEstrategica, ObjetivoEstrategico, AreaOrganizacional

class AccionEstrategicaForm(forms.ModelForm):
    class Meta:
        model = AccionEstrategica
        fields = ["objetivo", "codigo", "descripcion"]
        widgets = {
            "objetivo": forms.Select(attrs={"class": "form-select"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej.: 1, 2, ACT-01 (opcional)"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Describe la acción estratégica (producto)…"}),
        }
        help_texts = {
            "codigo": "Opcional; si lo usas, debe ser único dentro del mismo objetivo.",
        }

    def clean(self):
        cleaned = super().clean()
        objetivo = cleaned.get("objetivo")
        codigo = (cleaned.get("codigo") or "").strip()
        if codigo:
            cleaned["codigo"] = codigo
            qs = AccionEstrategica.objects.filter(objetivo=objetivo, codigo__iexact=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("codigo", "Ya existe una acción con ese código en este objetivo.")
        return cleaned


# planificacion/forms.py
from django import forms
from .models import Operacion, FuenteInformacion

class OperacionForm(forms.ModelForm):
    class Meta:
        model = Operacion
        fields = ["accion", "codigo", "descripcion"]
        widgets = {
            "accion": forms.Select(attrs={"class": "form-select"}),
            "codigo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej.: 9, 10, OP-01 (opcional)"
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Describe la operación (actividad concreta)…"
            }),
        }

    def clean(self):
        cleaned = super().clean()
        accion = cleaned.get("accion")
        codigo = (cleaned.get("codigo") or "").strip()
        if codigo:
            cleaned["codigo"] = codigo
            qs = Operacion.objects.filter(accion=accion, codigo__iexact=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("codigo", "Ya existe una operación con ese código en esta acción.")
        return cleaned


class FuenteInformacionForm(forms.ModelForm):
    class Meta:
        model = FuenteInformacion
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej.: Informe Académico de Gestión"
            }),
            "descripcion": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Detalles adicionales (opcional)"
            }),
        }



# planificacion/forms.py
from django import forms
from .models import Indicador, Operacion, FuenteInformacion, TipoIndicador, UnidadMedida

class IndicadorForm(forms.ModelForm):
    class Meta:
        model = Indicador
        fields = [
            "operacion", "codigo", "nombre", "tipo", "unidad",
            "formula_texto", "anio_linea_base", "linea_base",
            "anio_meta", "meta_valor", "fuentes", "observaciones",
        ]
        widgets = {
            "operacion": forms.Select(attrs={"class": "form-select"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Opcional"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej.: Nº de matriculados…"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "unidad": forms.Select(attrs={"class": "form-select"}),
            "formula_texto": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Ej.: TECPFAP = (ejecutado/programado)"}),
            "anio_linea_base": forms.NumberInput(attrs={"class": "form-control", "min": 1900, "max": 2100}),
            "linea_base": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "anio_meta": forms.NumberInput(attrs={"class": "form-control", "min": 1900, "max": 2100}),
            "meta_valor": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "fuentes": forms.SelectMultiple(attrs={"class": "form-select", "size": 6}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
        help_texts = {
            "operacion": "Operación a la que pertenece el indicador.",
            "tipo": "Clasificación (PDES, Gestión, Eficacia, etc.).",
            "unidad": "Número, Porcentaje o Texto.",
            "linea_base": "Valor en el año de línea base.",
            "meta_valor": "Valor objetivo al año meta.",
        }

    def clean(self):
        cleaned = super().clean()
        unidad = cleaned.get("unidad")
        linea_base = cleaned.get("linea_base")
        meta_valor = cleaned.get("meta_valor")

        # Si es porcentaje, validar 0..100
        if unidad == UnidadMedida.PORCENTAJE:
            for label, val in [("Línea base", linea_base), ("Meta", meta_valor)]:
                if val is not None and (val < 0 or val > 100):
                    self.add_error("meta_valor" if label == "Meta" else "linea_base",
                                   f"{label} debe estar entre 0 y 100 para unidad porcentaje.")

        # Unicidad lógica por (operacion, nombre)
        op = cleaned.get("operacion")
        nombre = cleaned.get("nombre")
        if op and nombre:
            qs = Indicador.objects.filter(operacion=op, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("nombre", "Ya existe un indicador con este nombre en la misma operación.")
        return cleaned



# planificacion/forms.py
from django import forms
from django.forms import modelformset_factory
from .models import SerieIndicador, Indicador, UnidadMedida

class SerieIndicadorForm(forms.ModelForm):
    class Meta:
        model = SerieIndicador
        fields = ["indicador", "anio", "valor", "es_programado", "nota"]
        widgets = {
            "indicador": forms.Select(attrs={"class": "form-select"}),
            "anio": forms.NumberInput(attrs={"class": "form-control", "min": 1900, "max": 2100}),
            "valor": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "es_programado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "nota": forms.TextInput(attrs={"class": "form-control", "placeholder": "Opcional"}),
        }
        help_texts = {
            "es_programado": "Marcado = Programado (plan). Desmarcado = Ejecutado (real).",
        }

    def clean(self):
        cleaned = super().clean()
        indicador = cleaned.get("indicador")
        anio = cleaned.get("anio")
        valor = cleaned.get("valor")
        es_prog = cleaned.get("es_programado", True)

        # Validación 0..100 si la unidad del indicador es %
        if indicador and indicador.unidad == UnidadMedida.PORCENTAJE and valor is not None:
            if valor < 0 or valor > 100:
                self.add_error("valor", "Para indicadores en %, el valor debe estar entre 0 y 100.")

        # Unicidad (indicador, año, es_programado)
        if indicador and anio:
            qs = SerieIndicador.objects.filter(indicador=indicador, anio=anio, es_programado=es_prog)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error("anio", "Ya existe una fila para este indicador/año y este tipo (programado/ejecutado).")
        return cleaned


# ---------- Editor masivo (para un indicador) ----------
class SerieIndicadorInlineForm(forms.ModelForm):
    class Meta:
        model = SerieIndicador
        fields = ["anio", "valor", "es_programado", "nota"]
        widgets = {
            "anio": forms.NumberInput(attrs={"class": "form-control", "min": 1900, "max": 2100}),
            "valor": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "es_programado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "nota": forms.TextInput(attrs={"class": "form-control", "placeholder": "Opcional"}),
        }

SerieIndicadorFormSet = modelformset_factory(
    SerieIndicador,
    form=SerieIndicadorInlineForm,
    extra=0, can_delete=True
)
