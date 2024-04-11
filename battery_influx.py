from config import influx as influxConfig

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

class BatteryInflux:
    def __init__(self, logger):        
        self.logger = logger

        self.enabled = influxConfig["enabled"]
        token = influxConfig["token"]
        org = influxConfig["org"]
        bucket = influxConfig["bucket"]
        url = influxConfig["url"]
        write_client = InfluxDBClient(url=url, token=token, org=org)

        self.org=org
        self.bucket=bucket
        self.write_api = write_client.write_api(write_options=SYNCHRONOUS)

    async def upload_soc(self, timestamp, soc, voltage, current):
        if self.enabled:
            self.logger.debug(f'InfluxDB upload soc {soc}, voltage {voltage}, current {current} at {timestamp}') 
            point = (
                Point("bms")
                .field("voltage", voltage)
                .field("soc", soc)
                .field("current", current)
                .time(int(timestamp.timestamp()), WritePrecision.S)
            )
           
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    async def upload_cell_voltage_range(self, timestamp, highest_voltage, highest_cell, lowest_voltage, lowest_cell):
        if self.enabled:
            self.logger.debug(f'InfluxDB upload cell voltage range: highest voltage {highest_voltage} at {highest_cell}, lowest voltage {lowest_voltage} at {lowest_voltage} at {timestamp}') 
            point = (
                Point("bms")
                .field("highestCellVoltage", highest_voltage)
                .field("lowestCellVoltage", lowest_voltage)
                .field("highestCellVoltageNumber", highest_cell)
                .field("lowestCellVoltageNumber", lowest_cell)
                .time(int(timestamp.timestamp()), WritePrecision.S)
            )
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    async def upload_temperature(self, timestamp, temperature):
        if self.enabled:
            self.logger.debug(f'InfluxDB upload temperature {temperature} at {timestamp}') 
            point = (
                Point("bms")
                .field("temperature", temperature)
                .time(int(timestamp.timestamp()), WritePrecision.S)
            )
            
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)

    async def upload_cell_voltages(self, timestamp, voltages):
        if self.enabled:
            self.logger.debug(f'InfluxDB upload cell voltages: {voltages} at {timestamp}') 
            point = (
                Point("bms")
                .field("cellVoltage01", voltages[0])
                .field("cellVoltage02", voltages[1])
                .field("cellVoltage03", voltages[2])
                .field("cellVoltage04", voltages[3])
                .field("cellVoltage05", voltages[4])
                .field("cellVoltage06", voltages[5])
                .field("cellVoltage07", voltages[6])
                .field("cellVoltage08", voltages[7])
                .field("cellVoltage09", voltages[8])
                .field("cellVoltage10", voltages[9])
                .field("cellVoltage11", voltages[10])
                .field("cellVoltage12", voltages[11])
                .field("cellVoltage13", voltages[12])
                .field("cellVoltage14", voltages[13])
                .field("cellVoltage15", voltages[14])
                .field("cellVoltage16", voltages[15])
                .time(int(timestamp.timestamp()), WritePrecision.S)
            )

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)