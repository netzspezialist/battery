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
    "client_id": "inverter",
    "topic": "inverter",
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
    "cellVoltageRange": 30,
    "temperature": 240,
    "cellVoltages": 120,
    "errors": 60,
    "mosfet": 60,
    "cycles": 3600
}