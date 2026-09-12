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

PIN_DIN = 18          # Pin GPIO 18 conectado a 'DIN'
CANTIDAD_PIXELES = 24 # 24 nodos integrados (72 LEDs físicos en grupos de 3)

MQTT_CLIENT_ID = "ESP32_PIXEL_12V_MIGUEL_RBG"
MQTT_BROKER = "test.mosquitto.org"
TOPIC = "sds/dato1"

# =====================================================
# CONFIGURACIÓN DEL HARDWARE
# =====================================================
pixel = NeoPixel(Pin(PIN_DIN), CANTIDAD_PIXELES)

def aplicar_3_secciones(col_izq, col_cen, col_der):
    """
    Divide la tira de 24 nodos (72 LEDs físicos) en 3 secciones de 8 nodos:
    - Nodos 0 a 7   (LEDs 1-24)  -> Sección 1 (Izquierda)
    - Nodos 8 a 15  (LEDs 25-48) -> Sección 2 (Centro)
    - Nodos 16 a 23 (LEDs 49-72) -> Sección 3 (Derecha)

    Aplica el orden estricto (R, B, G).
    """
    r1, g1, b1 = col_izq
    r2, g2, b2 = col_cen
    r3, g3, b3 = col_der

    # --- ZONA 1: Nodos 0 a 7 (LEDs 1 a 24) ---
    for i in range(0, 8):
        pixel[i] = (r1, b1, g1)

    # --- ZONA 2: Nodos 8 a 15 (LEDs 25 a 48) ---
    for i in range(8, 16):
        pixel[i] = (r2, b2, g2)

    # --- ZONA 3: Nodos 16 a 23 (LEDs 49 a 72) ---
    for i in range(16, 24):
        pixel[i] = (r3, b3, g3)

    pixel.write()

# Apagar al energizar
aplicar_3_secciones((0, 0, 0), (0, 0, 0), (0, 0, 0))

# =====================================================
# PRUEBA DE DIAGNÓSTICO DE 7 SEGUNDOS
# =====================================================
def animacion_inicio_7s():
    print("\n[DIAGNÓSTICO] Probando 3 secciones con orden (R, B, G)...")

    # Muestra de 3 secciones simultáneas (3.5s): Sec1=ROJO | Sec2=VERDE | Sec3=AZUL
    aplicar_3_secciones((255, 0, 0), (0, 255, 0), (0, 0, 255))
    time.sleep(3.5)

    # Inversión de prueba (3.5s): Sec1=AZUL | Sec2=ROJO | Sec3=VERDE
    aplicar_3_secciones((0, 0, 255), (255, 0, 0), (0, 255, 0))
    time.sleep(3.5)

    # Apagar tira antes de pasar a la cámara
    aplicar_3_secciones((0, 0, 0), (0, 0, 0), (0, 0, 0))
    print("[DIAGNÓSTICO] Prueba lista. Transicionando a modo Cámara por MQTT...\n")

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
    print("IP asignada:", wifi.ifconfig()[0])

def recibir_mensaje(topic, msg):
    try:
        datos = json.loads(msg.decode("utf-8"))

        if "Sec1" in datos and "Sec2" in datos and "Sec3" in datos:
            c1 = datos["Sec1"]
            c2 = datos["Sec2"]
            c3 = datos["Sec3"]

            aplicar_3_secciones(
                (int(c1[0]), int(c1[1]), int(c1[2])),
                (int(c2[0]), int(c2[1]), int(c2[2])),
                (int(c3[0]), int(c3[1]), int(c3[2]))
            )
            print(f"MQTT Cámara -> S1:{c1} | S2:{c2} | S3:{c3}")

    except Exception as e:
        print(f"Error procesando datos MQTT: {e}")

def main():
    conectar_wifi()
    
    # 1. Animación diagnóstica inicial de 7s
    animacion_inicio_7s()

    # 2. Conexión al servidor MQTT
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER)
    client.set_callback(recibir_mensaje)
    client.connect()
    client.subscribe(TOPIC)

    print(f"Sistema en línea. Escuchando tópico: {TOPIC}")

    # 3. Bucle continuo para recibir datos de la cámara
    while True:
        try:
            client.check_msg()
        except Exception as e:
            print(f"Reconectando a MQTT: {e}")
            time.sleep(1)
            try:
                client.connect()
                client.subscribe(TOPIC)
            except:
                pass
        time.sleep(0.01)

if __name__ == "__main__":
    main()