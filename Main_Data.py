from flask import Flask, request, jsonify
from pymongo import MongoClient
import datetime

app = Flask(__name__)

# Koneksi MongoDB 
MONGO_URI = "mongodb+srv://altalawilliam:testmongo11@clusterarunika.dcbuk.mongodb.net/?retryWrites=true&w=majority&appName=ClusterArunika"
client = MongoClient(MONGO_URI)
db = client["sensor_db"]  
collection = db["sensor_data"]

# Endpoint untuk menerima data dari ESP32
@app.route('/sensor', methods=['POST'])
def receive_sensor_data():
    data = request.json  
    
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Tambahkan timestamp
    data["timestamp"] = datetime.datetime.now()
    
    # Simpan ke MongoDB
    collection.insert_one(data)
    
    return jsonify({"message": "Data stored successfully", "data": data}), 201

@app.route('/sensor/latest', methods=['GET'])
def get_latest_sensor_data():
    latest_data = collection.find().sort("timestamp", -1).limit(1)  # Data terbaru
    result = list(latest_data)
    
    if not result:
        return jsonify({"error": "No data found"}), 404
    
    return jsonify(result[0]), 200

@app.route('/sensor/all', methods=['GET'])
def get_all_sensor_data():
    all_data = collection.find().sort("timestamp", -1)
    result = [{"temperature": d["temperature"], "humidity": d["humidity"], "co2": d["co2"], "distance": d["distance"], "timestamp": d["timestamp"]} for d in all_data]
    
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
