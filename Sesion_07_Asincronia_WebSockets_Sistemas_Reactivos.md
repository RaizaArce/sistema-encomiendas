# Python para Backend — Sesión 7
# Asincronía, WebSockets y Sistemas Reactivos

**Autor:** Javier Villegas  
**Fecha:** 14 de mayo 2026

---

## ¿Qué Construiremos en Esta Sesión?

Al terminar tendremos el sistema de encomiendas con capacidades en tiempo real:

1. **Notificaciones push:** cuando una encomienda cambia de estado, todos los clientes conectados reciben la actualización al instante.
2. **Dashboard live:** los contadores (activas, en tránsito, con retraso) se actualizan automáticamente sin recargar la página.
3. **Progreso de tareas:** el endpoint `bulk_create` reporta el avance de creación masiva en tiempo real.
4. **Feed de actividad:** cualquier empleado conectado ve todos los cambios del sistema en un feed en vivo.

---

## Asincronía y WebSockets

### Programación Síncrona vs Asíncrona

En la programación **síncrona**, cada operación bloquea la ejecución hasta completarse. En la programación **asíncrona**, mientras una operación espera (BD, red, archivo), Python puede atender otras solicitudes. El código síncrono ejecuta instrucciones secuencialmente (una tras otra), bloqueando el flujo hasta finalizar, mientras que el asíncrono permite iniciar tareas independientes sin esperar a que terminen, mejorando la eficiencia y evitando bloqueos.

La programación asíncrona es un paradigma que permite una mejor concurrencia. En Python, el módulo `asyncio` ofrece esta capacidad. Varias tareas pueden ejecutarse simultáneamente en un único subproceso, programado en un único núcleo de la CPU.

Aunque Python admite el multithreading, la concurrencia está limitada por el **Global Interpreter Lock (GIL)**. El GIL garantiza que solo un hilo pueda adquirir el bloqueo a la vez. La programación asíncrona no resuelve la limitación del GIL, pero permite una mejor concurrencia.

Con el **multiprocesamiento**, la programación de tareas la realiza el sistema operativo. Con el **multihilo**, el intérprete de Python se encarga de la programación. En la programación asíncrona, la programación la realiza el **bucle de eventos** (*event loop*). Los desarrolladores pueden especificar cuándo una tarea cede voluntariamente la CPU para que el bucle de eventos pueda programar otra tarea. Por esta razón, también se denomina **multitarea cooperativa**.

---

### El Event Loop — el motor de la asincronía

El event loop es un bucle que monitorea qué corrutinas están listas para ejecutarse. Cuando una corrutina llega a un `await`, cede el control al event loop. El event loop ejecuta otra corrutina disponible y vuelve a la primera cuando su operación de I/O ha terminado.

```python
# Total tiempo síncrono:  A + B + C = 300ms + 300ms + 300ms = 900ms
# Total tiempo asíncrono: max(A,B,C) = 300ms

import asyncio

async def consultar_encomiendas():
    # await le dice al event loop: 'pausa aquí y atiende a otros'
    await asyncio.sleep(0.3)   # simula la query a la BD
    return 'encomiendas ok'

async def consultar_clientes():
    await asyncio.sleep(0.3)
    return 'clientes ok'

async def consultar_rutas():
    await asyncio.sleep(0.3)
    return 'rutas ok'

async def main():
    # gather las lanza TODAS A LA VEZ y espera que terminen
    enc, cli, rut = await asyncio.gather(
        consultar_encomiendas(),
        consultar_clientes(),
        consultar_rutas(),
    )
    print(enc, cli, rut)

asyncio.run(main())   # crea el event loop, ejecuta main, lo cierra
```

---

### Corrutinas — funciones que pueden pausarse

Una **corrutina** es una función declarada con `async def`. A diferencia de una función normal, una corrutina puede suspenderse en puntos específicos (marcados con `await`) y retomar la ejecución exactamente donde se dejó.

#### Diferencia fundamental

```python
# ── Función normal ────────────────────────────────────────────────
def obtener_encomienda_sync(codigo: str):
    import time
    time.sleep(0.5)  # BLOQUEA: nadie más puede ejecutarse
    return Encomienda.objects.get(codigo=codigo)

# El hilo está BLOQUEADO 500ms. Nada más puede ejecutarse.


# ── Corrutina ──────────────────────────────────────────────────────
async def obtener_encomienda_async(codigo: str):
    # await: el event loop puede atender otros requests mientras espera
    enc = await Encomienda.objects.aget(codigo=codigo)
    return enc

# Llamada (solo funciona desde dentro de una función async):
enc = await obtener_encomienda_async('ENC-2026-001')
# El event loop CEDE el control mientras espera la BD.
# Otros requests pueden procesarse durante ese tiempo.


# ── Llamar una corrutina desde código síncrono ───────────────────
import asyncio
enc = asyncio.run(obtener_encomienda_async('ENC-2026-001'))
# asyncio.run() crea un event loop temporal, ejecuta la corrutina y lo cierra
```

#### Corrutina completa del proyecto

```python
# envios/async_services.py (nuevo archivo para servicios async)
import asyncio
import httpx
from django.utils import timezone

async def verificar_estado_transportista(codigo: str) -> dict:
    """
    Corrutina que consulta la API del transportista.
    Puede pausarse mientras espera la respuesta HTTP.
    """
    url = f'https://api.transportista.pe/v1/track/{codigo}'
    try:
        async with httpx.AsyncClient() as client:
            # await: se pausa aquí. El event loop atiende otros requests.
            response = await client.get(url, timeout=5.0)
            data = response.json()
            return {
                'codigo':     codigo,
                'encontrado': True,
                'estado_ext': data.get('status'),
                'ubicacion':  data.get('location'),
                'timestamp':  timezone.now().isoformat(),
            }
    except httpx.TimeoutException:
        return {'codigo': codigo, 'encontrado': False, 'error': 'timeout'}
    except httpx.ConnectError:
        return {'codigo': codigo, 'encontrado': False, 'error': 'conexion'}


async def actualizar_estados_en_transito() -> list:
    """
    Actualiza el estado de todas las encomiendas en tránsito
    consultando la API del transportista en paralelo.
    """
    # 1. Obtener encomiendas en tránsito (query async)
    encomiendas = await Encomienda.objects.en_transito().alist()

    if not encomiendas:
        return []

    # 2. Consultar el transportista para TODAS en paralelo
    #    Sin async: 50 enc * 1s = 50 segundos
    #    Con async: ~1 segundo (todas en paralelo)
    resultados = await asyncio.gather(
        *[verificar_estado_transportista(enc.codigo) for enc in encomiendas],
        return_exceptions=True
    )

    # 3. Procesar los resultados
    actualizadas = []
    for enc, resultado in zip(encomiendas, resultados):
        if isinstance(resultado, Exception):
            continue   # ignorar errores individuales
        if resultado.get('encontrado') and resultado.get('estado_ext') == 'DELIVERED':
            enc.estado = 'EN'
            enc.fecha_entrega_real = timezone.now().date()
            await enc.asave()  # guardar async
            actualizadas.append(enc.codigo)

    return actualizadas
```

---

### `await` — el punto de suspensión

La palabra clave `await` tiene dos efectos: suspende la corrutina actual y devuelve el control al event loop, y extrae el resultado de la corrutina cuando termina. Solo puede aparecer dentro de una función declarada con `async def`.

```python
# await puede usarse con:

# 1. Otras corrutinas
enc = await obtener_encomienda_async('ENC-001')

# 2. Métodos ORM async de Django 4.1+
enc   = await Encomienda.objects.aget(pk=1)
count = await Encomienda.objects.activas().acount()
await enc.asave()

# 3. Clientes HTTP async (httpx)
response = await client.get('https://api.transportista.pe/track/ENC-001')

# 4. asyncio.sleep (sin bloquear)
await asyncio.sleep(5)   # espera 5s sin bloquear el event loop

# 5. asyncio.gather (múltiples corrutinas en paralelo)
a, b, c = await asyncio.gather(f1(), f2(), f3())

# 6. asyncio.wait_for (con timeout)
resultado = await asyncio.wait_for(mi_corrutina(), timeout=3.0)

# ── Lo que NO se puede await ─────────────────────────────────────
# await time.sleep(1)              # ERROR: time.sleep no es awaitable
# await Encomienda.objects.all()   # ERROR: no es awaitable
# await enc.cambiar_estado('TR', emp)  # ERROR si no tiene async def
```

---

### `asyncio.gather` — paralelismo en el proyecto

La función `asyncio.gather()` toma múltiples corrutinas y las ejecuta todas a la vez. El resultado es una lista con los resultados en el mismo orden de los argumentos. Es el equivalente async de hacer varias queries a la BD simultáneamente.

#### Lab 1: Dashboard con 4 queries en paralelo

```python
# envios/views_async.py (nuevo archivo)
import asyncio
from django.http import JsonResponse
from django.utils import timezone
from .models import Encomienda

async def dashboard_stats_async(request):
    """
    Endpoint async que calcula las estadísticas del dashboard.
    ANTES (síncrono): 4 queries secuenciales = 4 * 10ms = 40ms
    AHORA (async):    4 queries en paralelo  = max(10ms) = 10ms
    """
    if not request.user.is_authenticated:
        from django.http import HttpResponse
        return HttpResponse(status=401)

    hoy = timezone.now().date()

    # Las 4 queries corren EN PARALELO
    activas, en_transito, con_retraso, entregadas_hoy = await asyncio.gather(
        Encomienda.objects.activas().acount(),
        Encomienda.objects.en_transito().acount(),
        Encomienda.objects.con_retraso().acount(),
        Encomienda.objects.filter(
            estado='EN', fecha_entrega_real=hoy
        ).acount(),
    )

    return JsonResponse({
        'activas':        activas,
        'en_transito':    en_transito,
        'con_retraso':    con_retraso,
        'entregadas_hoy': entregadas_hoy,
    })
```

#### Caso complejo: verificar 50 encomiendas en la API del transportista

```python
# envios/async_services.py
import asyncio
import httpx
from .models import Encomienda

async def verificar_una(session: httpx.AsyncClient, codigo: str) -> dict:
    """Verifica UNA encomienda. Se ejecuta en paralelo con las demás."""
    try:
        r = await session.get(
            f'https://api.transportista.pe/track/{codigo}',
            timeout=5.0
        )
        return {'codigo': codigo, 'ok': True, 'data': r.json()}
    except httpx.TimeoutException:
        return {'codigo': codigo, 'ok': False, 'error': 'timeout'}
    except Exception as e:
        return {'codigo': codigo, 'ok': False, 'error': str(e)}


async def verificar_lote_completo() -> dict:
    """
    Verifica TODAS las encomiendas en tránsito en paralelo.

    SÍNCRONO:  50 encomiendas * 1s por consulta = 50 SEGUNDOS
    ASÍNCRONO: todas en paralelo                = ~1 SEGUNDO
    """
    # 1. Obtener encomiendas en tránsito de la BD
    encomiendas = await Encomienda.objects.en_transito().alist()

    if not encomiendas:
        return {'verificadas': 0, 'resultados': []}

    print(f'Verificando {len(encomiendas)} encomiendas en paralelo...')

    # 2. Abrir una sesión HTTP compartida para todas las consultas
    async with httpx.AsyncClient() as session:
        # 3. Lanzar TODAS las consultas a la vez
        tareas = [
            verificar_una(session, enc.codigo)
            for enc in encomiendas
        ]
        # gather: las ejecuta en paralelo y espera a que todas terminen
        resultados = await asyncio.gather(*tareas, return_exceptions=True)

    # 4. Separar exitosas de fallidas
    exitosas = [r for r in resultados if isinstance(r, dict) and r['ok']]
    fallidas  = [r for r in resultados if isinstance(r, dict) and not r['ok']]
    errores   = [r for r in resultados if isinstance(r, Exception)]

    return {
        'verificadas': len(encomiendas),
        'exitosas':    len(exitosas),
        'fallidas':    len(fallidas),
        'errores':     len(errores),
        'resultados':  resultados,
    }

# Llamar desde un comando de management:
# import asyncio
# from envios.async_services import verificar_lote_completo
# asyncio.run(verificar_lote_completo())
```

---

### `asyncio.create_task` — lanzar en segundo plano

A diferencia de `await` que espera a que una corrutina termine, `asyncio.create_task()` la lanza en segundo plano y continúa la ejecución inmediatamente. Ideal para notificaciones y operaciones no críticas.

```python
import asyncio

async def enviar_notificacion_email(enc, nuevo_estado: str):
    """Envía un email de notificación. Puede tardar 500ms."""
    await asyncio.sleep(0.5)
    print(f'Email enviado: {enc.codigo} -> {nuevo_estado}')


async def registrar_en_log_externo(enc, estado: str):
    """Registra el cambio en un sistema de logs externo."""
    import httpx
    async with httpx.AsyncClient() as client:
        await client.post(
            'https://logs.empresa.pe/api/encomiendas',
            json={'codigo': enc.codigo, 'estado': estado},
            timeout=3.0
        )


async def cambiar_estado_vista(request, pk: int):
    """
    Vista async que cambia el estado y lanza las notificaciones
    en background sin hacer esperar al cliente.
    """
    enc         = await Encomienda.objects.aget(pk=pk)
    nuevo_estado = request.data.get('estado')

    # Paso 1: cambiar el estado (CRÍTICO - el cliente espera esto)
    enc.estado = nuevo_estado
    await enc.asave()

    # Paso 2: lanzar notificaciones en BACKGROUND (no críticas)
    asyncio.create_task(enviar_notificacion_email(enc, nuevo_estado))
    asyncio.create_task(registrar_en_log_externo(enc, nuevo_estado))

    return {'ok': True, 'estado': nuevo_estado}

# CON await:       espera a que el email termine antes de responder (+500ms de latencia)
# CON create_task: responde al cliente y el email se envía después (+0ms)
```

---

### `asyncio.wait_for` — timeout en operaciones async

La función `asyncio.wait_for()` ejecuta una corrutina con un tiempo límite. Si la corrutina no termina en ese tiempo, lanza `asyncio.TimeoutError`. Fundamental cuando se llama a APIs externas que pueden tardar demasiado.

```python
import asyncio
import httpx
from .models import Encomienda

async def verificar_con_timeout(enc) -> dict:
    """
    Verifica una encomienda en la API del transportista.
    Si no responde en 3 segundos, devuelve el último estado conocido.
    """
    try:
        # Máximo 3 segundos para la API externa
        resultado = await asyncio.wait_for(
            verificar_api_externa(enc.codigo),
            timeout=3.0
        )
        return resultado
    except asyncio.TimeoutError:
        return {
            'codigo':     enc.codigo,
            'estado':     enc.get_estado_display(),
            'fuente':     'cache_local',
            'advertencia': 'API del transportista no disponible',
        }


async def verificar_lote_con_timeout(codigos: list) -> list:
    encomiendas = await Encomienda.objects.filter(codigo__in=codigos).alist()

    resultados = await asyncio.gather(
        *[verificar_con_timeout(enc) for enc in encomiendas],
        return_exceptions=True
    )

    return [
        r if not isinstance(r, Exception) else {'error': str(r)}
        for r in resultados
    ]
```

---

### ORM Asíncrono de Django en el Proyecto

Desde Django 4.1, el ORM tiene equivalentes asíncronos de los métodos más usados. El prefijo `a` identifica la versión async.

| Método síncrono | Método asíncrono | Ejemplo en el proyecto |
|---|---|---|
| `Model.objects.get()` | `await Model.objects.aget()` | `await Encomienda.objects.aget(pk=1)` |
| `Model.objects.create()` | `await Model.objects.acreate()` | `await Encomienda.objects.acreate(...)` |
| `queryset.first()` | `await qs.afirst()` | `await Encomienda.objects.activas().afirst()` |
| `queryset.count()` | `await queryset.acount()` | `await Encomienda.objects.con_retraso().acount()` |
| `queryset.exists()` | `await queryset.aexists()` | `await Encomienda.objects.filter(codigo=c).aexists()` |
| `obj.save()` | `await obj.asave()` | `enc.estado = 'TR'; await enc.asave()` |
| `obj.delete()` | `await obj.adelete()` | `await enc.adelete()` |
| `list(queryset)` | `await queryset.alist()` | `await Encomienda.objects.en_transito().alist()` |
| `for obj in queryset:` | `async for obj in queryset:` | `async for enc in Encomienda.objects.all():` |

#### Iteración async y `sync_to_async`

```python
# ── async for: iterar un queryset sin bloquear el event loop ────────
async def procesar_encomiendas_en_transito():
    encomiendas_retrasadas = []

    async for enc in Encomienda.objects.en_transito().select_related('ruta'):
        if enc.tiene_retraso:   # @property del modelo
            encomiendas_retrasadas.append(enc)

    if encomiendas_retrasadas:
        await asyncio.gather(
            *[notificar_retraso(enc) for enc in encomiendas_retrasadas]
        )

    return len(encomiendas_retrasadas)


# ── sync_to_async: si Django < 4.1 o el ORM no tiene método async ──
from asgiref.sync import sync_to_async

@sync_to_async
def get_encomiendas_activas():
    return list(Encomienda.objects.activas().con_relaciones())

# Uso:
encomiendas = await get_encomiendas_activas()

# Alternativa en línea:
encomiendas = await sync_to_async(
    lambda: list(Encomienda.objects.activas().con_relaciones())
)()
```

---

### Errores Comunes y Cómo Evitarlos

| Error | Causa | Solución |
|---|---|---|
| `SyntaxError: await outside async` | Usar `await` en función sin `async def` | Declarar la función con `async def` |
| `RuntimeError: Event loop is closed` | Llamar `asyncio.run()` dentro de una corrutina | Usar `await` directamente, no `asyncio.run()` |
| `SynchronousOnlyOperation` | Llamar ORM sync desde contexto async | Usar `aget()`, `acount()` o `sync_to_async` |
| Task fue destruida pero está pendiente | `create_task()` sin guardar la referencia | `task = asyncio.create_task(...)` y guardarla |
| La corrutina nunca se ejecutó | Llamar una corrutina sin `await` ni `create_task` | Siempre `await` o `create_task` una corrutina |

```python
# ── Error 1: ORM síncrono en contexto async ─────────────────────
async def vista_mal(request):
    encs = list(Encomienda.objects.all())  # SynchronousOnlyOperation

async def vista_bien(request):
    encs = await Encomienda.objects.alist()  # correcto


# ── Error 2: await en función síncrona ───────────────────────────
def funcion_sync():
    enc = await Encomienda.objects.aget(pk=1)  # SyntaxError

async def funcion_async():
    enc = await Encomienda.objects.aget(pk=1)  # correcto


# ── Error 3: asyncio.run() dentro de una corrutina ───────────────
async def vista(request):
    enc = asyncio.run(obtener_encomienda(1))  # RuntimeError

async def vista_correcta(request):
    enc = await obtener_encomienda(1)  # correcto


# ── Error 4: corrutina sin await ─────────────────────────────────
async def vista(request):
    enc = Encomienda.objects.aget(pk=1)  # devuelve corrutina, no objeto
    print(enc)  # <coroutine object aget at 0x...>

async def vista_correcta(request):
    enc = await Encomienda.objects.aget(pk=1)  # objeto real
    print(enc)  # ENC-2026-001 [Pendiente]


# ── Error 5: Task destruida antes de terminar ────────────────────
async def vista_mal(request):
    asyncio.create_task(enviar_email(enc))  # tarea puede cancelarse

_tasks = set()
async def vista_bien(request):
    task = asyncio.create_task(enviar_email(enc))
    _tasks.add(task)                   # evitar que el GC la destruya
    task.add_done_callback(_tasks.discard)  # limpiar al terminar
```

---

### Resumen — Guía Rápida de Async/Await en el Proyecto

```
Declarar una corrutina:          async def mi_funcion():
Esperar una corrutina:           resultado = await mi_corrutina()
Ejecutar varias en paralelo:     a, b = await asyncio.gather(f1(), f2())
Lanzar en background:            asyncio.create_task(mi_corrutina())
Con timeout:                     await asyncio.wait_for(f(), timeout=3.0)
Desde código síncrono:           asyncio.run(mi_corrutina())
ORM async:                       await Encomienda.objects.aget(pk=1)
ORM async count:                 await Encomienda.objects.activas().acount()
ORM async guardar:               enc.estado = 'TR'; await enc.asave()
ORM async iterar:                async for enc in Encomienda.objects.all():
Convertir sync a async:          @sync_to_async / sync_to_async(lambda: ...)()
```

**Archivos nuevos en el proyecto:**
- `envios/async_services.py` → `verificar_lote_completo`, `verificar_con_timeout`
- `envios/views_async.py` → `dashboard_stats_async`, `cambiar_estado_vista`

---

## Introducción a WebSockets

WebSocket es un protocolo de comunicación que permite una conexión **bidireccional, persistente y en tiempo real** entre un navegador (cliente) y un servidor. A diferencia de HTTP, que requiere una petición por cada respuesta, WebSocket mantiene la conexión abierta, permitiendo el intercambio instantáneo de datos.

**Aspectos clave:**
- **Comunicación Bidireccional:** Tanto el cliente como el servidor pueden enviarse mensajes en cualquier momento.
- **Tiempo Real:** Ideal para chats, juegos online o marcadores deportivos.
- **Conexión Persistente:** Se establece un "handshake" inicial y la conexión permanece abierta (full-duplex).
- **Eficiencia:** Reduce la latencia y la sobrecarga de datos en comparación con HTTP.
- **Compatibilidad:** Funciona sobre los puertos estándar 80 y 443.

### La analogía: teléfono vs walkie-talkie

| HTTP (cartas) | WebSocket (teléfono) |
|---|---|
| El cliente escribe y envía una carta (request) | Ambos marcan el número y establecen la llamada |
| El servidor lee y responde con otra carta | Cualquiera puede hablar en cualquier momento |
| La carta llega y la comunicación termina | La línea se mantiene abierta mientras dure la sesión |
| Para saber si hay respuesta, hay que preguntar de nuevo | El servidor puede hablar sin que el cliente lo solicite |
| Cada carta tiene su propio sobre con dirección (headers) | Solo un «over» al inicio para abrir la línea (handshake) |

---

### El problema: HTTP polling vs WebSocket push

#### El problema del polling con HTTP

```python
# Lo que pasa con polling HTTP en el sistema de encomiendas:
#
# 10:00:00 - Navegador pregunta: GET /api/v1/encomiendas/1/ -> PE (Pendiente)
# 10:00:05 - Navegador pregunta: GET /api/v1/encomiendas/1/ -> PE (sin cambio)
# 10:00:10 - Navegador pregunta: GET /api/v1/encomiendas/1/ -> PE (sin cambio)
# 10:00:15 - Navegador pregunta: GET /api/v1/encomiendas/1/ -> PE (sin cambio)
# 10:00:18 - Luis cambia el estado a TR en el sistema
# 10:00:20 - Navegador pregunta: GET /api/v1/encomiendas/1/ -> TR (!)
#
# Problemas del polling:
# 1. Demora de hasta 5 segundos para enterarse del cambio
# 2. Con 50 empleados conectados: 50 requests cada 5s = 600 req/min
# 3. La mayoría de esos 600 requests devuelven 'sin cambio' (desperdicio)
# 4. El servidor procesa carga aunque no haya nada que reportar

# Implementación típica del polling (JavaScript):
setInterval(async () => {
    const r = await fetch('/api/v1/encomiendas/1/');
    const data = await r.json();
    if (data.estado !== estadoAnterior) {
        actualizarUI(data.estado);
        estadoAnterior = data.estado;
    }
}, 5000); // cada 5 segundos

# Con WebSocket: 0 requests hasta que algo cambia
```

#### La solución con WebSocket push

```python
# Lo que ocurre con WebSocket en el sistema de encomiendas:
#
# 10:00:00 - Empleado abre el navegador
# 10:00:00 - Navegador abre UN WebSocket: ws://localhost/ws/encomiendas/
# 10:00:00 - Servidor acepta la conexión (101 Switching Protocols)
# 10:00:00 - Servidor envía las estadísticas iniciales
#
# ... la conexión está ABIERTA, no se consume red ...
#
# 10:00:18 - Luis cambia ENC-2026-001 de PE a TR
# 10:00:18 - El modelo llama a channel_layer.group_send()
# 10:00:18 - TODOS los navegadores conectados reciben instantáneamente:
#            {tipo: 'estado_cambio', codigo: 'ENC-2026-001',
#             estado_anterior: 'PE', estado_nuevo: 'TR',
#             empleado: 'Mendoza Cruz, Luis'}
#
# Ventajas:
# 1. Notificación en <100ms
# 2. 0 requests adicionales hasta el próximo cambio
# 3. El servidor solo envía cuando hay algo que enviar
# 4. Escala a miles de conexiones con poco CPU
```

---

### El ciclo de vida de una conexión WebSocket

#### Fase 1: El Handshake

```
# ── PASO 1: El cliente envía una petición HTTP con cabeceras especiales ──
GET /ws/encomiendas/ HTTP/1.1
Host: localhost:8000
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: http://localhost:8000

# ── PASO 2: El servidor acepta y responde 101 ────────────────────────────
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

# ── PASO 3: Django Channels llama a connect() del consumidor ─────────────
class EncomiendaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add('encomiendas_global', self.channel_name)
        await self.accept()

        stats = await self.get_estadisticas()
        await self.send(text_data=json.dumps({
            'tipo':    'conectado',
            'mensaje': f'Bienvenido, {user.username}',
            'stats':   stats,
        }))
```

#### Fase 2: Comunicación bidireccional

```python
# ── Mensajes del cliente al servidor (receive) ───────────────────
ws.send(JSON.stringify({tipo: 'ping'}))

# El servidor responde en receive():
async def receive(self, text_data):
    data = json.loads(text_data)
    if data['tipo'] == 'ping':
        await self.send(text_data=json.dumps({'tipo': 'pong'}))


# ── Mensajes del servidor al cliente (push) ──────────────────────
async def encomienda_estado_cambio(self, event):
    """Handler: recibe del channel layer y reenvía al navegador"""
    await self.send(text_data=json.dumps({
        'tipo':             'estado_cambio',
        'encomienda_id':    event['encomienda_id'],
        'codigo':           event['codigo'],
        'estado_anterior':  event['estado_anterior'],
        'estado_nuevo':     event['estado_nuevo'],
        'empleado':         event['empleado'],
        'timestamp':        event['timestamp'],
    }))

# El navegador recibe el mensaje en onmessage:
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.tipo === 'estado_cambio') {
        mostrarToast(data.codigo, data.estado_anterior, data.estado_nuevo);
    }
}
```

#### Fase 3: El cierre ordenado

```python
# ── Cierre desde el cliente (JavaScript) ─────────────────────────
ws.close(1000, 'Usuario cerró la pestaña');

# El servidor recibe el cierre en disconnect():
async def disconnect(self, close_code):
    await self.channel_layer.group_discard(
        'encomiendas_global',
        self.channel_name
    )


# ── Cierre desde el servidor ──────────────────────────────────────
await self.close(code=4001)  # código personalizado: no autorizado

# El cliente recibe el cierre en onclose:
ws.onclose = function(event) {
    console.log(`Cerrado. Código: ${event.code}`);
    if (event.code === 4001) {
        window.location.href = '/accounts/login/';
    } else if (event.code !== 1000) {
        setTimeout(() => location.reload(), 3000);
    }
};
```

---

### Frames WebSocket — cómo viajan los mensajes

| Tipo de frame | Uso en el proyecto |
|---|---|
| Text frame (0x1) | Mensajes JSON del sistema (estado_cambio, stats, ping/pong) |
| Binary frame (0x2) | No usado en el proyecto |
| Close frame (0x8) | Cierre de conexión con código y razón |
| Ping frame (0x9) | Django Channels envía pings automáticos para mantener la conexión |
| Pong frame (0xA) | El cliente responde automáticamente a los pings del servidor |

```python
# Ejemplo: mensaje JSON '{"tipo":"ping"}' (13 caracteres)
# Overhead HTTP:  ~400-600 bytes de cabeceras
# Overhead WS:    2-6 bytes
# El frame WS es 100x más eficiente para mensajes cortos frecuentes
```

---

### La API JavaScript del WebSocket

#### Los 4 eventos del WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/encomiendas/');
// wss:// para HTTPS/SSL (siempre en producción)

// ── onopen: conexión establecida ─────────────────────────────────
ws.onopen = function(event) {
    console.log('¡Conectado!');
    document.getElementById('ws-badge').textContent = 'EN VIVO';
    document.getElementById('ws-badge').classList.add('text-success');
    ws.send(JSON.stringify({ tipo: 'solicitar_stats' }));
};

// ── onmessage: mensaje recibido del servidor ──────────────────────
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    switch(data.tipo) {
        case 'conectado':
            actualizarDashboard(data.stats);
            break;
        case 'estado_cambio':
            mostrarNotificacion(data.codigo, data.estado_anterior, data.estado_nuevo, data.empleado, data.timestamp);
            actualizarFilaTabla(data.codigo, data.estado_nuevo);
            break;
        case 'stats_actualizado':
            actualizarDashboard(data.stats);
            break;
        case 'progreso':
            const pct = Math.round(data.actual / data.total * 100);
            actualizarBarra(pct, data.codigo);
            break;
    }
};

// ── onclose: conexión cerrada ─────────────────────────────────────
ws.onclose = function(event) {
    document.getElementById('ws-badge').textContent = 'Desconectado';
    document.getElementById('ws-badge').classList.remove('text-success');

    if (event.code === 4001) {
        window.location.href = '/accounts/login/';
    } else if (event.code !== 1000 && event.code !== 1001) {
        console.log('Reconectando...');
        setTimeout(() => {
            const nuevoWs = new WebSocket(ws.url);
        }, 3000);
    }
};

// ── onerror: error de red ─────────────────────────────────────────
ws.onerror = function(error) {
    console.error('Error WebSocket:', error);
};
```

#### Códigos de cierre

| Código | Nombre | Cuándo ocurre |
|---|---|---|
| 1000 | Normal closure | El empleado cerró sesión voluntariamente |
| 1001 | Going away | El empleado cerró la pestaña |
| 1006 | Abnormal closure | Perdió la conexión a internet |
| 1011 | Internal error | Error no controlado en un consumer de Channels |
| 4001 | No autorizado | El usuario no está autenticado (código personalizado) |
| 4002 | Sesión expirada | El token JWT expiró (código personalizado) |

---

### Resumen — Conceptos Clave de WebSockets

```
Qué es: protocolo de comunicación bidireccional y persistente sobre TCP.

Diferencia con HTTP:
  HTTP:      el cliente pregunta, el servidor responde, la conexión se cierra.
  WebSocket: la conexión queda abierta, cualquiera puede enviar mensajes.

El handshake:
  1. Cliente envía GET con Upgrade: websocket
  2. Servidor responde 101 Switching Protocols
  3. La conexión TCP ya no habla HTTP, habla WebSocket frames
  4. Django Channels llama a connect() del consumer

Los 4 eventos del cliente JavaScript:
  onopen:    la conexión se estableció correctamente
  onmessage: llegó un mensaje del servidor (event.data = JSON string)
  onclose:   la conexión se cerró (event.code indica el motivo)
  onerror:   error de red (seguido siempre de onclose)

En el proyecto de encomiendas:
  ws://localhost:8000/ws/encomiendas/       <- notificaciones globales
  ws://localhost:8000/ws/encomiendas/{pk}/  <- una encomienda específica
  ws://localhost:8000/ws/dashboard/         <- estadísticas en tiempo real
```

---

## Ejemplo Completo: Dashboard en Tiempo Real

### Paso 1 — Template del dashboard (HTML + JavaScript)

```html
{% extends 'base.html' %}

{% block content %}
<!-- Indicador de conexión en el navbar -->
<div class="d-flex justify-content-between align-items-center mb-4">
  <h2>Dashboard</h2>
  <span id="ws-badge" class="badge bg-secondary">Conectando...</span>
</div>

<!-- Tarjetas de estadísticas -->
<div class="row g-3 mb-4">
  <div class="col-md-3">
    <div class="card shadow-sm">
      <div class="card-body text-center">
        <div class="fs-1">📦</div>
        <div class="fs-2 fw-bold text-primary" id="stat-activas">{{ stats.activas }}</div>
        <div class="text-muted">Activas</div>
      </div>
    </div>
  </div>
  <!-- ... más tarjetas ... -->
</div>

<!-- Feed de actividad en tiempo real -->
<div class="card shadow-sm">
  <div class="card-header d-flex justify-content-between">
    <span>Feed de actividad</span>
    <small class="text-muted" id="feed-count">0 eventos</small>
  </div>
  <ul class="list-group list-group-flush" id="feed-lista">
    <li class="list-group-item text-muted">Esperando eventos...</li>
  </ul>
</div>
{% endblock %}
```

```javascript
{% block extra_js %}
<script>
const WS_URL = 'ws://' + window.location.host + '/ws/dashboard/';
let ws;
let eventoCount = 0;

const ESTADOS = {
  PE: 'Pendiente', TR: 'En tránsito',
  DE: 'En destino', EN: 'Entregado', DV: 'Devuelto'
};

function conectarWebSocket() {
  ws = new WebSocket(WS_URL);

  ws.onopen = function() {
    const badge = document.getElementById('ws-badge');
    badge.textContent = 'EN VIVO';
    badge.className = 'badge bg-success';
  };

  ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.tipo === 'stats_iniciales' || data.tipo === 'stats_actualizado') {
      actualizarContador('stat-activas',     data.stats.activas);
      actualizarContador('stat-en-transito', data.stats.en_transito);
      actualizarContador('stat-retraso',     data.stats.con_retraso);
      actualizarContador('stat-entregadas',  data.stats.entregadas_hoy);
    }

    if (data.tipo === 'estado_cambio') {
      agregarAlFeed(data);
      mostrarToast(data);
    }
  };

  ws.onclose = function(event) {
    const badge = document.getElementById('ws-badge');
    badge.textContent = 'Desconectado';
    badge.className = 'badge bg-danger';
    if (event.code !== 1000) {
      setTimeout(conectarWebSocket, 3000);
    }
  };
}

function actualizarContador(id, nuevoValor) {
  const el = document.getElementById(id);
  if (!el || parseInt(el.textContent) === nuevoValor) return;
  el.style.transition = 'transform 0.2s';
  el.style.transform = 'scale(1.4)';
  el.textContent = nuevoValor;
  setTimeout(() => { el.style.transform = 'scale(1)'; }, 250);
}

document.addEventListener('DOMContentLoaded', conectarWebSocket);
</script>
{% endblock %}
```

### Paso 2 — Vista del dashboard

```python
# envios/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import Encomienda

@login_required
def dashboard(request):
    hoy = timezone.now().date()
    context = {
        'stats': {
            'activas':        Encomienda.objects.activas().count(),
            'en_transito':    Encomienda.objects.en_transito().count(),
            'con_retraso':    Encomienda.objects.con_retraso().count(),
            'entregadas_hoy': Encomienda.objects.filter(
                estado='EN', fecha_entrega_real=hoy
            ).count(),
        }
    }
    return render(request, 'envios/dashboard.html', context)
```

### Paso 3 — Consumer del dashboard

```python
# envios/consumers.py
class DashboardConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = 'dashboard'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        stats = await self.get_stats()
        await self.send(text_data=json.dumps({
            'tipo': 'stats_iniciales',
            'stats': stats,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def dashboard_actualizar(self, event):
        """Recibe del channel layer y reenvía al navegador"""
        await self.send(text_data=json.dumps({
            'tipo': 'stats_actualizado',
            'stats': event['stats'],
        }))

    @database_sync_to_async
    def get_stats(self):
        from .models import Encomienda
        from django.utils import timezone
        hoy = timezone.now().date()
        return {
            'activas':        Encomienda.objects.activas().count(),
            'en_transito':    Encomienda.objects.en_transito().count(),
            'con_retraso':    Encomienda.objects.con_retraso().count(),
            'entregadas_hoy': Encomienda.objects.filter(
                estado='EN', fecha_entrega_real=hoy
            ).count(),
        }
```

### Paso 4 — El modelo notifica al cambiar el estado

```python
# envios/models.py
def _notificar_cambio_estado(self, estado_anterior, estado_nuevo, empleado):
    from django.utils import timezone
    channel_layer = get_channel_layer()

    mensaje = {
        'encomienda_id':  self.pk,
        'codigo':         self.codigo,
        'estado_anterior': estado_anterior,
        'estado_nuevo':   estado_nuevo,
        'empleado':       str(empleado),
        'timestamp':      timezone.now().isoformat(),
    }

    # Notificar al grupo global
    async_to_sync(channel_layer.group_send)(
        'encomiendas_global',
        {'type': 'encomienda_estado_cambio', **mensaje}
    )

    # Notificar al dashboard con estadísticas actualizadas
    stats = {
        'activas':     Encomienda.objects.activas().count(),
        'en_transito': Encomienda.objects.en_transito().count(),
        'con_retraso': Encomienda.objects.con_retraso().count(),
    }
    async_to_sync(channel_layer.group_send)(
        'dashboard',
        {'type': 'dashboard_actualizar', 'stats': stats}
    )
```

### Paso 5 — URLs

```python
# envios/urls.py
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
```

### Resumen del flujo completo

```python
# El flujo completo cuando un empleado cambia un estado:
#
# 1. Empleado usa la API REST: POST /api/v1/encomiendas/1/cambiar_estado/
# 2. El ViewSet llama a enc.cambiar_estado('TR', empleado, obs)
# 3. El modelo guarda en BD y registra en HistorialEstado
# 4. El modelo llama a _notificar_cambio_estado():
#    channel_layer.group_send('encomiendas_global', {...})
#    channel_layer.group_send('dashboard', {stats: {...}})
# 5. Django Channels distribuye a todos los consumers conectados
# 6. Cada consumer envía el mensaje a su WebSocket
# 7. El navegador recibe en onmessage y actualiza la UI
#
# Todo esto ocurre en < 100ms sin ninguna recarga de página.
```

---

## Django Channels

Django Channels es un proyecto oficial que amplía las capacidades de Django para manejar protocolos asíncronos y de larga duración, como WebSockets, MQTT y otros protocolos de mensajería.

**Qué cubre este documento:**
1. Arquitectura de Django Channels: ASGI, channel layer, grupos, consumers
2. Tipos de consumer: `AsyncWebsocketConsumer`, `JsonWebsocketConsumer`, `HttpConsumer`
3. El channel layer: grupos, mensajes, broadcast y escalado con Redis
4. Autenticación y permisos en WebSockets
5. Routing: cómo Django Channels enruta conexiones WebSocket
6. Middleware propio para Channels
7. Testing de consumers con `WebsocketCommunicator`
8. Manejo de errores y reconexión automática
9. Monitoreo y debugging en producción

### Arquitectura de Django Channels

Django Channels extiende Django añadiendo una capa asíncrona sobre ASGI. Introduce tres conceptos nuevos: **consumers** (equivalente de las vistas), el **channel layer** (bus de mensajes entre consumers), y los **grupos** (conjuntos de consumers que reciben el mismo mensaje).

#### Conceptos clave

| Concepto | Equivalente en Django | Descripción en el proyecto |
|---|---|---|
| Consumer | Vista (View) | Clase que maneja una conexión WebSocket: connect, receive, disconnect |
| Channel | Hilo de ejecución | Canal único de comunicación de una conexión. Cada cliente tiene uno |
| Group | Sala / canal público | Conjunto de channels. `'encomiendas_global'` incluye a todos los empleados |
| Channel Layer | Base de datos | Bus de mensajes (Redis) que conecta consumers de distintos servidores |
| Scope | Request object | Diccionario con información de la conexión: usuario, URL, headers |
| ASGI | WSGI | Protocolo asíncrono que reemplaza a WSGI para soportar WebSockets |

---

### Tipos de Consumer

#### `AsyncWebsocketConsumer` — el consumer principal

```python
# envios/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class EncomiendaConsumer(AsyncWebsocketConsumer):
    """
    Consumer del canal global de encomiendas.
    Cada empleado conectado tiene una instancia de este consumer.
    """

    async def connect(self):
        """
        self.scope contiene:
          self.scope['user']        : usuario autenticado
          self.scope['url_route']   : parámetros de la URL
          self.scope['headers']     : cabeceras HTTP del handshake
          self.scope['path']        : ruta de la URL WebSocket
          self.scope['query_string']: query string de la URL
        """
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = 'encomiendas_global'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name  # ID único de este consumer
        )
        await self.accept()

        stats = await self.get_estadisticas()
        await self.send(text_data=json.dumps({
            'tipo':    'conectado',
            'usuario': user.username,
            'stats':   stats,
        }))

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'tipo': 'error', 'mensaje': 'JSON inválido'
            }))
            return

        tipo = data.get('tipo')

        if tipo == 'ping':
            await self.send(text_data=json.dumps({'tipo': 'pong'}))
        elif tipo == 'solicitar_stats':
            stats = await self.get_estadisticas()
            await self.send(text_data=json.dumps({'tipo': 'stats', 'stats': stats}))
        elif tipo == 'suscribir_encomienda':
            enc_id = data.get('encomienda_id')
            if enc_id:
                await self.channel_layer.group_add(
                    f'encomienda_{enc_id}',
                    self.channel_name
                )
                await self.send(text_data=json.dumps({
                    'tipo': 'suscrito', 'encomienda_id': enc_id
                }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def encomienda_estado_cambio(self, event):
        """
        IMPORTANTE: 'type' usa puntos en lugar de underscores:
          'encomienda.estado.cambio' -> encomienda_estado_cambio()
        """
        await self.send(text_data=json.dumps({
            'tipo':             'estado_cambio',
            'encomienda_id':    event['encomienda_id'],
            'codigo':           event['codigo'],
            'estado_anterior':  event['estado_anterior'],
            'estado_nuevo':     event['estado_nuevo'],
            'empleado':         event['empleado'],
            'timestamp':        event['timestamp'],
        }))

    @database_sync_to_async
    def get_estadisticas(self):
        from .models import Encomienda
        return {
            'activas':     Encomienda.objects.activas().count(),
            'en_transito': Encomienda.objects.en_transito().count(),
            'con_retraso': Encomienda.objects.con_retraso().count(),
        }
```

#### `AsyncJsonWebsocketConsumer` — sin `json.loads/dumps` manual

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class EncomiendaJsonConsumer(AsyncJsonWebsocketConsumer):
    """
    AsyncJsonWebsocketConsumer parsea JSON automáticamente.
    receive_json() recibe un dict en lugar de un string.
    send_json()    acepta un dict en lugar de un string.
    """

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = 'encomiendas_global'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        stats = await self.get_estadisticas()
        await self.send_json({'tipo': 'conectado', 'stats': stats})

    async def receive_json(self, content, **kwargs):
        # content ya es un dict, no hay que hacer json.loads()
        tipo = content.get('tipo')
        if tipo == 'ping':
            await self.send_json({'tipo': 'pong'})
        elif tipo == 'solicitar_stats':
            stats = await self.get_estadisticas()
            await self.send_json({'tipo': 'stats', 'stats': stats})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def encomienda_estado_cambio(self, event):
        await self.send_json({
            'tipo':   'estado_cambio',
            'codigo': event['codigo'],
            'nuevo':  event['estado_nuevo'],
        })
```

#### `WebsocketConsumer` — versión síncrona (referencia)

```python
from channels.generic.websocket import WebsocketConsumer

class ConsumerSimple(WebsocketConsumer):
    """
    Versión síncrona: sin async/await.
    Channels lo ejecuta en un ThreadPoolExecutor.
    Usar cuando se necesita llamar a código síncrono de terceros.
    """
    def connect(self):
        self.accept()
        self.send(text_data='{"tipo": "conectado"}')

    def receive(self, text_data):
        data = json.loads(text_data)
        self.send(text_data=json.dumps({'tipo': 'eco', 'dato': data}))

    def disconnect(self, close_code):
        pass
```

---

### El Channel Layer en Profundidad

El channel layer es la capa de mensajería que conecta consumers entre sí, incluso si están en distintos procesos o servidores. Redis actúa como intermediario.

#### Las 4 operaciones del channel layer

```python
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# 1. group_add: unir un channel a un grupo (en connect())
await channel_layer.group_add(
    'encomiendas_global',
    self.channel_name
)

# 2. group_discard: quitar un channel de un grupo (en disconnect())
await channel_layer.group_discard(
    'encomiendas_global',
    self.channel_name
)

# 3. group_send: enviar un mensaje a TODOS los channels del grupo
# 'type' indica qué método del consumer recibe el mensaje.
await channel_layer.group_send(
    'encomiendas_global',
    {
        'type':           'encomienda_estado_cambio',
        'encomienda_id':  enc.pk,
        'codigo':         enc.codigo,
        'estado_anterior': anterior,
        'estado_nuevo':   nuevo,
        'empleado':       str(empleado),
        'timestamp':      timezone.now().isoformat(),
    }
)

# 4. send: enviar a UN channel específico (mensajes directos)
await channel_layer.send(
    'specific.channel.name',
    {'type': 'chat.message', 'message': 'Hola'}
)
```

#### Llamar al channel layer desde código síncrono

```python
# envios/models.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

class Encomienda(models.Model):

    def cambiar_estado(self, nuevo_estado, empleado, observacion=''):
        estado_anterior = self.estado
        self.estado = nuevo_estado
        if nuevo_estado == 'EN':
            self.fecha_entrega_real = timezone.now().date()
        self.save()

        HistorialEstado.objects.create(
            encomienda=self,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            empleado=empleado,
            observacion=observacion,
        )

        self._notificar_websocket(estado_anterior, nuevo_estado, empleado)

    def _notificar_websocket(self, estado_anterior, estado_nuevo, empleado):
        channel_layer = get_channel_layer()
        if not channel_layer:
            return   # sin channel layer configurado (tests unitarios)

        mensaje = {
            'type':           'encomienda_estado_cambio',
            'encomienda_id':  self.pk,
            'codigo':         self.codigo,
            'estado_anterior': estado_anterior,
            'estado_nuevo':   estado_nuevo,
            'empleado':       str(empleado),
            'timestamp':      timezone.now().isoformat(),
        }

        async_to_sync(channel_layer.group_send)('encomiendas_global', mensaje)
        async_to_sync(channel_layer.group_send)(f'encomienda_{self.pk}', mensaje)

        stats = {
            'activas':     Encomienda.objects.activas().count(),
            'en_transito': Encomienda.objects.en_transito().count(),
            'con_retraso': Encomienda.objects.con_retraso().count(),
        }
        async_to_sync(channel_layer.group_send)(
            'dashboard',
            {'type': 'dashboard_actualizar', 'stats': stats}
        )
```

#### Grupos dinámicos por encomienda

```python
# Grupos en el sistema de encomiendas:
#
# 'encomiendas_global'   <- todos los empleados conectados
# 'encomienda_42'        <- quien está viendo el detalle de la enc. 42
# 'dashboard'            <- quien tiene el dashboard abierto

class EncomiendaDetalleConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        self.enc_pk    = self.scope['url_route']['kwargs']['pk']
        self.group_name = f'encomienda_{self.enc_pk}'

        existe = await self.enc_existe(self.enc_pk)
        if not existe:
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        enc_data = await self.get_encomienda(self.enc_pk)
        await self.send(text_data=json.dumps({
            'tipo':       'estado_actual',
            'encomienda': enc_data,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass  # solo recibe, no procesa mensajes del cliente

    async def encomienda_estado_cambio(self, event):
        await self.send(text_data=json.dumps({
            'tipo':            'estado_cambio',
            'estado_anterior': event['estado_anterior'],
            'estado_nuevo':    event['estado_nuevo'],
            'empleado':        event['empleado'],
            'timestamp':       event['timestamp'],
        }))

    @database_sync_to_async
    def enc_existe(self, pk):
        from .models import Encomienda
        return Encomienda.objects.filter(pk=pk).exists()

    @database_sync_to_async
    def get_encomienda(self, pk):
        from .models import Encomienda
        from .serializers import EncomiendaDetailSerializer
        try:
            enc = Encomienda.objects.con_relaciones().get(pk=pk)
            return dict(EncomiendaDetailSerializer(enc).data)
        except Encomienda.DoesNotExist:
            return None
```

---

### Routing — Cómo Channels Enruta Conexiones

```python
# envios/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Consumer general
    re_path(
        r'^ws/encomiendas/$',
        consumers.EncomiendaConsumer.as_asgi(),
        name='ws-encomiendas'
    ),

    # Consumer de detalle (con pk dinámico)
    re_path(
        r'^ws/encomiendas/(?P<pk>\d+)/$',
        consumers.EncomiendaDetalleConsumer.as_asgi(),
        name='ws-encomienda-detalle'
    ),

    # Consumer del dashboard
    re_path(
        r'^ws/dashboard/$',
        consumers.DashboardConsumer.as_asgi(),
        name='ws-dashboard'
    ),
]

# Nota: re_path es necesario porque ws:// no soporta todos los patrones de path()
# El grupo (?P<nombre>patron) captura el valor en url_route['kwargs']
# Acceso en el consumer: self.scope['url_route']['kwargs']['pk']
```

```python
# config/asgi.py
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from envios.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

# AllowedHostsOriginValidator: rechaza conexiones de orígenes no en ALLOWED_HOSTS
# AuthMiddlewareStack: lee la cookie de sesión y popula self.scope['user']
```

---

### Autenticación y Permisos en WebSockets

#### Autenticación por sesión (para vistas web Django)

```python
async def connect(self):
    user = self.scope['user']
    # user.is_authenticated es True si el usuario está logueado
    if not user.is_authenticated:
        await self.close(code=4001)
        return
    await self.accept()
```

#### Autenticación por JWT — middleware personalizado

```python
# channels_middleware.py
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_string):
    try:
        token   = AccessToken(token_string)
        user_id = token['user_id']
        return User.objects.get(pk=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    El token llega como parámetro de la URL:
      ws://localhost:8000/ws/encomiendas/?token=eyJhbGci...
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            query_string = scope.get('query_string', b'').decode('utf-8')
            params       = parse_qs(query_string)
            token_list   = params.get('token', [])

            if token_list:
                scope['user'] = await get_user_from_token(token_list[0])
            else:
                scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
```

```python
# config/asgi.py — usar el middleware JWT
from channels_middleware import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

# Uso desde el cliente JavaScript:
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/ws/encomiendas/?token=${token}`);
```

---

### `database_sync_to_async` — ORM en Consumers

El ORM de Django es síncrono. Llamarlo directamente desde un consumer async bloquearía el event loop. La solución es `database_sync_to_async`.

```python
from channels.db import database_sync_to_async

class EncomiendaConsumer(AsyncWebsocketConsumer):

    # ── Patrón 1: decorador @database_sync_to_async ──────────────
    @database_sync_to_async
    def get_encomiendas_activas(self):
        from .models import Encomienda
        return list(Encomienda.objects.activas().con_relaciones())

    # ── Patrón 2: sync_to_async inline ────────────────────────────
    async def receive(self, text_data):
        from asgiref.sync import sync_to_async
        from .models import Encomienda

        count = await sync_to_async(
            lambda: Encomienda.objects.activas().count()
        )()

    # ── Patrón 3: ORM async nativo (Django 4.1+) ─────────────────
    async def receive(self, text_data):
        from .models import Encomienda
        count = await Encomienda.objects.activas().acount()
        enc   = await Encomienda.objects.aget(pk=1)
        encs  = await Encomienda.objects.en_transito().alist()
        await enc.asave()

    # ── INCORRECTO: nunca llamar ORM síncrono directo ─────────────
    async def receive_mal(self, text_data):
        encs  = list(Encomienda.objects.all())  # SynchronousOnlyOperation
        count = Encomienda.objects.count()      # SynchronousOnlyOperation
```

---

### Testing de Consumers

```python
# requirements.txt
# pytest-django==4.8.0
# channels==4.0.0

# config/settings.py — channel layer en memoria para tests
if 'test' in sys.argv or 'pytest' in sys.modules:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }
```

```python
# envios/tests/test_consumers.py
import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from config.asgi import application
from .factories import UserFactory, EncomiendaFactory

@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestEncomiendaConsumer:

    async def test_conexion_sin_autenticacion(self):
        """Sin autenticar: el servidor debe rechazar con código 4001"""
        communicator = WebsocketCommunicator(application, '/ws/encomiendas/')
        connected, code = await communicator.connect()
        assert not connected
        assert code == 4001
        await communicator.disconnect()

    async def test_conexion_autenticada(self):
        """Con usuario autenticado: el servidor acepta y envía stats"""
        user = await database_sync_to_async(UserFactory)()
        communicator = WebsocketCommunicator(application, '/ws/encomiendas/')
        communicator.scope['user'] = user

        connected, _ = await communicator.connect()
        assert connected

        response = await communicator.receive_json_from(timeout=3)
        assert response['tipo'] == 'conectado'
        assert 'stats' in response

        await communicator.disconnect()

    async def test_ping_pong(self):
        """El consumer responde pong al recibir ping"""
        user = await database_sync_to_async(UserFactory)()
        communicator = WebsocketCommunicator(application, '/ws/encomiendas/')
        communicator.scope['user'] = user

        await communicator.connect()
        await communicator.receive_json_from(timeout=2)   # mensaje bienvenida

        await communicator.send_json_to({'tipo': 'ping'})
        response = await communicator.receive_json_from(timeout=2)
        assert response['tipo'] == 'pong'

        await communicator.disconnect()

    async def test_notificacion_via_channel_layer(self):
        """El consumer recibe y reenvía mensajes del channel layer"""
        user = await database_sync_to_async(UserFactory)()
        communicator = WebsocketCommunicator(application, '/ws/encomiendas/')
        communicator.scope['user'] = user

        await communicator.connect()
        await communicator.receive_json_from(timeout=2)   # bienvenida

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            'encomiendas_global',
            {
                'type':           'encomienda_estado_cambio',
                'encomienda_id':  1,
                'codigo':         'ENC-2026-001',
                'estado_anterior': 'PE',
                'estado_nuevo':   'TR',
                'empleado':       'Mendoza Cruz, Luis',
                'timestamp':      '2026-05-14T10:00:00Z',
            }
        )

        response = await communicator.receive_json_from(timeout=3)
        assert response['tipo']        == 'estado_cambio'
        assert response['codigo']      == 'ENC-2026-001'
        assert response['estado_nuevo'] == 'TR'

        await communicator.disconnect()

# Ejecutar los tests:
# docker compose exec web pytest envios/tests/test_consumers.py -v
```

---

### Manejo de Errores y Reconexión

#### Errores en el consumer

```python
class EncomiendaConsumer(AsyncWebsocketConsumer):

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            await self.procesar_mensaje(data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'tipo':    'error',
                'codigo':  'JSON_INVALIDO',
                'mensaje': 'El mensaje no es JSON válido',
            }))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error en consumer: {e}', exc_info=True)
            await self.send(text_data=json.dumps({
                'tipo':    'error',
                'codigo':  'ERROR_INTERNO',
                'mensaje': 'Error interno del servidor',
            }))
```

#### Reconexión automática con backoff exponencial

```javascript
class EncomiendaWebSocket {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.intentos = 0;
        this.maxIntentos = 10;
        this.baseDelay = 1000;   // 1 segundo inicial
    }

    conectar() {
        if (this.ws?.readyState === WebSocket.OPEN) return;
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            this.intentos = 0;
            document.getElementById('ws-badge').textContent = 'EN VIVO';
            document.getElementById('ws-badge').className = 'badge bg-success';
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.onMensaje(data);
        };

        this.ws.onclose = (event) => {
            document.getElementById('ws-badge').textContent = 'Reconectando...';
            document.getElementById('ws-badge').className = 'badge bg-warning';

            if (event.code === 4001) {
                window.location.href = '/accounts/login/';
                return;
            }
            if (event.code === 1000) return;

            // Backoff exponencial: 1s, 2s, 4s, 8s, ... máx 30s
            const delay = Math.min(this.baseDelay * Math.pow(2, this.intentos), 30000);
            this.intentos++;
            if (this.intentos <= this.maxIntentos) {
                setTimeout(() => this.conectar(), delay);
            } else {
                document.getElementById('ws-badge').textContent = 'Desconectado';
                document.getElementById('ws-badge').className = 'badge bg-danger';
            }
        };
    }

    onMensaje(data) {
        console.log('Mensaje recibido:', data);
    }

    enviar(data) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    desconectar() {
        this.intentos = this.maxIntentos + 1;
        this.ws?.close(1000, 'Desconexión manual');
    }
}

// Uso:
const wsEnc = new EncomiendaWebSocket('ws://' + window.location.host + '/ws/encomiendas/');
wsEnc.onMensaje = (data) => {
    if (data.tipo === 'estado_cambio') mostrarToast(data);
    if (data.tipo === 'stats_actualizado') actualizarDashboard(data.stats);
};
wsEnc.conectar();
```

---

### Entregable — Django Channels en Profundidad

**Consumers:**
1. `EncomiendaConsumer`: autenticación en `connect()`, 3 tipos de mensaje en `receive()`, `group_add/discard` en `connect/disconnect`, handler de grupo.
2. `EncomiendaDetalleConsumer`: grupo dinámico por pk, verificar existencia, enviar estado actual al conectarse.
3. `DashboardConsumer`: grupo `'dashboard'`, stats iniciales, handler `dashboard_actualizar`.
4. Todos los consumers usan `@database_sync_to_async` para el ORM.

**Channel Layer:**
5. `group_add/group_discard` en `connect/disconnect` de cada consumer.
6. `group_send` desde el modelo con `async_to_sync`.
7. Los tres grupos funcionan independientemente.

**Autenticación:**
8. `AuthMiddlewareStack` llena `self.scope['user']` para sesiones web.
9. `JWTAuthMiddleware` lee el token del query string para la API REST.
10. Conexiones sin autenticar se rechazan con código 4001.

**Testing:**
11. 4 tests con `WebsocketCommunicator`: sin auth, conectado, ping/pong, notificación via channel layer.
12. `InMemoryChannelLayer` en `settings.py` para tests sin Redis.

**Reconexión:**
13. El cliente JavaScript reconecta con backoff exponencial.
14. El badge cambia a `'EN VIVO'`, `'Reconectando...'` o `'Desconectado'`.
15. La reconexión NO se ejecuta para códigos 4001 (no autorizado) ni 1000 (normal).

---

## Redis como Channel Layer

**Qué cubre este documento:**
1. Qué es Redis y por qué es el channel layer recomendado para producción
2. Cómo funciona Redis internamente como bus de mensajes (Pub/Sub)
3. Instalación y configuración de Redis en Docker paso a paso
4. Configuración avanzada de `CHANNEL_LAYERS` en `settings.py`
5. `InMemoryChannelLayer` vs `RedisChannelLayer`: diferencias y cuándo usar cada uno
6. El problema del escalado horizontal y cómo Redis lo resuelve
7. Grupos en Redis: cómo se almacenan y expiran
8. Monitoreo de Redis: `redis-cli`, comandos de diagnóstico
9. Persistencia: RDB, AOF y configuración óptima para Channels
10. Redis Sentinel y Redis Cluster para alta disponibilidad

### Qué es Redis y por qué se usa como Channel Layer

Redis (Remote Dictionary Server) es una base de datos en memoria, de clave-valor, extremadamente rápida. Soporta estructuras de datos avanzadas (listas, sets, hashes, streams) y tiene un sistema de Pub/Sub nativo.

#### El problema del escalado horizontal

```python
# ESCENARIO SIN REDIS: dos instancias del servidor
#
# Servidor A → Juan, María conectados
# Servidor B → Pedro conectado
#
# Luis cambia el estado (petición llega al Servidor A)
#
# Sin Redis:
#   Juan  recibe la notificación [OK]
#   María recibe la notificación [OK]
#   Pedro NO recibe nada          [PROBLEMA]
#
# Con Redis (intermediario compartido):
#   Juan  recibe la notificación [OK]
#   María recibe la notificación [OK]
#   Pedro recibe la notificación [OK]
```

#### InMemoryChannelLayer vs RedisChannelLayer

| Característica | InMemoryChannelLayer | RedisChannelLayer |
|---|---|---|
| Almacenamiento | RAM del proceso Python | Redis Server (proceso separado) |
| Escala horizontal | No: cada proceso es una isla | Sí: todos los procesos comparten Redis |
| Persistencia | Se pierde al reiniciar | Configurable (RDB/AOF) |
| Velocidad | Muy rápida (misma RAM) | Rápida (~1ms de latencia de red) |
| Cuándo usar | Tests y desarrollo solo | Producción y cualquier escenario real |

---

### Cómo Funciona Redis como Bus de Mensajes

```python
# Flujo cuando Luis cambia el estado de ENC-2026-001:
#
# PASO 1: Luis hace POST /api/v1/encomiendas/1/cambiar_estado/
# PASO 2: El ViewSet llama a enc.cambiar_estado('TR', empleado)
# PASO 3: El modelo guarda en PostgreSQL y llama a _notificar_websocket()
# PASO 4: _notificar_websocket() ejecuta:
#   async_to_sync(channel_layer.group_send)(
#       'encomiendas_global',
#       {'type': 'encomienda_estado_cambio', 'codigo': 'ENC-2026-001', ...}
#   )
# PASO 5: channels-redis serializa el mensaje y lo publica en Redis:
#   PUBLISH asgi:group:encomiendas_global '{"codigo":"ENC-2026-001",...}'
# PASO 6: Redis distribuye el mensaje a todos los canales suscritos
# PASO 7: Cada Daphne worker recibe el mensaje de Redis
# PASO 8: Channels llama al handler del consumer
# PASO 9: El consumer envía el mensaje al WebSocket
# PASO 10: El navegador recibe el mensaje y actualiza la UI
```

#### Estructuras de datos de Redis usadas por Channels

```python
# channels-redis usa estas estructuras internamente:

# 1. KEYS (canales individuales): tipo Lista (cola FIFO)
#    Formato: asgi:specific.<channel_name>
#    TTL: expira automáticamente si no se lee

# 2. SETS (grupos): tipo Set
#    Formato: asgi:group:<nombre_del_grupo>
#    Contiene: todos los channel_names del grupo

# Verificar en redis-cli:
docker compose exec redis redis-cli
# KEYS asgi:*
# SMEMBERS asgi:group:encomiendas_global
# SCARD asgi:group:encomiendas_global
```

---

### Instalación y Configuración Paso a Paso

#### Paso 1 — Agregar dependencias

```
# requirements.txt
Django==4.2
channels==4.0.0
daphne==4.0.0
channels-redis==4.1.0   # cliente de Redis para Channels
redis==5.0.1            # cliente Python de Redis (para monitoreo)
```

#### Paso 2 — Docker Compose

```yaml
# docker-compose.yml
version: '3.9'

services:
  web:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    volumes:
      - .:/app
    ports:
      - '8000:8000'
    env_file:
      - .env
    depends_on:
      - db
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/1

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB:       ${DB_NAME}
      POSTGRES_USER:     ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    ports:
      - '6379:6379'
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ['CMD', 'redis-cli', 'ping']
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

#### Paso 3 — Crear redis.conf

```
# redis.conf
# Configuración de Redis optimizada para Django Channels

# ── Red ──────────────────────────────────────────────────────────
bind 0.0.0.0
port 6379
tcp-keepalive 60

# ── Memoria ──────────────────────────────────────────────────────
maxmemory 256mb
maxmemory-policy allkeys-lru  # eliminar las claves menos usadas

# ── Persistencia: RDB ────────────────────────────────────────────
save 900 1      # guardar si hay 1 cambio en 900 segundos
save 300 10     # guardar si hay 10 cambios en 300 segundos
save 60 10000   # guardar si hay 10000 cambios en 60 segundos
dbfilename dump.rdb
dir /data

# ── Logs ─────────────────────────────────────────────────────────
loglevel notice
logfile ''    # stdout (visible en docker logs)

# ── Bases de datos ───────────────────────────────────────────────
databases 16  # Channels usa la BD 1

# ── Timeouts ─────────────────────────────────────────────────────
timeout 0     # no cerrar conexiones inactivas
tcp-backlog 511
```

#### Paso 4 — Configurar CHANNEL_LAYERS en settings.py

```python
# config/settings.py
import sys

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
            'capacity': 100,     # máx mensajes en la cola de un canal
            'expiry': 60,        # segundos antes de expirar mensajes sin leer
            'prefix': 'encomiendas',  # prefijo para claves en Redis
        },
    },
}

# Channel layer en memoria solo para tests
if 'pytest' in sys.modules or 'test' in sys.argv:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }
```

#### Paso 5 — Reconstruir y verificar

```bash
docker compose down
docker compose build
docker compose up -d

docker compose ps
# Debe aparecer encomiendas-redis Up (healthy)

# Verificar que Redis responde
docker compose exec redis redis-cli ping
# PONG

# Verificar que Django puede conectarse
docker compose exec web python manage.py shell
>>> from channels.layers import get_channel_layer
>>> from asgiref.sync import async_to_sync
>>> cl = get_channel_layer()
>>> async_to_sync(cl.group_send)('test_grupo', {'type': 'test.mensaje'})
# Si no lanza excepción: Redis está correctamente conectado

# Verificar que la clave apareció en Redis
docker compose exec redis redis-cli -n 1 KEYS 'encomiendas:*'
# 1) 'encomiendas:group:test_grupo'
```

---

### Opciones de Configuración del Channel Layer

| Opción | Valor por defecto | Descripción |
|---|---|---|
| `hosts` | `[('localhost', 6379)]` | Lista de URLs o tuplas (host, puerto) de Redis |
| `prefix` | `"asgi"` | Prefijo para todas las claves en Redis |
| `expiry` | `60` | Segundos antes de que un mensaje sin leer expire |
| `group_expiry` | `86400` | Segundos antes de que un grupo sin actividad expire (24h) |
| `capacity` | `100` | Máx mensajes en la cola de un canal antes de descartar |
| `channel_capacity` | `{}` | Capacidad por canal individual (override de `capacity`) |
| `symmetric_encryption_keys` | `None` | Claves para cifrar mensajes en Redis |

```python
# config/settings.py — configuración detallada
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.environ.get('REDIS_URL', 'redis://redis:6379/1')],
            # Para Redis con autenticación: 'hosts': ['redis://:password@redis:6379/1'],
            # Para Redis con SSL:           'hosts': ['rediss://redis:6380/1'],

            'prefix': 'encomiendas',

            'expiry': 60,
            'capacity': 100,

            'channel_capacity': {
                'ws.connect.*': 200,
                'http.request': 200,
            },

            'group_expiry': 86400,

            # 'symmetric_encryption_keys': [os.environ.get('REDIS_SECRET')],
        },
    },
}
```

---

### Grupos en Redis — Cómo se Almacenan

```python
# Lo que channels-redis hace internamente al llamar a group_add():
#   SADD encomiendas:group:encomiendas_global <channel_name>
#   EXPIRE encomiendas:group:encomiendas_global 86400

# Lo que channels-redis hace internamente al llamar a group_send():
#   1. SMEMBERS encomiendas:group:encomiendas_global
#      -> {'channel_abc', 'channel_def', 'channel_ghi'}
#   2. Para cada channel_name del set:
#      RPUSH encomiendas:specific.channel_abc <mensaje_serializado>
#      EXPIRE encomiendas:specific.channel_abc 60

# Verificar los grupos desde redis-cli:
docker compose exec redis redis-cli -n 1

# Ver todas las claves del proyecto
KEYS encomiendas:*
# 1) "encomiendas:group:encomiendas_global"
# 2) "encomiendas:group:dashboard"
# 3) "encomiendas:group:encomienda_42"

# Ver cuántos empleados están conectados
SCARD encomiendas:group:encomiendas_global
# (integer) 3

# Ver los channel_names conectados al dashboard
SMEMBERS encomiendas:group:dashboard

# Ver el TTL de un grupo
TTL encomiendas:group:encomiendas_global
# (integer) 85234  (~23 horas restantes)
```

---

### Monitoreo de Redis en el Sistema de Encomiendas

#### Comandos de diagnóstico esenciales

```bash
# Información general
docker compose exec redis redis-cli INFO

# Estadísticas por BD
docker compose exec redis redis-cli INFO keyspace
# db1:keys=12,expires=10,avg_ttl=43200000

# Clientes conectados
docker compose exec redis redis-cli INFO clients

# Uso de memoria
docker compose exec redis redis-cli INFO memory

# Monitor en tiempo real (todos los comandos)
docker compose exec redis redis-cli MONITOR
# Ctrl+C para detener. ADVERTENCIA: en producción puede generar mucho output

# Latencia de comandos
docker compose exec redis redis-cli --latency
# min: 0, max: 1, avg: 0.09 (samples: 2500)
```

#### Endpoint de salud del sistema (desde Python)

```python
# envios/views.py
import redis
from django.http import JsonResponse
from django.conf import settings

def health_check(request):
    """
    GET /health/
    Verifica que todos los servicios del sistema estén funcionando.
    """
    estado = {
        'postgres': False,
        'redis':    False,
        'channels': False,
    }

    # Verificar PostgreSQL
    try:
        from django.db import connection
        connection.ensure_connection()
        estado['postgres'] = True
    except Exception as e:
        estado['postgres_error'] = str(e)

    # Verificar Redis directamente
    try:
        r = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        r.ping()
        info = r.info()
        estado['redis']          = True
        estado['redis_memoria']  = info.get('used_memory_human')
        estado['redis_clientes'] = info.get('connected_clients')
        estado['redis_version']  = info.get('redis_version')
    except Exception as e:
        estado['redis_error'] = str(e)

    # Verificar Channel Layer
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        cl = get_channel_layer()
        async_to_sync(cl.group_send)('health_check', {'type': 'health.ping'})
        estado['channels'] = True
    except Exception as e:
        estado['channels_error'] = str(e)

    # Contar empleados conectados
    try:
        r = redis.from_url(settings.REDIS_URL)
        estado['empleados_conectados'] = r.scard('encomiendas:group:encomiendas_global')
    except Exception:
        estado['empleados_conectados'] = None

    todo_ok     = all([estado['postgres'], estado['redis'], estado['channels']])
    http_status = 200 if todo_ok else 503
    return JsonResponse(estado, status=http_status)

# envios/urls.py
urlpatterns += [
    path('health/', views.health_check, name='health'),
]
```

---

### Persistencia en Redis

Redis puede persistir datos en disco para recuperarse ante reinicios. Django Channels usa Redis para colas de mensajes (efímeros), por lo que el RDB es suficiente.

#### RDB vs AOF

| Mecanismo | Cómo funciona | Ventaja | Desventaja |
|---|---|---|---|
| RDB (snapshot) | Guarda una foto de toda la BD en disco cada X segundos | Archivo compacto, recuperación rápida | Puede perder hasta X segundos de datos |
| AOF (append-only file) | Guarda cada comando de escritura en un log | Pérdida de datos mínima | Archivo más grande, recuperación más lenta |
| Ninguno | Solo en memoria, sin persistencia | Máxima velocidad | Pierde todo al reiniciar |

```
# redis.conf — persistencia recomendada para Django Channels

# ── RDB ─────────────────────────────────────────────────────────
save 900 1
save 300 10
save 60 10000

dbfilename encomiendas-dump.rdb
dir /data
stop-writes-on-bgsave-error yes
rdbcompression yes

# ── AOF: NO recomendado para Channels ──────────────────────────
# Los mensajes del channel layer son efímeros (expiran en 60s).
# El RDB es suficiente.
appendonly no
```

---

### Alta Disponibilidad con Redis Sentinel

```yaml
# docker-compose.yml — con Redis Sentinel (producción)
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --port 6379
    volumes:
      - redis_master_data:/data

  redis-replica:
    image: redis:7-alpine
    command: redis-server --port 6379 --replicaof redis-master 6379
    depends_on: [redis-master]

  redis-sentinel:
    image: redis:7-alpine
    command: >
      redis-sentinel /etc/redis/sentinel.conf
      --sentinel monitor mymaster redis-master 6379 1
      --sentinel down-after-milliseconds mymaster 5000
      --sentinel failover-timeout mymaster 10000
    depends_on: [redis-master, redis-replica]
```

```python
# config/settings.py — usar Sentinel
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                {
                    'sentinels': [('redis-sentinel', 26379)],
                    'master_name': 'mymaster',
                    'sentinel_kwargs': {},
                    'db': 1,
                }
            ],
            'prefix': 'encomiendas',
        },
    }
}
```

---

### Problemas Comunes y Soluciones

| Problema | Causa probable | Solución |
|---|---|---|
| `ConnectionRefusedError` al iniciar | Redis no está corriendo | `docker compose up -d redis && redis-cli ping` |
| Los consumers no reciben mensajes | Prefijo incorrecto en `CHANNEL_LAYERS` | Verificar que `'prefix'` coincide en `settings.py` y `redis.conf` |
| Mensajes se descartan (capacity exceeded) | Consumer muy lento o `'capacity'` muy bajo | Aumentar `'capacity'`, revisar el handler del consumer |
| Grupos no se limpian (memory leak) | `group_discard()` no se llama en `disconnect` | Asegurarse de llamar `group_discard` en `disconnect()` |
| Redis usa demasiada memoria | Demasiados canales o mensajes pendientes | Revisar `'maxmemory'` y `'maxmemory-policy'` en `redis.conf` |
| Latencia alta en notificaciones | Redis en servidor distinto o sobrecargado | Colocar Redis cerca del servidor web, revisar `INFO latency` |
| `django.core.exceptions.ImproperlyConfigured` | `CHANNEL_LAYERS` no configurado en settings | Agregar el bloque `CHANNEL_LAYERS` completo a `settings.py` |

#### Diagnosticar un problema de mensajes perdidos

```bash
# 1. Verificar que Redis está corriendo
docker compose exec redis redis-cli ping

# 2. Verificar que el channel layer funciona desde Django
docker compose exec web python manage.py shell
>>> from channels.layers import get_channel_layer
>>> from asgiref.sync import async_to_sync
>>> cl = get_channel_layer()
>>> print(cl)  # debe mostrar RedisChannelLayer, no InMemoryChannelLayer
>>> async_to_sync(cl.group_send)('encomiendas_global', {'type': 'test'})

# 3. Verificar que los grupos existen en Redis
docker compose exec redis redis-cli -n 1
KEYS encomiendas:group:*
# Si no aparece: ningún consumer está conectado o el prefijo es incorrecto

# 4. Verificar el prefijo
docker compose exec redis redis-cli -n 1 KEYS '*:group:*'
# Si aparece 'asgi:group:...' en lugar de 'encomiendas:group:...',
# el prefix en settings.py no está siendo aplicado correctamente

# 5. Ver los logs de Daphne en tiempo real
docker compose logs -f web
```
