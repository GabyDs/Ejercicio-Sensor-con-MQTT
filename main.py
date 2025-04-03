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


# Callback para manejar el estado de la conexión WiFi
async def wifi_han(state):
    """
    Muestra el estado de la conexión WiFi.
    """
    print("WiFi is", "connected" if state else "disconnected")
    await asyncio.sleep(1)


async def messages(client):  # Respond to incoming messages
    async for topic, msg, retained in client.queue:
        print(topic.decode(), msg.decode(), retained)


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
        print(f"Subscribed to topic: {topic}")
        await asyncio.sleep(0.5)


async def main(client):
    """
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

        # Crear el mensaje JSON con los datos
        data = {
            "temperatura": temperatura,
            "humedad": humedad,
        }

        # Publicar los datos en el tópico MQTT
        mensaje = ujson.dumps(data)
        # print(f"Publicando mensaje: {mensaje}")
        await client.publish(id, mensaje, qos=1)


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
config["server"] = config["server"]
config["connect_coro"] = conn_han
config["wifi_coro"] = wifi_han
config["queue_len"] = 1  # Use event interface with default queue size
MQTTClient.DEBUG = True  # Optional: print diagnostic messages

client = MQTTClient(config)

# ---------- Configuracion del cliente MQTT ----------

# Ejecucion del programa

try:
    """
    run: El planificador pone en la cola el 'coro' pasado para
    que se ejecute lo antes posible
    """
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
