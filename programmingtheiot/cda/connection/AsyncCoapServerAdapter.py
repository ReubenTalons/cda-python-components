import logging

import asyncio
import time
import traceback
import threading

import aiocoap
import aiocoap.resource as resource

from aiocoap.resource import Resource

from typing import Optional, Dict, Any
from contextlib import suppress

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.cda.connection.handlers.AsyncGetTelemetryResourceHandler import AsyncGetTelemetryResourceHandler
from programmingtheiot.cda.connection.handlers.AsyncGetSystemPerformanceResourceHandler import AsyncGetSystemPerformanceResourceHandler
from programmingtheiot.cda.connection.handlers.AsyncUpdateActuatorResourceHandler import AsyncUpdateActuatorResourceHandler

class AsyncCoapServerAdapter():
	"""
	Async CoAP Server Adapter using aiocoap library with asyncio
	"""
	
	def __init__(self, dataMsgListener = None):
		self.config = ConfigUtil()
		self.dataMsgListener = dataMsgListener
		self.enableConfirmedMsgs = False
		
		self.host = self.config.getProperty(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.HOST_KEY, ConfigConst.DEFAULT_HOST)
		self.port = self.config.getInteger(ConfigConst.COAP_GATEWAY_SERVICE, ConfigConst.PORT_KEY, ConfigConst.DEFAULT_COAP_PORT)
		
		self.serverUri = f"coap://{self.host}:{self.port}"

		self.coapServer   = None
		self.rootResource = None
		
		self._serverTask: Optional[asyncio.Task] = None
		self._eventLoopThread: Optional[asyncio.AbstractEventLoop] = None
		self._executionThread: Optional[threading.Thread] = None
		self._shutdownEvent: Optional[asyncio.Event] = None
		self._shutdownFuture: Optional[asyncio.Future] = None

		self._initServer()
		
		logging.info(f"Async CoAP Server configured at {self.serverUri}")
	
	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True
		
		return False
	
	def addResource(self, resourcePath: ResourceNameEnum = None, endName: str = None, resource: Resource = None):
		if resourcePath and resource:
			uriPath = resourcePath.value
			
			if endName:
				uriPath = uriPath + '/' + endName
				
			resourceList = uriPath.split('/')
			
			if not self.rootResource:
				self.rootResource = resource.Site()
				
			logging.info(f"Adding resource to server: {resourceList}")

			try:
				self.rootResource.add_resource(resourceList, resource)
				
			except Exception as e:
				logging.error(f"Failed to add resource to server: {resourceList}")
		else:
			logging.warning(f"No resource provided for path: {resourcePath}")
	
	def startServer(self) -> bool:
		if self._serverTask and not self._serverTask.done():
			logging.warning("Server already running. Ignoring start request.")
			return False
		
		if not self.rootResource:
			logging.error("No resources configured. Nothing for server to do.")
			return False
		
		try:
			logging.info(f"Starting Async CoAP Server at {self.serverUri}")

			self._eventLoopThread = asyncio.new_event_loop()
			self._shutdownEvent = asyncio.Event()

			self._executionThread = threading.Thread(
				target = self._runServerTask,
				daemon = True,
				name = "Async-CoAP-Server-Thread")
			
			self._executionThread.start()

			# wait a fraction of a second so server can spin up
			time.sleep(0.5)

			logging.info(f"Async CoAP Server started at {self.serverUri}")

			return True
		
		except Exception as e:
			logging.error(f"Failed to start Async CoAP Server at {self.serverUri}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False
	
	def stopServer(self) -> bool:
		if not self._eventLoopThread or not self._serverTask:
			logging.warning("Async CoAP Server not yet running. Ignoring stop request.")
			return False

		try:
			logging.info(f"Shutting down Async CoAP Server at {self.serverUri}")

			if self._eventLoopThread.is_running():
				asyncio.run_coroutine_threadsafe(
					self._shutdownServer(),
					self._eventLoopThread)

			for _ in range(5):
				if self._serverTask.done():
					break

				time.sleep(1.0)

			if self._eventLoopThread.is_running():
				self._eventLoopThread.call_soon_threadsafe(self._eventLoopThread.stop)

			logging.info(f"Async CoAP Server shutdown: {self.serverUri}")

			return True
		
		except Exception as e:
			logging.error(f"Failed to shutdown Async CoAP Server at {self.serverUri}")
			traceback.print_exception(type(e), e, e.__traceback__)
			return False
	
	def _initServer(self):
		try:
			# Resource tree creation - lib-specific (this next line of code assumes use of aiocoap)
			self.rootResource = resource.Site()
			
			# Necessary to ensure discovery will function
			self.rootResource.add_resource( \
				['.well-known', 'core'], \
				resource.WKCResource(self.rootResource.get_resources_as_linkheader))
			
			self.addResource( \
				resourcePath = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, \
				endName = ConfigConst.HUMIDIFIER_ACTUATOR_NAME, \
				resource = AsyncUpdateActuatorResourceHandler(dataMsgListener = self.dataMsgListener))
				
			# TODO: add other actuator resource handlers (for HVAC, etc.)
			
			sysPerfDataListener = AsyncGetSystemPerformanceResourceHandler()
			
			self.addResource( \
				resourcePath = ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE, \
				resource = sysPerfDataListener)
			
			sensorDataListener = AsyncGetTelemetryResourceHandler()
			
			self.addResource( \
				resourcePath = ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, \
				resource = sensorDataListener)
			
			# Register the callbacks with the data message listener instance
			self.dataMsgListener.setTelemetryDataListener(listener = sensorDataListener)
			self.dataMsgListener.setSystemPerformanceDataListener(listener = sysPerfDataListener)
			
			logging.info("Created CoAP server with default resources.")
			
		except Exception as e:
			traceback.print_exception(type(e), e, e.__traceback__)
			logging.warning(f"Failed to create Async CoAP Server at {self.serverUri}")
	
	async def _runServer(self):
		if self.rootResource:
			logging.info("Creating Async CoAP Server context...")

			try:
				bindTuple = (self.host, self.port)
				
				self.coapServer = \
					await aiocoap.Context.create_server_context( \
						site = self.rootResource, \
						bind = bindTuple)

				logging.info("Initializing Async CoAP Server Task...")

				self._serverTask = asyncio.current_task()

				await self._keepServerRunning()

			except asyncio.CancelledError:
				logging.info("Server coroutine cancelled.")

			except Exception as e:
				logging.exception(f"Failed to spin up Async CoAP Server task: {e}")

		else:
			logging.warning("Root resource not yet created. Can't start server.")
	
	def _runServerTask(self):
		logging.info("Starting Async CoAP Server task...")

		asyncio.set_event_loop(self._eventLoopThread)

		try:
			self._eventLoopThread.run_until_complete(self._runServer())

		except asyncio.CancelledError:
			logging.info("Server task cancelled.")

		except Exception as e:
			logging.exception(f"Error starting Async CoAP Server task: {e}")
			traceback.print_exception(type(e), e, e.__traceback__)

		finally:
			pendingTasks = asyncio.all_tasks(self._eventLoopThread)

			try:
				for task in pendingTasks:
					task.cancel()

				if pendingTasks:
					self._eventLoopThread.run_until_complete(
						asyncio.gather(*pendingTasks, return_exceptions = True))

				self._eventLoopThread.close()

			except Exception as e:
				logging.exception(f"Async CoAP Server event loop thread exception: {e}")
				traceback.print_exception(type(e), e, e.__traceback__)

			logging.info("Successfully closed Async CoAP Server event loop.")
	
	async def _keepServerRunning(self):
		try:
			logging.info("Initializing Async CoAP Server shutdown future...")

			self._shutdownFuture = asyncio.get_running_loop().create_future()

			await self._shutdownFuture

		except asyncio.CancelledError:
			logging.info("Server keep-alive cancelled.")

		except Exception as e:
			logging.info("Async CoAP Server future cancelled [OK]")
	
	async def _shutdownServer(self):
		try:
			if self.coapServer:
				logging.info(f"Shutting down Async CoAP Server at {self.serverUri}")

				await self.coapServer.shutdown()

				self.coapServer = None

				if hasattr(self, "_shutdownFuture") and not self._shutdownFuture.done():
					self._shutdownFuture.set_result(None)

				if self._serverTask and not self._serverTask.done():
					self._serverTask.cancel()

					with suppress(asyncio.exceptions.CancelledError):
						await self._serverTask

				logging.info("Async CoAP Server shutdown completed.")

		except Exception as e:
			logging.warning("Failed to shutdown Async CoAP server.")
			traceback.print_exception(type(e), e, e.__traceback__)
