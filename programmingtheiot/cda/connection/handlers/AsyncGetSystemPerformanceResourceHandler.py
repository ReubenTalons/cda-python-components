

import logging

import aiocoap

from aiocoap.resource import ObservableResource

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener 
from programmingtheiot.common.ITelemetryDataListener import ITelemetryDataListener

from programmingtheiot.data.DataUtil import DataUtil

from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData

class AsyncGetSystemPerformanceResourceHandler(ObservableResource, ISystemPerformanceDataListener):
	def __init__(self):
		super().__init__()

		self.pollCycles = \
			ConfigUtil().getInteger( \
				section = ConfigConst.CONSTRAINED_DEVICE, \
				key = ConfigConst.POLL_CYCLES_KEY, \
				defaultVal = ConfigConst.DEFAULT_POLL_CYCLES)
		
		self.dataUtil = DataUtil()
		self.sysPerfData = None
		
		# for testing
		self.payload = "GetSysPerfData"
		
	async def render_get(self, request):
		responseCode = aiocoap.Code.CONTENT
		
		if not self.sysPerfData:
			self.sysPerfData = SystemPerformanceData()
			responseCode = aiocoap.Code.CONTENT
			
		jsonData = self.dataUtil.systemPerformanceDataToJson(self.sysPerfData)
		
		logging.info('Returning latest SystemPerformanceData: ' + jsonData)
		
		return aiocoap.Message(code = responseCode, payload = jsonData.encode('ascii'))

	def onSystemPerformanceDataUpdate(self, data: SystemPerformanceData) -> bool:
		pass
