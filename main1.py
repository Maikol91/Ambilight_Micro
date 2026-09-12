import time
import json
import network
from machine import Pin
from neopixel import NeoPixel
from umqtt.simple import MQTTClient

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================
WIFI_SSID = "Miguel"
WIFI_PASS = "miguel123"

PIN_DIN = 18          # Pin de la ESP32 conectado a 'DIN'
CANTIDAD_PIXELES = 65 # píxeles configurados

MQTT_CLIENT_ID = "ESP32_PIXEL_12V"
MQTT_BROKER = "test.mosquitto.org"
TOPIC = "sds/dato1"

# =====================================================
# CONFIGURACIÓN DEL HARDWARE
# =====================================================
pixel = NeoPixel(Pin(PIN_DIN), CANTIDAD_PIXELES)

def aplicar_color(r, g, b):
    # Intercambiados (g) y (b) -> Orden asignado: (r, b, g)
    # Esto corrige el cruce entre Verde y Azul en cintas 12V
    for i in range(CANTIDAD_PIXELES):
        pixel[i] = (r, b, g)
    pixel.write()

# Apagar al iniciar
aplicar_color(0, 0, 0)

# =====================================================
# CONEXIÓN WI-FI Y MQTT
# =====================================================
def conectar_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    if not wifi.isconnected():
        print(f"Conectando a Wi-Fi '{WIFI_SSID}'...", end="")
        wifi.connect(WIFI_SSID, WIFI_PASS)
        while not wifi.isconnected():
            time.sleep(0.2)
            print(".", end="")
        print(" OK!")

def recibir_mensaje(topic, msg):
    try:
        datos = json.loads(msg.decode("utf-8"))
        
        r = int(datos.get("Num1", 0))
        g = int(datos.get("Num2", 0))
        b = int(datos.get("Num3", 0))
        
        aplicar_color(r, g, b)
        print(f"Luz Pixel 12V -> RGB({r}, {g}, {b})")
        
    except Exception as e:
        print(f"Error procesando datos: {e}")

def main():
    conectar_wifi()
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.set_callback(recibir_mensaje)
    client.connect()
    client.subscribe(TOPIC)
    
    print(f"Sistema listo. Escuchando tópico MQTT: {TOPIC}")

    while True:
        try:
            client.check_msg()
        except Exception as e:
            print(f"Reconectando MQTT... ({e})")
            time.sleep(1)
            try:
                client.connect()
                client.subscribe(TOPIC)
            except:
                pass
        time.sleep(0.01)

if __name__ == "__main__":
    main()