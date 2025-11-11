import streamlit as st
import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import minimalmodbus

# ──────── Inicialización ────────
i2c = busio.I2C(board.SCL, board.SDA)
ads_48 = ADS1115(i2c, address=0x48)
ads_49 = ADS1115(i2c, address=0x49)
ads_48.gain = 1
ads_49.gain = 1

# ──────── Inicialización Modbus ────────
instrument = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
instrument.serial.baudrate = 9600
instrument.serial.bytesize = 8
instrument.serial.parity   = minimalmodbus.serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout  = 1

# ──────── Canales ────────
canal_temp      = AnalogIn(ads_48, 0)
canal_presion   = AnalogIn(ads_48, 1)
canal_humedad   = AnalogIn(ads_48, 2)
canal_radiacion = AnalogIn(ads_48, 3)
canal_velocidad_viento = AnalogIn(ads_49, 0)
canal_direccion_viento = AnalogIn(ads_49, 1)

# ──────── Fórmulas ────────
def calcular_temperatura(v): return ((v - 0.88) / 3.52) * 100.0 - 10.0
def calcular_presion(v): return ((v - 0.5) / 4.0) * 800.0 + 600.0
def calcular_humedad(v): return v * 10.0
def calcular_radiacion(v): return v * 200.0
def calcular_velocidad_viento(v): return max(0, v - 0.5) * 32.4
def calcular_direccion_viento(v): return ((v / 3.3) * 360.0) % 360.0

def direccion_cardinal(grados):
    if grados >= 337.5 or grados < 22.5:
        return "Norte"
    elif grados < 67.5:
        return "Noreste"
    elif grados < 112.5:
        return "Este"
    elif grados < 157.5:
        return "Sureste"
    elif grados < 202.5:
        return "Sur"
    elif grados < 247.5:
        return "Suroeste"
    elif grados < 292.5:
        return "Oeste"
    else:
        return "Noroeste"

# ──────── Interfaz Streamlit ────────
st.set_page_config(page_title="Estación Meteorológica BGI", layout="wide")
st.title("🌦️ Estación Meteorológica BGI")
st.subheader("Lecturas en tiempo real desde sensores ADS1115 + RK520-02")

placeholder = st.empty()

while True:
    v_temp = canal_temp.voltage
    v_presion = canal_presion.voltage
    v_humedad = canal_humedad.voltage
    v_radiacion = canal_radiacion.voltage
    v_velocidad = canal_velocidad_viento.voltage
    v_direccion = canal_direccion_viento.voltage

    temperatura = calcular_temperatura(v_temp)
    presion = calcular_presion(v_presion)
    humedad = calcular_humedad(v_humedad)
    radiacion = calcular_radiacion(v_radiacion)
    velocidad_viento = calcular_velocidad_viento(v_velocidad)
    direccion_viento = calcular_direccion_viento(v_direccion)
    cardinal = direccion_cardinal(direccion_viento)

    # ──────── Lectura RK520-02 ────────
    try:
        humedad_suelo = instrument.read_register(0, 1)
        humedad_suelo_str = f"{humedad_suelo:.1f} %"
    except Exception as e:
        humedad_suelo_str = "Error"

    with placeholder.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("🌡️ Temperatura (°C)", f"{temperatura:.2f}")
        col2.metric("🌬️ Presión (hPa)", f"{presion:.2f}")
        col3.metric("💧 Humedad (%RH)", f"{humedad:.2f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("☀️ Radiación (W/m²)", f"{radiacion:.2f}")
        col5.metric("🌪️ Velocidad Viento (km/h)", f"{velocidad_viento:.2f}")
        col6.metric("🧭 Dirección Viento (°)", f"{direccion_viento:.2f} ({cardinal})")

        st.metric("🌱 Humedad del Suelo (%)", humedad_suelo_str)
        st.caption("Actualizado cada segundo")

    time.sleep(1)