import pytest
from django.contrib.auth.models import User
from django.test import Client as DjangoClient
from django.test.utils import override_settings
from rest_framework.test import APIClient
from envios.models import Empleado, Encomienda
from clientes.models import Cliente
from rutas.models import Ruta
from config.choices import EstadoGeneral


@pytest.fixture(autouse=True)
def _test_settings(settings):
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'anon': '1000/hour',
        'user': '10000/hour',
        'empleado': '1000/hour',
        'cambio_estado': '1000/hour',
        'login_attempt': '1000/min',
    }
    settings.MIDDLEWARE = [m for m in settings.MIDDLEWARE if 'silk' not in m.lower()]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def django_client():
    return DjangoClient()


@pytest.fixture
def user_admin(db):
    return User.objects.create_superuser('admin', 'admin@encomiendas.com', 'admin123')


@pytest.fixture
def user_empleado(db):
    return User.objects.create_user('empleado1', 'empleado1@encomiendas.com', 'pass123')


@pytest.fixture
def empleado(user_empleado, db):
    return Empleado.objects.create(
        codigo='EMP003',
        nombres='Juan',
        apellidos='Perez',
        cargo='Operador',
        email=user_empleado.email,
        telefono='999888777',
        estado=EstadoGeneral.ACTIVO,
        fecha_ingreso='2025-01-01',
    )


@pytest.fixture
def empleado_admin(user_admin, db):
    return Empleado.objects.create(
        codigo='EMP001',
        nombres='Admin',
        apellidos='Principal',
        cargo='Administrador',
        email=user_admin.email,
        telefono='999888000',
        estado=EstadoGeneral.ACTIVO,
        fecha_ingreso='2025-01-01',
    )


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(
        tipo_doc='DNI',
        nro_doc='12345678',
        nombres='Carlos',
        apellidos='Lopez',
        telefono='999111222',
        email='carlos@example.com',
    )


@pytest.fixture
def cliente2(db):
    return Cliente.objects.create(
        tipo_doc='DNI',
        nro_doc='87654321',
        nombres='Maria',
        apellidos='Garcia',
        telefono='999333444',
        email='maria@example.com',
    )


@pytest.fixture
def ruta(db):
    return Ruta.objects.create(
            codigo='LIM-CUS',
        origen='Lima',
        destino='Cusco',
        precio_base=25.00,
        dias_entrega=3,
        estado=EstadoGeneral.ACTIVO,
    )


@pytest.fixture
def encomienda(empleado, cliente, cliente2, ruta, db):
    from datetime import timedelta
    from django.utils import timezone
    import uuid
    codigo = f'ENC-{timezone.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:6].upper()}'
    return Encomienda.objects.create(
        codigo=codigo,
        descripcion='Paquete de prueba',
        peso_kg=2.5,
        remitente=cliente,
        destinatario=cliente2,
        ruta=ruta,
        empleado_registro=empleado,
        costo_envio=25.00,
        fecha_entrega_est=timezone.now().date() + timedelta(days=3),
    )


@pytest.fixture
def token(api_client, empleado_admin):
    response = api_client.post('/api/v1/auth/token/', {
        'username': 'admin', 'password': 'admin123'
    })
    return response.data['access']


@pytest.fixture
def auth_client(api_client, token):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return api_client
