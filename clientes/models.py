from django.db import models
from config.choices import EstadoGeneral, TipoDocumento
from envios.querysets import ClienteQuerySet

# ============================================================
# MODELO: Cliente
# ============================================================
# Representa a una persona que envía o recibe encomiendas.
# Cada cliente tiene un tipo de documento (DNI, RUC, Pasaporte)
# y su número único, más datos de contacto.
# ============================================================
class Cliente(models.Model):
    # --- Identificación ---
    # Tipo de documento: usa el enumerado TipoDocumento (DNI/RUC/PAS)
    tipo_doc = models.CharField(
        max_length=3,
        choices=TipoDocumento.choices,
        default=TipoDocumento.DNI
    )
    # Número de documento (único en el sistema)
    nro_doc        = models.CharField(max_length=15, unique=True)
    nombres        = models.CharField(max_length=100)
    apellidos      = models.CharField(max_length=100)

    # --- Contacto (opcional) ---
    telefono       = models.CharField(max_length=15, blank=True, null=True)
    email          = models.EmailField(blank=True, null=True)
    direccion      = models.TextField(blank=True, null=True)

    # --- Estado y auditoría ---
    # Estado: Activo (1) o De baja (9) - usa el enumerado EstadoGeneral
    estado         = models.IntegerField(
        choices=EstadoGeneral.choices,
        default=EstadoGeneral.ACTIVO
    )
    # Fecha de registro: se asigna automáticamente al crear
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # --- Representación ---
    def __str__(self):
        return f'{self.nro_doc} - {self.apellidos}, {self.nombres}'

    # ── Propiedades útiles ─────────────────────────────────
    @property
    def nombre_completo(self):
        """Nombre y apellidos en formato legible"""
        return f'{self.apellidos}, {self.nombres}'

    @property
    def esta_activo(self):
        """Devuelve True si el estado es ACTIVO"""
        return self.estado == EstadoGeneral.ACTIVO

    @property
    def total_encomiendas_enviadas(self):
        """Número de encomiendas donde este cliente es remitente"""
        return self.envios_como_remitente.count()

    # ── Manager personalizado ──────────────────────────────
    objects = ClienteQuerySet.as_manager()

    # --- Metadatos ---
    class Meta:
        db_table          = 'clientes'              # Nombre de la tabla en BD
        verbose_name      = 'Cliente'               # Nombre singular en Admin
        verbose_name_plural = 'Clientes'             # Nombre plural en Admin
        ordering          = ['apellidos', 'nombres'] # Orden por defecto