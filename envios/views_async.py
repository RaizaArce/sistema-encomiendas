import asyncio
from django.http import JsonResponse
from django.utils import timezone
from .models import Encomienda


async def dashboard_stats_async(request):
    if not request.user.is_authenticated:
        from django.http import HttpResponse
        return HttpResponse(status=401)

    hoy = timezone.now().date()

    activas, en_transito, con_retraso, entregadas_hoy = await asyncio.gather(
        Encomienda.objects.activas().acount(),
        Encomienda.objects.en_transito().acount(),
        Encomienda.objects.con_retraso().acount(),
        Encomienda.objects.filter(
            estado='EN', fecha_entrega_real=hoy
        ).acount(),
    )

    return JsonResponse({
        'activas': activas,
        'en_transito': en_transito,
        'con_retraso': con_retraso,
        'entregadas_hoy': entregadas_hoy,
    })
