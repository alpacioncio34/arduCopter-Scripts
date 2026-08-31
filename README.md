# ArduPilot scripts

## 1. Flujo de Operación Básica: Despegue y Control

### Procedimiento de Despegue

Por defecto, el despegue manual controlado por comandos solo está permitido en modo `GUIDED` *(para despegar en modo `AUTO` se requiere modificar parámetros de la aeronave)*.

```text
mode guided
arm throttle
takeoff 40

```

Una vez armados los motores (`arm throttle`), se dispone de un **intervalo de 15 segundos** para ejecutar el orden de despegue; de lo contrario, el sistema desarmará los motores por seguridad.

---

### Control de Movimiento y Navegación

Una vez en el aire, el dron puede dirigirse a nuevas coordenadas haciendo clic derecho en la interfaz gráfica del mapa (**Fly to**) o mediante línea de comandos:

```text
guided <latitud> <longitud> <altitud>

```

#### Parámetros de control dinámico en modo GUIDED:

* **Orientación:** `setyaw <ÁNGULO> <VELOCIDAD_ANGULAR> <MODO>` *(Donde MODO: 0 = Absoluto, 1 = Relativo)*.
* **Velocidad lineal:** `setspeed <VALOR_VELOCIDAD>`
* **Vectores de velocidad:** `velocity <x> <y> <z>` *(en m/s)*.

---

### Modo Circular (`CIRCLE`)

Podemos hacer que el dron ejecute una trayectoria circular configurando el radio con el parámetro `CIRCLE_RADIUS_M` y activando el modo `CIRCLE`.

 **Observación técnica sobre la pérdida de altitud:** Durante las pruebas, se detectó que el dron tiende a descender si no se fuerza la señal del acelerador mediante el comando `rc 3 1500`. Esto ocurre porque el acelerador (*throttle*) se mantiene por defecto en 1000 (valor mínimo necesario para superar los chequeos pre-vuelo / *pre-arm checks*).

---

## 2. Ejecución de Misiones Autónomas

Es posible cargar y ejecutar rutas de vuelo previamente planificadas mediante scripts de waypoints.

### Workflow de prueba de misión:

```text
wp load ../Tools/autotest/Generic_Missions/CMAC-circuit.txt
mode AUTO
wp set 3
wp loop

```

* **`wp load`**: Carga la lista de waypoints desde el archivo local.
* **`mode AUTO`**: Inicia la navegación autónoma.
* **`wp set 3`**: Establece el waypoint #3 como el objetivo actual (el dron se dirigirá inmediatamente a este punto y continuará la secuencia desde ahí).
* **`wp loop`**: Configura la misión para ejecutarse en bucle continuo.

---

## 3. Configuración Avanzada y Entorno

### GeoFence (Barreras Virtuales)

Permite delimitar el espacio aéreo del dron. Si la aeronave supera los límites configurados de altitud o distancia longitudinal (de normal no los podrás superar sino que no te dejará viajar fuera de la barrera), el sistema activará automáticamente el retorno a casa (*RTL*) o el aterrizaje de emergencia.

* **Consultar parámetros:** `params show fence*`

Dentro de los parámetros tendremos uno para habilitar o deshabilitar la barrera

---

### Ubicaciones Personalizadas

Mediante el parámetro `-L` al lanzar el simulador, podemos hacer que el dron aparezca en coordenadas específicas previamente guardadas en el archivo `locations.txt`.

---

### Scripts de Inicio (`.mavinit.scr`)

Para automatizar configuraciones iniciales o alias de comandos al arrancar MAVProxy, se utiliza el archivo de script ubicado en el directorio raíz del usuario: `~/.mavinit.scr`.

---

## 4. Integración de Hardware: Control por Joystick

ArduPilot permite la integración de mandos físicos para el control de la simulación.

### Mapeo de Mando Xbox

En este entorno de pruebas se configuró un mando de Xbox. Fue necesario crear una regla de asignación de nombre personalizada para su detección correcta por parte del módulo `mavproxy_joystick`:

```bash
mkdir -p ~/.mavproxy/joysticks
cp /home/alpacioncio/venv-ardupilot/lib/python3.14/site-packages/MAVProxy/modules/mavproxy_joystick/joysticks/xbox-360.yml ~/.mavproxy/joysticks/generic-xbox.yml

```

> **Nota de usabilidad:** Dentro de `generic-xbox.yml` se debe editar la propiedad `name` para que coincida exactamente con la cadena de texto reportada por el sistema al conectar el mando por primera vez.
>  *El pilotaje manual requiere práctica previa debido a la alta sensibilidad de los joysticks; se recomienda realizar las pruebas utilizando el modo **LOITER**.*

# Paso a código
Una vez ya entendemos un poco como funciona el simulador, lo que queremos hacer es realizar una conexión a nuestro simulador a través de código para poder realizar comandas al dron desde un lenguaje como puede ser python, el objetivo de esto es que si lo logramos podremos integrar control remoto de un dron en una aplicación, por ejemplo podemos poner un mapa y que el usuario elija ciertos puntos que quiere seguir el dron, luego la app lo formateará como una misión y se comandará al dron usando el protocolo adecuado (estas ideas aún están un poco verdes ya que toca indagar los límites y posibilidades de esto).

## Elección de framework
De primeras la opción más amigable es aparentemente Dronekit, ya que es de alto nivel y tiene una sintaxis muy amigable que facilita mucho el trabajo, sin embargo la comunidad lo considera obsoleta ya que lleva varios años sin mantenimiento, es por ello que nos vamos a otra opciòn un poco más compleja pero muy reliable.

Usaremos PyMavLink, el cual es de bajo nivel, por lo que nos exige entender mejor como funciona el protocolo (por ejemplo, empaquetar comandos específicos y escuchar los "hearbeats" del dron), pero a cambio ofrece control absoluto sobre la aeronave.

## Estructura del sistema
Vamos a crear scripts de python que se ejecuten para realizar tareas concretas, estos scripts usarán las funciones definidas en drone_actions.py.

Para aumentar la seguridad del sistema, comprobaremos siempre que nos haya llegado el ACK de respuesta del dron y que este haya aceptado la petición, en caso contrario o bien cortaremos la ejecución del script de python o activaremos un modo seguro como STABILIZE o LAND.

## Roadmap
Ahora que sabemos los comandos para comandar al dron usando el protocolo MAVLINK, podemos replicar el mismo control usando pymavlink desde python, quiero seguir el siguiente orden de desarroll:

1. Replicar todos los controles mencionados arriba en funciones de python y realizar scripts para varias tareas (despegar, volar en circulo, ir hacia cierta posición)
2. Simular la velocidad de una persona caminando y realizar un script que siga las posiciones generadas por dicha simulacion.
3. Aprender sobre los logs para debuggear bien en un futuro cuando el sistema se haga mucho mas complejo.

### Movimiento
El dron puede moverse de varias formas, podemos indicarle que avanze ciertos metros en los ejes longitudinales correspondientes (ojo: al indicarle el eje Y se toma como valor negativo, por lo que si indicas 10 metros de altitud el dron bajará 10 metros).

También podemos indicarles unas coordenadas globales a las que el dron irá, cabe recalcar que las coordenadas se usarán escaladas en enteros para mandar el comando como int y asi tener más precisión.

También podemos modificar el yaw rate y la velocidad del dron:

A la hora de cambiar la velocidad distinguimos entre dos tipos distintos de velocidad: Groundspeed y airspeed

- Groundspeed: Velocidad con respecto al suelo, la cual usa el GPS y mide el avance real del dron, esta cambia si hay viendo de frente o de cola

- Airspeed: Es la velocidad del viento que pasa por los sensores del dron.

Esta distinción es necesaria porque drones y aviones en arduPilot comparten la misma interfaz, pero nosotros usamos arduCopter que traducirá siempre a velocidad con respecto al suelo.

Y por último podemos modificar el yaw rate (velocidad a la que el propio dron gira sobre su porpio eje longitudinal central en grados por segundo), un yaw rate alto hace que el dron gire rapido, lo que puede causar que el video desde el dron se vea inestable o que se salta momentaneamente de trayectoria al hacer un giro.

### Following
Dado el script walk.py, tenemos una publicación constante de coordenadas que simulan a una persona andando, por lo que ahora queremos hacer que el dron siga a esta "persona", lo podemos hacer de 2 maneras:

1. Seguimiento propio a mano usando la función go_to (la que usa coordenadas) para ir constantemente hacia la posición publicada.

2. Usando el follow mode incorporado en el propio ArduPilot, 

Para realizar este seguimiento, debemos conseguir que MAVLink se vea como un objetivo a seguir para que ArduPilot lo detecte.

ArduPilot no sigue coordenadas sueltas, sino un sistema identificado por su system.id, que va publicando su posición con mensajes GLOBAL_POSITION_INT, aunque ArduPilot funciona mejor si se usa el mensaje dedicado FOLLOW_TARGET(pero por simplicidad vamos a comenzar con el global).

Primero crearemos el script followed_system.py para poder publicar los mensajes, este script leerá los datos que walk_sim.py va creando y los publicara como si fuesen ellos, aparte de esto este script iniciará una conexión con mavlink pero con otro source ID (en este caso 2).

### Logs
Hay dos formas distintas de poder guardar nuestros datos de vuelo, dos métodos que recopilan datos similares pero de formas muy diferentes:

1. Dataflash logs: Se graban en el propio arduPilot (normalmente en una tarjetra SD), por lo que tienen que ser descargados al terminar el vuelo

2. Telemetry logs: Son grabados por aquello que controle el dron desde tierra, como puede ser nuestro PC a través de un telemetry link.

En nuestro caso, vamos a trabajar más con los Dataflash logs ya que son mucho más completos, para ver los los del simulador SITL solo tenemos que entrar en la propia carpeta de arduCopter donde lanzamos el sim_vehicle.py y entrar en la carpeta logs, aquí dentro podremos ver todos los logs guardados como archivos binarios.

Y para poder ver estos archivos binarios, ya tenemos instalado MAVExplorer.py, que trae un montón de gráficas predefinidas para poder analizar los logs a mano. Más adelante profundizaré más en la lectura y uso de estos logs.

## Detección de objetos
Ahora vamos a subir un poco el nivel, pero antes de nada, vamos a simular la detección de obstáculos usando un mensaje de MAVLink, DISTANCE_SENSOR manda una lectura por dirección, por lo que para fabricar un obstáculo "delante a dos metros" mandas un único mensaje con ese sector y esa distancia, es lo más simple para empezar.



#### Mini script de debug
Con propósitos de debuggear en casos como este o como en el modo follow cuando tambien publicabamos mensajes constantemente, podemos usar el script de message_checker.py cambiando los datos adaptandolo al tipo de mensaje que quieras.

// TODO: 1. Conseguir entender la arquitectura mejor y como hacer que el script de debuggeo funcione
// TODO: 2. Conseguir un script exitoso de evasión de objetos automática
// TODO: Después de ello, continuar con gazebo






