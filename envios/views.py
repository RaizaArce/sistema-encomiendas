import redis
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.conf import settings

from .models import Encomienda, Empleado
from config.choices import EstadoEnvio


# ── Helper: obtener empleado del usuario logueado ──────────────────
def _get_empleado(request):
    """
    Retorna el Empleado asociado al email del usuario autenticado.
    Si no existe, retorna None y agrega un mensaje de error.
    """
    try:
        return Empleado.objects.get(email=request.user.email)
    except Empleado.DoesNotExist:
        messages.error(
            request,
            'No tienes un perfil de empleado asociado a tu usuario. '
            'Contacta al administrador para que cree uno en /admin/.'
        )
        return None


# ── Dashboard del sistema ─────────────────────────────────────────
@login_required
def dashboard(request):
    """Vista principal del sistema con estadisticas"""
    hoy = timezone.now().date()

    context = {
        'stats': {
            'activas':        Encomienda.objects.activas().count(),
            'en_transito':    Encomienda.objects.en_transito().count(),
            'con_retraso':    Encomienda.objects.con_retraso().count(),
            'entregadas_hoy': Encomienda.objects.filter(
                estado=EstadoEnvio.ENTREGADO, fecha_entrega_real=hoy
            ).count(),
        },
        'ultimas': Encomienda.objects.con_relaciones()[:5],
    }
    return render(request, 'envios/dashboard.html', context)


# ── Listado de encomiendas con paginacion y filtros ───────────────
@require_GET
@login_required
def encomienda_lista(request):
    """Listado paginado con filtro por estado y busqueda"""
    qs = Encomienda.objects.con_relaciones()

    # Filtros opcionales
    estado = request.GET.get('estado', '')
    q      = request.GET.get('q', '')

    if estado:
        qs = qs.filter(estado=estado)
    if q:
        qs = qs.filter(
            Q(codigo__icontains=q)              |
            Q(remitente__apellidos__icontains=q) |
            Q(destinatario__apellidos__icontains=q)
        )

    # Paginacion: 15 encomiendas por pagina
    paginator   = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    encomiendas = paginator.get_page(page_number)

    return render(request, 'envios/lista.html', {
        'encomiendas':   encomiendas,
        'estados':       EstadoEnvio.choices,
        'estado_activo': estado,
        'q':             q,
    })


# ── Detalle de una encomienda ─────────────────────────────────────
@login_required
def encomienda_detalle(request, pk):
    """Muestra el detalle completo de una encomienda y su historial"""
    enc = get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)
    historial = enc.historial.select_related('empleado').all()
    return render(request, 'envios/detalle.html', {
        'encomienda': enc,
        'historial':  historial,
        'estados':    EstadoEnvio.choices,
    })


# ── Crear nueva encomienda ────────────────────────────────────────
@require_http_methods(['GET', 'POST'])
@login_required
def encomienda_crear(request):
    """
    GET  -> muestra el formulario vacio
    POST -> valida, guarda y redirige al detalle
    """
    from .forms import EncomiendaForm

    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            empleado = _get_empleado(request)
            if not empleado:
                return redirect('encomienda_crear')
            enc = form.save(commit=False)
            enc.empleado_registro = empleado
            enc.save()
            messages.success(request, f'Encomienda {enc.codigo} registrada correctamente.')
            return redirect('encomienda_detalle', pk=enc.pk)
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = EncomiendaForm()

    return render(request, 'envios/form.html', {
        'form':   form,
        'titulo': 'Nueva Encomienda',
    })


# ── Cambiar estado de una encomienda ──────────────────────────────
@require_POST
@login_required
def encomienda_cambiar_estado(request, pk):
    """Cambia el estado de una encomienda via POST"""
    enc = get_object_or_404(Encomienda, pk=pk)
    nuevo_estado = request.POST.get('estado')

    if not nuevo_estado or nuevo_estado not in dict(EstadoEnvio.choices):
        messages.error(request, 'Estado invalido.')
        return redirect('encomienda_detalle', pk=pk)

    empleado = _get_empleado(request)
    if not empleado:
        return redirect('encomienda_detalle', pk=pk)

    try:
        enc.cambiar_estado(nuevo_estado, empleado=empleado)
        messages.success(request, f'Encomienda {enc.codigo} actualizada a {enc.get_estado_display()}.')
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('encomienda_detalle', pk=pk)


# ── Endpoint JSON para el badge del navbar ────────────────────────
@login_required
def encomienda_estado_json(request, pk):
    """Devuelve datos de la encomienda en formato JSON"""
    enc = get_object_or_404(Encomienda, pk=pk)
    return JsonResponse({
        'codigo':  enc.codigo,
        'estado':  enc.estado,
        'display': enc.get_estado_display(),
        'retraso': enc.tiene_retraso,
        'dias':    enc.dias_en_transito,
    })


def health_check(request):
    estado = {
        'postgres': False,
        'redis': False,
        'channels': False,
    }

    try:
        from django.db import connection
        connection.ensure_connection()
        estado['postgres'] = True
    except Exception as e:
        estado['postgres_error'] = str(e)

    try:
        r = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        info = r.info()
        estado['redis'] = True
        estado['redis_memoria'] = info.get('used_memory_human')
        estado['redis_clientes'] = info.get('connected_clients')
        estado['redis_version'] = info.get('redis_version')
    except Exception as e:
        estado['redis_error'] = str(e)

    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        cl = get_channel_layer()
        async_to_sync(cl.group_send)('health_check', {'type': 'health.ping'})
        estado['channels'] = True
    except Exception as e:
        estado['channels_error'] = str(e)

    try:
        r = redis.from_url(settings.REDIS_URL)
        estado['empleados_conectados'] = r.scard('encomiendas:group:encomiendas_global')
    except Exception:
        estado['empleados_conectados'] = None

    todo_ok = all([estado['postgres'], estado['redis'], estado['channels']])
    http_status = 200 if todo_ok else 503
    return JsonResponse(estado, status=http_status)
