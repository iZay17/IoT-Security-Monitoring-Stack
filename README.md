# IoT Security Monitoring Stack

A containerized IoT security lab that monitors MQTT traffic with **Suricata IDS**, ships alerts through **Filebeat** into **Elasticsearch/Kibana**, and hardens the broker with **mutual TLS**. Built for CYT160 (IoT Security) in Seneca Polytechnic's Cybersecurity and Threat Management program, 2026.

## Architecture

```
Raspberry Pi (TLS client) ──8883/mTLS──┐
Test publishers ────────────1883───────┤
                                       ▼
                         ┌────────────────────────┐
                         │ Mosquitto MQTT broker  │  (AWS EC2, Docker)
                         │   Suricata IDS  ◄──────┤  shares broker's network namespace
                         └───────────┬────────────┘
                                     │ eve.json
                                     ▼
                              Filebeat → Elasticsearch → Kibana dashboards
```

| Component | Role |
|---|---|
| **Mosquitto 2** | MQTT broker with two listeners: 1883 (plaintext, lab baseline) and 8883 (TLS 1.2, client certificates required) |
| **Suricata** | Runs in the broker's network namespace and inspects all MQTT traffic against custom rules |
| **Filebeat 8.11** | Ships Suricata `eve.json` events to Elasticsearch |
| **Kibana** | Three dashboards for sensor data, security alerts and pipeline health |

## What's in this repo

| Path | Contents |
|---|---|
| `docker-compose.yml` | Full stack definition (broker, IDS, log shipper) |
| `suricata/rules/local.rules` | Custom detection rules for malicious MQTT payloads |
| `mosquitto/config/mosquitto.conf` | Broker hardening: mTLS listener, anonymous access disabled, certificate identity as username |
| `iot-lab5/mqtt_publish_tls.py` | Python (paho-mqtt) client that publishes sensor data from a Raspberry Pi over mutual TLS |
| `filebeat/filebeat.yml` | Suricata → Elasticsearch pipeline config |
| `kibana-dashboards.ndjson` | Exported Kibana dashboards and index patterns |
| `project2_alerts.json` | Sample Suricata alerts captured during attack simulation |
| `lab5_answers.md` | Analysis: plaintext vs. TLS packet captures and what the IDS can still see |

## Detection rules

```
alert tcp any any -> any 1883 (msg:"MQTT Malformed Payload - Too long"; content:"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"; depth:100; sid:1000001; rev:1;)
alert tcp any any -> any 1883 (msg:"MQTT Suspicious Payload - Shell pattern"; content:"rm -rf"; sid:1000002; rev:1;)
```

- **sid 1000001** flags oversized, repeated-byte payloads typical of buffer-overflow and fuzzing attempts against IoT devices.
- **sid 1000002** flags shell-command injection (`rm -rf`) inside MQTT messages.

During the attack simulation, the stack produced **8 alerts** (6 malformed-payload, 2 shell-pattern). They're in `project2_alerts.json` and shown on the Security Threat Overview dashboard.

## Broker hardening (mutual TLS)

The 8883 listener requires every client to present a certificate signed by the lab CA (`require_certificate true`). Unauthenticated clients are rejected at the TLS handshake before any MQTT data is exchanged, which effectively gives the broker a cryptographic allowlist of devices.

Comparing packet captures (`tcpdump`) of the two listeners:
- **Plaintext (1883):** topic names, sensor values and client IDs are all readable, which is enough to spoof a device or inject false readings.
- **TLS (8883):** an observer sees only IPs, ports and handshake metadata.

Suricata can't decrypt the 8883 traffic, but it still sees flow metadata, connection rates and TLS handshake parameters. That supports detecting beaconing, scanning, or weak cipher suites without breaking encryption. Full write-up in [`lab5_answers.md`](lab5_answers.md).

## Kibana dashboards

1. **IoT Temperature Data**: sensor telemetry arriving through the broker
2. **Security Threat Overview**: Suricata alerts by signature, source and time
3. **System Health and Pipeline Activity**: event throughput across the Filebeat → Elasticsearch pipeline

Import them via *Stack Management → Saved Objects → Import* using `kibana-dashboards.ndjson`.

## Running it

```bash
# 1. Generate a CA plus broker/client certificates into ./certs (git-ignored)
# 2. Start Elasticsearch + Kibana on the host (port 9200)
docker compose up -d
# 3. Publish test data
python3 iot-lab5/mqtt_publish_tls.py
```

Set `BROKER` and the certificate paths in `mqtt_publish_tls.py` for your environment. Private keys and certificates are intentionally excluded from the repo.

## Skills demonstrated

IDS rule writing · network security monitoring · SIEM pipelines (ELK) · TLS/PKI and certificate-based authentication · Docker · AWS EC2 · Raspberry Pi · MQTT/IoT protocol analysis · packet capture analysis
