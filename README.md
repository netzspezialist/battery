# battery

## description

## requirements
```
pip3 install bluetooth_auto_recovery
```

## install and start battery service for monitoring
```
sudo cp battery.service /etc/systemd/system/battery.service
sudo systemctl daemon-reload
sudo systemctl enable battery.service
sudo systemctl start battery.service
```