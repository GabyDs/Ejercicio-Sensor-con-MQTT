# ---------- Importaciones necesarias ----------

# Modulo para entrada y salida
from machine import Pin, unique_id

# Modulo para funcines asincronas
import uasyncio as asyncio

# Modulo para manejar archivos JSON
import ujson

# Modulo para comunicacion mediante MQTT
from mqtt_as import MQTTClient
from mqtt_local import config

# Datos de configuraciones
from settings import SSID, PASSWORD, BROKER

# Modulo del sensor
import dht

# ---------- Importaciones necesarias ----------

# ---------- Funciones principales ----------


# Función para cargar parámetros desde el archivo JSON
def load_params():
    try:
        with open(PARAMS_FILE, "r") as f:
            params = ujson.load(f)
            print(f"Parametros cargados: {params}")
            return params
    except (OSError, ValueError):
        print("No se puede cargar el archivos de parametros.")
        print("Se utilizan los valores por defecto.")
        save_params(DEFAULT_PARAMS)  # Crear el archivo si no existe
        return DEFAULT_PARAMS.copy()


# Función para guardar parámetros en el archivo JSON
def save_params(params):
    try:
        with open(PARAMS_FILE, "w") as f:
            ujson.dump(params, f)
            print(f"Parametros guardados: {params}")
    except OSError as e:
        print(f"Error guardando parametros: {e}")


# Callback para manejar el estado de la conexión WiFi
async def wifi_han(state):
    """
    Muestra el estado de la conexión WiFi.
    """
    print("WiFi ", "conectado" if state else "desconectado")
    await asyncio.sleep(1)


# Callback para manejar mensajes recibidos en los tópicos suscritos
def sub_cb(topic, msg, retained):
    """
    Procesa los mensajes recibidos por MQTT y actualiza los parámetros.
    """
    global params
    topic = topic.decode()
    msg = msg.decode()
    print(f"Mensaje recibido: {topic} -> {msg}")

    # Cargamos el mensaje como JSON
    msg_json = ujson.loads(msg)

    # Procesar el mensaje según el tópico
    if topic.endswith("/setpoint"):

        """Procesa el mensaje para el tópico /periodo."""
        if "setpoint" in msg_json:
            params["setpoint"] = int(msg_json["setpoint"])
            print(f"Setpoint actualizado a: {params['setpoint']}")
        else:
            print("No existe la clave.")

    elif topic.endswith("/periodo"):

        if "periodo" in msg_json:
            new_periodo = int(msg_json["periodo"])
            if new_periodo > 0:
                params["periodo"] = new_periodo
                print(f"Periodo actualizado a: {params['periodo']}")
            else:
                print("El periodo debe ser un numero positivo mayor a cero.")
        else:
            print("No existe la clave.")

    elif topic.endswith("/modo"):

        """Procesa el mensaje para el tópico /modo."""
        if "modo" in msg_json and msg_json["modo"] in ["automatico", "manual"]:
            params["modo"] = msg_json["modo"]
            print(f"Modo actualizado a: {params['modo']}")
        else:
            print("No existe la clave.")

    elif topic.endswith("/rele"):

        """Procesa el mensaje para el tópico /rele."""
        if "rele" in msg_json:
            params["rele"] = int(msg_json["rele"])
            relay.value(params["rele"])
            print(f"Rele actualizado a: {params['rele']}")
        else:
            print("No existe la clave.")

    elif topic.endswith("/destello"):

        """Procesa el mensaje para el tópico /destello."""
        # print("Comando de destello recibibo.")

        """Teoria
        create_task: El planificador convierte el 'coro' en una tarea y la pone en cola
        para que se ejecute lo antes posible
        """
        asyncio.create_task(flash_led())
    else:
        print(f"No existe el topico: {topic}")


# Función para parpadear el LED integrado
async def flash_led():
    """Parpadea el LED integrado durante 3 segundos."""
    led.value(1)
    await asyncio.sleep(3)
    led.value(0)


# Callback para manejar la conexión al broker MQTT
async def conn_han(client):
    """
    Se ejecuta al conectar con el broker MQTT y suscribe a los tópicos necesarios.
    """
    topics = [
        f"{id}/setpoint",
        f"{id}/periodo",
        f"{id}/destello",
        f"{id}/modo",
        f"{id}/rele",
    ]

    for topic in topics:
        await client.subscribe(topic, 1)
        print(f"Subscrito al topico: {topic}")
        await asyncio.sleep(0.5)


async def main(client):
    """Teoria
    await: Inicia la tarea lo antes posible. La tarea en espera
    se bloquea hasta que la tarea esperada se haya ejecutado por completo
    """
    await client.connect()
    # print("BROKER conectado")

    while True:
        # Lectura del sensor DHT11
        # try:
        #     sensor.measure()
        #     temperatura = sensor.temperature()
        #     humedad = sensor.humidity()
        # except Exception as e:
        #     print(f"Error reading DHT11 sensor: {e}")
        #     temperatura = None
        #     humedad = None

        # Simular lectura de sensor
        temperatura = 25
        humedad = 50

        # Control automático del relé
        if params["modo"] == "automatico":
            # Tiene lógica invertida, se activa con un cero
            relay.value(0 if temperatura >= params["setpoint"] else 1)
            print("ENCENDIDO RELE")
        else:
            # A la vista del tiene que ser un 1 el significado de encendido
            relay.value(int(not params["rele"]))
            print("RELE MANUAL")

        # Crear el mensaje JSON con los datos
        data = {
            "temperatura": temperatura,
            "humedad": humedad,
            "setpoint": params["setpoint"],
            "periodo": params["periodo"],
            "modo": params["modo"],
            "rele": int(not relay.value()),
        }

        # Publicar los datos en el tópico MQTT
        mensaje = ujson.dumps(data)
        # print(f"Publicando mensaje: {mensaje}")
        await client.publish(id, mensaje, qos=1)

        # El periodo lo utilizamos para manejar el tiempo de publicacion
        # en el broker
        await asyncio.sleep(params["periodo"])


# ---------- Funciones principales ----------

# ---------- Configuracion de pines ----------

# Configuracion del sensor DHT
sensor = dht.DHT11(15)

# Configuración de LED y relé
# led = Pin(25, Pin.OUT)  # LED integrado en la placa
led = Pin("LED", Pin.OUT)  # pico 2w

relay = Pin(16, Pin.OUT, value=1)  # Pin GPIO 16 para el control del relé

# ---------- Configuracion de pines ----------

# ---------- Configuracion del cliente MQTT ----------

# Obtener el ID único del dispositivo para el topico
id = "".join("{:02X}".format(b) for b in unique_id())
print(f"Device ID: {id}")

config["ssid"] = SSID
config["password"] = PASSWORD
config["subs_cb"] = sub_cb
config["server"] = config["server"]
config["connect_coro"] = conn_han
config["wifi_coro"] = wifi_han
config["ssl"] = True

MQTTClient.DEBUG = True  # Optional: print diagnostic messages

client = MQTTClient(config)

# ---------- Configuracion del cliente MQTT ----------

# ---------- Configuracion de los valores predeterminados ----------

# Archivo para almacenamiento no volátil
PARAMS_FILE = "params.json"

# Parámetros iniciales por defecto
DEFAULT_PARAMS = {
    "setpoint": 25,  # Temperatura objetivo para el modo automático
    "periodo": 10,  # Intervalo de publicación en segundos
    "modo": "manual",  # Modo inicial: manual
    "rele": 0,  # Estado inicial del relé (apagado)
}
# Cargar los parámetros al inicio
params = load_params()

# ---------- Configuracion de los valores predeterminados ----------

# ---------- Ejecucion del programa ----------

try:
    """Teoria
    run: El planificador pone en la cola el 'coro' pasado para
    que se ejecute lo antes posible
    """
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors

# ---------- Ejecucion del programa ----------
