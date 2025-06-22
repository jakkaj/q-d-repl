"""Debug Adapter Protocol (DAP) message definitions using Pydantic."""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DAPRequest(BaseModel):
    """DAP request message structure."""
    model_config = ConfigDict(extra='allow')
    
    seq: int
    type: str = "request"
    command: str
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DAPResponse(BaseModel):
    """DAP response message structure."""
    model_config = ConfigDict(extra='allow')
    
    seq: int
    type: str = "response"
    request_seq: int
    success: bool
    command: str
    message: Optional[str] = None
    body: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DAPEvent(BaseModel):
    """DAP event message structure."""
    model_config = ConfigDict(extra='allow')
    
    seq: int
    type: str = "event"
    event: str
    body: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DAPMessage(BaseModel):
    """Generic DAP message that can be any of the above types."""
    model_config = ConfigDict(extra='allow')
    
    seq: int
    type: str  # "request", "response", or "event"


# Specific DAP request/response models for type safety

class InitializeArguments(BaseModel):
    """Arguments for initialize request."""
    model_config = ConfigDict(extra='allow')
    
    clientID: Optional[str] = None
    clientName: Optional[str] = None
    adapterID: str
    locale: Optional[str] = "en-us"
    linesStartAt1: bool = True
    columnsStartAt1: bool = True
    pathFormat: str = "path"
    supportsVariableType: bool = True
    supportsVariablePaging: bool = True
    supportsRunInTerminalRequest: bool = False


class InitializeResponse(BaseModel):
    """Response body for initialize request."""
    model_config = ConfigDict(extra='allow')
    
    supportsConfigurationDoneRequest: bool = True
    supportsEvaluateForHovers: bool = True
    supportsConditionalBreakpoints: bool = False
    supportsSetVariable: bool = True
    supportsRestartRequest: bool = False
    supportsGotoTargetsRequest: bool = False
    supportsCompletionsRequest: bool = False
    supportsModulesRequest: bool = False
    supportsRestartFrame: bool = False
    supportsValueFormattingOptions: bool = True
    supportsExceptionInfoRequest: bool = False
    supportTerminateDebuggee: bool = True
    supportsDelayedStackTraceLoading: bool = True


class Source(BaseModel):
    """Source file reference."""
    model_config = ConfigDict(extra='allow')
    
    name: Optional[str] = None
    path: Optional[str] = None
    sourceReference: Optional[int] = None
    presentationHint: Optional[str] = None
    origin: Optional[str] = None
    sources: Optional[List['Source']] = None
    adapterData: Optional[Any] = None
    checksums: Optional[List[Dict[str, str]]] = None


class Breakpoint(BaseModel):
    """Breakpoint information."""
    model_config = ConfigDict(extra='allow')
    
    id: Optional[int] = None
    verified: bool = False
    message: Optional[str] = None
    source: Optional[Source] = None
    line: Optional[int] = None
    column: Optional[int] = None
    endLine: Optional[int] = None
    endColumn: Optional[int] = None
    instructionReference: Optional[str] = None
    offset: Optional[int] = None


class SourceBreakpoint(BaseModel):
    """Source breakpoint specification."""
    model_config = ConfigDict(extra='allow')
    
    line: int
    column: Optional[int] = None
    condition: Optional[str] = None
    hitCondition: Optional[str] = None
    logMessage: Optional[str] = None


class SetBreakpointsArguments(BaseModel):
    """Arguments for setBreakpoints request."""
    model_config = ConfigDict(extra='allow')
    
    source: Source
    breakpoints: Optional[List[SourceBreakpoint]] = Field(default_factory=list)
    lines: Optional[List[int]] = None
    sourceModified: bool = False


class SetBreakpointsResponse(BaseModel):
    """Response body for setBreakpoints request."""
    model_config = ConfigDict(extra='allow')
    
    breakpoints: List[Breakpoint]


class LaunchArguments(BaseModel):
    """Base arguments for launch request."""
    model_config = ConfigDict(extra='allow')
    
    noDebug: bool = False
    restart: Optional[Dict[str, Any]] = None


class AttachArguments(BaseModel):
    """Base arguments for attach request."""
    model_config = ConfigDict(extra='allow')
    
    restart: Optional[Dict[str, Any]] = None


class Thread(BaseModel):
    """Thread information."""
    model_config = ConfigDict(extra='allow')
    
    id: int
    name: str


class ThreadsResponse(BaseModel):
    """Response body for threads request."""
    model_config = ConfigDict(extra='allow')
    
    threads: List[Thread]


class StackFrame(BaseModel):
    """Stack frame information."""
    model_config = ConfigDict(extra='allow')
    
    id: int
    name: str
    source: Optional[Source] = None
    line: int
    column: int
    endLine: Optional[int] = None
    endColumn: Optional[int] = None
    canRestart: bool = False
    instructionPointerReference: Optional[str] = None
    moduleId: Optional[Union[int, str]] = None
    presentationHint: Optional[str] = None


class StackTraceArguments(BaseModel):
    """Arguments for stackTrace request."""
    model_config = ConfigDict(extra='allow')
    
    threadId: int
    startFrame: Optional[int] = 0
    levels: Optional[int] = None
    format: Optional[Dict[str, Any]] = None


class StackTraceResponse(BaseModel):
    """Response body for stackTrace request."""
    model_config = ConfigDict(extra='allow')
    
    stackFrames: List[StackFrame]
    totalFrames: Optional[int] = None


class Scope(BaseModel):
    """Scope information."""
    model_config = ConfigDict(extra='allow')
    
    name: str
    presentationHint: Optional[str] = None
    variablesReference: int
    namedVariables: Optional[int] = None
    indexedVariables: Optional[int] = None
    expensive: bool = False
    source: Optional[Source] = None
    line: Optional[int] = None
    column: Optional[int] = None
    endLine: Optional[int] = None
    endColumn: Optional[int] = None


class ScopesArguments(BaseModel):
    """Arguments for scopes request."""
    model_config = ConfigDict(extra='allow')
    
    frameId: int


class ScopesResponse(BaseModel):
    """Response body for scopes request."""
    model_config = ConfigDict(extra='allow')
    
    scopes: List[Scope]


class Variable(BaseModel):
    """Variable information."""
    model_config = ConfigDict(extra='allow')
    
    name: str
    value: str
    type: Optional[str] = None
    presentationHint: Optional[Dict[str, Any]] = None
    evaluateName: Optional[str] = None
    variablesReference: int = 0
    namedVariables: Optional[int] = None
    indexedVariables: Optional[int] = None
    memoryReference: Optional[str] = None


class VariablesArguments(BaseModel):
    """Arguments for variables request."""
    model_config = ConfigDict(extra='allow')
    
    variablesReference: int
    filter: Optional[str] = None
    start: Optional[int] = None
    count: Optional[int] = None
    format: Optional[Dict[str, Any]] = None


class VariablesResponse(BaseModel):
    """Response body for variables request."""
    model_config = ConfigDict(extra='allow')
    
    variables: List[Variable]


class EvaluateArguments(BaseModel):
    """Arguments for evaluate request."""
    model_config = ConfigDict(extra='allow')
    
    expression: str
    frameId: Optional[int] = None
    context: Optional[str] = "repl"  # "watch", "repl", "hover", "clipboard"
    format: Optional[Dict[str, Any]] = None


class EvaluateResponse(BaseModel):
    """Response body for evaluate request."""
    model_config = ConfigDict(extra='allow')
    
    result: str
    type: Optional[str] = None
    presentationHint: Optional[Dict[str, Any]] = None
    variablesReference: int = 0
    namedVariables: Optional[int] = None
    indexedVariables: Optional[int] = None
    memoryReference: Optional[str] = None


class StoppedEventBody(BaseModel):
    """Body for stopped event."""
    model_config = ConfigDict(extra='allow')
    
    reason: str  # "step", "breakpoint", "exception", "pause", "entry", "goto", "function breakpoint", "data breakpoint", "instruction breakpoint"
    description: Optional[str] = None
    threadId: Optional[int] = None
    preserveFocusHint: bool = False
    text: Optional[str] = None
    allThreadsStopped: bool = False
    hitBreakpointIds: Optional[List[int]] = None


class ContinuedEventBody(BaseModel):
    """Body for continued event."""
    model_config = ConfigDict(extra='allow')
    
    threadId: int
    allThreadsContinued: bool = False


class ExitedEventBody(BaseModel):
    """Body for exited event."""
    model_config = ConfigDict(extra='allow')
    
    exitCode: int


class TerminatedEventBody(BaseModel):
    """Body for terminated event."""
    model_config = ConfigDict(extra='allow')
    
    restart: Optional[Dict[str, Any]] = None


class OutputEventBody(BaseModel):
    """Body for output event."""
    model_config = ConfigDict(extra='allow')
    
    category: Optional[str] = "console"  # "console", "stdout", "stderr", "telemetry"
    output: str
    group: Optional[str] = None
    variablesReference: Optional[int] = None
    source: Optional[Source] = None
    line: Optional[int] = None
    column: Optional[int] = None
    data: Optional[Any] = None


class DisconnectArguments(BaseModel):
    """Arguments for disconnect request."""
    model_config = ConfigDict(extra='allow')
    
    restart: bool = False
    terminateDebuggee: bool = False
    suspendDebuggee: bool = False


# Update forward references
Source.model_rebuild()