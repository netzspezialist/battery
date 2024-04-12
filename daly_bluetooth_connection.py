import config
from daly_bms_bluetooth import DalyBMSBluetooth
from bluetooth_auto_recovery import recover_adapter

class DalyBluetoothConnection:

    def __init__(self, logger=None):
        request_retries = config.bms["request_retries"]
        self.bt_bms = DalyBMSBluetooth(request_retries,logger)
        self.mac_address = config.bms["mac_address"]
        self.request_delay = config.bms["request_delay"]

    async def get_cell_voltage_range(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_cell_voltage_range()

    async def get_status(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_status()

    async def get_soc(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_soc()

    async def get_mosfet(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_mosfet_status()

    async def get_temps(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_max_min_temperature()

    async def get_bal(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_balancing_status()

    async def get_errors(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_errors()
    
    async def get_cell_voltages(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_cell_voltages()

    async def get_all(self):
        if not self.bt_bms.is_connected:
           await self.bt_bms.connect(mac_address=self.mac_address)
        return await self.bt_bms.get_all()

    async def disconnect(self):
        if self.bt_bms.is_connected:
            await self.bt_bms.disconnect()

    async def recover_bluetooth(self):
        await recover_adapter(0, self.mac_address)