from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

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

    # Tarjetas de estadisticas: tupla de (label, valor, color_bootstrap, icono_fa)
    stats = [
        ('Activas',      Encomienda.objects.activas().count(),      'primary',   'box'),
        ('En transito',  Encomienda.objects.en_transito().count(),  'info',      'truck'),
        ('Con retraso',  Encomienda.objects.con_retraso().count(),  'danger',    'exclamation-triangle'),
        ('Entregadas hoy', Encomienda.objects.filter(
                            estado=EstadoEnvio.ENTREGADO,
                            fecha_entrega_real=hoy).count(),      'success',   'check-circle'),
    ]

    context = {
        'stats':   stats,
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
