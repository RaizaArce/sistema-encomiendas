from django.db import models
from config.choices import EstadoGeneral
from envios.querysets import RutaQuerySet

# ============================================================
# MODELO: Ruta
# ============================================================
# Define los trayectos disponibles para enviar encomiendas.
# Ej: Ruta "LIM-TRU" va de Lima a Trujillo, cuesta S/25.00,
# tarda 2 días hábiles en llegar.
# ============================================================
class Ruta(models.Model):
    # Código único de ruta, ej: "LIM-TRU" (Lima → Trujillo)
    codigo       = models.CharField(max_length=10, unique=True)
    # Ciudad de origen
    origen       = models.CharField(max_length=100)
    # Ciudad de destino
    destino      = models.CharField(max_length=100)
    # Descripción opcional del trayecto
    descripcion  = models.TextField(blank=True, null=True)
    # Precio base del envío en esta ruta
    precio_base  = models.DecimalField(max_digits=10, decimal_places=2)
    # Días estimados de entrega (mínimo 1)
    dias_entrega = models.PositiveIntegerField(default=1)
    # Estado: Activo (1) o De baja (9)
    estado       = models.IntegerField(
        choices=EstadoGeneral.choices,
        default=EstadoGeneral.ACTIVO
    )

    def __str__(self):
        # Muestra: "LIM-TRU: Lima → Trujillo"
        return f'{self.codigo}: {self.origen} → {self.destino}'

    # ── Manager personalizado ──────────────────────────────
    objects = RutaQuerySet.as_manager()

    class Meta:
        db_table          = 'rutas'
        verbose_name      = 'Ruta'
        verbose_name_plural = 'Rutas'
        ordering          = ['origen', 'destino']