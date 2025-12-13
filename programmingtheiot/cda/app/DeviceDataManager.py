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

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.cda.connection.CoapClientConnector import CoapClientConnector
from programmingtheiot.cda.connection.AsyncCoapClientConnector import AsyncCoapClientConnector
from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector
from programmingtheiot.cda.connection.AsyncCoapServerAdapter import AsyncCoapServerAdapter

from programmingtheiot.cda.system.ActuatorAdapterManager import ActuatorAdapterManager
from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.cda.system.SystemPerformanceManager import SystemPerformanceManager

from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData
from programmingtheiot.data.DataUtil import DataUtil

class DeviceDataManager(IDataMessageListener):
	"""
	Shell representation of class for student implementation.
	
	LAB MODULE 12: Enhanced with adaptive threshold management for intelligent HVAC control.
	"""
	
	def __init__(self):
		self.configUtil = ConfigUtil()
		
		self.enableSystemPerf = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SYSTEM_PERF_KEY)
			
		self.enableSensing = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_SENSING_KEY)
		
		# NOTE: this can also be retrieved from the configuration file
		self.enableActuation = True
		
		# NEW: Enable MQTT client based on configuration
		self.enableMqttClient = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_MQTT_CLIENT_KEY)

		# NEW: Enable CoAP server based on configuration
		self.enableCoapServer = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_COAP_SERVER_KEY)
		
		# NEW: Enable CoAP client based on configuration
		self.enableCoapClient = \
			self.configUtil.getBoolean( \
				section = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_COAP_CLIENT_KEY)
		
		self.sysPerfMgr = None
		self.sensorAdapterMgr = None
		self.actuatorAdapterMgr = None
		
		# NOTE: The following aren't used until Part III but should be declared now
		self.mqttClient = None
		self.coapClient = None
		self.coapServer = None
		
		# NEW: Initialize MQTT client if enabled
		if self.enableMqttClient:
			self.mqttClient = MqttClientConnector()
			self.mqttClient.setDataMessageListener(self)
			logging.info("MQTT client enabled and initialized")

		# NEW: Initialize CoAP server if enabled
		if self.enableCoapServer:
			self.coapServer = AsyncCoapServerAdapter(dataMsgListener = self)
			logging.info("Async CoAP server enabled and initialized")
		
		# NEW: Initialize CoAP client if enabled (using async version)
		if self.enableCoapClient:
			self.coapClient = AsyncCoapClientConnector(dataMsgListener = self)
			logging.info("Async CoAP client enabled and initialized")
		
		# Initialize caches for data
		self.actuatorResponseCache = {}
		self.sensorDataCache = {}
		self.sysPerfDataCache = {}
		
		if self.enableSystemPerf:
			self.sysPerfMgr = SystemPerformanceManager()
			self.sysPerfMgr.setDataMessageListener(self)
			logging.info("Local system performance tracking enabled")
		
		if self.enableSensing:
			self.sensorAdapterMgr = SensorAdapterManager()
			self.sensorAdapterMgr.setDataMessageListener(self)
			logging.info("Local sensor tracking enabled")
			
		if self.enableActuation:
			self.actuatorAdapterMgr = ActuatorAdapterManager(dataMsgListener = self)
			logging.info("Local actuation capabilities enabled")
		
		self.handleTempChangeOnDevice = \
			self.configUtil.getBoolean( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.HANDLE_TEMP_CHANGE_ON_DEVICE_KEY)
			
		self.triggerHvacTempFloor = \
			self.configUtil.getFloat( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_FLOOR_KEY)
				
		self.triggerHvacTempCeiling = \
			self.configUtil.getFloat( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.TRIGGER_HVAC_TEMP_CEILING_KEY)
		
		# LAB MODULE 12: Track threshold update count
		self.thresholdUpdateCount = 0
		
		logging.info(f"Initial HVAC thresholds: Floor={self.triggerHvacTempFloor}°C, Ceiling={self.triggerHvacTempCeiling}°C")
		
	def getLatestActuatorDataResponseFromCache(self, name: str = None) -> ActuatorData:
		"""
		Retrieves the named actuator data (response) item from the internal data cache.
		
		@param name
		@return ActuatorData
		"""
		if name in self.actuatorResponseCache:
			return self.actuatorResponseCache[name]
		return None
		
	def getLatestSensorDataFromCache(self, name: str = None) -> SensorData:
		"""
		Retrieves the named sensor data item from the internal data cache.
		
		@param name
		@return SensorData
		"""
		if name in self.sensorDataCache:
			return self.sensorDataCache[name]
		return None
	
	def getLatestSystemPerformanceDataFromCache(self, name: str = None) -> SystemPerformanceData:
		"""
		Retrieves the named system performance data from the internal data cache.
		
		@param name
		@return SystemPerformanceData
		"""
		if name in self.sysPerfDataCache:
			return self.sysPerfDataCache[name]
		return None
	
	def handleActuatorCommandMessage(self, data: ActuatorData) -> ActuatorData:
		"""
		This callback method will be invoked by the connection that's handling
		an incoming ActuatorData command message.
		
		LAB MODULE 12: Enhanced to detect and process threshold update commands from GDA.
		
		@param data The incoming ActuatorData command message.
		@return ActuatorData
		"""
		logging.info("Actuator data: " + str(data))
		
		if data:
			# LAB MODULE 12: Check if this is a threshold update command from GDA
			if data.getName() and "THRESHOLDS" in data.getName():
				logging.warning("🔧 THRESHOLD UPDATE COMMAND RECEIVED FROM GDA!")
				self._handleThresholdUpdate(data)
				
				# Create response indicating threshold update was processed
				responseData = ActuatorData(typeID=ConfigConst.HVAC_ACTUATOR_TYPE)
				responseData.setName("ThresholdUpdateResponse")
				responseData.setCommand(ConfigConst.COMMAND_OFF)
				responseData.setAsResponse()
				return responseData
			else:
				# Normal actuator command processing
				logging.info("Processing actuator command message.")
				return self.actuatorAdapterMgr.sendActuatorCommand(data)
		else:
			logging.warning("Incoming actuator command is invalid (null). Ignoring.")
			return None
	
	def handleActuatorCommandResponse(self, data: ActuatorData) -> bool:
		"""
		This callback method will be invoked by the actuator manager that just
		processed an ActuatorData command, which creates a new ActuatorData
		instance and sets it as a response before calling this method.
		
		@param data The incoming ActuatorData response message.
		@return boolean
		"""
		if data:
			logging.debug("Incoming actuator response received (from actuator manager): " + str(data))
			
			# store the data in the cache
			self.actuatorResponseCache[data.getName()] = data
			
			# convert ActuatorData to JSON and get the msg resource
			actuatorMsg = DataUtil().actuatorDataToJson(data)
			resourceName = ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE
			
			# delegate to the transmit function any potential upstream comm's
			self._handleUpstreamTransmission(resource = resourceName, msg = actuatorMsg)
			
			return True
		else:
			logging.warning("Incoming actuator response is invalid (null). Ignoring.")
			
			return False
	
	def handleIncomingMessage(self, resourceEnum: ResourceNameEnum, msg: str) -> bool:
		"""
		This callback method is generic and designed to handle any incoming string-based
		message, which will likely be JSON-formatted and need to be converted to the appropriate
		data type. You may not need to use this callback at all.
		
		@param data The incoming JSON message.
		@return boolean
		"""
		logging.info("Handling incoming message: " + str(msg))
		self._handleIncomingDataAnalysis(msg)
		return True
	
	def handleSensorMessage(self, data: SensorData) -> bool:
		"""
		This callback method will be invoked by the sensor manager that just processed
		a new sensor reading, which creates a new SensorData instance that will be
		passed to this method.
		
		@param data The incoming SensorData message.
		@return boolean
		"""
		if data:
			logging.debug("Incoming sensor data received (from sensor manager): " + str(data))
			
			# store in cache
			self.sensorDataCache[data.getName()] = data
			# Publish sensor data to MQTT broker (Ubidots)
			if self.mqttClient:
				topic = f"/v1.6/devices/constraineddevice001/{data.getName().lower()}"
				payload = f'{{"value": {data.getValue()}}}'
				self.mqttClient.publishMessage(resource=None, msg=payload, qos=0, topic=topic)
				logging.debug(f"Published sensor data to topic: {topic}")

			
			self._handleSensorDataAnalysis(data = data)
			return True
		else:
			logging.warning("Incoming sensor data is invalid (null). Ignoring.")
			return False
	
	def handleSystemPerformanceMessage(self, data: SystemPerformanceData) -> bool:
		"""
		This callback method will be invoked by the system performance manager that just
		processed a new sensor reading, which creates a new SystemPerformanceData instance
		that will be passed to this method.
		
		@param data The incoming SystemPerformanceData message.
		@return boolean
		"""
		if data:
			logging.debug("Incoming system performance message received (from sys perf manager): " + str(data))
			
			# store in cache
			self.sysPerfDataCache[data.getName()] = data
			# Publish system performance data to MQTT broker (Ubidots)
			if self.mqttClient:
				topic = "/v1.6/devices/constraineddevice001/systemperfmsg"
				payload = f'{{"cpuutil": {data.getCpuUtilization()}, "memutil": {data.getMemoryUtilization()}}}'
				self.mqttClient.publishMessage(resource=None, msg=payload, qos=0)
				logging.debug(f"Published system performance to topic: {topic}")

			
			return True
		else:
			logging.warning("Incoming system performance data is invalid (null). Ignoring.")
			return False
	
	def setSystemPerformanceDataListener(self, listener = None):
		pass
			
	def setTelemetryDataListener(self, name: str = None, listener = None):
		pass
			
	def startManager(self):
		logging.info("Starting DeviceDataManager...")
		
		# NEW: Connect MQTT client
		# Subscription now handled automatically in MqttClientConnector.onConnect()
		if self.mqttClient:
			self.mqttClient.connectClient()
			# self.mqttClient.subscribeToTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, callback = None, qos = ConfigConst.DEFAULT_QOS)

		# NEW: Start CoAP server
		if self.coapServer:
			self.coapServer.startServer()
		
		if self.sysPerfMgr:
			self.sysPerfMgr.startManager()
		
		if self.sensorAdapterMgr:
			self.sensorAdapterMgr.startManager()
			
		logging.info("Started DeviceDataManager.")
		
	def stopManager(self):
		logging.info("Stopping DeviceDataManager...")
		
		# NEW: Unsubscribe and disconnect MQTT client
		if self.mqttClient:
			self.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
			self.mqttClient.disconnectClient()

		# NEW: Stop CoAP server
		if self.coapServer:
			self.coapServer.stopServer()
		
		if self.sysPerfMgr:
			self.sysPerfMgr.stopManager()
		
		if self.sensorAdapterMgr:	
			self.sensorAdapterMgr.stopManager()
			
		logging.info("Stopped DeviceDataManager.")
		
	def _handleIncomingDataAnalysis(self, msg: str):
		"""
		Call this from handleIncomeMessage() to determine if there's
		any action to take on the message. Steps to take:
		1) Validate msg: Most will be ActuatorData, but you may pass other info as well.
		2) Convert msg: Use DataUtil to convert if appropriate.
		3) Act on msg: Determine what - if any - action is required, and execute.
		"""
		logging.info("Analyzing incoming data message...")
		# For now, basic implementation - will be expanded in later modules
		pass
		
	def _handleSensorDataAnalysis(self, data: SensorData):
		"""
		Call this from handleSensorMessage() to determine if there's
		any action to take on the message. Steps to take:
		1) Check config: Is there a rule or flag that requires immediate processing of data?
		2) Act on data: If # 1 is true, determine what - if any - action is required, and execute.
		"""
		if self.handleTempChangeOnDevice and data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
			logging.info("Handle temp change: %s - type ID: %s", str(self.handleTempChangeOnDevice), str(data.getTypeID()))
			logging.warning(f"🌡️  CURRENT TEMP: {data.getValue():.2f}°C | Floor: {self.triggerHvacTempFloor:.2f}°C | Ceiling: {self.triggerHvacTempCeiling:.2f}°C")
			
			ad = ActuatorData(typeID = ConfigConst.HVAC_ACTUATOR_TYPE)
			ad.setLocationID(data.getLocationID())
			
			hvac_status = 0  # 0=OFF, 1=HEATING, 2=COOLING
			status_message = "COMFORT ZONE"
			
			if data.getValue() > self.triggerHvacTempCeiling:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setValue(self.triggerHvacTempCeiling)
				hvac_status = 2
				status_message = "COOLING ACTIVE"
			elif data.getValue() < self.triggerHvacTempFloor:
				ad.setCommand(ConfigConst.COMMAND_ON)
				ad.setValue(self.triggerHvacTempFloor)
				hvac_status = 1
				status_message = "HEATING ACTIVE"
			else:
				ad.setCommand(ConfigConst.COMMAND_OFF)
				hvac_status = 0
				status_message = "COMFORT ZONE"
			
			# Publish HVAC status to dashboard
			if self.mqttClient:
				status_topic = "/v1.6/devices/constraineddevice001/hvac_status"
				status_payload = f'{{"value": {hvac_status}, "context": {{"status": "{status_message}"}}}}'
				self.mqttClient.publishMessage(resource=None, msg=status_payload, qos=0, topic=status_topic)
				logging.info(f"📊 Published HVAC Status: {status_message} (value={hvac_status})")
			
			self.handleActuatorCommandMessage(ad)
	
	def _handleThresholdUpdate(self, data: ActuatorData):
		"""
		LAB MODULE 12: Handles adaptive threshold updates.
		
		Supports two formats:
		1. Full update: "HvacActuator-THRESHOLDS-FLOOR=XX.XX-CEILING=YY.YY"
		2. Manual single: "HvacActuator-MANUAL-FLOOR=XX.XX" or "HvacActuator-MANUAL-CEILING=XX.XX"
		
		@param data The ActuatorData containing threshold update information
		"""
		try:
			name = data.getName()
			logging.info(f"Parsing threshold update from: {name}")
			
			# Check if this is a manual single-value update
			if "MANUAL-FLOOR=" in name:
				# Extract just the floor value
				floor_start = name.index("MANUAL-FLOOR=") + 13
				new_floor = float(name[floor_start:])
				new_ceiling = self.triggerHvacTempCeiling  # Keep existing ceiling
				
				old_floor = self.triggerHvacTempFloor
				self.triggerHvacTempFloor = new_floor
				self.thresholdUpdateCount += 1
				
				logging.warning("=" * 70)
				logging.warning("✅ MANUAL THRESHOLD UPDATE - FLOOR")
				logging.warning(f"  Update #{self.thresholdUpdateCount}")
				logging.warning(f"  OLD Floor: {old_floor:.2f}°C")
				logging.warning(f"  NEW Floor: {new_floor:.2f}°C")
				logging.warning(f"  Ceiling unchanged: {new_ceiling:.2f}°C")
				logging.warning("=" * 70)
				
				# Publish event
				self._publishThresholdEvent(
					event_type="MANUAL_FLOOR_ADJUSTMENT",
					floor_temp=new_floor,
					ceiling_temp=new_ceiling,
					reason=f"Manual update #{self.thresholdUpdateCount}"
				)
				return
				
			elif "MANUAL-CEILING=" in name:
				# Extract just the ceiling value
				ceiling_start = name.index("MANUAL-CEILING=") + 15
				new_ceiling = float(name[ceiling_start:])
				new_floor = self.triggerHvacTempFloor  # Keep existing floor
				
				old_ceiling = self.triggerHvacTempCeiling
				self.triggerHvacTempCeiling = new_ceiling
				self.thresholdUpdateCount += 1
				
				logging.warning("=" * 70)
				logging.warning("✅ MANUAL THRESHOLD UPDATE - CEILING")
				logging.warning(f"  Update #{self.thresholdUpdateCount}")
				logging.warning(f"  OLD Ceiling: {old_ceiling:.2f}°C")
				logging.warning(f"  NEW Ceiling: {new_ceiling:.2f}°C")
				logging.warning(f"  Floor unchanged: {new_floor:.2f}°C")
				logging.warning("=" * 70)
				
				# Publish event
				self._publishThresholdEvent(
					event_type="MANUAL_CEILING_ADJUSTMENT",
					floor_temp=new_floor,
					ceiling_temp=new_ceiling,
					reason=f"Manual update #{self.thresholdUpdateCount}"
				)
				return
			
			# Original full format: FLOOR=XX-CEILING=YY
			if "FLOOR=" in name:
				floor_start = name.index("FLOOR=") + 6
				floor_end = name.index("-CEILING")
				new_floor = float(name[floor_start:floor_end])
				
				# Extract CEILING value  
				ceiling_start = name.index("CEILING=") + 8
				new_ceiling = float(name[ceiling_start:])
				
				# Update thresholds
				old_floor = self.triggerHvacTempFloor
				old_ceiling = self.triggerHvacTempCeiling
				
				self.triggerHvacTempFloor = new_floor
				self.triggerHvacTempCeiling = new_ceiling
				self.thresholdUpdateCount += 1
				
				logging.warning("=" * 70)
				logging.warning("✅ ADAPTIVE THRESHOLDS UPDATED!")
				logging.warning(f"  Update #{self.thresholdUpdateCount}")
				logging.warning(f"  OLD: Floor={old_floor:.2f}°C, Ceiling={old_ceiling:.2f}°C")
				logging.warning(f"  NEW: Floor={new_floor:.2f}°C, Ceiling={new_ceiling:.2f}°C")
				logging.warning("  System will now use updated thresholds for HVAC control")
				logging.warning("=" * 70)
				
				# Publish threshold change event to Ubidots dashboard
				self._publishThresholdEvent(
					event_type="THRESHOLD_ADJUSTED",
					floor_temp=new_floor,
					ceiling_temp=new_ceiling,
					reason=f"Update #{self.thresholdUpdateCount}"
				)
				
		except Exception as e:
			logging.error(f"❌ Failed to parse threshold update: {e}")
			logging.error(f"Actuator data name: {data.getName()}")
		

	def _publishThresholdEvent(self, event_type: str, floor_temp: float, ceiling_temp: float, reason: str = ""):
		"""
		Publish threshold change events to Ubidots for dashboard visualization.
		Publishes floor and ceiling as separate variables for better dashboard display.
		"""
		if self.mqttClient:
			try:
				# Publish floor threshold
				floor_topic = "/v1.6/devices/constraineddevice001/threshold_floor"
				floor_payload = f'{{"value": {floor_temp}}}'
				self.mqttClient.publishMessage(resource=None, msg=floor_payload, qos=0, topic=floor_topic)
				
				# Publish ceiling threshold
				ceiling_topic = "/v1.6/devices/constraineddevice001/threshold_ceiling"
				ceiling_payload = f'{{"value": {ceiling_temp}}}'
				self.mqttClient.publishMessage(resource=None, msg=ceiling_payload, qos=0, topic=ceiling_topic)
				
				# Publish event log with context
				event_topic = "/v1.6/devices/constraineddevice001/threshold_events"
				event_message = f"{event_type}: Floor={floor_temp}°C, Ceiling={ceiling_temp}°C"
				if reason:
					event_message += f" ({reason})"
				event_payload = f'{{"value": 1, "context": {{"message": "{event_message}"}}}}'
				self.mqttClient.publishMessage(resource=None, msg=event_payload, qos=0, topic=event_topic)
				
				logging.info(f"Published threshold update: Floor={floor_temp}°C, Ceiling={ceiling_temp}°C")
			except Exception as e:
				logging.error(f"Failed to publish threshold event: {e}")

	def _handleUpstreamTransmission(self, resource: ResourceNameEnum = None, msg: str = None):
		"""
		Call this from handleActuatorCommandResponse(), handlesensorMessage(), and handleSystemPerformanceMessage()
		to determine if the message should be sent upstream. Steps to take:
		1) Check connection: Is there a client connection configured (and valid) to a remote MQTT or CoAP server?
		2) Act on msg: If # 1 is true, send message upstream using one (or both) client connections.
		"""
		logging.info("Upstream transmission invoked for resource: " + str(resource))
		
		# Publish actuator responses to Ubidots
		if resource == ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE and self.mqttClient:
			try:
				import json
				data_dict = json.loads(msg)
				actuator_name = data_dict.get('name', 'unknown').lower()
				actuator_value = data_dict.get('value', 0)
				actuator_command = data_dict.get('command', 0)
				
				topic = f"/v1.6/devices/constraineddevice001/{actuator_name}"
				payload = f'{{"value": {actuator_value}, "command": {actuator_command}}}'
				self.mqttClient.publishMessage(resource=None, msg=payload, qos=0, topic=topic)
				logging.debug(f"Published actuator response to topic: {topic}")
			except Exception as e:
				logging.error(f"Failed to publish actuator response: {e}")
