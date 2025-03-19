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

# Inisialisasi sensor
adc_temp = ADC(Pin(26))  # Sensor suhu (GPIO 26 - ADC0)
adc_ph = ADC(Pin(27))    # Sensor pH (GPIO 27 - ADC1)
adc_tds = ADC(Pin(28))   # Sensor TDS (GPIO 28 - ADC2)
adc_o2 = ADC(Pin(29))    # Sensor Oksigen (GPIO 29 - ADC3)
adc_turbidity = ADC(Pin(26))  # Sensor Kekeruhan (GPIO 26 - ADC0, contoh)

relay_pump = Pin(15, Pin.OUT)  # Relay Pompa (GPIO 15)
motion_sensor = Pin(14, Pin.IN)  # Sensor gerak PIR (GPIO 14)

# Ambang batas sensor
TEMP_THRESHOLD = 30.0
PH_LOW = 6.5
PH_HIGH = 8.5
TURBIDITY_THRESHOLD = 2.0

# Variabel waktu untuk pengiriman data
last_sent_time = time.time()
last_movement_time = 0

# Fungsi membaca sensor analog
def read_sensor(sensor):
    return sensor.read_u16() / 65535 * 3.3  # Konversi ke tegangan

# Fungsi mengecek kondisi air
def check_conditions():
    temp_value = read_sensor(adc_temp) * 10
    ph_value = read_sensor(adc_ph) * 3
    turbidity_value = read_sensor(adc_turbidity) * 5

    if temp_value > TEMP_THRESHOLD or turbidity_value > TURBIDITY_THRESHOLD or not (PH_LOW <= ph_value <= PH_HIGH):
        relay_pump.value(1)  # Nyalakan pompa jika kondisi tidak baik
    else:
        relay_pump.value(0)  # Matikan pompa jika kondisi baik

# Fungsi mendeteksi gerakan kepiting
def detect_movement():
    global last_movement_time
    movement_intensity = motion_sensor.value()
    current_time = time.time()

    if movement_intensity:  # Jika ada gerakan
        if (current_time - last_movement_time) < 5:  # Gerakan mendadak dalam 5 detik
            return "HARVESTED"  # Kepiting kemungkinan diambil/panen
        else:
            last_movement_time = current_time  # Perbarui waktu terakhir bergerak
            return "ACTIVE"  # Kepiting bergerak alami
    else:
        return "IDLE"  # Tidak ada gerakan

# Route API untuk mengambil data sensor
@app.route('/data')
def get_data(request):
    global last_sent_time
    current_time = time.time()

    if current_time - last_sent_time >= 60:  # 1 menit = 60 detik
        last_sent_time = current_time  # Update waktu terakhir pengiriman

        check_conditions()
        data = {
            "temperature": read_sensor(adc_temp) * 10,
            "ph": read_sensor(adc_ph) * 3,
            "tds": read_sensor(adc_tds),
            "oxygen": read_sensor(adc_o2),
            "turbidity": read_sensor(adc_turbidity) * 5,
            "pump_status": "ON" if relay_pump.value() else "OFF",
            "crab_movement": detect_movement()  # Deteksi gerakan kepiting
        }

        print("Data dikirim:", data)
        return json.dumps(data)  # Kirim data dalam format JSON

    return json.dumps({"message": "Data hanya dikirim setiap 1 menit"}), 429  # 429 = Too Many Requests

# Route API untuk mengontrol pompa air
@app.route('/pump/<action>')
def control_pump(request, action):
    if action == 'on':
        relay_pump.value(1)
    elif action == 'off':
        relay_pump.value(0)
    return json.dumps({"pump_status": "ON" if relay_pump.value() else "OFF"})

# Mulai server
print("Server berjalan di http://{}:5000".format(ip_address))
app.run(host=ip_address, port=5000)
