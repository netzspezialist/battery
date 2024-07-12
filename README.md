# battery

## description

## requirements
```
cd toProjectDir
python -m venv venv
source venv/bin/activate
pip install bleak
pip install serial
pip install bluetooth_auto_recovery
pip install influxdb_client
python service_host.py

```

## install and start battery service for monitoring
```
sudo cp battery.service /etc/systemd/system/battery.service
sudo systemctl daemon-reload
sudo systemctl enable battery.service
sudo systemctl start battery.service
```