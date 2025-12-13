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
import ssl
import paho.mqtt.client as mqttClient

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.data.DataUtil import DataUtil

from programmingtheiot.cda.connection.IPubSubClient import IPubSubClient

class MqttClientConnector(IPubSubClient):
	"""
	Shell representation of class for student implementation.
	
	"""
	
	def __init__(self, clientID: str = None):
		"""
		Default constructor. This will set remote broker information and client connection
		information based on the default configuration file contents.
		
		@param clientID Defaults to None. Can be set by caller. If this is used, it's
		critically important that a unique, non-conflicting name be used so to avoid
		causing the MQTT broker to disconnect any client using the same name. With
		auto-reconnect enabled, this can cause a race condition where each client with
		the same clientID continuously attempts to re-connect, causing the broker to
		disconnect the previous instance.
		"""
		self.config = ConfigUtil()
		self.dataMsgListener = None
		
		self.host = \
			self.config.getProperty( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)
		
		self.port = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_MQTT_PORT)
		
		self.keepAlive = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.KEEP_ALIVE_KEY, ConfigConst.DEFAULT_KEEP_ALIVE)
		
		self.defaultQos = \
			self.config.getInteger( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.DEFAULT_QOS_KEY, ConfigConst.DEFAULT_QOS)
		
		# TLS/Encryption configuration
		self.enableEncryption = \
			self.config.getBoolean( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.ENABLE_CRYPT_KEY)
		
		self.pemFileName = \
			self.config.getProperty( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.CERT_FILE_KEY)
		
		# Authentication configuration
		self.enableAuth = \
			self.config.getBoolean( \
				ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.ENABLE_AUTH_KEY)
		
		self.username = None
		self.password = None
		
		if self.enableAuth:
			# Load credentials from credential file
			credentials = self.config.getCredentials(ConfigConst.MQTT_GATEWAY_SERVICE)
			if credentials:
				self.username = credentials.get('username')
				self.password = credentials.get(ConfigConst.USER_NAME_TOKEN_KEY)
			
			if self.username and self.password:
				logging.info("MQTT authentication enabled")
			else:
				logging.warning("MQTT auth enabled but credentials not found")
		
		self.mqttClient = None
		
		if not clientID:
			# Use a unique client ID - modify this to your preference
			clientID = 'CDAMqttClientID001'
			
		self.clientID = \
			self.config.getProperty( \
				ConfigConst.CONSTRAINED_DEVICE, ConfigConst.DEVICE_LOCATION_ID_KEY, clientID)
		
		# Validate clientID
		if not self.clientID or len(self.clientID.strip()) == 0:
			self.clientID = 'CDAMqttClientID001'
			
		logging.info('\tMQTT Client ID:   ' + self.clientID)
		logging.info('\tMQTT Broker Host: ' + self.host)
		logging.info('\tMQTT Broker Port: ' + str(self.port))
		logging.info('\tMQTT Keep Alive:  ' + str(self.keepAlive))
	
	def connectClient(self) -> bool:
		if not self.mqttClient:
			# Create MQTT client with clean session
			self.mqttClient = mqttClient.Client(client_id = self.clientID, clean_session = True)
			
			# Set authentication if enabled
			if self.enableAuth and self.username and self.password:
				logging.info("Setting MQTT authentication credentials")
				self.mqttClient.username_pw_set(self.username, self.password)
			
			try:
				if self.enableEncryption:
					logging.info("Enabling TLS encryption...")
					
					self.port = \
						self.config.getInteger( \
							ConfigConst.MQTT_GATEWAY_SERVICE, ConfigConst.SECURE_PORT_KEY, ConfigConst.DEFAULT_MQTT_SECURE_PORT)
					
					# Configure TLS for self-signed certificates (testing only)
					self.mqttClient.tls_set(
						ca_certs=self.pemFileName,
						cert_reqs=ssl.CERT_NONE,
						tls_version=ssl.PROTOCOL_TLS_CLIENT)
					
					# Allow self-signed certificates for testing
					self.mqttClient.tls_insecure_set(True)
			except Exception as e:
				logging.exception("Failed to enable TLS encryption: %s", e)
				logging.warning("Using unencrypted connection.")
			
			# Set callback functions
			self.mqttClient.on_connect = self.onConnect
			self.mqttClient.on_disconnect = self.onDisconnect
			self.mqttClient.on_message = self.onMessage
			self.mqttClient.on_publish = self.onPublish
			self.mqttClient.on_subscribe = self.onSubscribe
		
		if not self.mqttClient.is_connected():
			logging.info('MQTT client connecting to broker at host: ' + self.host)
			self.mqttClient.connect(self.host, self.port, self.keepAlive)
			self.mqttClient.loop_start()
			
			return True
		else:
			logging.warning('MQTT client is already connected. Ignoring connect request.')
			
			return False
		
	def disconnectClient(self) -> bool:
		if self.mqttClient.is_connected():
			logging.info('Disconnecting MQTT client from broker: ' + self.host)
			self.mqttClient.loop_stop()
			self.mqttClient.disconnect()
			
			return True
		else:
			logging.warning('MQTT client already disconnected. Ignoring.')
			
			return False
		

	def onThresholdControlMessage(self, client, userdata, msg):
		"""
		Callback for threshold control messages from Ubidots dashboard sliders.
		Parses floor/ceiling values and triggers threshold update.
		"""
		try:
			import json
			payload = msg.payload.decode('utf-8')
			data = json.loads(payload)
			
			# Handle both dict and direct float value
			if isinstance(data, dict):
				new_value = float(data.get('value', 0))
			else:
				new_value = float(data)
			topic = msg.topic
			
			logging.info(f"Received threshold control: {topic} = {new_value}")
			
			# Determine which threshold changed
			if 'threshold_floor' in topic:
				threshold_type = 'floor'
			elif 'threshold_ceiling' in topic:
				threshold_type = 'ceiling'
			else:
				logging.warning(f"Unknown threshold control topic: {topic}")
				return
			
			# Create actuator data with manual threshold update format
			from programmingtheiot.data.ActuatorData import ActuatorData
			actuator_data = ActuatorData()
			
			# Format: "HvacActuator-MANUAL-FLOOR=XX.XX" or "HvacActuator-MANUAL-CEILING=XX.XX"
			actuator_data.setName(f"HvacActuator-MANUAL-{threshold_type.upper()}={new_value:.2f}")
			
			# Pass to data message listener (DeviceDataManager)
			if self.dataMsgListener:
				self.dataMsgListener.handleActuatorCommandMessage(actuator_data)
			
		except Exception as e:
			logging.exception(f"Failed to process threshold control message: {e}")

	def onConnect(self, client, userdata, flags, rc):
		logging.info('[Callback] Connected to MQTT broker. Result code: ' + str(rc))
		
		# Subscribe to actuator command topic
		self.mqttClient.subscribe(
			topic = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value,
			qos = self.defaultQos)
		
		# Add topic-specific callback for actuator commands
		self.mqttClient.message_callback_add(
			sub = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value,
			callback = self.onActuatorCommandMessage)
		
		# Subscribe to Ubidots actuator command topic (for cloud-to-device control)
		ubidots_actuator_topic = "/v1.6/devices/constraineddevice001/hvacactuator"
		self.mqttClient.subscribe(topic=ubidots_actuator_topic, qos=self.defaultQos)
		logging.info(f"Subscribed to Ubidots actuator topic: {ubidots_actuator_topic}")
		
		# Add callback for Ubidots actuator commands
		self.mqttClient.message_callback_add(
			sub=ubidots_actuator_topic,
			callback=self.onActuatorCommandMessage)
		
		# Subscribe to threshold control topics (for manual threshold adjustment)
		# Try both with and without /lv suffix
		floor_control_topic = "/v1.6/devices/constraineddevice001/threshold_floor"
		ceiling_control_topic = "/v1.6/devices/constraineddevice001/threshold_ceiling"
		
		self.mqttClient.subscribe(topic=floor_control_topic, qos=self.defaultQos)
		self.mqttClient.subscribe(topic=ceiling_control_topic, qos=self.defaultQos)
		logging.info(f"Subscribed to threshold control topics for manual adjustment")
		
		# Add callbacks for threshold controls
		self.mqttClient.message_callback_add(
			sub=floor_control_topic,
			callback=self.onThresholdControlMessage)
		self.mqttClient.message_callback_add(
			sub=ceiling_control_topic,
			callback=self.onThresholdControlMessage)
		
	def onDisconnect(self, client, userdata, rc):
		logging.info('MQTT client disconnected from broker: ' + str(client))
		
	def onMessage(self, client, userdata, msg):
		payload = msg.payload
		
		if payload:
			logging.info('MQTT message received with payload: ' + str(payload.decode("utf-8")))
		else:
			logging.info('MQTT message received with no payload: ' + str(msg))
			
	def onPublish(self, client, userdata, mid):
		# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
		pass
		# logging.info('MQTT message published: ' + str(mid))
	
	def onSubscribe(self, client, userdata, mid, granted_qos):
		logging.info('[Callback] Subscribed MID: ' + str(mid))
	
	def onActuatorCommandMessage(self, client, userdata, msg):
		"""
		Callback to handle incoming actuator command messages.
		Converts JSON payload to ActuatorData and passes to listener.
		
		@param client The client reference context.
		@param userdata The user reference context.
		@param msg The message context, including the embedded payload.
		"""
		logging.info('[Callback] Actuator command message received. Topic: %s.', msg.topic)
		
		if self.dataMsgListener:
			try:
				# assumes all data is encoded using UTF-8 (between GDA and CDA)
				actuatorData = DataUtil().jsonToActuatorData(msg.payload.decode('utf-8'))
				
				self.dataMsgListener.handleActuatorCommandMessage(actuatorData)
			except:
				logging.exception("Failed to convert incoming actuation command payload to ActuatorData: ")
	
	def publishMessage(self, resource: ResourceNameEnum = None, msg: str = None, qos: int = ConfigConst.DEFAULT_QOS, topic: str = None) -> bool:
		# Determine the topic to use
		topic_to_publish = None
		
		# If a raw topic string is provided, use it (for Ubidots)
		if topic:
			topic_to_publish = topic
		# Otherwise, use the ResourceNameEnum
		elif resource:
			topic_to_publish = resource.value
		else:
			# No topic specified
			# logging.warning('No topic specified. Cannot publish message.')
			return False
		
		# check validity of message
		if not msg:
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.warning('No message specified. Cannot publish message to topic: ' + topic_to_publish)
			return False
		
		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
		
		# publish message and wait for completion (ENABLED FOR PERFORMANCE TESTING)
		msgInfo = self.mqttClient.publish(topic = topic_to_publish, payload = msg, qos = qos)
		msgInfo.wait_for_publish()
		
		return True
	
	def subscribeToTopic(self, resource: ResourceNameEnum = None, callback = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot subscribe.')
			return False
		
		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
		
		# subscribe to topic
		logging.info('Subscribing to topic %s', resource.value)
		self.mqttClient.subscribe(resource.value, qos)
		
		return True
	
	def unsubscribeFromTopic(self, resource: ResourceNameEnum = None) -> bool:
		# check validity of resource (topic)
		if not resource:
			logging.warning('No topic specified. Cannot unsubscribe.')
			return False
		
		logging.info('Unsubscribing to topic %s', resource.value)
		self.mqttClient.unsubscribe(resource.value)
		
		return True
	
	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True
		return False