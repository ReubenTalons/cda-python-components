import sys
sys.path.append('.')

from programmingtheiot.cda.app.DeviceDataManager import DeviceDataManager
from programmingtheiot.data.ActuatorData import ActuatorData
import time

# Create DeviceDataManager instance
ddm = DeviceDataManager()
ddm.startManager()

# Wait a moment for MQTT to connect
time.sleep(3)

# Create a threshold update command
actuator_data = ActuatorData()
actuator_data.setName("HvacActuator-THRESHOLDS-FLOOR=17.5-CEILING=20.5")

# Trigger the threshold update
print("\n🔧 Sending threshold update event...")
ddm._handleThresholdUpdate(actuator_data)

# Wait to ensure message is published
time.sleep(2)

print("✅ Test complete! Check Ubidots for 'threshold_events' variable")

# Stop manager
ddm.stopManager()
