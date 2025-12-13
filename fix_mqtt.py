# Read the file
with open('programmingtheiot/cda/connection/MqttClientConnector.py', 'r') as f:
    content = f.read()

# Old code
old_code = '''	def publishMessage(self, resource: ResourceNameEnum = None, msg: str = None, qos: int = ConfigConst.DEFAULT_QOS) -> bool:
		# check validity of resource (topic)
		if not resource:
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.warning('No topic specified. Cannot publish message.')
			return False
		
		# check validity of message
		if not msg:
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.warning('No message specified. Cannot publish message to topic: ' + resource.value)
			return False
		
		# check validity of QoS - set to default if necessary
		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS
		
		# publish message and wait for completion (ENABLED FOR PERFORMANCE TESTING)
		msgInfo = self.mqttClient.publish(topic = resource.value, payload = msg, qos = qos)
		msgInfo.wait_for_publish()
		
		return True'''

# New code
new_code = '''	def publishMessage(self, resource: ResourceNameEnum = None, msg: str = None, qos: int = ConfigConst.DEFAULT_QOS, topic: str = None) -> bool:
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
		
		return True'''

# Replace
content = content.replace(old_code, new_code)

# Write back
with open('programmingtheiot/cda/connection/MqttClientConnector.py', 'w') as f:
    f.write(content)

print("Fixed MqttClientConnector.py")
