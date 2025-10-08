#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 
# You may find it more helpful to your design to adjust the
# functionality, constants and interfaces (if there are any)
# provided within in order to meet the needs of your specific
# Programming the Internet of Things project.
# 

import logging

from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator

import programmingtheiot.common.ConfigConst as ConfigConst

try:
	import smbus
	i2cImported = True
except ImportError:
	i2cImported = False
	logging.warning("smbus library not available. TemperatureI2cSensorAdapterTask will not function.")

class TemperatureI2cSensorAdapterTask(BaseSensorSimTask):
	"""
	I2C-based temperature sensor adapter for Sense HAT hardware.
	"""
	
	def __init__(self):
		super(TemperatureI2cSensorAdapterTask, self).__init__(
			name = ConfigConst.TEMP_SENSOR_NAME,
			typeID = ConfigConst.TEMP_SENSOR_TYPE)
		
		# Temperature sensor I2C address for Sense HAT (same as humidity sensor)
		self.tempAddr = 0x5F
		
		if i2cImported:
			# Initialize I2C bus 1 (used by Sense HAT on Raspberry Pi)
			self.i2cBus = smbus.SMBus(1)
			self.i2cBus.write_byte_data(self.tempAddr, 0, 0)
		else:
			self.i2cBus = None
	
	def generateTelemetry(self) -> SensorData:
		sensorData = SensorData(name = self.getName(), typeID = self.getTypeID())
		
		if self.i2cBus:
			try:
				# Read temperature data from I2C sensor
				sensorVal = self.getTelemetryValue()
				sensorData.setValue(sensorVal)
			except Exception as e:
				logging.error("Failed to read temperature sensor via I2C: " + str(e))
				sensorData.setValue(0.0)
		else:
			logging.warning("I2C bus not available. Returning default value.")
			sensorData.setValue(0.0)
		
		self.latestSensorData = sensorData
		return sensorData
	
	def getTelemetryValue(self) -> float:
		if self.i2cBus:
			# Read from I2C registers - implementation depends on sensor datasheet
			return 22.0  # Default placeholder value (room temperature)
		return 0.0
