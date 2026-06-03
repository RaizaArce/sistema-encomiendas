from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from django.conf import settings

from .models import Encomienda, Empleado
from .serializers import (
    EncomiendaSerializer, EncomiendaDetailSerializer,
    EncomiendaV2Serializer, HistorialEstadoSerializer,
    EncomiendaListSerializer, EncomiendaBulkSerializer,
)
from api.pagination import EncomiendaPagination, HistorialPagination
from api.filters import EncomiendaFilter
from api.permissions import EsEmpleadoActivo, EsPropietarioOAdmin
from api.throttles import CambioEstadoThrottle
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend


@extend_schema_view(
    list=extend_schema(summary='Listar encomiendas', tags=['Encomiendas']),
    create=extend_schema(summary='Crear encomienda', tags=['Encomiendas']),
    retrieve=extend_schema(summary='Detalle de encomienda', tags=['Encomiendas']),
    update=extend_schema(summary='Actualizar encomienda', tags=['Encomiendas']),
    partial_update=extend_schema(summary='Actualizar parcial', tags=['Encomiendas']),
    destroy=extend_schema(summary='Eliminar encomienda', tags=['Encomiendas']),
)
class EncomiendaViewSet(viewsets.ModelViewSet):
    queryset            = Encomienda.objects.con_relaciones()
    serializer_class    = EncomiendaSerializer
    permission_classes  = [IsAuthenticated, EsEmpleadoActivo]
    pagination_class    = EncomiendaPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EncomiendaFilter
    search_fields   = ['codigo', 'remitente__apellidos', 'destinatario__apellidos', 'descripcion']
    ordering_fields = ['fecha_registro', 'peso_kg', 'costo_envio']
    ordering        = ['-fecha_registro']

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ['update', 'partial_update', 'destroy']:
            permissions.append(EsPropietarioOAdmin())
        return permissions

    def get_serializer_class(self):
        version = getattr(self.request, 'version', 'v1')
        if version == 'v2':
            return EncomiendaV2Serializer
        if self.action == 'retrieve':
            return EncomiendaDetailSerializer
        if self.action == 'list':
            return EncomiendaListSerializer
        return EncomiendaSerializer

    def get_queryset(self):
        qs = Encomienda.objects.con_relaciones()
        if self.action == 'list':
            qs = qs.only(
                'id', 'codigo', 'descripcion', 'peso_kg',
                'remitente', 'destinatario', 'ruta', 'empleado_registro',
                'estado', 'costo_envio', 'fecha_registro', 'fecha_entrega_est',
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(empleado_registro=self.request.user.empleado)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response['X-API-Version'] = getattr(request, 'version', 'v1')
        return response

    # Accion de detalle: POST /encomiendas/{pk}/cambiar_estado/
    @extend_schema(
        summary='Cambiar estado de encomienda',
        description='Cambia el estado y registra el cambio en el historial. Estados: PE, TR, DE, EN, DV.',
        responses={200: EncomiendaSerializer, 400: OpenApiResponse(description='Estado invalido')},
        examples=[
            OpenApiExample('Pasar a En transito', value={'estado': 'TR', 'observacion': 'Recogido en agencia Lima'}, request_only=True),
            OpenApiExample('Marcar como Entregado', value={'estado': 'EN', 'observacion': 'Entregado al destinatario'}, request_only=True),
        ],
        tags=['Encomiendas'],
    )
    @action(detail=True, methods=['post'], url_path='cambiar_estado', throttle_classes=[CambioEstadoThrottle])
    def cambiar_estado(self, request, pk=None):
        enc          = self.get_object()
        nuevo_estado = request.data.get('estado')
        observacion  = request.data.get('observacion', '')

        if not nuevo_estado:
            return Response({'error': 'El campo estado es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            empleado = Empleado.objects.get(email=request.user.email)
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            return Response(EncomiendaSerializer(enc).data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Accion de lista: GET /encomiendas/con_retraso/
    @action(detail=False, methods=['get'], url_path='con_retraso')
    def con_retraso(self, request):
        qs = Encomienda.objects.con_retraso().con_relaciones()
        return Response(self.get_serializer(qs, many=True).data)

    # Accion de lista: GET /encomiendas/pendientes/
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        qs = Encomienda.objects.pendientes().con_relaciones()
        return Response(self.get_serializer(qs, many=True).data)

    # GET /encomiendas/{pk}/historial/
    @action(detail=True, methods=['get'], url_path='historial')
    def historial(self, request, pk=None):
        enc       = self.get_object()
        qs        = enc.historial.select_related('empleado').order_by('-fecha_cambio')
        paginator = HistorialPagination()
        page      = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = HistorialEstadoSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        return Response(HistorialEstadoSerializer(qs, many=True).data)

    # GET /encomiendas/estadisticas/
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        from django.utils import timezone
        hoy = timezone.now().date()
        return Response({
            'total_activas':  Encomienda.objects.activas().count(),
            'en_transito':    Encomienda.objects.en_transito().count(),
            'con_retraso':    Encomienda.objects.con_retraso().count(),
            'entregadas_hoy': Encomienda.objects.filter(estado='EN', fecha_entrega_real=hoy).count(),
        })

    # POST /encomiendas/bulk_create/
    @extend_schema(
        summary='Crear multiples encomiendas',
        request=EncomiendaBulkSerializer,
        responses={201: EncomiendaSerializer(many=True)},
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = EncomiendaBulkSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response({
            'created': EncomiendaSerializer(result['created'], many=True).data,
            'errors': result['errors'],
        }, status=status.HTTP_201_CREATED)

    # POST /encomiendas/bulk_estado/
    @extend_schema(
        summary='Cambiar estado a multiples encomiendas',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'encomienda_ids': {'type': 'array', 'items': {'type': 'integer'}},
                    'estado': {'type': 'string'},
                    'observacion': {'type': 'string'},
                },
                'required': ['encomienda_ids', 'estado'],
            }
        },
        tags=['Encomiendas'],
    )
    @action(detail=False, methods=['post'], url_path='bulk_estado')
    def bulk_estado(self, request):
        ids = request.data.get('encomienda_ids', [])
        nuevo_estado = request.data.get('estado')
        observacion = request.data.get('observacion', '')

        if not ids or not nuevo_estado:
            return Response({'error': 'encomienda_ids y estado son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            empleado = Empleado.objects.get(email=request.user.email)
        except Empleado.DoesNotExist:
            return Response({'error': 'Empleado no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for pk in ids:
            try:
                enc = Encomienda.objects.get(pk=pk)
                enc.cambiar_estado(nuevo_estado, empleado, observacion)
                results.append({'id': pk, 'codigo': enc.codigo, 'success': True})
            except Exception as e:
                results.append({'id': pk, 'success': False, 'error': str(e)})

        return Response({'results': results})
