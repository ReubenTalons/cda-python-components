#####
# 
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
# 
# Copyright (c) 2020 - 2025 by Andrew D. King
# 

import logging
import unittest
import time

from programmingtheiot.cda.connection.CoapClientConnector import CoapClientConnector
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.SensorData import SensorData

class CoapClientPerformanceTest(unittest.TestCase):
	"""
	Performance test case class for CoapClientConnector.
	Tests CoAP POST request performance with CON and NON message types.
	"""
	
	NS_IN_MILLIS = 1000000
	
	# NOTE: Reduced to 100 for faster testing
	MAX_TEST_RUNS = 100
	
	@classmethod
	def setUpClass(cls):
		"""Disable most logging to focus on performance results"""
		logging.disable(level = logging.WARNING)
		
	def setUp(self):
		"""Initialize CoAP client before each test"""
		self.coapClient = CoapClientConnector()

	def tearDown(self):
		"""Cleanup after each test"""
		pass
					
	# @unittest.skip("Ignore for now.")
	def testPostRequestCon(self):
		"""Test POST with CON (Confirmable) messages"""
		print("Testing POST - CON")
		self._execTestPost(self.MAX_TEST_RUNS, True)

	# @unittest.skip("Ignore for now.")
	def testPostRequestNon(self):
		"""Test POST with NON (Non-confirmable) messages"""
		print("Testing POST - NON")
		self._execTestPost(self.MAX_TEST_RUNS, False)

	def _execTestPost(self, maxTestRuns: int, useCon: bool):
		"""
		Helper method to execute POST performance tests.
		
		@param maxTestRuns: Number of POST requests to send
		@param useCon: True for CON messages, False for NON messages
		"""
		sensorData = SensorData()
		payload = DataUtil().sensorDataToJson(sensorData)
		
		startTime = time.time_ns()
		
		for seqNo in range(0, maxTestRuns):
			self.coapClient.sendPostRequest(
				resource = ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, 
				enableCON = useCon, 
				payload = payload,
				timeout = 1  # 1 second timeout
			)
			
		endTime = time.time_ns()
		elapsedMillis = (endTime - startTime) / self.NS_IN_MILLIS
		
		print("POST message - useCON = " + str(useCon) + " [" + str(maxTestRuns) + "]: " + str(elapsedMillis) + " ms")

if __name__ == "__main__":
	unittest.main()