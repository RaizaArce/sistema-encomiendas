from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Encomienda
from .serializers import EncomiendaSerializer


# ── 5.2 FBV con @api_view ──────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def encomienda_list(request):
    if request.method == 'GET':
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EncomiendaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(empleado_registro=request.user.empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def encomienda_detail(request, pk):
    enc = get_object_or_404(Encomienda, pk=pk)

    if request.method == 'GET':
        return Response(EncomiendaSerializer(enc).data)

    elif request.method in ['PUT', 'PATCH']:
        s = EncomiendaSerializer(enc, data=request.data, partial=(request.method == 'PATCH'))
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    elif request.method == 'DELETE':
        enc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── 5.3 APIView ────────────────────────────────────────────────────
from rest_framework.views import APIView
from .serializers import EncomiendaDetailSerializer


class EncomiendaListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Encomienda.objects.con_relaciones()
        serializer = EncomiendaSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = EncomiendaSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(empleado_registro=request.user.empleado)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EncomiendaDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)

    def get(self, request, pk):
        enc = self.get_object(pk)
        return Response(EncomiendaDetailSerializer(enc).data)

    def put(self, request, pk):
        enc = self.get_object(pk)
        s = EncomiendaSerializer(enc, data=request.data, context={'request': request})
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def patch(self, request, pk):
        enc = self.get_object(pk)
        s = EncomiendaSerializer(enc, data=request.data, partial=True, context={'request': request})
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)

    def delete(self, request, pk):
        enc = self.get_object(pk)
        enc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── 5.5 Vistas Genericas ───────────────────────────────────────────
from rest_framework import generics
from clientes.models import Cliente
from rutas.models import Ruta
from .serializers import ClienteSerializer, RutaSerializer


class ClienteListView(generics.ListAPIView):
    serializer_class   = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cliente.objects.activos()


class RutaListView(generics.ListAPIView):
    serializer_class   = RutaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Ruta.objects.activas()
