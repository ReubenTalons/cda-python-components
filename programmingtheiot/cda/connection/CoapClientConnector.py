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
import socket
import traceback

from coapthon import defines
from coapthon.client.helperclient import HelperClient
from coapthon.messages.option import Option
from coapthon.utils import parse_uri
from coapthon.utils import generate_random_token

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.cda.connection.IRequestResponseClient import IRequestResponseClient

from programmingtheiot.data.DataUtil import DataUtil


class HandleActuatorEvent():
	"""
	Helper class to handle actuator observation events.
	Processes incoming ActuatorData updates from the CoAP server.
	"""
	
	def __init__(self, listener: IDataMessageListener = None, resource: ResourceNameEnum = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, requests = None):
		"""
		Constructor for the observation event handler.
		
		@param listener: The data message listener
		@param resource: The resource being observed
		@param requests: Dictionary tracking active observations
		"""
		self.listener = listener
		self.resource = resource
		self.observeRequests = requests
		
		if not self.resource:
			self.resource = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE
	
	def handleActuatorResponse(self, response):
		"""
		Callback method invoked when an observed resource changes.
		
		@param response: The CoAP response containing updated data
		"""
		if response:
			jsonData = response.payload
			
			# Track the response
			if self.observeRequests is not None:
				self.observeRequests[self.resource] = response
			
			logging.info(f"Received actuator command response to resource {self.resource} -> {jsonData}")
			
			# Pass to listener if available
			if self.listener:
				try:
					data = DataUtil().jsonToActuatorData(jsonData=jsonData)
					self.listener.handleActuatorCommandMessage(data=data)
				except:
					logging.warning(f"Failed to decode actuator data. Ignoring: {jsonData}")


class CoapClientConnector(IRequestResponseClient):
	"""
	CoAP client connector implementation using CoAPthon3 library.
	"""
	
	def __init__(self, dataMsgListener: IDataMessageListener = None):
		"""
		Constructor - initializes the CoAP client connector.
		
		@param dataMsgListener: The callback listener for incoming messages
		"""
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		self.coapClient = None
		
		self.observeRequests = {}
		
		# Load host and port from configuration
		self.host = self.config.getProperty(
			ConfigConst.COAP_GATEWAY_SERVICE, 
			ConfigConst.HOST_KEY, 
			ConfigConst.DEFAULT_HOST
		)
		self.port = self.config.getInteger(
			ConfigConst.COAP_GATEWAY_SERVICE, 
			ConfigConst.PORT_KEY, 
			ConfigConst.DEFAULT_COAP_PORT
		)
		
		self.includeDebugLogDetail = True
		
		try:
			# Resolve hostname to IP address
			tmpHost = socket.gethostbyname(self.host)
			
			if tmpHost:
				self.host = tmpHost
				self.uriPath = f"coap://{self.host}:{self.port}/"
				logging.info(f"CoAP client will connect to: {self.uriPath}")
				self._initClient()
			else:
				logging.error(f"Can't resolve host: {self.host}")
				raise
			
		except socket.gaierror:
			logging.error(f"Failed to resolve host: {self.host}")
			raise
	
	
	def sendDiscoveryRequest(self, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""
		Send a discovery request to find available resources on the CoAP server.
		Uses the standard CoAP discovery endpoint: .well-known/core
		
		@param timeout: Request timeout in seconds
		@return: True if successful, False otherwise
		"""
		logging.info("Discovering remote resources...")
		
		# Create resource path for discovery
		resourcePath = self._createResourcePath(None, '.well-known/core')
		
		logging.info(f"Issuing DISCOVERY with path: {resourcePath}")
		
		# Create GET request for discovery
		request = self.coapClient.mk_request(defines.Codes.GET, path=resourcePath)
		request.token = generate_random_token(2)
		
		# Send request with callback
		self.coapClient.send_request(request=request, timeout=timeout, callback=self._onDiscoveryResponse)
		
		return True
	
	
	def sendDeleteRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""
		Send a DELETE request to remove a resource on the CoAP server.
		
		@param resource: The resource type (enum)
		@param name: Optional resource name
		@param enableCON: Enable confirmable message (requires acknowledgment)
		@param timeout: Request timeout in seconds
		@return: True if successful, False otherwise
		"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			
			logging.info(f"Issuing DELETE with path: {resourcePath}")
			
			# Create DELETE request
			request = self.coapClient.mk_request(defines.Codes.DELETE, path=resourcePath)
			request.token = generate_random_token(2)
			
			# Set message type (CON or NON)
			if not enableCON:
				request.type = defines.Types["NON"]
			
			# Send request with callback
			self.coapClient.send_request(request=request, callback=self._onDeleteResponse, timeout=timeout)
			
			return True
		else:
			logging.warning("Can't send DELETE - no resource path provided.")
			return False
	
	
	def sendGetRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""
		Send a GET request to retrieve data from the CoAP server.
		
		@param resource: The resource type (enum)
		@param name: Optional resource name
		@param enableCON: Enable confirmable message (requires acknowledgment)
		@param timeout: Request timeout in seconds
		@return: True if successful, False otherwise
		"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			
			logging.info(f"Issuing GET with path: {resourcePath}")
			
			# Create GET request
			request = self.coapClient.mk_request(defines.Codes.GET, path=resourcePath)
			request.token = generate_random_token(2)
			
			# Set message type (CON or NON)
			if not enableCON:
				request.type = defines.Types["NON"]
			
			# Send request and get response
			response = self.coapClient.send_request(request=request, timeout=timeout)
			
			# Process response
			self._onGetResponse(response=response, resourcePath=resourcePath)
			
			return True
		else:
			logging.warning("Can't send GET - no resource path provided.")
			return False
	
	
	def sendPostRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, payload: str = None, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""
		Send a POST request to create a new resource on the CoAP server.
		
		@param resource: The resource type (enum)
		@param name: Optional resource name
		@param enableCON: Enable confirmable message (requires acknowledgment)
		@param payload: The data to send (JSON string)
		@param timeout: Request timeout in seconds
		@return: True if successful, False otherwise
		"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.info(f"Issuing POST with path: {resourcePath}")
			
			# Create POST request
			request = self.coapClient.mk_request(defines.Codes.POST, path=resourcePath)
			request.token = generate_random_token(2)
			request.payload = payload
			
			# Set message type (CON or NON)
			if not enableCON:
				request.type = defines.Types["NON"]
			
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.info(f"Sending POST with payload: {payload}")
			
			# Send request SYNCHRONOUSLY (no callback) for performance testing
			response = self.coapClient.send_request(request=request, callback=None, timeout=timeout)
			
			return True
		else:
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.warning("Can't send POST - no resource path provided.")
			return False
	
	
	def sendPutRequest(self, resource: ResourceNameEnum = None, name: str = None, enableCON: bool = False, payload: str = None, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""
		Send a PUT request to update a resource on the CoAP server.
		
		@param resource: The resource type (enum)
		@param name: Optional resource name
		@param enableCON: Enable confirmable message (requires acknowledgment)
		@param payload: The data to send (JSON string)
		@param timeout: Request timeout in seconds
		@return: True if successful, False otherwise
		"""
		if resource or name:
			resourcePath = self._createResourcePath(resource, name)
			
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.info(f"Issuing PUT with path: {resourcePath}")
			
			# Create PUT request
			request = self.coapClient.mk_request(defines.Codes.PUT, path=resourcePath)
			request.token = generate_random_token(2)
			request.payload = payload
			
			# Set message type (CON or NON)
			if not enableCON:
				request.type = defines.Types["NON"]
			
			# Send request SYNCHRONOUSLY (no callback) for performance testing
			response = self.coapClient.send_request(request=request, callback=None, timeout=timeout)
			
			return True
		else:
			# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
			# logging.warning("Can't send PUT - no resource path provided.")
			return False
	
	
	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		"""
		Set or update the callback listener for incoming messages.
		
		@param listener: The data message listener
		@return: True if set successfully, False otherwise
		"""
		if listener:
			self.dataMsgListener = listener
			return True
		
		return False
	
	
	def startObserver(self, resource: ResourceNameEnum = None, name: str = None, ttl: int = IRequestResponseClient.DEFAULT_TTL) -> bool:
		"""
		Start observing a resource for changes (similar to MQTT subscribe).
		Client will receive automatic updates when the resource changes.
		
		@param resource: The resource type to observe
		@param name: Optional resource name
		@param ttl: Time to live for the observation
		@return: True if started successfully, False otherwise
		"""
		if resource or name:
			if resource in self.observeRequests:
				logging.warning(f"Already observing resource {resource}. Ignoring start observe request.")
				return False
			
			self.observeRequests[resource] = None
			
			resourcePath = self._createResourcePath(resource, name)
			
			# Create handler for observation updates
			observeActuatorCmdHandler = HandleActuatorEvent(
				listener=self.dataMsgListener,
				resource=resource,
				requests=self.observeRequests
			)
			
			try:
				self.coapClient.observe(path=resourcePath, callback=observeActuatorCmdHandler.handleActuatorResponse)
				logging.info(f"Started observing resource: {resourcePath}")
				return True
			except Exception as e:
				logging.warning(f"Failed to observe path: {resourcePath}")
				traceback.print_exception(type(e), e, e.__traceback__)
				return False
		else:
			logging.warning("Can't start observer - no resource path provided.")
			return False
	
	
	def stopObserver(self, resource: ResourceNameEnum = None, name: str = None, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""
		Stop observing a resource.
		
		@param resource: The resource type to stop observing
		@param name: Optional resource name
		@param timeout: Request timeout in seconds
		@return: True if stopped successfully, False otherwise
		"""
		if resource or name:
			if not resource in self.observeRequests:
				logging.warning(f"Resource {resource} not being observed. Ignoring stop observe request.")
				return False
			
			response = self.observeRequests[resource]
			
			if response:
				logging.info(f"Cancelling observe for resource {resource}.")
				
				try:
					self.coapClient.cancel_observing(response=response, send_rst=True)
					del self.observeRequests[resource]
					logging.info(f"Cancelled observe for resource {resource}.")
					return True
				except Exception as e:
					logging.warning(f"Failed to cancel observe for resource {resource}")
					traceback.print_exception(type(e), e, e.__traceback__)
					return False
			else:
				logging.warning(f"No response yet for observed resource {resource}. Attempting to stop anyway.")
				
				try:
					self.coapClient.cancel_observing(response=None, send_rst=True)
					logging.info(f"Canceled observe for resource {resource}.")
					return True
				except Exception as e:
					logging.warning(f"Failed to cancel observe for resource {resource}.")
					traceback.print_exception(type(e), e, e.__traceback__)
					return False
		else:
			logging.warning("Can't stop observer - no resource path provided.")
			return False
	
	
	# =========================================================================
	# Private Methods
	# =========================================================================
	
	def _initClient(self):
		"""
		Initialize the CoAP client connection.
		Creates a HelperClient instance pointing to the configured server.
		"""
		try:
			self.coapClient = HelperClient(server=(self.host, self.port))
			logging.info(f"Client created. Will invoke resources at {self.uriPath}")
		except Exception as e:
			logging.error(f"Failed to create CoAP client to URI path {self.uriPath}")
			traceback.print_exception(type(e), e, e.__traceback__)
	
	
	def _createResourcePath(self, resource: ResourceNameEnum = None, name: str = None):
		"""
		Build a resource path from components.
		
		Example: resource=SENSOR, name=temp → "SENSOR/temp"
		
		@param resource: The resource enum (e.g., ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE)
		@param name: Optional specific resource name
		@return: Complete resource path string
		"""
		resourcePath = ""
		hasResource = False
		
		if resource:
			resourcePath = resourcePath + resource.value
			hasResource = True
		
		if name:
			if hasResource:
				resourcePath = resourcePath + "/"
			
			resourcePath = resourcePath + name
		
		return resourcePath
	
	
	# =========================================================================
	# Response Handler Methods (callbacks for server responses)
	# =========================================================================
	
	def _onDeleteResponse(self, response):
		"""
		Handle response from DELETE request.
		Logs the server's response to the DELETE operation.
		
		@param response: The CoAP response object
		"""
		if not response:
			logging.warning("DELETE response invalid. Ignoring.")
			return
		
		logging.info(f"DELETE response received: {response.payload}")
	
	
	def _onDiscoveryResponse(self, response):
		"""
		Handle response from discovery request.
		Parses the list of available resources from the server.
		
		@param response: The CoAP response object
		"""
		if not response:
			logging.warning("DISCOVERY response invalid. Ignoring.")
			return
		
		logging.info(f"DISCOVERY response received: {response.payload}")
	
	
	def _onGetResponse(self, response, resourcePath: str = None):
		"""
		Handle response from GET request.
		Parses the payload and determines the data type, then processes accordingly.
		
		@param response: The CoAP response object
		@param resourcePath: The resource path that was queried
		"""
		if not response:
			logging.warning("GET response invalid. Ignoring.")
			return
		
		logging.info("GET response received.")
		
		# Get the payload (JSON data)
		jsonData = response.payload
		
		# Parse the resource path to determine data type
		locationPath = resourcePath.split('/')
		
		if len(locationPath) > 2:
			dataType = locationPath[2]
			
			# Check if this is ActuatorData
			if dataType == ConfigConst.ACTUATOR_CMD:
				logging.info(f"ActuatorData received: {jsonData}")
				
				try:
					# Convert JSON to ActuatorData object
					ad = DataUtil().jsonToActuatorData(jsonData)
					
					# Pass to data message listener if available
					if self.dataMsgListener:
						self.dataMsgListener.handleActuatorCommandMessage(ad)
				except:
					logging.warning(f"Failed to decode actuator data. Ignoring: {jsonData}")
					return
			else:
				# Generic response data
				logging.info(f"Response data received. Payload: {jsonData}")
		else:
			# Generic response data
			logging.info(f"Response data received. Payload: {jsonData}")
	
	
	def _onPostResponse(self, response):
		"""
		Handle response from POST request.
		Logs the server's response to the POST operation.
		
		@param response: The CoAP response object
		"""
		# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
		pass
		# if not response:
		# 	logging.warning("POST response invalid. Ignoring.")
		# 	return
		# 
		# logging.info(f"POST response received: {response.payload}")
	
	
	def _onPutResponse(self, response):
		"""
		Handle response from PUT request.
		Logs the server's response to the PUT operation.
		
		@param response: The CoAP response object
		"""
		# TEMPORARILY DISABLED FOR PERFORMANCE TESTING
		pass
		# if not response:
		# 	logging.warning("PUT response invalid. Ignoring.")
		# 	return
		# 
		# logging.info(f"PUT response received: {response.payload}")