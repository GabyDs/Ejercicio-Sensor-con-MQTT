# Ejercicio-Sensor-con-MQTT

## Consiga

Este programa publica periódicamente en el tópico "ID_DEL_DISPOSITIVO" los siguientes parámetros:
temperatura, humedad, setpoint, periodo y modo. Los datos se envían en una sola publicación en formato JSON.

Suscripciones a los siguientes tópicos:
- "ID_DEL_DISPOSITIVO/setpoint"
- "ID_DEL_DISPOSITIVO/periodo"
- "ID_DEL_DISPOSITIVO/destello"
- "ID_DEL_DISPOSITIVO/modo"
- "ID_DEL_DISPOSITIVO/rele"

Características:
- Almacena de manera no volátil los parámetros: setpoint, periodo, modo y rele (usando un archivo JSON).
- Parpadea un LED por unos segundos cuando recibe la orden "destello" por MQTT.
- Actualiza los parámetros almacenados y actúa en consecuencia al recibir nuevos valores.

Modos de operación:
- Automático: El relé se activa cuando la temperatura supera el setpoint.
- Manual: El relé se activa o desactiva según la orden "rele" enviada por MQTT.

