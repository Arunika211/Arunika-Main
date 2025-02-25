import network
import urequests
import time
import random
from machine import Pin, ADC
import dht

# ==== KONFIGURASI ====
WIFI_SSID = "Jawara59"         # Ganti dengan WiFi kamu
WIFI_PASSWORD = "kopisusu"  # Ganti dengan password WiFi kamu
UBIDOTS_TOKEN = "BBUS-b6d507cd1cfc7ae59c2e7371fff45f76db7"  # Ganti dengan Token API Ubidots
UBIDOTS_DEVICE = "Arunika"    # Nama device di Ubidots
UBIDOTS_URL = f"https://industrial.api.ubidots.com/api/v1.6/devices/{UBIDOTS_DEVICE}/"

# GPIO Sensor
DHT_PIN = 18  # Pin DHT11
MQ2_PIN = 2  # MQ-2
TRIG_PIN = 19  # HC-SR04 Trig
ECHO_PIN = 21  # HC-SR04 Echo

# Inisialisasi Sensor
dht_sensor = dht.DHT11(Pin(DHT_PIN))
mq2_sensor = ADC(Pin(MQ2_PIN))
mq2_sensor.atten(ADC.ATTN_11DB)  
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)

# ==== Fungsi untuk Koneksi WiFi ====
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    while not wlan.isconnected():
        print("Menghubungkan ke WiFi...")
        time.sleep(2)

    print("Terhubung ke WiFi:", wlan.ifconfig())

# ==== Fungsi Membaca Sensor Ultrasonik ====
def read_ultrasonic():
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    duration = time_pulse_us(echo, 1, 30000)  # Timeout 30ms jika tidak ada respons
    if duration < 0:
        return None  # Tidak ada objek terdeteksi
    
    distance = (duration / 2) * 0.0343  # Konversi ke cm
    return round(distance, 2)

# ==== Fungsi Membaca DHT11 ====
def read_dht11():
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()  # Suhu dalam °C
        hum = dht_sensor.humidity()  # Kelembaban dalam %
        return temp, hum
    except Exception as e:
        return None, None

# ==== Fungsi Membaca MQ-2 (Gas CO2) ====
def read_mq2():
    try:
        raw_value = mq2_sensor.read()  # Baca nilai analog (0 - 4095)
        voltage = (raw_value / 4095) * 3.3  # Konversi ke Volt
        co2_ppm = (raw_value / 4095) * 1000  # Perkiraan kasar
        return raw_value, round(voltage, 2), round(co2_ppm, 2)
    except Exception as e:
        return None, None, None

# ==== Kirim Data ke Ubidots ====
def send_to_ubidots(temp, hum, co2, distance):
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    payload = {
        "temperature": temp,
        "humidity": hum,
        "co2": co2,
        "distance": distance
    }

    try:
        response = urequests.post(UBIDOTS_URL, json=payload, headers=headers)
        response.close()
        return True
    except Exception as e:
        return False

# ==== Looping untuk Kirim Data ====
connect_wifi()

while True:
    # Baca sensor
    suhu, kelembaban = read_dht11()
    adc_value, tegangan, co2 = read_mq2()
    jarak = read_ultrasonic()

    # Print hasil pembacaan sensor
    print("=====================================")
    print("📊 Hasil Pembacaan Sensor:")

    # Cek Sensor DHT11
    print("🌡️ Sensor DHT11:")
    if suhu is None or kelembaban is None:
        print("❌ Gagal membaca data DHT11!")
    else:
        print(f"   🔥 Suhu: {suhu}°C")
        print(f"   💧 Kelembaban: {kelembaban}%")

    # Cek Sensor MQ-2
    print("\n🛢️ Sensor MQ-2:")
    if adc_value is None:
        print("❌ Gagal membaca MQ-2!")
    else:
        print(f"   🔢 Nilai ADC: {adc_value}")
        print(f"   ⚡ Tegangan: {tegangan} V")
        print(f"   🌿 CO₂ PPM: {co2} ppm")
        if co2 > 800:
            print("   ⚠️ Kadar gas tinggi!")
        else:
            print("   ✅ Kadar gas dalam batas normal.")

    # Cek Sensor Ultrasonik
    print("\n📏 Sensor Ultrasonik:")
    if jarak is None:
        print("❌ Gagal membaca sensor jarak!")
    else:
        print(f"   📶 Jarak: {jarak} cm")

    # Kirim ke Ubidots jika data valid
    if suhu is not None and kelembaban is not None and co2 is not None and jarak is not None:
        status = send_to_ubidots(suhu, kelembaban, co2, jarak)
        print("\n📡 Status Upload ke Ubidots:")
        if status:
            print("✅ Data berhasil dikirim!")
        else:
            print("❌ Gagal mengirim data!")
    else:
        print("\n❌ Data tidak lengkap, tidak dikirim ke Ubidots.")

    print("=====================================")
    time.sleep(10)  # Kirim data setiap 10 detik
