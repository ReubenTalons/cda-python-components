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
import threading
import traceback

import asyncio

from aiocoap import *

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

from programmingtheiot.cda.connection.IRequestResponseClient import IRequestResponseClient

from programmingtheiot.data.DataUtil import DataUtil


class AsyncCoapClientConnector(IRequestResponseClient):
	"""
	Async CoAP client connector implementation using aiocoap library with asyncio.
	"""
	
	def __init__(self, dataMsgListener: IDataMessageListener = None):
		"""
		Constructor - initializes the async CoAP client connector.
		
		@param dataMsgListener: The callback listener for incoming messages
		"""
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		self.coapClient = None
		
		self.observeRequests = {}
		self.observeTasks = {}
		
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
				self._initEventLoop()
			else:
				logging.error(f"Can't resolve host: {self.host}")
				raise
			
		except socket.gaierror:
			logging.error(f"Failed to resolve host: {self.host}. Check hostname in config.")
			raise
	
	
	def sendDiscoveryRequest(self, timeout: int = IRequestResponseClient.DEFAULT_TIMEOUT) -> bool:
		"""
		Send a discovery request to find available resources on the CoAP server.
		Uses the standard CoAP discovery endpoint: .well-known/core
		
		@param timeout: Request timeout in seconds
		@return: True if successful, False otherwise
		"""
		logging.info("Discovering remote resources...")
		
		resourcePath = self._createResourcePath(None, ".well-known/core")
		
		logging.info(f"Issuing Async GET - DISCOVERY to path: {resourcePath}")
		
		future = asyncio.run_coroutine_threadsafe(
			self._handleDiscoveryRequest(resourcePath),
			self._eventLoopThread
		)
		
		return future.result()
	
	
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
			
			logging.info(f"Issuing Async DELETE to path: {resourcePath}")
			
			future = asyncio.run_coroutine_threadsafe(
				self._handleDeleteRequest(resourcePath, enableCON),
				self._eventLoopThread
			)
			
			return future.result()
		else:
			logging.warning("Can't issue Async DELETE - no path provided.")
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
			
			logging.info(f"Issuing Async GET to path: {resourcePath}")
			
			future = asyncio.run_coroutine_threadsafe(
				self._handleGetRequest(resourcePath, enableCON),
				self._eventLoopThread
			)
			
			return future.result()
		else:
			logging.warning("Can't issue Async GET - no path provided.")
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
			
			logging.info(f"Issuing Async POST to path: {resourcePath}")
			
			future = asyncio.run_coroutine_threadsafe(
				self._handlePostRequest(resourcePath, payload, enableCON),
				self._eventLoopThread
			)
			
			return future.result()
		else:
			logging.warning("Can't issue Async POST - no path provided.")
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
			
			logging.info(f"Issuing Async PUT to path: {resourcePath}")
			
			future = asyncio.run_coroutine_threadsafe(
				self._handlePutRequest(resourcePath, payload, enableCON),
				self._eventLoopThread
			)
			
			return future.result()
		else:
			logging.warning("Can't issue Async PUT - no path provided.")
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
			resourcePath = self._createResourcePath(resource, name)
			
			if resourcePath in self.observeTasks:
				logging.warning(f"Already observing resource {resourcePath}. Ignoring start observe request.")
				return False
			
			fullPath = self.uriPath + resourcePath
			
			task = asyncio.run_coroutine_threadsafe(
				self._handleStartObserveRequest(fullPath),
				self._eventLoopThread
			)
			
			self.observeTasks[resourcePath] = task
			
			logging.info(f"Started observing: {resourcePath}")
			return True
		else:
			logging.warning("Can't issue Async OBSERVE - GET - no path provided.")
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
			resourcePath = self._createResourcePath(resource, name)
			
			if resourcePath not in self.observeTasks:
				logging.warning(f"Resource {resourcePath} not being observed. Ignoring stop observe request.")
				return False
			
			task = self.observeTasks[resourcePath]
			task.cancel()
			
			cleanup_future = asyncio.run_coroutine_threadsafe(
				self._handleStopObserveRequest(resourcePath, ignoreErr=True),
				self._eventLoopThread
			)
			
			try:
				cleanup_future.result(timeout=5.0)
				logging.info(f"Stopped observing: {resourcePath}")
				del self.observeTasks[resourcePath]
				return True
			except Exception as e:
				logging.error(f"Error stopping observation: {e}")
				return False
		else:
			logging.warning("Can't cancel OBSERVE - GET - no path provided.")
			return False
	
	
	# =========================================================================
	# Private Methods
	# =========================================================================
	
	def _initEventLoop(self):
		"""
		Initialize the asyncio event loop in a separate thread.
		This allows async operations to run alongside the synchronous CDA code.
		"""
		def startEventLoop(loop):
			asyncio.set_event_loop(loop)
			loop.run_forever()
		
		self._eventLoopThread = asyncio.new_event_loop()
		self._executionThread = threading.Thread(
			target=startEventLoop,
			args=(self._eventLoopThread,),
			daemon=True
		)
		
		self._executionThread.start()
		
		future = asyncio.run_coroutine_threadsafe(
			self._initClientContext(),
			self._eventLoopThread
		)
		
		future.result()
	
	
	async def _initClientContext(self):
		"""
		Create the aiocoap client context.
		This is the async initialization that runs in the event loop.
		"""
		self.clientContext = await Context.create_client_context()
		logging.info("Async CoAP client context created")
	
	
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
	# Async Request Handler Methods
	# =========================================================================
	
	async def _handleStartObserveRequest(self, resourcePath: str = None):
		"""
		Async handler to start observing a CoAP resource.
		Continuously receives updates from the server until cancelled.
		
		@param resourcePath: The full URI path to observe
		"""
		logging.info(f"Handle start observe invoked. Waiting for each input: {resourcePath}")
		
		try:
			msg = Message(code=Code.GET, uri=resourcePath, observe=0)
			req = self.clientContext.request(msg)
			
			# Store with relative path as key (needed for cleanup)
			relativePath = resourcePath.replace(self.uriPath, "")
			self.observeRequests[relativePath] = req
			
			# Get initial response
			responseData = await req.response
			self._onGetResponse(responseData)
			
			# Continue observation - async for loop receives updates
			async for responseData in req.observation:
				self._onGetResponse(responseData)
		
		except asyncio.CancelledError:
			# Expected when observation is stopped
			logging.info(f"Observation cancelled for {resourcePath}")
		
		except Exception as e:
			logging.warning(f"Failed to execute OBSERVE - GET. Error: {e}")
			traceback.print_exception(type(e), e, e.__traceback__)
		
		finally:
			relativePath = resourcePath.replace(self.uriPath, "")
			
			if relativePath in self.observeRequests:
				del self.observeRequests[relativePath]
	
	
	async def _handleStopObserveRequest(self, resourcePath: str = None, ignoreErr: bool = False):
		"""
		Async handler to stop observing a CoAP resource.
		Cleans up observation request and cancels ongoing updates.
		
		@param resourcePath: The resource path to stop observing
		@param ignoreErr: Whether to ignore errors during stop
		"""
		if resourcePath in self.observeRequests:
			logging.info(f"Handle stop observe invoked: {resourcePath}")
			
			try:
				observeRequest = self.observeRequests[resourcePath]
				observeRequest.observation.cancel()
			except Exception as e:
				if not ignoreErr:
					logging.warning(f"Failed to cancel OBSERVE - GET: {resourcePath}")
			
			try:
				del self.observeRequests[resourcePath]
			except Exception as e:
				if not ignoreErr:
					logging.warning(f"Failed to remove observable from list: {resourcePath}")
		else:
			if not ignoreErr:
				logging.warning(f"Resource not currently under observation. Ignoring: {resourcePath}")
	
	
	async def _handleDeleteRequest(self, resourcePath: str = None, enableCON: bool = False):
		"""
		Async handler for DELETE requests.
		Sends a DELETE request to remove a resource on the CoAP server.
		
		@param resourcePath: The resource path to delete
		@param enableCON: Enable confirmable message
		"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
			
			msgType = NON
			
			if enableCON:
				msgType = CON
			
			msg = Message(mtype=msgType, code=Code.DELETE, uri=uriAndResourcePath)
			
			responseData = await self.clientContext.request(request_message=msg).response
			
			self._onDeleteResponse(responseData)
			
			return True
			
		except Exception as e:
			logging.warning(f"Failed to process Async DELETE request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False
	
	
	async def _handleDiscoveryRequest(self, resourcePath: str = None, enableCON: bool = False):
		"""
		Async handler for discovery requests.
		Sends a GET to .well-known/core to discover available resources.
		
		@param resourcePath: The resource path for discovery
		@param enableCON: Enable confirmable message
		"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
			
			msgType = NON
			
			if enableCON:
				msgType = CON
			
			msg = Message(mtype=msgType, code=Code.GET, uri=uriAndResourcePath)
			
			responseData = await self.clientContext.request(request_message=msg).response
			
			self._onDiscoveryResponse(responseData)
			
			return True
			
		except Exception as e:
			logging.warning(f"Failed to process Async DISCOVERY request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False
	
	
	async def _handleGetRequest(self, resourcePath: str = None, enableCON: bool = False):
		"""
		Async handler for GET requests.
		
		@param resourcePath: The resource path to retrieve
		@param enableCON: Enable confirmable message
		"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
			
			msgType = NON
			
			if enableCON:
				msgType = CON
			
			msg = Message(mtype=msgType, code=Code.GET, uri=uriAndResourcePath)
			
			responseData = await self.clientContext.request(request_message=msg).response
			
			self._onGetResponse(responseData)
			
			return True
			
		except Exception as e:
			logging.warning(f"Failed to process Async GET request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False
	
	
	async def _handlePostRequest(self, resourcePath: str = None, payload: str = None, enableCON: bool = False):
		"""
		Async handler for POST requests.
		Sends data to create a new resource on the CoAP server.
		
		@param resourcePath: The resource path to post to
		@param payload: The data to send (JSON string)
		@param enableCON: Enable confirmable message
		"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
			
			msgType = NON
			
			if enableCON:
				msgType = CON
			
			# Create POST message with payload
			msg = Message(mtype=msgType, payload=payload.encode("utf-8"), code=Code.POST, uri=uriAndResourcePath)
			
			responseData = await self.clientContext.request(request_message=msg).response
			
			self._onPostResponse(responseData)
			
			return True
			
		except Exception as e:
			logging.warning(f"Failed to process Async POST request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False
	
	
	async def _handlePutRequest(self, resourcePath: str = None, payload: str = None, enableCON: bool = False):
		"""
		Async handler for PUT requests.
		Sends data to update a resource on the CoAP server.
		
		@param resourcePath: The resource path to update
		@param payload: The data to send (JSON string)
		@param enableCON: Enable confirmable message
		"""
		try:
			uriAndResourcePath = self.uriPath + resourcePath
			
			msgType = NON
			
			if enableCON:
				msgType = CON
			
			# Create PUT message with payload
			msg = Message(mtype=msgType, payload=payload.encode("utf-8"), code=Code.PUT, uri=uriAndResourcePath)
			
			responseData = await self.clientContext.request(request_message=msg).response
			
			self._onPutResponse(responseData)
			
			return True
			
		except Exception as e:
			logging.warning(f"Failed to process Async PUT request for path: {uriAndResourcePath}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False
	
	
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
			logging.warning("Async DELETE response invalid. Ignoring.")
			return
		
		logging.info("Async DELETE response received.")
		
		responseData = response.payload.decode("utf-8")
		
		logging.info(f"Response data received. Payload: {responseData}")
	
	
	def _onDiscoveryResponse(self, response):
		"""
		Handle response from discovery request.
		Logs the list of available resources from the server.
		
		@param response: The CoAP response object
		"""
		if not response:
			logging.warning("Async GET - DISCOVERY response invalid. Ignoring.")
			return
		
		logging.info("Async GET - DISCOVERY response received.")
		
		if len(response.requested_path) >= 2:
			logging.info("Resources: " + str(response.payload))
		else:
			logging.info("Response: " + str(response))
	
	
	def _onGetResponse(self, response):
		"""
		Handle response from GET request.
		Parses the payload and determines the data type, then processes accordingly.
		
		@param response: The CoAP response object
		"""
		if not response:
			logging.warning("Async GET response invalid. Ignoring.")
			return
		
		logging.info("Async GET response received.")
		
		# Decode the payload from bytes to string
		jsonData = response.payload.decode("utf-8")
		
		if len(response.requested_path) >= 2:
			logging.info(f"Response: {response.requested_path}")
			
			dataType = response.requested_path[1]
			
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
		if not response:
			logging.warning("Async POST response invalid. Ignoring.")
			return
		
		logging.info("Async POST response received.")
		
		responseData = response.payload.decode("utf-8")
		
		logging.info(f"Response data received. Payload: {responseData}")
	
	
	def _onPutResponse(self, response):
		"""
		Handle response from PUT request.
		Logs the server's response to the PUT operation.
		
		@param response: The CoAP response object
		"""
		if not response:
			logging.warning("Async PUT response invalid. Ignoring.")
			return
		
		logging.info("Async PUT response received.")
		
		responseData = response.payload.decode("utf-8")
		
		logging.info(f"Response data received. Payload: {responseData}")