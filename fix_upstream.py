# Read the file
with open('programmingtheiot/cda/app/DeviceDataManager.py', 'r') as f:
    content = f.read()

# Old code
old_code = '''	def _handleUpstreamTransmission(self, resource: ResourceNameEnum = None, msg: str = None):
		"""
		Call this from handleActuatorCommandResponse(), handlesensorMessage(), and handleSystemPerformanceMessage()
		to determine if the message should be sent upstream. Steps to take:
		1) Check connection: Is there a client connection configured (and valid) to a remote MQTT or CoAP server?
		2) Act on msg: If # 1 is true, send message upstream using one (or both) client connections.
		"""
		logging.info("Upstream transmission invoked for resource: " + str(resource))
		# For now, basic implementation - will be expanded in Part III
		pass'''

# New code with actuator response publishing
new_code = '''	def _handleUpstreamTransmission(self, resource: ResourceNameEnum = None, msg: str = None):
		"""
		Call this from handleActuatorCommandResponse(), handlesensorMessage(), and handleSystemPerformanceMessage()
		to determine if the message should be sent upstream. Steps to take:
		1) Check connection: Is there a client connection configured (and valid) to a remote MQTT or CoAP server?
		2) Act on msg: If # 1 is true, send message upstream using one (or both) client connections.
		"""
		logging.info("Upstream transmission invoked for resource: " + str(resource))
		
		# Publish actuator responses to Ubidots
		if resource == ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE and self.mqttClient:
			# Parse the actuator data from JSON to get details
			try:
				import json
				data_dict = json.loads(msg)
				actuator_name = data_dict.get('name', 'unknown').lower()
				actuator_value = data_dict.get('value', 0)
				actuator_command = data_dict.get('command', 0)
				
				# Publish to Ubidots with actuator name
				topic = f"/v1.6/devices/constraineddevice001/{actuator_name}"
				payload = f'{{"value": {actuator_value}, "command": {actuator_command}}}'
				self.mqttClient.publishMessage(resource=None, msg=payload, qos=0, topic=topic)
				logging.debug(f"Published actuator response to topic: {topic}")
			except Exception as e:
				logging.error(f"Failed to publish actuator response: {e}")'''

# Replace
content = content.replace(old_code, new_code)

# Write back
with open('programmingtheiot/cda/app/DeviceDataManager.py', 'w') as f:
    f.write(content)

print("Fixed _handleUpstreamTransmission method")
