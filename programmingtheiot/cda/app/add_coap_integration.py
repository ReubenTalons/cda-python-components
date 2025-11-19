#!/usr/bin/env python3

# Read the file
with open('DeviceDataManager.py', 'r') as f:
    lines = f.readlines()

# Find and add import
for i, line in enumerate(lines):
    if 'from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector' in line:
        lines.insert(i + 1, 'from programmingtheiot.cda.connection.AsyncCoapServerAdapter import AsyncCoapServerAdapter\n')
        break

# Find and add enableCoapServer config
for i, line in enumerate(lines):
    if 'self.enableMqttClient = \\' in line:
        # Find the end of this config block (3 lines)
        insert_pos = i + 3
        lines.insert(insert_pos, '\n')
        lines.insert(insert_pos + 1, '\t\t# NEW: Enable CoAP server based on configuration\n')
        lines.insert(insert_pos + 2, '\t\tself.enableCoapServer = \\\n')
        lines.insert(insert_pos + 3, '\t\t\tself.configUtil.getBoolean( \\\n')
        lines.insert(insert_pos + 4, '\t\t\t\tsection = ConfigConst.CONSTRAINED_DEVICE, key = ConfigConst.ENABLE_COAP_SERVER_KEY)\n')
        break

# Find and add CoAP server initialization
for i, line in enumerate(lines):
    if 'logging.info("MQTT client enabled and initialized")' in line:
        lines.insert(i + 1, '\n')
        lines.insert(i + 2, '\t\t# NEW: Initialize CoAP server if enabled\n')
        lines.insert(i + 3, '\t\tif self.enableCoapServer:\n')
        lines.insert(i + 4, '\t\t\tself.coapServer = AsyncCoapServerAdapter(dataMsgListener = self)\n')
        lines.insert(i + 5, '\t\t\tlogging.info("Async CoAP server enabled and initialized")\n')
        break

# Find and add startServer call
for i, line in enumerate(lines):
    if 'self.mqttClient.subscribeToTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE' in line:
        lines.insert(i + 1, '\n')
        lines.insert(i + 2, '\t\t# NEW: Start CoAP server\n')
        lines.insert(i + 3, '\t\tif self.coapServer:\n')
        lines.insert(i + 4, '\t\t\tself.coapServer.startServer()\n')
        break

# Find and add stopServer call
for i, line in enumerate(lines):
    if 'self.mqttClient.disconnectClient()' in line:
        lines.insert(i + 1, '\n')
        lines.insert(i + 2, '\t\t# NEW: Stop CoAP server\n')
        lines.insert(i + 3, '\t\tif self.coapServer:\n')
        lines.insert(i + 4, '\t\t\tself.coapServer.stopServer()\n')
        break

# Write back
with open('DeviceDataManager.py', 'w') as f:
    f.writelines(lines)

print("✓ DeviceDataManager.py updated successfully!")
