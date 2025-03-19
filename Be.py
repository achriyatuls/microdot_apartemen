from microdot import Microdot, Response
from machine import ADC, Pin
import json
import network
import time

# Setup koneksi WiFi
ssid = "BOE-"
password = ""

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)

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
adc_temp = ADC(Pin(26))
adc_ph = ADC(Pin(27))
adc_tds = ADC(Pin(28))
adc_o2 = ADC(Pin(29))
adc_turbidity = ADC(Pin(26))

relay_pump = Pin(15, Pin.OUT)
motion_sensor = Pin(14, Pin.IN)

def read_sensor(sensor):
    return round(sensor.read_u16() / 65535 * 3.3, 2)

def get_status(value, low, high):
    if low <= value <= high:
        return "success"
    return "warning"

@app.route('/data')
def get_data(request):
    temp_value = read_sensor(adc_temp) * 10
    ph_value = read_sensor(adc_ph) * 3
    tds_value = read_sensor(adc_tds) * 5
    oxygen_value = read_sensor(adc_o2) * 2
    turbidity_value = read_sensor(adc_turbidity) * 4

    data = [
        {
            "kamar": "Kamar 1",
            "tanggal_masuk": "12-02-2025",
            "temperatur": { "value": temp_value, "status": get_status(temp_value, 20, 30) },
            "ph": { "value": ph_value, "status": get_status(ph_value, 6.5, 8.5) },
            "garam": { "value": tds_value, "status": get_status(tds_value, 10, 15) },
            "oksigen": { "value": oxygen_value, "status": get_status(oxygen_value, 7, 9) },
            "debit": { "value": turbidity_value, "status": get_status(turbidity_value, 5, 10) },
            "life": { "value": "ada", "status": "success" },
            "pompa": "on" if relay_pump.value() else "off",
            "aerator": "on"
        }
    ]
    return json.dumps(data)

@app.route('/pump/<action>')
def control_pump(request, action):
    if action == 'on':
        relay_pump.value(1)
    elif action == 'off':
        relay_pump.value(0)
    return json.dumps({"pump_status": "on" if relay_pump.value() else "off"})

print("Server berjalan di http://{}:5000".format(ip_address))
app.run(host=ip_address, port=5000)

