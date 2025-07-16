from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class AreaEstrategica(models.Model):
    """Áreas estratégicas del plan de desarrollo"""
    codigo_area = models.IntegerField(unique=True, verbose_name="Código de Área")
    nombre_area = models.CharField(max_length=100, verbose_name="Nombre del Área")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Área Estratégica"
        verbose_name_plural = "Áreas Estratégicas"
        ordering = ['codigo_area']

    def __str__(self):
        return f"{self.codigo_area} - {self.nombre_area}"


class Entidad(models.Model):
    """Entidades u organizaciones responsables"""
    codigo_entidad = models.IntegerField(verbose_name="Código de Entidad")
    nombre_entidad = models.CharField(max_length=100, verbose_name="Nombre de la Entidad")
    tipo_entidad = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tipo de Entidad")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Entidad"
        verbose_name_plural = "Entidades"
        ordering = ['codigo_entidad', 'nombre_entidad']

    def __str__(self):
        return f"{self.codigo_entidad} - {self.nombre_entidad}"


class AreaOrganizacional(models.Model):
    """Áreas organizacionales dentro de las entidades"""
    entidad = models.ForeignKey(Entidad, on_delete=models.CASCADE, related_name='areas_organizacionales')
    codigo_area_org = models.IntegerField(verbose_name="Código de Área Organizacional")
    nombre_area_org = models.CharField(max_length=100, verbose_name="Nombre del Área Organizacional")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Área Organizacional"
        verbose_name_plural = "Áreas Organizacionales"
        ordering = ['entidad', 'codigo_area_org']
        unique_together = ['entidad', 'codigo_area_org']

    def __str__(self):
        return f"{self.entidad.nombre_entidad} - {self.nombre_area_org}"


class TipoIndicador(models.Model):
    """Tipos de indicadores (Gestión, Resultado PDU, etc.)"""
    TIPO_CHOICES = [
        ('gestion', 'Gestión'),
        ('resultado_pdu', 'Resultado PDU'),
        ('resultado_pdes', 'Resultado PDES'),
    ]
    
    nombre_tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, unique=True, verbose_name="Tipo de Indicador")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Tipo de Indicador"
        verbose_name_plural = "Tipos de Indicadores"

    def __str__(self):
        return self.get_nombre_tipo_display()


class TipoResultado(models.Model):
    """Tipos de resultados (PDU, PDES, etc.)"""
    TIPO_CHOICES = [
        ('pdu', 'PDU'),
        ('pdes', 'PDES'),
        ('n_c', 'N/C'),
    ]
    
    nombre_tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, unique=True, verbose_name="Tipo de Resultado")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Tipo de Resultado"
        verbose_name_plural = "Tipos de Resultados"

    def __str__(self):
        return self.get_nombre_tipo_display()


class ObjetivoEstrategico(models.Model):
    """Objetivos estratégicos del plan"""
    area_estrategica = models.ForeignKey(AreaEstrategica, on_delete=models.CASCADE, related_name='objetivos')
    codigo_objetivo = models.IntegerField(verbose_name="Código del Objetivo")
    descripcion_objetivo = models.TextField(verbose_name="Descripción del Objetivo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Objetivo Estratégico"
        verbose_name_plural = "Objetivos Estratégicos"
        ordering = ['area_estrategica', 'codigo_objetivo']

    def __str__(self):
        return f"{self.codigo_objetivo} - {self.descripcion_objetivo[:50]}..."


class Operacion(models.Model):
    """Operaciones específicas dentro de cada objetivo"""
    objetivo = models.ForeignKey(ObjetivoEstrategico, on_delete=models.CASCADE, related_name='operaciones')
    codigo_operacion = models.IntegerField(verbose_name="Código de Operación")
    descripcion_operacion = models.TextField(verbose_name="Descripción de la Operación")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Operación"
        verbose_name_plural = "Operaciones"
        ordering = ['objetivo', 'codigo_operacion']

    def __str__(self):
        return f"{self.codigo_operacion} - {self.descripcion_operacion[:50]}..."


class Indicador(models.Model):
    """Indicadores específicos para medir el cumplimiento"""
    codigo_indicador = models.IntegerField(unique=True, verbose_name="Código del Indicador")
    nombre_indicador = models.CharField(max_length=200, verbose_name="Nombre del Indicador")
    descripcion_indicador = models.TextField(blank=True, null=True, verbose_name="Descripción del Indicador")
    tipo_indicador = models.ForeignKey(TipoIndicador, on_delete=models.PROTECT, verbose_name="Tipo de Indicador")
    tipo_resultado = models.ForeignKey(TipoResultado, on_delete=models.PROTECT, blank=True, null=True, verbose_name="Tipo de Resultado")
    formula = models.CharField(max_length=500, blank=True, null=True, verbose_name="Fórmula")
    linea_base_2020 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Línea Base 2020")
    meta_2025 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Meta 2025")
    fuente_informacion = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fuente de Información")
    area_organizacional = models.ForeignKey(AreaOrganizacional, on_delete=models.CASCADE, related_name='indicadores')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Indicador"
        verbose_name_plural = "Indicadores"
        ordering = ['codigo_indicador']

    def __str__(self):
        return f"{self.codigo_indicador} - {self.nombre_indicador}"


class AccionEstrategica(models.Model):
    """Acciones estratégicas específicas"""
    operacion = models.ForeignKey(Operacion, on_delete=models.CASCADE, related_name='acciones')
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, related_name='acciones')
    descripcion_accion = models.TextField(verbose_name="Descripción de la Acción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Acción Estratégica"
        verbose_name_plural = "Acciones Estratégicas"

    def __str__(self):
        return f"{self.descripcion_accion[:50]}..."


class ProgramacionFisica(models.Model):
    """Programación física anual de los indicadores"""
    ANIOS_CHOICES = [
        (2021, '2021'),
        (2022, '2022'),
        (2023, '2023'),
        (2024, '2024'),
        (2025, '2025'),
    ]
    
    indicador = models.ForeignKey(Indicador, on_delete=models.CASCADE, related_name='programaciones')
    anio = models.IntegerField(choices=ANIOS_CHOICES, validators=[MinValueValidator(2021), MaxValueValidator(2025)])
    valor_programado = models.CharField(max_length=50, blank=True, null=True, verbose_name="Valor Programado")
    valor_ejecutado = models.CharField(max_length=50, blank=True, null=True, verbose_name="Valor Ejecutado")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Programación Física"
        verbose_name_plural = "Programaciones Físicas"
        unique_together = ['indicador', 'anio']
        ordering = ['indicador', 'anio']

    def __str__(self):
        return f"{self.indicador.nombre_indicador} - {self.anio}"


class TasaEficacia(models.Model):
    """Tasas de eficacia para grupos de indicadores"""
    area_organizacional = models.ForeignKey(AreaOrganizacional, on_delete=models.CASCADE, related_name='tasas_eficacia')
    nombre_tasa = models.CharField(max_length=200, verbose_name="Nombre de la Tasa")
    formula_tasa = models.CharField(max_length=500, blank=True, null=True, verbose_name="Fórmula de la Tasa")
    linea_base = models.CharField(max_length=50, blank=True, null=True, verbose_name="Línea Base")
    meta_2025 = models.CharField(max_length=50, blank=True, null=True, verbose_name="Meta 2025")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tasa de Eficacia"
        verbose_name_plural = "Tasas de Eficacia"

    def __str__(self):
        return self.nombre_tasa


class ProgramacionTasaEficacia(models.Model):
    """Programación anual de las tasas de eficacia"""
    ANIOS_CHOICES = [
        (2021, '2021'),
        (2022, '2022'),
        (2023, '2023'),
        (2024, '2024'),
        (2025, '2025'),
    ]
    
    tasa = models.ForeignKey(TasaEficacia, on_delete=models.CASCADE, related_name='programaciones')
    anio = models.IntegerField(choices=ANIOS_CHOICES, validators=[MinValueValidator(2021), MaxValueValidator(2025)])
    valor_programado = models.CharField(max_length=50, blank=True, null=True, verbose_name="Valor Programado")
    valor_ejecutado = models.CharField(max_length=50, blank=True, null=True, verbose_name="Valor Ejecutado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Programación de Tasa de Eficacia"
        verbose_name_plural = "Programaciones de Tasas de Eficacia"
        unique_together = ['tasa', 'anio']
        ordering = ['tasa', 'anio']

    def __str__(self):
        return f"{self.tasa.nombre_tasa} - {self.anio}"


# Managers personalizados para consultas comunes
class IndicadorManager(models.Manager):
    def por_area_organizacional(self, area_id):
        return self.filter(area_organizacional_id=area_id)
    
    def por_tipo(self, tipo):
        return self.filter(tipo_indicador__nombre_tipo=tipo)
    
    def con_programacion_anual(self):
        return self.prefetch_related('programaciones').all()


class ProgramacionFisicaManager(models.Manager):
    def por_anio(self, anio):
        return self.filter(anio=anio)
    
    def con_valores_ejecutados(self):
        return self.exclude(valor_ejecutado__isnull=True).exclude(valor_ejecutado='')


# Asignar managers personalizados
Indicador.add_to_class('objects', IndicadorManager())
ProgramacionFisica.add_to_class('objects', ProgramacionFisicaManager())