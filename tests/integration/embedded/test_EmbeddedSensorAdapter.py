#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 

import logging
import unittest

from time import sleep

from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.common.DefaultDataMessageListener import DefaultDataMessageListener

class EmbeddedSensorAdapterTest(unittest.TestCase):
	"""
	This test case class contains basic unit tests for
	SensorAdapterManager using I2C hardware sensors.
	
	NOTE: This test requires a physical Raspberry Pi with
	a Sense HAT attached via GPIO pins. It will NOT work
	in emulation or simulation mode, and will NOT work
	on a virtual machine or standard PC.
	
	REQUIREMENTS:
	- Raspberry Pi (3/4 or newer)
	- Sense HAT hardware attached to GPIO
	- smbus library installed
	- PiotConfig.props with enableSenseHAT = True
	"""
	
	@classmethod
	def setUpClass(self):
		logging.basicConfig(format = '%(asctime)s:%(module)s:%(levelname)s:%(message)s', level = logging.DEBUG)
		logging.info("Testing SensorAdapterManager class [using I2C hardware sensors]...")
		logging.warning("NOTE: This test requires physical Raspberry Pi + Sense HAT hardware!")
		
		self.defaultMsgListener = DefaultDataMessageListener()
		self.sensorAdapterMgr = SensorAdapterManager()
		self.sensorAdapterMgr.setDataMessageListener(self.defaultMsgListener)
		
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def testRunI2CSensors(self):
		"""
		Test I2C sensor reading from hardware.
		This will only work on a Raspberry Pi with Sense HAT.
		"""
		logging.info("Starting I2C sensor adapter manager...")
		
		self.sensorAdapterMgr.startManager()
		
		# Run for 60 seconds to collect sensor data
		sleep(60)
		
		self.sensorAdapterMgr.stopManager()
		
		logging.info("I2C sensor adapter manager stopped.")

if __name__ == "__main__":
	unittest.main()
