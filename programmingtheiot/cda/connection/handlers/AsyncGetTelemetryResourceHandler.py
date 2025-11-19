
import logging

import aiocoap

from aiocoap.resource import ObservableResource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener 
from programmingtheiot.common.ITelemetryDataListener import ITelemetryDataListener

from programmingtheiot.data.DataUtil import DataUtil

from programmingtheiot.data.SensorData import SensorData

class AsyncGetTelemetryResourceHandler(ObservableResource, ITelemetryDataListener):
	def __init__(self):
		super().__init__()
		
		self.pollCycles = \
			ConfigUtil().getInteger( \
				section = ConfigConst.CONSTRAINED_DEVICE, \
				key = ConfigConst.POLL_CYCLES_KEY, \
				defaultVal = ConfigConst.DEFAULT_POLL_CYCLES)
		
		self.dataUtil = DataUtil()
		self.sensorData = None
		
		# for testing
		self.payload = "GetSensorData"
		
	async def render_get(self, request):
		responseCode = aiocoap.Code.CONTENT
		
		if not self.sensorData:
			self.sensorData = SensorData()
			responseCode = aiocoap.Code.CONTENT
			
		jsonData = self.dataUtil.sensorDataToJson(self.sensorData)
		
		logging.info('Returning latest SensorData: ' + jsonData)
		
		return aiocoap.Message(code = responseCode, payload = jsonData.encode('ascii'))

	def onSensorDataUpdate(self, data: SensorData = None) -> bool:
		pass









