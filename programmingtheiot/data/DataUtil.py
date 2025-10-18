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

import json

from json import JSONEncoder

from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData

class DataUtil():
	"""
	Utility class for converting data objects to/from JSON.
	
	"""
	def __init__(self, encodeToUtf8 = False):
		self.encodeToUtf8 = encodeToUtf8
	
	def actuatorDataToJson(self, data: ActuatorData = None):
		"""
		Converts ActuatorData to JSON string.
		"""
		if data:
			jsonData = json.dumps(data, cls=JsonDataEncoder)
			return jsonData
		else:
			return None
	
	def sensorDataToJson(self, data: SensorData = None):
		"""
		Converts SensorData to JSON string.
		"""
		if data:
			jsonData = json.dumps(data, cls=JsonDataEncoder)
			return jsonData
		else:
			return None
	
	def systemPerformanceDataToJson(self, data: SystemPerformanceData = None):
		"""
		Converts SystemPerformanceData to JSON string.
		"""
		if data:
			jsonData = json.dumps(data, cls=JsonDataEncoder)
			return jsonData
		else:
			return None
	
	def jsonToActuatorData(self, jsonData: str = None):
		"""
		Converts JSON string to ActuatorData object.
		"""
		if jsonData:
			jsonStruct = json.loads(jsonData)
			data = ActuatorData()
			
			self._updateIotData(data, jsonStruct)
			
			# Preserve timestamp from JSON - MUST BE AFTER setValue/setCommand/setStateData!
			if 'timeStamp' in jsonStruct:
				data.timeStamp = jsonStruct['timeStamp']
			
			return data
		else:
			return None
	
	def jsonToSensorData(self, jsonData: str = None):
		"""
		Converts JSON string to SensorData object.
		"""
		if jsonData:
			jsonStruct = json.loads(jsonData)
			data = SensorData()
			
			self._updateIotData(data, jsonStruct)
			
			# Preserve timestamp from JSON - MUST BE AFTER setValue!
			if 'timeStamp' in jsonStruct:
				data.timeStamp = jsonStruct['timeStamp']
			
			return data
		else:
			return None
	
	def jsonToSystemPerformanceData(self, jsonData: str = None):
		"""
		Converts JSON string to SystemPerformanceData object.
		"""
		if jsonData:
			jsonStruct = json.loads(jsonData)
			data = SystemPerformanceData()
			
			self._updateIotData(data, jsonStruct)
			
			if 'cpuUtil' in jsonStruct:
				data.setCpuUtilization(jsonStruct['cpuUtil'])
			if 'memUtil' in jsonStruct:
				data.setMemoryUtilization(jsonStruct['memUtil'])
			
			# Preserve timestamp from JSON - MUST BE AFTER setCpuUtilization/setMemoryUtilization!
			if 'timeStamp' in jsonStruct:
				data.timeStamp = jsonStruct['timeStamp']
			
			return data
		else:
			return None
	
	def _updateIotData(self, data, jsonStruct):
		"""
		Helper method to update common IoT data fields from JSON.
		"""
		if 'name' in jsonStruct:
			data.setName(jsonStruct['name'])
		if 'typeID' in jsonStruct:
			data.setTypeID(jsonStruct['typeID'])
		if 'statusCode' in jsonStruct:
			data.setStatusCode(jsonStruct['statusCode'])
		if 'locationID' in jsonStruct:
			data.setLocationID(jsonStruct['locationID'])
		if 'latitude' in jsonStruct:
			data.setLatitude(jsonStruct['latitude'])
		if 'longitude' in jsonStruct:
			data.setLongitude(jsonStruct['longitude'])
		if 'elevation' in jsonStruct:
			data.setElevation(jsonStruct['elevation'])
		
		# For SensorData and ActuatorData
		if 'value' in jsonStruct:
			data.setValue(jsonStruct['value'])
		if 'command' in jsonStruct:
			data.setCommand(jsonStruct['command'])
		if 'stateData' in jsonStruct:
			data.setStateData(jsonStruct['stateData'])

class JsonDataEncoder(JSONEncoder):
	"""
	Convenience class to facilitate JSON encoding of an object that
	can be converted to a dict.
	
	"""
	def default(self, o):
		return o.__dict__