import re

# Read the file
with open('programmingtheiot/cda/app/DeviceDataManager.py', 'r') as f:
    lines = f.readlines()

# Find and replace the _handleUpstreamTransmission method
in_method = False
method_start = -1
method_end = -1

for i, line in enumerate(lines):
    if 'def _handleUpstreamTransmission(' in line:
        in_method = True
        method_start = i
    elif in_method and line.strip() == 'pass':
        method_end = i
        break

if method_start != -1 and method_end != -1:
    # Replace the pass statement with actual implementation
    new_implementation = '''		
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
				logging.error(f"Failed to publish actuator response: {e}")
'''
    
    # Replace the 'pass' line
    lines[method_end] = new_implementation
    
    # Write back
    with open('programmingtheiot/cda/app/DeviceDataManager.py', 'w') as f:
        f.writelines(lines)
    
    print(f"Fixed _handleUpstreamTransmission method at line {method_end}")
else:
    print("Could not find method to fix")
