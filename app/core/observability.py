from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObservabilityState:
    def __init__(self) -> None:
        self._lock = RLock()
        self._traces: dict[str, dict[str, Any]] = {}
        self._logs: list[dict[str, Any]] = []
        self._timelines: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._audit_events: list[dict[str, Any]] = []

    def clear(self) -> None:
        with self._lock:
            self._traces.clear()
            self._logs.clear()
            self._timelines.clear()
            self._audit_events.clear()

    def start_trace(
        self,
        *,
        trace_id: str,
        correlation_id: str,
        method: str,
        path: str,
    ) -> dict[str, Any]:
        trace = {
            "trace_id": trace_id,
            "correlation_id": correlation_id,
            "method": method,
            "path": path,
            "status": "IN_PROGRESS",
            "status_code": None,
            "started_at": utc_now_iso(),
            "completed_at": None,
            "duration_ms": None,
        }
        with self._lock:
            self._traces[trace_id] = trace
        return deepcopy(trace)

    def finish_trace(
        self,
        *,
        trace_id: str,
        status_code: int,
        duration_ms: float,
    ) -> dict[str, Any] | None:
        with self._lock:
            trace = self._traces.get(trace_id)
            if trace is None:
                return None

            trace["status"] = "COMPLETED"
            trace["status_code"] = status_code
            trace["completed_at"] = utc_now_iso()
            trace["duration_ms"] = round(duration_ms, 3)
            return deepcopy(trace)

    def get_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self._lock:
            trace = self._traces.get(trace_id)
            return deepcopy(trace) if trace is not None else None

    def add_log(
        self,
        *,
        level: str,
        event: str,
        message: str,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        log = {
            "log_id": str(uuid4()),
            "timestamp": utc_now_iso(),
            "level": level.upper(),
            "event": event,
            "message": message,
            "correlation_id": correlation_id,
            "trace_id": trace_id,
            "context": context or {},
        }
        with self._lock:
            self._logs.append(log)
        return deepcopy(log)

    def list_logs(
        self,
        *,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        level: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._lock:
            logs = list(self._logs)

        if correlation_id is not None:
            logs = [
                item for item in logs
                if item["correlation_id"] == correlation_id
            ]
        if trace_id is not None:
            logs = [
                item for item in logs
                if item["trace_id"] == trace_id
            ]
        if level is not None:
            normalized_level = level.upper()
            logs = [
                item for item in logs
                if item["level"] == normalized_level
            ]

        return deepcopy(logs[-max(1, limit):])

    def add_timeline_event(
        self,
        *,
        correlation_id: str,
        event: str,
        elapsed_ms: float,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        timeline_event = {
            "event_id": str(uuid4()),
            "timestamp": utc_now_iso(),
            "event": event,
            "elapsed_ms": round(elapsed_ms, 3),
            "details": details or {},
        }
        with self._lock:
            self._timelines[correlation_id].append(timeline_event)
        return deepcopy(timeline_event)

    def get_timeline(self, correlation_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self._timelines.get(correlation_id, []))

    def add_audit_event(
        self,
        *,
        event_type: str,
        actor: str,
        resource: str,
        action: str,
        outcome: str,
        correlation_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "audit_event_id": str(uuid4()),
            "timestamp": utc_now_iso(),
            "event_type": event_type,
            "actor": actor,
            "resource": resource,
            "action": action,
            "outcome": outcome,
            "correlation_id": correlation_id,
            "details": details or {},
        }
        with self._lock:
            self._audit_events.append(event)
        return deepcopy(event)

    def list_audit_events(
        self,
        *,
        event_type: str | None = None,
        actor: str | None = None,
        correlation_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._lock:
            events = list(self._audit_events)

        if event_type is not None:
            events = [
                item for item in events
                if item["event_type"] == event_type
            ]
        if actor is not None:
            events = [
                item for item in events
                if item["actor"] == actor
            ]
        if correlation_id is not None:
            events = [
                item for item in events
                if item["correlation_id"] == correlation_id
            ]

        return deepcopy(events[-max(1, limit):])


observability_state = ObservabilityState()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or str(uuid4())
        )
        trace_id = (
            request.headers.get("X-Trace-ID")
            or str(uuid4())
        )
        started = perf_counter()

        request.state.correlation_id = correlation_id
        request.state.trace_id = trace_id

        observability_state.start_trace(
            trace_id=trace_id,
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )
        observability_state.add_timeline_event(
            correlation_id=correlation_id,
            event="REQUEST_STARTED",
            elapsed_ms=0.0,
            details={
                "method": request.method,
                "path": request.url.path,
                "trace_id": trace_id,
            },
        )
        observability_state.add_log(
            level="INFO",
            event="REQUEST_STARTED",
            message=f"{request.method} {request.url.path}",
            correlation_id=correlation_id,
            trace_id=trace_id,
            context={
                "method": request.method,
                "path": request.url.path,
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (perf_counter() - started) * 1000
            observability_state.finish_trace(
                trace_id=trace_id,
                status_code=500,
                duration_ms=duration_ms,
            )
            observability_state.add_timeline_event(
                correlation_id=correlation_id,
                event="REQUEST_FAILED",
                elapsed_ms=duration_ms,
                details={
                    "error_type": type(exc).__name__,
                    "trace_id": trace_id,
                },
            )
            observability_state.add_log(
                level="ERROR",
                event="REQUEST_FAILED",
                message=str(exc),
                correlation_id=correlation_id,
                trace_id=trace_id,
                context={
                    "error_type": type(exc).__name__,
                    "path": request.url.path,
                },
            )
            raise

        duration_ms = (perf_counter() - started) * 1000

        observability_state.finish_trace(
            trace_id=trace_id,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        observability_state.add_timeline_event(
            correlation_id=correlation_id,
            event="REQUEST_COMPLETED",
            elapsed_ms=duration_ms,
            details={
                "status_code": response.status_code,
                "trace_id": trace_id,
            },
        )
        observability_state.add_log(
            level="INFO",
            event="REQUEST_COMPLETED",
            message=f"{request.method} {request.url.path}",
            correlation_id=correlation_id,
            trace_id=trace_id,
            context={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 3),
            },
        )

        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time-Ms"] = str(
            round(duration_ms, 3)
        )
        return response
