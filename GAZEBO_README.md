# Gazebo - Explicación
El sistema de simulación entre Gazebo Harmonic y ArduPilot SITL funciona mediante una arquitectura distribuida cliente-servidor en bucle cerrado. En lugar de ejecutar todo dentro de un único programa, el entorno físico y el controlador de vuelo corren como procesos independientes comunicándose a través de sockets de red UDP.

## Componentes principales
Gazebo Harmonic (Motor de Física y Renderizado): Es el entorno 3D encargando de simular las leyes físicas (gravedad, colisiones, inercia) y la representación visual del mundo (.sdf). Gazebo no sabe cómo pilotar un dron; su única función es calcular qué le ocurre al modelo 3D cuando se le aplican fuerzas.

Plugin Interfaz (libArduPilotPlugin.so): Es una librería en C++ que se ejecuta dentro del motor de Gazebo. Actúa como el puente de traducción de hardware: lee el estado del dron simulado en Gazebo y lo convierte en datos que ArduPilot pueda entender.

ArduPilot SITL: Es el código fuente real del firmware de ArduCopter compilado para ejecutarse nativamente en Linux. Cree que está instalado dentro de una placa controladora real y ejecuta los mismos algoritmos de estimación de posición (EKF), bucles PID y navegación autónoma.

MAVProxy / Estación de Control Terreno (GCS): Se conecta a SITL mediante el protocolo MAVLink (a través del puerto TCP 5760 o UDP 14550). Es la interfaz humana para enviar órdenes de vuelo (arm, takeoff, rutas de waypoints) y monitorear la telemetría en tiempo real.

## Bucle de comunicación
El intercambio de información ocurre de manera continua en un ciclo cerrado de alta frecuencia a través del puerto UDP 9002:

1. Lectura de Sensores (Gazebo -> SITL):
Gazebo calcula el estado del dron en el mundo virtual. El plugin extrae los datos de la unidad IMU (acelerómetros y giroscopios), GPS, barómetro o sensores de rango, los empaqueta en formato JSON y los envía por el socket UDP hacia ArduPilot SITL.

2. Procesamiento de Control (SITL):
ArduPilot recibe las lecturas de los sensores simulados, actualiza sus algoritmos de actitud/posición y determina qué potencia necesita cada motor para mantener el control o seguir la trayectoria deseada.

3. Comando de Actuadores (SITL -> Gazebo):
ArduPilot responde enviando un paquete JSON de vuelta al puerto UDP del plugin con la velocidad de giro (RPM) o empuje requerido para cada una de las hélices.

4. Aplicación de Fuerzas (Gazebo):
El plugin aplica esas fuerzas a las hélices del modelo 3D dentro del motor físico de Gazebo, lo que genera movimiento en el espacio virtual y reinicia el ciclo para el siguiente paso de tiempo.

# Uso de SITL + Gazebo Harmonic

## 1. Preparación de entornos y variables
El error más común proviene de ejecutar ambos comandos en la misma terminal o mezclar dependencias de Conda (en caso de que tu gazebo esté instalado en un entorno conda) con las librerías del sistema.

### Terminal 1: Gazebo
Debe tener activo el entorno correspondiente con las rutas a los plugins y modelos compilados exportadas:

export GZ_VERSION=harmonic
export GZ_SIM_SYSTEM_PLUGIN_PATH=$HOME/ardupilot_gazebo/build:$GZ_SIM_SYSTEM_PLUGIN_PATH
export GZ_SIM_RESOURCE_PATH=$HOME/ardupilot_gazebo/models:$HOME/ardupilot_gazebo/worlds:$GZ_SIM_RESOURCE_PATH

### Terminal 2: SITL
Lanzamos el simulador tal y como lo habíamos estado haciendo, solo que añadimos la opción -f gazebo-iris

## 2. Comandos de lanzamiento

### Gazebo: 
gz sim -v4 -r <archivo_mundo>.sdf

-v4: Muestra logs detallados por consola, útil para saber si se ha conectado correctamente el plugin de c++.
-r(run): Arranca el motor de física en reproducción inmediata (no empieza pausado).

### SITL
sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --console --map
-v: Vehiculo
-f: Perfil de vehículo para gazebo
--model JSON Obliga al simulador a usar la interfaz de sockets JSON (UDP 9002/9003) requerida por gazebo harmonic.
-w (opcional): Resetea la memoria y reestablece todos los parámetros.
Es importante anotar que si usamos esto nos dará un error si queremos armar los motores sin mas (arm throttle), ya que borran la configuración FRAME_CLASS y FRAME_TYPE.
FRAME_CLASS: 0 es indefinido y causa error, hay que ponerlo a 1 (4 motores)
FRAME_TYPE: 1 indica que dos motores quedan hacia delante formando la geometría en X que gazebo usa.


