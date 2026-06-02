from django.db import models
from config.choices import EstadoGeneral, EstadoEnvio


# ============================================================
# QUERYSETS PERSONALIZADOS
# ============================================================
# Un QuerySet personalizado encapsula consultas frecuentes
# como métodos reutilizables.
# Ej: Encomienda.objects.activas()
# ============================================================


class EncomiendaQuerySet(models.QuerySet):
    """QuerySet personalizado para el modelo Encomienda"""

    # ── Filtros por estado ───────────────────────────
    def pendientes(self):
        return self.filter(estado=EstadoEnvio.PENDIENTE)

    def en_transito(self):
        return self.filter(estado=EstadoEnvio.EN_TRANSITO)

    def entregadas(self):
        return self.filter(estado=EstadoEnvio.ENTREGADO)

    def devueltas(self):
        return self.filter(estado=EstadoEnvio.DEVUELTO)

    def activas(self):
        """Pendientes + en tránsito + en destino"""
        return self.filter(
            estado__in=[EstadoEnvio.PENDIENTE, EstadoEnvio.EN_TRANSITO, EstadoEnvio.EN_DESTINO]
        )

    # ── Filtros compuestos ─────────────────────────
    def por_ruta(self, ruta):
        return self.filter(ruta=ruta)

    def por_remitente(self, cliente):
        return self.filter(remitente=cliente)

    def por_destinatario(self, cliente):
        return self.filter(destinatario=cliente)

    def en_transito_por_ruta(self, ruta):
        return self.en_transito().por_ruta(ruta)

    # ── Con retraso ────────────────────────────
    def con_retraso(self):
        """Encomiendas activas cuya fecha estimada ya pasó"""
        from django.utils import timezone
        return self.activas().filter(
            fecha_entrega_est__lt=timezone.now().date()
        )

    # ── Optimización de consultas ──────────────────
    def con_relaciones(self):
        """Precarga las relaciones más usadas (evita el problema N+1)"""
        return self.select_related(
            'remitente', 'destinatario', 'ruta', 'empleado_registro'
        )


class ClienteQuerySet(models.QuerySet):
    """QuerySet personalizado para el modelo Cliente"""

    def activos(self):
        return self.filter(estado=EstadoGeneral.ACTIVO)

    def de_baja(self):
        return self.filter(estado=EstadoGeneral.DE_BAJA)

    def con_dni(self):
        return self.filter(tipo_doc='DNI')

    def buscar(self, termino):
        """Búsqueda por nombre, apellido o número de documento"""
        return self.filter(
            models.Q(nombres__icontains=termino) |
            models.Q(apellidos__icontains=termino) |
            models.Q(nro_doc__icontains=termino)
        )


class RutaQuerySet(models.QuerySet):
    """QuerySet personalizado para el modelo Ruta"""

    def activas(self):
        return self.filter(estado=EstadoGeneral.ACTIVO)

    def por_origen(self, ciudad):
        return self.filter(origen__icontains=ciudad)

    def por_destino(self, ciudad):
        return self.filter(destino__icontains=ciudad)
