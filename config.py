influx = {
    "enabled": True,
    "url": "http://192.168.88.2:8086",
    "org": "org",
    "bucket": "energy",
    "token": '8NSTtcmBwEUUoOl5E3nhvoIOwIzZgNbUbOpdhN7UOMY452Y7srgClN5JZBerPSBBlelIR2Q6ZSukRqPg77GZOA==',
}
mqtt = { 
    "enabled": True,
    "broker_address": "localhost",
    "port": 1883,
    "client_id": "bms",
    "topic": "bms",
    "username": "user",
    "password": "password"
}
bms = {
    "mac_address": "17:71:06:05:08:C7",
    "request_delay": 1,
    "request_retries": 2
}
minimumRequestDelaySeconds = {
    "soc": 60,
    "cellVoltageRange": 60,
    "temperature": 120,
    "cellVoltages": 120,
    "errors": 120,
    "mosfet": 120,
    "cycles": 3600
}