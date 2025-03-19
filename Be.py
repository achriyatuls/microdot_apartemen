from microdot import Microdot, Response
from machine import ADC, Pin
import json
import network
import time

# Setup koneksi WiFi
ssid = "BOE-"
password = ""

# Hubungkan ke WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)

# Tunggu sampai terhubung
print("Menghubungkan ke WiFi...")
while not wifi.isconnected():
    time.sleep(1)
    print("Menghubungkan...")

print("Terhubung ke WiFi")
ip_address = wifi.ifconfig()[0]
print("IP Address:", ip_address)

# Inisialisasi Microdot
app = Microdot()
Response.default_content_type = 'application/json'

# Inisialisasi sensor (gunakan pin yang valid untuk ADC pada Pico W)
adc_temp = ADC(Pin(26))  # GPIO 26 (ADC0)
adc_ph = ADC(Pin(27))    # GPIO 27 (ADC1)
adc_tds = ADC(Pin(28))   # GPIO 28 (ADC2)
adc_o2 = ADC(Pin(29))    # GPIO 29 (ADC3, sensor suhu internal)
adc_turbidity = ADC(Pin(26))  # GPIO 26 (ADC0, contoh)

relay_pump = Pin(15, Pin.OUT)  # GPIO 15 untuk relay

# Ambang batas sensor
TEMP_THRESHOLD = 30.0  # Contoh batas suhu dalam derajat Celsius
PH_LOW = 6.5
PH_HIGH = 8.5
TURBIDITY_THRESHOLD = 2.0  # Nilai ambang batas kekeruhan (contoh)

def read_sensor(sensor):
    return sensor.read_u16() / 65535 * 3.3  # Konversi ke tegangan

def check_conditions():
    temp_value = read_sensor(adc_temp) * 10  # Konversi contoh
    ph_value = read_sensor(adc_ph) * 3
    turbidity_value = read_sensor(adc_turbidity) * 5

    if temp_value > TEMP_THRESHOLD or turbidity_value > TURBIDITY_THRESHOLD or not (PH_LOW <= ph_value <= PH_HIGH):
        relay_pump.value(1)  # Nyalakan pompa jika kondisi tidak sesuai
    else:
        relay_pump.value(0)  # Matikan pompa jika kondisi baik

# Route API data sensor
@app.route('/data')
def get_data(request):
    check_conditions()
    data = {
        "temperature": read_sensor(adc_temp) * 10,
        "ph": read_sensor(adc_ph) * 3,
        "tds": read_sensor(adc_tds),
        "oxygen": read_sensor(adc_o2),
        "turbidity": read_sensor(adc_turbidity) * 5,
        "pump_status": "ON" if relay_pump.value() else "OFF"
    }
    print(data)
    return json.dumps(data)

@app.route('/pump/<action>')
def control_pump(request, action):
    if action == 'on':
        relay_pump.value(1)
    elif action == 'off':
        relay_pump.value(0)
    return json.dumps({"pump_status": "ON" if relay_pump.value() else "OFF"})

# Mulai server
print("Server berjalan di http://{}:5000".format(ip_address))
app.run(debug=True, host=ip_address, port=5000)