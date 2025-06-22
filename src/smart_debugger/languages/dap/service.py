"""Generic DAP service for communicating with debug adapters."""

import json
import socket
import subprocess
import threading
import time
import queue
import os
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path

from .protocol import (
    DAPRequest, DAPResponse, DAPEvent, DAPMessage,
    InitializeArguments, InitializeResponse,
    SetBreakpointsArguments, SetBreakpointsResponse,
    StackTraceArguments, StackTraceResponse,
    EvaluateArguments, EvaluateResponse,
    StoppedEventBody, Source, SourceBreakpoint,
    DisconnectArguments
)


logger = logging.getLogger(__name__)


class DAPTransportError(Exception):
    """Exception for DAP transport errors."""
    pass


class DAPService:
    """Universal DAP client that works with any DAP-compliant debug adapter."""
    
    def __init__(self, adapter_config: Dict[str, Any]):
        """
        Initialize DAP service with adapter configuration.
        
        Args:
            adapter_config: Configuration dictionary containing:
                - command: List of command arguments to start adapter
                - transport: "stdio" or "tcp"
                - port: Port number for TCP transport
                - timeout: Optional timeout for operations
        """
        self.adapter_config = adapter_config
        self.command = adapter_config['command']
        self.transport = adapter_config.get('transport', 'stdio')
        self.port = adapter_config.get('port')
        self.timeout = adapter_config.get('timeout', 30)
        
        # State
        self.process = None
        self.socket = None
        self.seq = 0
        self.running = False
        self.capabilities = {}
        
        # Message handling
        self.pending_responses: Dict[int, queue.Queue] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.events_queue = queue.Queue()
        self.message_thread = None
        self.stop_event = threading.Event()
    
    def start_adapter(self) -> bool:
        """
        Start the debug adapter based on configuration.
        
        Returns:
            True if adapter started successfully
        """
        try:
            logger.info(f"Starting adapter with command: {self.command}")
            
            if self.transport == 'stdio':
                self.process = subprocess.Popen(
                    self.command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=0  # Unbuffered for real-time communication
                )
                logger.info("Adapter started with stdio transport")
                
            elif self.transport == 'tcp':
                if not self.port:
                    raise ValueError("Port required for TCP transport")
                
                # Start adapter in server mode
                cmd = self.command.copy()
                cmd.extend(['--server', f'--port={self.port}'])
                
                self.process = subprocess.Popen(
                    cmd,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for server to start and connect
                time.sleep(2)
                self._connect_tcp()
                logger.info(f"Adapter started with TCP transport on port {self.port}")
            
            else:
                raise ValueError(f"Unsupported transport: {self.transport}")
            
            self.running = True
            self._start_message_handler()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start adapter: {e}")
            self._cleanup()
            return False
    
    def _connect_tcp(self):
        """Connect to TCP debug adapter."""
        for attempt in range(10):  # Try up to 10 times
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect(('localhost', self.port))
                self.socket.settimeout(self.timeout)
                logger.info(f"Connected to TCP adapter on port {self.port}")
                return
            except ConnectionRefusedError:
                time.sleep(0.5)
                continue
        
        raise DAPTransportError(f"Could not connect to TCP adapter on port {self.port}")
    
    def _start_message_handler(self):
        """Start the message handling thread."""
        self.message_thread = threading.Thread(
            target=self._handle_messages,
            daemon=True
        )
        self.message_thread.start()
        logger.debug("Message handler thread started")
    
    def _handle_messages(self):
        """Handle incoming messages from the adapter."""
        try:
            while self.running and not self.stop_event.is_set():
                try:
                    message = self._read_message()
                    if message:
                        self._process_message(message)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    break
        except Exception as e:
            logger.error(f"Message handler error: {e}")
        finally:
            logger.debug("Message handler thread stopped")
    
    def _read_message(self) -> Optional[Dict[str, Any]]:
        """Read a single DAP message."""
        if self.transport == 'stdio':
            return self._read_stdio_message()
        elif self.transport == 'tcp':
            return self._read_tcp_message()
        return None
    
    def _read_stdio_message(self) -> Optional[Dict[str, Any]]:
        """Read message from stdio."""
        if not self.process or not self.process.stdout:
            return None
        
        try:
            # Read Content-Length header
            while True:
                line = self.process.stdout.readline()
                if not line:
                    return None
                
                line = line.strip()
                if line.startswith('Content-Length:'):
                    content_length = int(line.split(':')[1].strip())
                    break
                elif line == '':
                    # Empty line before content
                    continue
            
            # Read empty line separator
            self.process.stdout.readline()
            
            # Read content
            content = self.process.stdout.read(content_length)
            if not content:
                return None
            
            return json.loads(content)
            
        except (json.JSONDecodeError, ValueError, IOError) as e:
            logger.error(f"Error reading stdio message: {e}")
            return None
    
    def _read_tcp_message(self) -> Optional[Dict[str, Any]]:
        """Read message from TCP socket."""
        if not self.socket:
            return None
        
        try:
            # Read headers
            headers = {}
            while True:
                line = self.socket.recv(1024).decode('utf-8')
                if not line:
                    return None
                
                if '\r\n\r\n' in line:
                    header_part, content_part = line.split('\r\n\r\n', 1)
                    for header_line in header_part.split('\r\n'):
                        if ':' in header_line:
                            key, value = header_line.split(':', 1)
                            headers[key.strip()] = value.strip()
                    
                    content_length = int(headers.get('Content-Length', 0))
                    remaining = content_length - len(content_part)
                    
                    if remaining > 0:
                        content_part += self.socket.recv(remaining).decode('utf-8')
                    
                    return json.loads(content_part)
            
        except (json.JSONDecodeError, socket.error, ValueError) as e:
            logger.error(f"Error reading TCP message: {e}")
            return None
    
    def _process_message(self, message_data: Dict[str, Any]):
        """Process an incoming DAP message."""
        try:
            msg_type = message_data.get('type')
            seq = message_data.get('seq')
            
            if msg_type == 'response':
                request_seq = message_data.get('request_seq')
                if request_seq in self.pending_responses:
                    self.pending_responses[request_seq].put(message_data)
                else:
                    logger.warning(f"Received response for unknown request: {request_seq}")
            
            elif msg_type == 'event':
                event_name = message_data.get('event')
                
                # Put event in general events queue
                self.events_queue.put(message_data)
                
                # Call registered handlers
                if event_name in self.event_handlers:
                    for handler in self.event_handlers[event_name]:
                        try:
                            handler(message_data)
                        except Exception as e:
                            logger.error(f"Error in event handler: {e}")
            
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message to the adapter."""
        try:
            content = json.dumps(message)
            header = f"Content-Length: {len(content)}\r\n\r\n"
            full_message = header + content
            
            if self.transport == 'stdio':
                if self.process and self.process.stdin:
                    self.process.stdin.write(full_message)
                    self.process.stdin.flush()
                    return True
            
            elif self.transport == 'tcp':
                if self.socket:
                    self.socket.sendall(full_message.encode('utf-8'))
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def _send_request(self, command: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a request and wait for response."""
        self.seq += 1
        request = DAPRequest(
            seq=self.seq,
            command=command,
            arguments=arguments or {}
        )
        
        # Create response queue
        response_queue = queue.Queue()
        self.pending_responses[self.seq] = response_queue
        
        try:
            # Send request
            if not self._send_message(request.model_dump()):
                raise DAPTransportError(f"Failed to send {command} request")
            
            # Wait for response
            try:
                response_data = response_queue.get(timeout=self.timeout)
                return response_data
            except queue.Empty:
                raise DAPTransportError(f"Timeout waiting for {command} response")
        
        finally:
            # Clean up
            if self.seq in self.pending_responses:
                del self.pending_responses[self.seq]
    
    def initialize(self, client_id: str = "smart-debugger") -> Dict[str, Any]:
        """Initialize the debug adapter."""
        args = InitializeArguments(
            clientID=client_id,
            clientName="Smart Debugger",
            adapterID=self.adapter_config.get('language', 'unknown')
        )
        
        response = self._send_request('initialize', args.model_dump())
        
        if response.get('success'):
            self.capabilities = response.get('body', {})
            logger.info("Adapter initialized successfully")
        else:
            logger.error(f"Adapter initialization failed: {response.get('message')}")
        
        return response
    
    def set_breakpoints(self, file_path: str, lines: List[int]) -> Dict[str, Any]:
        """Set breakpoints in a source file."""
        source = Source(path=file_path, name=os.path.basename(file_path))
        breakpoints = [SourceBreakpoint(line=line) for line in lines]
        
        args = SetBreakpointsArguments(
            source=source,
            breakpoints=breakpoints
        )
        
        response = self._send_request('setBreakpoints', args.model_dump())
        logger.debug(f"Set breakpoints at lines {lines} in {file_path}")
        return response
    
    def launch(self, launch_config: Dict[str, Any]) -> Dict[str, Any]:
        """Launch the program with the given configuration."""
        response = self._send_request('launch', launch_config)
        if response.get('success'):
            logger.info("Program launched successfully")
        else:
            logger.error(f"Program launch failed: {response.get('message')}")
        return response
    
    def attach(self, attach_config: Dict[str, Any]) -> Dict[str, Any]:
        """Attach to a running program."""
        response = self._send_request('attach', attach_config)
        if response.get('success'):
            logger.info("Attached to program successfully")
        else:
            logger.error(f"Attach failed: {response.get('message')}")
        return response
    
    def configuration_done(self) -> Dict[str, Any]:
        """Signal that configuration is complete."""
        response = self._send_request('configurationDone')
        logger.debug("Configuration done")
        return response
    
    def wait_for_event(self, event_name: str, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Wait for a specific event."""
        timeout = timeout or self.timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                event = self.events_queue.get(timeout=1)
                if event.get('event') == event_name:
                    return event
                else:
                    # Put it back for other waiters
                    self.events_queue.put(event)
            except queue.Empty:
                continue
        
        return None
    
    def get_stack_trace(self, thread_id: int) -> Dict[str, Any]:
        """Get stack trace for a thread."""
        args = StackTraceArguments(
            threadId=thread_id,
            startFrame=0,
            levels=20
        )
        
        response = self._send_request('stackTrace', args.model_dump())
        logger.debug(f"Got stack trace for thread {thread_id}")
        return response
    
    def evaluate(self, expression: str, frame_id: int, context: str = 'repl') -> Dict[str, Any]:
        """Evaluate an expression in the given frame context."""
        args = EvaluateArguments(
            expression=expression,
            frameId=frame_id,
            context=context
        )
        
        response = self._send_request('evaluate', args.model_dump())
        logger.debug(f"Evaluated expression: {expression}")
        return response
    
    def disconnect(self, terminate_debuggee: bool = True) -> Dict[str, Any]:
        """Disconnect from the debug adapter."""
        args = DisconnectArguments(
            terminateDebuggee=terminate_debuggee
        )
        
        try:
            response = self._send_request('disconnect', args.model_dump())
            logger.info("Disconnected from adapter")
            return response
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            self._cleanup()
    
    def add_event_handler(self, event_name: str, handler: Callable):
        """Add an event handler for a specific event type."""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        self.event_handlers[event_name].append(handler)
    
    def remove_event_handler(self, event_name: str, handler: Callable):
        """Remove an event handler."""
        if event_name in self.event_handlers:
            try:
                self.event_handlers[event_name].remove(handler)
            except ValueError:
                pass
    
    def _cleanup(self):
        """Clean up resources."""
        logger.debug("Cleaning up DAP service")
        
        self.running = False
        self.stop_event.set()
        
        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Terminate process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except:
                pass
            self.process = None
        
        # Wait for message thread
        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=2)
        
        # Clear pending responses
        for response_queue in self.pending_responses.values():
            try:
                response_queue.put({'success': False, 'message': 'Service stopped'})
            except:
                pass
        self.pending_responses.clear()
        
        logger.debug("DAP service cleanup complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup()