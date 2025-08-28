# planificacion/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

DECIMALS = dict(max_digits=14, decimal_places=2)

class TimeStampedModel(models.Model):
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Entidad(TimeStampedModel):
    nombre = models.CharField(max_length=150, unique=True)
    sigla = models.CharField(max_length=20, blank=True)
    def __str__(self): return self.nombre

class AreaOrganizacional(TimeStampedModel):
    entidad = models.ForeignKey(Entidad, on_delete=models.CASCADE, related_name="areas")
    nombre = models.CharField(max_length=180)
    responsable = models.CharField(max_length=120, blank=True)
    class Meta:
        unique_together = [("entidad", "nombre")]
        indexes = [models.Index(fields=["entidad","nombre"])]
        verbose_name = "Área organizacional"
        verbose_name_plural = "Áreas organizacionales"
    def __str__(self): return f"{self.nombre} ({self.entidad.sigla or self.entidad.nombre})"

class AreaEstrategica(TimeStampedModel):
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True)
    def __str__(self): return self.nombre

class ObjetivoEstrategico(TimeStampedModel):
    area_org = models.ForeignKey(AreaOrganizacional, on_delete=models.CASCADE, related_name="objetivos")
    area_estrategica = models.ForeignKey(AreaEstrategica, on_delete=models.SET_NULL, null=True, blank=True, related_name="objetivos")
    codigo = models.CharField(max_length=20, blank=True)  # columna COD
    descripcion = models.TextField()
    class Meta:
        unique_together = [("area_org","codigo")]
        indexes = [models.Index(fields=["area_org","codigo"])]
        verbose_name = "Objetivo estratégico"
    def __str__(self): return f"{self.codigo or ''} {self.descripcion[:60]}"

class AccionEstrategica(TimeStampedModel):
    objetivo = models.ForeignKey(ObjetivoEstrategico, on_delete=models.CASCADE, related_name="acciones")
    codigo = models.CharField(max_length=20, blank=True)
    descripcion = models.TextField()  # “Incrementar el número de estudiantes…”
    class Meta:
        unique_together = [("objetivo","codigo")]
        indexes = [models.Index(fields=["objetivo","codigo"])]
        verbose_name = "Acción estratégica (producto)"
    def __str__(self): return f"{self.codigo or ''} {self.descripcion[:60]}"

class Operacion(TimeStampedModel):
    accion = models.ForeignKey(AccionEstrategica, on_delete=models.CASCADE, related_name="operaciones")
    codigo = models.CharField(max_length=20, blank=True)  # el “9”, “10”, “14”, “15” de tu cuadro
    descripcion = models.TextField()  # “Difundir a través de los medios…”
    class Meta:
        unique_together = [("accion","codigo")]
        indexes = [models.Index(fields=["accion","codigo"])]
        verbose_name = "Operación"
    def __str__(self): return f"Op.{self.codigo or '-'} - {self.descripcion[:60]}"

class FuenteInformacion(TimeStampedModel):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True)
    def __str__(self): return self.nombre

class TipoIndicador(models.TextChoices):
    RESULTADO_PDES = "RESULTADO_PDES", "Resultado PDES"
    GESTION = "GESTION", "Gestión"
    EFICACIA = "EFICACIA", "Eficacia"
    EFICIENCIA = "EFICIENCIA", "Eficiencia"
    CALIDAD = "CALIDAD", "Calidad"
    COBERTURA = "COBERTURA", "Cobertura"
    OTRO = "OTRO", "Otro"

class UnidadMedida(models.TextChoices):
    NUMERO = "NRO", "Número"
    PORCENTAJE = "PCT", "Porcentaje"
    TEXTO = "TXT", "Texto"

class Indicador(TimeStampedModel):
    operacion = models.ForeignKey(Operacion, on_delete=models.CASCADE, related_name="indicadores")
    codigo = models.CharField(max_length=30, blank=True)  # si manejas un código interno del indicador
    nombre = models.CharField(max_length=300)  # “Nº de matriculados…”, “Tasa de eficacia…”
    tipo = models.CharField(max_length=20, choices=TipoIndicador.choices, default=TipoIndicador.OTRO)
    unidad = models.CharField(max_length=3, choices=UnidadMedida.choices, default=UnidadMedida.NUMERO)
    formula_texto = models.TextField(blank=True)  # “TECPFAP = …” o “N/C”
    anio_linea_base = models.PositiveSmallIntegerField(default=2020)
    linea_base = models.DecimalField(**DECIMALS, null=True, blank=True)
    anio_meta = models.PositiveSmallIntegerField(default=2025)
    meta_valor = models.DecimalField(**DECIMALS, null=True, blank=True)
    fuentes = models.ManyToManyField(FuenteInformacion, blank=True, related_name="indicadores")
    observaciones = models.TextField(blank=True)

    class Meta:
        unique_together = [("operacion","nombre")]
        indexes = [models.Index(fields=["operacion","nombre"]), models.Index(fields=["tipo","unidad"])]
        verbose_name = "Indicador"
    def __str__(self): return self.nombre

    @property
    def es_porcentaje(self) -> bool:
        return self.unidad == UnidadMedida.PORCENTAJE

class SerieIndicador(TimeStampedModel):
    """Programación física y/o ejecución por año."""
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, related_name="series")
    anio = models.PositiveSmallIntegerField()
    valor = models.DecimalField(**DECIMALS, null=True, blank=True)
    es_programado = models.BooleanField(default=True)  # True: plan; False: ejecutado/real
    nota = models.CharField(max_length=250, blank=True)

    class Meta:
        unique_together = [("indicador","anio","es_programado")]
        indexes = [models.Index(fields=["indicador","anio"])]
        ordering = ["indicador","anio"]
        verbose_name = "Serie anual de indicador"
    def __str__(self): return f"{self.indicador.nombre[:40]} - {self.anio} ({'Prog' if self.es_programado else 'Ejec'})"

    def clean(self):
        # Si el indicador es % limitar lógicamente 0..100
        if self.indicador and self.indicador.unidad == UnidadMedida.PORCENTAJE and self.valor is not None:
            if self.valor < 0 or self.valor > 100:
                from django.core.exceptions import ValidationError
                raise ValidationError("Para indicadores en %, el valor debe estar entre 0 y 100.")
