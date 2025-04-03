# ---------- Importaciones necesarias ----------

# Modulo para funcines asincronas
import uasyncio as asyncio

# Modulo para comunicacion mediante MQTT
from mqtt_as import MQTTClient
from mqtt_local import config

# Datos de configuraciones
from settings import SSID, PASSWORD, BROKER

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


async def up(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        await client.subscribe("foo_topic", 1)  # renew subscriptions


async def main(client):
    """
    await: Inicia la tarea lo antes posible. La tarea en espera
    se bloquea hasta que la tarea esperada se haya ejecutado por completo
    """
    await client.connect()
    # print("BROKER conectado")

    for coroutine in (up, messages):
        asyncio.create_task(coroutine(client))
        n = 0

    while True:
        await asyncio.sleep(5)
        # If WiFi is down the following will pause for the duration.
        await client.publish("result", "{}".format(n), qos=1)
        n += 1


# ---------- Funciones principales ----------

# ---------- Configuracion del cliente MQTT ----------

config["ssid"] = SSID
config["password"] = PASSWORD
config["server"] = config["server"]
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
