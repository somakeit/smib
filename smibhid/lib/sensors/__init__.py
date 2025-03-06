from asyncio import create_task, sleep
from machine import I2C
from config import SENSOR_MODULES, SDA_PIN, SCL_PIN, I2C_ID
from lib.ulogging import uLogger
from lib.sensors.SGP30 import SGP30
from lib.sensors.sensor_module import SensorModule

class Sensors:
    def __init__(self) -> None:
        self.log = uLogger("Sensors")
        self.i2c = I2C(I2C_ID, sda = SDA_PIN, scl = SCL_PIN, freq = 400000) # TODO: load from HID for here and display
        self.SENSOR_MODULES = SENSOR_MODULES
        self.available_modules: dict[str, SensorModule] = {}
        self.available_modules["SGP30"] = SGP30(self.i2c)
        self.configured_modules: dict[str, SensorModule] = {}
        self._load_modules()   

    def _load_modules(self) -> None:
        self.log.info(f"Attempting to locate drivers for: {self.SENSOR_MODULES}")
        for sensor_module in self.SENSOR_MODULES:
            if sensor_module in self.available_modules:
                self.log.info(f"Found driver for {sensor_module}")
                self.configured_modules[sensor_module] = self.available_modules[sensor_module]
                self.log.info(f"Loaded {sensor_module} sensor module")
                self.log.info(f"Available sensors: {self.configured_modules[sensor_module].get_sensors()}")
            else:
                self.log.error(f"Driver not found for {sensor_module}")

        self.log.info(f"Configured modules: {self.get_modules()}")

    def startup(self) -> None:
        self.log.info(f"Starting sensors: {self.configured_modules}")
        create_task(self._poll_sensors())

    async def _poll_sensors(self) -> None:
        """
        Asynchronously poll sensors and log readings every X seconds as per
        config.
        """
        while True:
            readings = self.get_readings()
            for reading in readings:
                self.log.info(f"Module: {reading}: {readings[reading]}")
            await sleep(5)
    
    def get_modules(self) -> list:
        """
        Return a dictionary of configured sensor modules.
        """
        return list(self.configured_modules.keys())

    def get_sensors(self, module: SensorModule) -> list:
        """
        Return list of sensors for a specific module.
        """
        return module.get_sensors()

    def get_readings(self, module: str = "") -> dict:
        """
        Return readings from a specific module by passing it's name as a
        string, or all modules if none specified.
        """
        readings = {}
        if module:
            readings[module] = self.configured_modules[module].get_reading()
        else:
            for name, instance in self.configured_modules.items():
                readings[name] = instance.get_reading()
        return readings
