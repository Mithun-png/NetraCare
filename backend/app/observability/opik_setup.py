"""Opik Tracing & Observability Setup for NetraCare.
Implements Requirement R1:
- Configures Opik projects: `netracare-dev` (default) and `netracare-evals`.
- Traces chat turns, red flag checks, doctor summaries, and Fact of the Day.
- Provides LangChain integration (`OpikTracer`) and function tracking (`track`).
- Graceful degradation: if OPIK_API_KEY is missing or Opik is offline,
  all decorators and tracers return no-op mocks and the app continues seamlessly.
"""
import os
import functools
import logging
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger(__name__)

# Check for Opik API key in environment
OPIK_API_KEY = os.getenv("OPIK_API_KEY", "").strip()

try:
    import opik
    from opik import track as _real_track
    from opik.integrations.langchain import OpikTracer as _RealOpikTracer
    _OPIK_AVAILABLE = True
except ImportError:
    _OPIK_AVAILABLE = False
    _real_track = None
    _RealOpikTracer = None


def is_opik_enabled() -> bool:
    """Return True if Opik is installed and configured with an API key."""
    return bool(_OPIK_AVAILABLE and os.getenv("OPIK_API_KEY", "").strip())


try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    class BaseCallbackHandler:
        pass

class NoOpCallbackHandler(BaseCallbackHandler):
    """Fallback no-op callback handler when Opik is disabled or unavailable."""
    def flush(self): pass


def get_opik_tracer(
    project_name: str = "netracare-dev",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Return an OpikTracer instance for LangChain / LangGraph, or None if disabled."""
    if is_opik_enabled() and _RealOpikTracer is not None:
        try:
            return _RealOpikTracer(
                project_name=project_name,
                tags=tags or [],
                metadata=metadata or {}
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpikTracer: {e}. Falling back to None.")
            return None
    return None


def track_op(
    name: Optional[str] = None,
    project_name: str = "netracare-dev",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    capture_input: bool = True,
    capture_output: bool = True,
):
    """Decorator to trace functions in Opik with graceful fallback if Opik is disabled."""
    def decorator(fn: Callable):
        if is_opik_enabled() and _real_track is not None:
            try:
                opik_decorator = _real_track(
                    name=name or fn.__name__,
                    project_name=project_name,
                    tags=tags,
                    metadata=metadata,
                    capture_input=capture_input,
                    capture_output=capture_output,
                )
                return opik_decorator(fn)
            except Exception as e:
                logger.warning(f"Could not apply opik @track to {fn.__name__}: {e}")

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def flush_opik():
    """Flush pending traces to Opik if enabled."""
    if is_opik_enabled():
        try:
            opik.flush_tracker()
        except Exception as e:
            logger.debug(f"Opik flush error: {e}")
