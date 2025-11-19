import logging

import aiocoap

from aiocoap.resource import Resource

from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.ActuatorData import ActuatorData

class AsyncUpdateActuatorResourceHandler(Resource):
	"""
	Standard resource that will handle an incoming actuation command,
	and return the command response.
	"""

	def __init__(self, dataMsgListener: IDataMessageListener = None):
		super().__init__()
		self.dataMsgListener = dataMsgListener
		self.dataUtil = DataUtil()
		
	async def render_put(self, request):
		try:
			responseCode = aiocoap.Code.NOT_ACCEPTABLE
			 
			# TODO: validate the request!
			# Check payload
			# Check content-type (should be JSON)
			actuatorCmdData = self.dataUtil.jsonToActuatorData(request.payload)
			
			logging.info('Handling PUT request: ' + str(actuatorCmdData))
			
			return self._createResponse(actuatorCmdData)
			
		except:
			logging.warning("Failed to validate and convert actuation command.")
			
		return aiocoap.Message(code = responseCode)
	
	def _createResponse(self, data: ActuatorData = None):
		responseCode = aiocoap.Code.CHANGED 
		
		actuatorResponseData = self.dataMsgListener.handleActuatorCommandMessage(data)
		
		# TODO: validate the data and convert to JSON
		
		# return a Message instance
		jsonData = self.dataUtil.actuatorDataToJson(actuatorResponseData)
		return aiocoap.Message(code = responseCode, payload = jsonData.encode('ascii'))
