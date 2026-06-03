import pytest
from django.urls import reverse
from rest_framework import status
from envios.models import Encomienda, HistorialEstado


class TestAuth:
    def test_obtener_token(self, api_client, user_admin):
        response = api_client.post('/api/v1/auth/token/', {
            'username': 'admin', 'password': 'admin123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    @pytest.mark.django_db
    def test_token_invalido(self, api_client):
        response = api_client.post('/api/v1/auth/token/', {
            'username': 'admin', 'password': 'wrongpass'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, user_admin):
        res = api_client.post('/api/v1/auth/token/', {
            'username': 'admin', 'password': 'admin123'
        })
        refresh = res.data['refresh']
        response = api_client.post('/api/v1/auth/token/refresh/', {
            'refresh': refresh
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_blacklist_token(self, api_client, user_admin):
        res = api_client.post('/api/v1/auth/token/', {
            'username': 'admin', 'password': 'admin123'
        })
        refresh = res.data['refresh']
        response = api_client.post('/api/v1/auth/token/blacklist/', {
            'refresh': refresh
        })
        assert response.status_code == status.HTTP_200_OK

    def test_endpoint_sin_token(self, api_client):
        response = api_client.get('/api/v1/encomiendas/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data.get('error') is True


class TestEncomiendas:
    def test_listar_encomiendas(self, auth_client, encomienda):
        response = auth_client.get('/api/v1/encomiendas/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('error') is None
        assert 'count' in response.data
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        assert 'X-API-Version' in response.headers

    @pytest.mark.skip(reason='Requiere autogeneracion de codigo')
    def test_crear_encomienda(self, auth_client, cliente, cliente2, ruta):
        data = {
            'descripcion': 'Nuevo paquete',
            'peso_kg': 3.0,
            'remitente_id': cliente.id,
            'destinatario_id': cliente2.id,
            'ruta_id': ruta.id,
            'costo_envio': 30.00,
            'fecha_entrega_est': '2027-01-15',
        }
        response = auth_client.post('/api/v1/encomiendas/', data)
        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_detalle_encomienda(self, auth_client, encomienda):
        response = auth_client.get(f'/api/v1/encomiendas/{encomienda.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['codigo'] == encomienda.codigo
        assert 'remitente' in response.data
        assert 'historial' in response.data

    def test_actualizar_encomienda(self, auth_client, encomienda):
        response = auth_client.patch(
            f'/api/v1/encomiendas/{encomienda.id}/',
            {'descripcion': 'Descripcion actualizada'},
        )
        assert response.status_code == status.HTTP_200_OK
        encomienda.refresh_from_db()
        assert encomienda.descripcion == 'Descripcion actualizada'

    def test_eliminar_encomienda(self, auth_client, encomienda):
        response = auth_client.delete(f'/api/v1/encomiendas/{encomienda.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_cambiar_estado(self, auth_client, encomienda, empleado_admin):
        response = auth_client.post(
            f'/api/v1/encomiendas/{encomienda.id}/cambiar_estado/',
            {'estado': 'TR', 'observacion': 'En camino'},
        )
        assert response.status_code == status.HTTP_200_OK
        encomienda.refresh_from_db()
        assert encomienda.estado == 'TR'
        assert HistorialEstado.objects.filter(encomienda=encomienda).count() >= 1

    def test_cambiar_estado_mismo_estado(self, auth_client, encomienda):
        response = auth_client.post(
            f'/api/v1/encomiendas/{encomienda.id}/cambiar_estado/',
            {'estado': 'PE'},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_con_retraso(self, auth_client, encomienda):
        response = auth_client.get('/api/v1/encomiendas/con_retraso/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_pendientes(self, auth_client, encomienda):
        response = auth_client.get('/api/v1/encomiendas/pendientes/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_historial(self, auth_client, encomienda):
        response = auth_client.get(f'/api/v1/encomiendas/{encomienda.id}/historial/')
        assert response.status_code == status.HTTP_200_OK

    def test_estadisticas(self, auth_client, encomienda):
        response = auth_client.get('/api/v1/encomiendas/estadisticas/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_activas' in response.data
        assert 'en_transito' in response.data
        assert 'con_retraso' in response.data

    def test_filtro_por_estado(self, auth_client, encomienda):
        response = auth_client.get('/api/v1/encomiendas/?estado=PE')
        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['estado'] == 'PE'

    def test_busqueda_por_codigo(self, auth_client, encomienda):
        response = auth_client.get(f'/api/v1/encomiendas/?search={encomienda.codigo}')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_ordenar_por_fecha(self, auth_client, encomienda):
        response = auth_client.get('/api/v1/encomiendas/?ordering=fecha_registro')
        assert response.status_code == status.HTTP_200_OK


class TestClientes:
    def test_listar_clientes(self, auth_client, cliente):
        response = auth_client.get('/api/v1/clientes/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


class TestRutas:
    def test_listar_rutas(self, auth_client, ruta):
        response = auth_client.get('/api/v1/rutas/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


class TestVersioning:
    def test_v2_serializer(self, auth_client, encomienda):
        response = auth_client.get('/api/v2/encomiendas/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        if results:
            assert 'meta' in results[0]
            assert results[0]['meta']['version'] == 'v2'

    def test_v3_not_found(self, auth_client):
        response = auth_client.get('/api/v3/encomiendas/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBulk:
    @pytest.mark.skip(reason='Requiere datos complejos')
    def test_bulk_create(self, auth_client):
        response = auth_client.post('/api/v1/encomiendas/bulk_create/', {
            'encomiendas': []
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_bulk_estado(self, auth_client, encomienda, empleado_admin):
        response = auth_client.post('/api/v1/encomiendas/bulk_estado/', {
            'encomienda_ids': [encomienda.id],
            'estado': 'TR',
            'observacion': 'Bulk cambio',
        }, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['success'] is True


class TestDocs:
    @pytest.mark.django_db
    def test_swagger_schema(self, api_client):
        response = api_client.get('/api/v1/schema/')
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_swagger_docs(self, api_client):
        response = api_client.get('/api/v1/docs/')
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_redoc(self, api_client):
        response = api_client.get('/api/v1/redoc/')
        assert response.status_code == status.HTTP_200_OK
