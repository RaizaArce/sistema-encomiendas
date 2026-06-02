# Taller de Lenguajes de Programación
## Sesión 01: Introducción a Python y Backend

---

## Introducción

El propósito de esta primera sesión es que te familiarices con lo básico de Python para luego llevarte paso a paso en el desarrollo de aplicaciones web con Django y Django Rest Framework (DRF). Es importante que realices los ejercicios que se plantean en esta guía.

En esta sesión introductoria veremos los siguientes temas:

1. Funciones en Python
2. Statements y Funciones de Control
3. Tipos de datos complejos: Listas, diccionarios y tuplas
4. Decoradores
5. Control de Excepciones
6. Programación Orientada a Objetos

Para ejecutar los ejercicios puedes usar cualquiera de las siguientes alternativas:

1. Editor online: [https://onecompiler.com/python/](https://onecompiler.com/python/)
2. Visual Studio Code de manera local

---

## Funciones en Python

Una función es un bloque de código que realiza una tarea específica. Dividir un problema complejo en porciones más pequeñas hace que nuestro programa sea fácil de entender y reutilizar. Nos ayuda a evitar la repetición, mejorar la organización del código y facilitar el mantenimiento.

### Creando una función

```python
def greet():
    print("Hello there!")
```

> **Nota:** Cuando escribas una función, presta atención a la sangría (los espacios al principio de una línea de código).

### Llamando una función

Crear una función no significa que estamos ejecutando el código dentro de ella. Para utilizarla, tenemos que llamarla:

```python
greet()
```

### Argumentos y parámetros de una función

```python
def greet(name):
    print(f"Hello, {name}!")

greet("Javier")
```

### 5 tipos de argumentos de funciones de Python

1. Argumentos por defecto
2. Argumentos de palabra clave (keyword)
3. Argumentos posicionales
4. Argumentos posicionales arbitrarios (`*args`)
5. Argumentos de palabra clave arbitrarios (`**kwargs`)

#### 1. Argumentos por defecto

```python
def sumatoria(num1, num2=3, num3=5):
    return num1 + num2 + num3

# Llamada con un solo parámetro
print(sumatoria(2))    # 10

# Llamada con los tres parámetros
print(sumatoria(2, 4, 6))  # 12
```

#### 2. Argumentos keyword

```python
def describe_pet(animal_type, pet_name):
    """Display information about a pet."""
    print(f"\nI have a {animal_type}.")
    print(f"My {animal_type}'s name is {pet_name.title()}.")

# Llamada con argumentos con nombre (el orden no importa)
describe_pet(pet_name='Duque', animal_type='Cat')
```

#### 3. Argumentos posicionales

```python
def describe_pet(animal_type, pet_name):
    print(f"\nI have a {animal_type}.")
    print(f"My {animal_type}'s name is {pet_name.title()}.")

describe_pet('Dog', 'Duque')
```

**Puntos importantes:**

1. Los argumentos por defecto deben seguir a los que no lo son.
2. Los argumentos de palabras clave deben seguir a los argumentos posicionales.
3. Todos los argumentos de palabra clave pasados deben coincidir con uno de los argumentos aceptados por la función.
4. Ningún argumento debe recibir valor más de una vez.
5. Los argumentos por defecto son opcionales.

#### 6. Argumentos posicionales arbitrarios (`*args`)

```python
def add(*b):
    result = 0
    for i in b:
        result = result + i
    return result

print(add(1, 2, 3, 4, 5))  # 15
print(add(10, 20))          # 30
```

#### 7. Argumentos arbitrarios de palabras clave (`**kwargs`)

```python
def fn(**a):
    for i in a.items():
        print(i)

fn(numbers=5, colors="blue", fruits="apple")
# ('numbers', 5)
# ('colors', 'blue')
# ('fruits', 'apple')
```

---

## Listas en Python

Las listas permiten almacenar múltiples elementos en una sola variable. Son similares a los arrays en otros lenguajes de programación.

**Propiedades de una lista:**

1. **Mutable:** Los elementos de la lista pueden modificarse.
2. **Ordenada:** Los elementos tienen un valor de índice único.
3. **Heterogénea:** Puede contener diferentes tipos de elementos.
4. **Duplicados:** Puede contener elementos con los mismos valores.

### Creando listas en Python

```python
# Usando el constructor list()
my_list1 = list((1, 2, 3))
print(my_list1)  # [1, 2, 3]

# Usando corchetes []
my_list2 = [1, 2, 3]
print(my_list2)  # [1, 2, 3]

# Con elementos heterogéneos
my_list3 = [1.0, 'Jessa', 3]
print(my_list3)  # [1.0, 'Jessa', 3]
```

### Accediendo a elementos de la lista

**Indexación:**

```python
languages = ['Python', 'Swift', 'C++']
print('languages[0] =', languages[0])   # Python
print('languages[2] =', languages[2])   # C++
```

**Índice negativo:**

```python
my_list = [10, 20, 'Jessa', 12.50, 'Emma']
print(my_list[-1])   # 'Emma'
print(my_list[-2])   # 12.5
print(my_list[-4])   # 20
```

**List Slicing:**

```python
my_list = [0, 1, 2, 3, 4, 5, 6, 7, 8]
print(my_list[-3:-1])     # [6, 7]
print(my_list[-1:])       # [8]
print(my_list[:-4])       # [0, 1, 2, 3, 4]
print(my_list[-7:-1:2])   # [2, 4, 6]
```

### Iterando una lista

```python
my_list = [5, 8, 'Tom', 7.50, 'Emma']
for item in my_list:
    print(item)
```

### Agregando elementos a la lista

```python
my_list = list([5, 8, 'Tom', 7.50])

# append() — añade al final
my_list.append('Emma')
print(my_list)  # [5, 8, 'Tom', 7.5, 'Emma']

# insert() — añade en posición específica
my_list.insert(2, 25)
print(my_list)  # [5, 8, 25, 'Tom', 7.5, 'Emma']

# extend() — añade múltiples elementos al final
my_list.extend([100, 200])
print(my_list)
```

### Modificando los elementos de la lista

```python
my_list = list([2, 4, 6, 8, 10, 12])

# Modificar un solo item
my_list[0] = 20
print(my_list)  # [20, 4, 6, 8, 10, 12]

# Modificar un rango de items
my_list[1:4] = [40, 60, 80]
print(my_list)  # [20, 40, 60, 80, 10, 12]
```

### Eliminando los elementos de la lista

```python
my_list = list([2, 4, 6, 8, 10, 12])

# remove() — elimina la primera ocurrencia del elemento
my_list.remove(6)
print(my_list)  # [2, 4, 8, 10, 12]

# pop() — elimina el elemento en el índice dado
my_list.pop(2)
print(my_list)  # [2, 4, 10, 12]

# del — elimina un rango de elementos
del my_list[1:3]
print(my_list)  # [2, 12]

# clear() — elimina todos los elementos
my_list.clear()
print(my_list)  # []
```

### List Comprehension

```python
inputList = [4, 7, 11, 13, 18, 20]
squareList = [var**2 for var in inputList if var % 2 == 0]
print(squareList)  # [16, 324, 400]

# Primeros diez números pares
even_numbers = [x for x in range(1, 21) if x % 2 == 0]
print(even_numbers)  # [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
```

---

## Tuplas en Python

Las tuplas son colecciones ordenadas de datos heterogéneos que son **inmutables**.

**Características:**

- **Ordenadas:** Mantienen el orden de inserción.
- **Inalterables:** No podemos añadir o eliminar elementos después de su creación.
- **Heterogéneas:** Pueden contener diferentes tipos de datos.
- **Contienen duplicados:** Pueden tener elementos con el mismo valor.

### Creación de una tupla

```python
# Usando paréntesis ()
number_tuple = (10, 20, 25.75)
print(number_tuple)  # (10, 20, 25.75)

# Usando tuple()
sample_tuple2 = tuple(('Jessa', 30, 45.75, [23, 78]))
print(sample_tuple2)  # ('Jessa', 30, 45.75, [23, 78])

# Tupla con un solo elemento (necesita coma)
single_tuple1 = ('Hello',)
print(type(single_tuple1))  # class 'tuple'
```

### Empaquetado y desempaquetado

```python
# Packing
tuple1 = 1, 2, "Hello"
print(tuple1)  # (1, 2, 'Hello')

# Unpacking
i, j, k = tuple1
print(i, j, k)  # 1 2 Hello
```

---

## Diccionarios en Python

Los diccionarios son colecciones ordenadas de valores únicos almacenados en **pares clave-valor**. Cada clave está vinculada a un valor específico.

**Características:**

- **Ordenados** (Python 3.7+)
- **Únicos:** Las claves deben ser únicas.
- **Mutables:** Se pueden añadir o eliminar elementos.

### Creación de un Diccionario

```python
# Usando {}
person = {"name": "Jessa", "country": "USA", "telephone": 1178}
print(person)

# Usando dict()
person = dict({"name": "Jessa", "country": "USA", "telephone": 1178})
print(person)

# Con valor como lista
person = {"name": "Jessa", "telephones": [1178, 2563, 4569]}
print(person)
```

### Acceso a los elementos de un diccionario

```python
person = {"name": "Jessa", "country": "USA", "telephone": 1178}

# Usando []
print(person['name'])           # 'Jessa'

# Usando get()
print(person.get('telephone'))  # 1178

# Obtener todas las claves y valores
print(person.keys())    # dict_keys(['name', 'country', 'telephone'])
print(person.values())  # dict_values(['Jessa', 'USA', 1178])
print(person.items())   # dict_items([...])
```

### Iteración de un diccionario

```python
person = {"name": "Jessa", "country": "USA", "telephone": 1178}

for key in person:
    print(key, ':', person[key])
```

### Añadiendo y modificando elementos

```python
person = {"name": "Jessa", "country": "USA", "telephone": 1178}

# Añadir nuevas claves
person["weight"] = 50
person.update({"height": 6})
print(person)

# Modificar valores
person["country"] = "Canada"
print(person['country'])  # Canada
```

### Eliminar elementos del diccionario

```python
person = {'name': 'Jessa', 'country': 'USA', 'telephone': 1178, 'weight': 50, 'height': 6}

# popitem() — elimina el último elemento insertado
deleted_item = person.popitem()   # ('height', 6)

# pop() — elimina la clave indicada
deleted_item = person.pop('telephone')  # 1178

# del — elimina una clave específica
del person['weight']

# clear() — elimina todos los elementos
person.clear()
```

### Unir dos diccionarios

```python
dict1 = {'Jessa': 70, 'Arul': 80, 'Emma': 55}
dict2 = {'Kelly': 68, 'Harry': 50, 'Olivia': 66}

# Usando update()
dict1.update(dict2)
print(dict1)

# Usando **kwargs
student_dict1 = {'Aadya': 1, 'Arul': 2}
student_dict2 = {'Harry': 5, 'Olivia': 6}
student_dict = {**student_dict1, **student_dict2}
print(student_dict)
```

---

## Decoradores en Python

Los decoradores son una característica potente y elegante de Python que permite modificar o ampliar el comportamiento de funciones y métodos sin cambiar su código.

### Funciones como objetos de primera clase

Las funciones en Python son **first-class citizens**: pueden pasarse como argumento, devolverse desde una función, y asignarse a variables.

```python
def plus_one(number):
    return number + 1

add_one = plus_one
print(add_one(5))  # 6
```

### Funciones internas y cierres

```python
def outer_function(message):
    def inner_function():
        print(f"Message from closure: {message}")
    return inner_function

closure_function = outer_function("Hello, closures!")
closure_function()
# Output: Message from closure: Hello, closures!
```

### Creación de un decorador

```python
def simple_decorator(func):
    def wrapper():
        print("Before the function call")
        func()
        print("After the function call")
    return wrapper

@simple_decorator
def greet():
    print("Hello!")

greet()
# Before the function call
# Hello!
# After the function call
```

### Ejemplo: decorador que convierte a mayúsculas

```python
def uppercase_decorator(function):
    def wrapper():
        func = function()
        make_uppercase = func.upper()
        return make_uppercase
    return wrapper

@uppercase_decorator
def say_hi():
    return 'hello there'

say_hi()  # HELLO THERE
```

---

## Manejo de Excepciones en Python

Un **error** es un problema crítico que impide completar la tarea. Una **excepción** es una condición que interrumpe el flujo normal del programa y que sí debería detectarse.

### Tipos de excepciones en Python

- `TypeError` — operación aplicada a un tipo inapropiado.
- `ZeroDivisionError` — división por cero.
- `OverflowError` — cálculo excede el límite del tipo numérico.
- `IndexError` — índice fuera del rango de la secuencia.
- `KeyError` — clave no existe en el diccionario.
- `FileNotFoundError` — archivo no encontrado.
- `ImportError` — falla la importación de un módulo.

### try / except

```python
try:
    print(x)
except:
    print("An exception has occurred. X is unknown!")
```

### Múltiples cláusulas except

```python
try:
    print(1 / 0)
except ZeroDivisionError:
    print("You cannot divide a value with zero")
except:
    print("Something else went wrong")
```

### try / except / else

```python
try:
    result = 1 / 3
except ZeroDivisionError as err:
    print(err)
else:
    print(f"Your answer is {result}")
```

### try / except / else / finally

```python
def divide(x, y):
    try:
        result = x / y
    except ZeroDivisionError:
        print("Please change 'y' argument to non-zero value")
    except:
        print("Something went wrong")
    else:
        print(f"Your answer is {result}")
    finally:
        print("\033[92m Code by USS\033[00m")

divide(1, 0)   # ZeroDivisionError + finally
divide(3, 4)   # 0.75 + finally
```

---

## Type Hints en Python

Los type hints (anotaciones de tipo) son una característica de Python 3.5+ que permite indicar el tipo de dato esperado para variables, parámetros y valores de retorno. No son obligatorios, pero son fundamentales en código profesional y en Django moderno.

### Sintaxis Básica

```python
# Sin type hints
def calcular_tarifa(peso, tipo_servicio):
    tarifas = {"ESTANDAR": 5.0, "EXPRESS": 15.0}
    return tarifas[tipo_servicio] + (peso * 2.5)

# Con type hints
def calcular_tarifa(peso: float, tipo_servicio: str) -> float:
    """
    Calcula la tarifa de una encomienda.
    Args:
        peso: Peso en kilogramos
        tipo_servicio: "ESTANDAR", "EXPRESS" o "ECONOMICO"
    Returns:
        Tarifa en soles (S/.)
    """
    tarifas = {"ESTANDAR": 5.0, "EXPRESS": 15.0, "ECONOMICO": 3.0}
    base = tarifas.get(tipo_servicio, 5.0)
    return base + (peso * 2.5)
```

### Tipos Básicos

```python
from typing import Optional, List, Dict

# Tipos primitivos
codigo: str   = "ENC-001"
peso: float   = 2.5
activo: bool  = True
cantidad: int = 10

# Listas tipadas
estados: List[str] = ["PENDIENTE", "EN_TRANSITO", "ENTREGADO"]

# Diccionarios tipados
tarifa_por_tipo: Dict[str, float] = {
    "ESTANDAR": 5.0,
    "EXPRESS":  15.0,
    "ECONOMICO": 3.0,
}

# Optional: puede ser el tipo indicado o None
telefono: Optional[str] = None

# Python 3.10+ (sintaxis simplificada)
telefono: str | None = None
```

---

## Statements y Control de Flujo

### Condicionales — if / elif / else

```python
estado = "EN_TRANSITO"

if estado == "REGISTRADA":
    print("La encomienda acaba de registrarse.")
elif estado == "EN_TRANSITO":
    print("La encomienda va en camino.")
elif estado == "EN_AGENCIA_DESTINO":
    print("Ya llegó a la ciudad de destino.")
elif estado == "ENTREGADA":
    print("Encomienda entregada exitosamente.")
else:
    print("Estado desconocido o cancelado.")
```

### Operadores de comparación y lógicos

```python
peso_kg = 2.5
tipo_servicio = "EXPRESS"
valor_declarado = 500

# Operadores lógicos: and, or, not
if tipo_servicio == "EXPRESS" and peso_kg <= 30:
    print("Puede enviarse como Express.")

if peso_kg > 30 or valor_declarado > 5000:
    print("Requiere aprobación especial.")

if not (estado == "CANCELADA"):
    print("Encomienda activa.")
```

### Bucle for

```python
encomiendas = [
    {"codigo": "ENC-001", "peso": 2.5,  "estado": "EN_TRANSITO"},
    {"codigo": "ENC-002", "peso": 0.8,  "estado": "ENTREGADA"},
    {"codigo": "ENC-003", "peso": 15.0, "estado": "REGISTRADA"},
]

for enc in encomiendas:
    print(f"Codigo: {enc['codigo']} | Estado: {enc['estado']}")

# for con range()
for i in range(1, 10, 2):
    print(i)  # 1, 3, 5, 7, 9

# for con enumerate()
ciudades = ["Lima", "Arequipa", "Trujillo", "Cusco"]
for indice, ciudad in enumerate(ciudades, start=1):
    print(f"{indice}. {ciudad}")

# for sobre diccionario
tarifas = {"ESTANDAR": 5.0, "EXPRESS": 15.0, "ECONOMICO": 3.0}
for tipo, precio in tarifas.items():
    print(f"Tipo {tipo}: S/. {precio:.2f}")
```

### Bucle while

```python
intentos = 0
max_intentos = 3
entregada = False

while intentos < max_intentos and not entregada:
    intentos += 1
    print(f"Intento {intentos} de entrega...")
    if intentos == 2:
        entregada = True
        print("Encomienda entregada exitosamente.")

if not entregada:
    print(f"No se pudo entregar después de {max_intentos} intentos.")
```

---

## Programación Orientada a Objetos

En Django, **cada modelo es una clase** (hereda de `models.Model`), cada vista es una clase y cada serializer es una clase.

### ¿Qué es una Clase?

Una clase es un molde o plantilla para crear objetos. Define qué datos tiene (atributos) y qué puede hacer (métodos).

```python
class Encomienda:
    """Representa una encomienda en el sistema."""

    def __init__(self, codigo: str, peso: float, remitente: str):
        self.codigo    = codigo
        self.peso      = peso
        self.remitente = remitente
        self.estado    = "REGISTRADA"  # valor por defecto

    def cambiar_estado(self, nuevo_estado: str) -> None:
        self.estado = nuevo_estado
        print(f"Encomienda {self.codigo} -> {nuevo_estado}")

    def __str__(self) -> str:
        return f"[{self.codigo}] {self.remitente} | Estado: {self.estado}"

# Instanciar la clase
enc1 = Encomienda("ENC-001", 2.5, "Juan Perez")
enc2 = Encomienda("ENC-002", 0.8, "Maria Garcia")

print(enc1.codigo)           # ENC-001
enc1.cambiar_estado("EN_TRANSITO")
print(enc1)                  # [ENC-001] Juan Perez | Estado: EN_TRANSITO
```

### Atributos de Clase vs. Atributos de Instancia

```python
class Encomienda:
    # ─── ATRIBUTOS DE CLASE ───────────────────────────────────────
    # Compartidos por todos los objetos
    TARIFAS_BASE = {
        "ESTANDAR": 5.0,
        "EXPRESS":  15.0,
        "ECONOMICO": 3.0,
    }
    ESTADOS_VALIDOS = ["REGISTRADA", "EN_TRANSITO", "ENTREGADA", "CANCELADA"]

    # ─── ATRIBUTOS DE INSTANCIA ───────────────────────────────────
    # Únicos para cada objeto
    def __init__(self, codigo: str, peso: float, tipo: str):
        self.codigo = codigo
        self.peso   = peso
        self.tipo   = tipo
        self.estado = "REGISTRADA"
```

**La diferencia clave:**

```python
enc1 = Encomienda("ENC-001", 2.5, "EXPRESS")
enc2 = Encomienda("ENC-002", 8.0, "ESTANDAR")

print(enc1.codigo)       # ENC-001   <- diferente
print(enc2.codigo)       # ENC-002   <- diferente

print(enc1.TARIFAS_BASE) # igual para los dos
print(enc2.TARIFAS_BASE) # igual para los dos

# Puedes acceder sin crear ningún objeto
print(Encomienda.ESTADOS_VALIDOS)
```

### Properties — Atributos Calculados

```python
class Encomienda:
    def __init__(self, codigo, peso, largo=None, ancho=None, alto=None):
        self.codigo = codigo
        self.peso   = peso
        self.largo  = largo
        self.ancho  = ancho
        self.alto   = alto

    @property
    def volumen_cm3(self):
        if all([self.largo, self.ancho, self.alto]):
            return self.largo * self.ancho * self.alto
        return None

    @property
    def es_paquete_grande(self) -> bool:
        return self.peso > 20.0

    @property
    def descripcion_corta(self) -> str:
        tipo = "Grande" if self.es_paquete_grande else "Pequeño"
        return f"{self.codigo} ({tipo}, {self.peso}kg)"

# Acceso como atributo, no como método (sin paréntesis)
enc = Encomienda("ENC-001", 25.0, largo=30, ancho=20, alto=15)
print(enc.volumen_cm3)       # 9000
print(enc.es_paquete_grande) # True
print(enc.descripcion_corta) # ENC-001 (Grande, 25.0kg)
```

### Herencia — La base de Django

```python
class EntidadBase:
    """Clase abstracta con campos de auditoría."""

    def __init__(self):
        import datetime
        self.creado_en     = datetime.datetime.now()
        self.actualizado_en = datetime.datetime.now()
        self.activo        = True

    def desactivar(self) -> None:
        self.activo = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(activo={self.activo})"


class Agencia(EntidadBase):
    """Agencia de encomiendas en una ciudad."""

    def __init__(self, nombre: str, ciudad: str, codigo: str):
        super().__init__()   # Llama al __init__ del padre
        self.nombre  = nombre
        self.ciudad  = ciudad
        self.codigo  = codigo
        self.es_hub  = False

    def __str__(self) -> str:
        return f"{self.nombre} - {self.ciudad}"


class AgenciaHub(Agencia):
    """Agencia hub: centro de distribución regional."""

    def __init__(self, nombre: str, ciudad: str, codigo: str, region: str):
        super().__init__(nombre, ciudad, codigo)
        self.es_hub   = True
        self.region   = region
        self.agencias_dependientes = []

    def agregar_agencia(self, agencia: Agencia) -> None:
        self.agencias_dependientes.append(agencia)

    def __str__(self) -> str:
        return f"HUB {self.nombre} ({self.region}) - {len(self.agencias_dependientes)} agencias"


# Uso
ag1 = Agencia("Agencia Lima Centro", "Lima", "LIM-001")
hub = AgenciaHub("Hub Lima Norte", "Lima", "LIM-HUB", "Lima Metropolitana")
hub.agregar_agencia(ag1)

print(ag1)          # Agencia Lima Centro - Lima
print(hub)          # HUB Hub Lima Norte (Lima Metropolitana) - 1 agencias
hub.desactivar()    # Heredado de EntidadBase
print(hub.activo)   # False
```

### Métodos especiales (`__dunder__` methods)

```python
class Encomienda:
    def __init__(self, codigo: str, peso: float, estado: str):
        self.codigo = codigo
        self.peso   = peso
        self.estado = estado

    # Lo que ve el usuario: print()
    def __str__(self) -> str:
        return f"Encomienda {self.codigo} | {self.peso}kg | {self.estado}"

    # La representación para el desarrollador: shell de Python
    def __repr__(self) -> str:
        return f"Encomienda(codigo={self.codigo!r}, peso={self.peso})"

    # Operador ==
    def __eq__(self, other) -> bool:
        if not isinstance(other, Encomienda):
            return False
        return self.codigo == other.codigo

    # len()
    def __len__(self) -> int:
        return int(self.peso * 1000)


enc1 = Encomienda("ENC-001", 2.5, "EN_TRANSITO")
enc2 = Encomienda("ENC-001", 3.0, "ENTREGADA")
enc3 = Encomienda("ENC-002", 1.0, "REGISTRADA")

print(str(enc1))      # Encomienda ENC-001 | 2.5kg | EN_TRANSITO
print(repr(enc1))     # Encomienda(codigo='ENC-001', peso=2.5)
print(enc1 == enc2)   # True  (mismo código)
print(enc1 == enc3)   # False (diferente código)
print(len(enc1))      # 2500  (gramos)
```

---

## Instalación de Python

### Instalando Python desde Microsoft Store

1. Abre Microsoft Store en Windows.
2. Busca "Python" y selecciona la versión `3.12`.
3. Haz clic en "Get" e instala.
4. Verifica en la terminal: `python --version`.

### Instalando Python desde python.org

1. Ve a [https://www.python.org/downloads/](https://www.python.org/downloads/).
2. Descarga el instalador de la versión más reciente para Windows (64-bit).
3. Ejecuta el instalador y marca **"Add Python to PATH"**.
4. Haz clic en "Install Now".

---

## Cómo instalar paquetes Python

```bash
# Instalar un paquete
pip3 install {package_name}

# Actualizar un paquete
pip3 install --upgrade {package_name}

# Listar paquetes instalados
pip3 freeze

# Exportar dependencias del proyecto
python -m pip freeze > requirements.txt
```

---

## Entornos Virtuales en Python

Un entorno virtual crea un entorno específico para una aplicación, separándolo de otros recursos del sistema.

### Creando un entorno virtual

```bash
# 1. Crear la carpeta del proyecto
mkdir sesion02 && cd sesion02

# 2. Crear el entorno virtual
python -m venv env

# 3. Activar el entorno virtual
# Windows:
env\Scripts\activate
# Unix/Mac:
source env/bin/activate

# 4. Desactivar el entorno
deactivate
```

Al activar el entorno, la línea de comandos mostrará el prefijo `(env)`.

---

## Laboratorio: Setup completo del proyecto

```bash
# 1. Crear el directorio y entorno virtual
mkdir sistema_encomiendas && cd sistema_encomiendas
python3 -m venv venv
source venv/bin/activate   # Linux/Mac

# 2. Instalar dependencias base
pip install django==5.0.6 djangorestframework==3.15.2 django-environ==0.11.2
pip freeze > requirements.txt
```
