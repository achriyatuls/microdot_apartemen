from microdot import Microdot, Response
import random
from machine import ADC
import json
import socket
import network



# setup koneksi wifi
ssid = "BOE-"
password = ""

#get data wifi otomatis


#hubungkan ke wifi
hostname = socket.gethostname()  # Mendapatkan nama host
ip_address = socket.gethostbyname(hostname)  # Mendapatkan IP lokal

#inisialisasi microdot
app = Microdot()
Response.default_content_type = 'application/json'

# Inisialisasi sensor (contoh, sesuaikan dengan pin dan library yang digunakan)
temp_sensor = round(random.uniform(20, 35), 2)  #sensor suhu
ph_sensor = round(random.uniform(60, 100), 2) #sensor kelembapan
tds_sensor = round(random.uniform(6.5, 9.0), 2) #kadar garam
o2_sensor = round(random.uniform(20, 35), 2) #kadar oksigen
turbidity_sensor = round(random.uniform(20, 35), 2) #sensor kekeruhan
relay_pump = machine.Pin(15, machine.Pin.OUT)

# Ambang batas sensor
TEMP_THRESHOLD = 30.0  # Contoh batas suhu dalam derajat Celsius
PH_LOW = 6.5
PH_HIGH = 8.5
TURBIDITY_THRESHOLD = 2.0  # Nilai ambang batas kekeruhan (contoh)


def read_sensor(sensor):
    return sensor.read_u16() / 65535 * 3.3  # Konversi ke tegangan


def check_conditions():
    temp_value = read_sensor(temp_sensor) * 10  # Konversi contoh
    ph_value = read_sensor(ph_sensor) * 3
    turbidity_value = read_sensor(turbidity_sensor) * 5

    if temp_value > TEMP_THRESHOLD or turbidity_value > TURBIDITY_THRESHOLD or not (PH_LOW <= ph_value <= PH_HIGH):
        relay_pump.value(1)  # Nyalakan pompa jika kondisi tidak sesuai
    else:
        relay_pump.value(0)  # Matikan pompa jika kondisi baik

#route API data sensor
@app.route('/data')
def get_data(request):
    check_conditions()
    data = {
        "temperature": read_sensor(temp_sensor) * 10,
        "ph": read_sensor(ph_sensor) * 3,
        "tds": read_sensor(tds_sensor),
        "oxygen": read_sensor(o2_sensor),
        "turbidity": read_sensor(turbidity_sensor) * 5,
        "pump_status": "ON" if relay_pump.value() else "OFF"
    }
    return json.dumps(data)

@app.route('/pump/<action>')
def control_pump(request, action):
    if action == 'on':
        relay_pump.value(1)
    elif action == 'off':
        relay_pump.value(0)
    return json.dumps({"pump_status": "ON" if relay_pump.value() else "OFF"})




# Mulai server
print(ip_address)
app.run(debug=True, host=ip_address, port=5000)

