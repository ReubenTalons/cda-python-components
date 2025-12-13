# Read the file
with open('programmingtheiot/cda/app/DeviceDataManager.py', 'r') as f:
    lines = f.readlines()

# Fix line 256 (sensor data publishing)
for i, line in enumerate(lines):
    if 'self.mqttClient.publishMessage(resource=None, msg=payload, qos=0)' in line and i > 250 and i < 260:
        # Replace with correct call that passes the topic
        lines[i] = '\t\t\t\tself.mqttClient.publishMessage(resource=None, msg=payload, qos=0, topic=topic)\n'
        print(f"Fixed line {i+1} (sensor data)")
    elif 'self.mqttClient.publishMessage(resource=None, msg=payload, qos=0)' in line and i > 280 and i < 290:
        # Replace with correct call that passes the topic
        lines[i] = '\t\t\t\tself.mqttClient.publishMessage(resource=None, msg=payload, qos=0, topic=topic)\n'
        print(f"Fixed line {i+1} (system perf)")

# Write back
with open('programmingtheiot/cda/app/DeviceDataManager.py', 'w') as f:
    f.writelines(lines)

print("Fixed DeviceDataManager.py")
