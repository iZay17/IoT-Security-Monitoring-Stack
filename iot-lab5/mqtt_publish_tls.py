import paho.mqtt.client as mqtt
import ssl, time, json

BROKER = 'YOUR_BROKER_IP'  # e.g. EC2 public IP
PORT = 8883
TOPIC = 'iot/lab/topic'
CA    = '/home/mypi/mqtt-certs/ca.crt'
CERT  = '/home/mypi/mqtt-certs/client.crt'
KEY   = '/home/mypi/mqtt-certs/client.key'

client = mqtt.Client(client_id='rpi-tls-client')
client.tls_set(ca_certs=CA, certfile=CERT, keyfile=KEY,
               tls_version=ssl.PROTOCOL_TLSv1_2)

client.connect(BROKER, PORT, 60)
for i in range(10):
    payload = json.dumps({"device": "rpi-tls-client", "temp": 20 + i * 0.5, "unit": "C"})
    client.publish(TOPIC, payload)
    print(f'Sent: {payload}')
    time.sleep(1)
client.disconnect()
