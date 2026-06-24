from datetime import datetime, timezone
from uuid import uuid4

from app.models.run import Run, RunEvent, Step, Task
from modules.demo_agent import run_demo_agent_state_machine


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}
        self._events: dict[str, list[RunEvent]] = {}

    def create_run(self, task_input: str) -> Run:
        task = Task(id=self._new_id("task"), input=task_input)
        run = Run(id=self._new_id("run"), status="pending", task=task)
        self._runs[run.id] = run
        self._events[run.id] = []
        self._add_event(run.id, "run.created", "Run created")

        run.status = "running"
        self._add_event(run.id, "run.started", "Run started")

        state = run_demo_agent_state_machine(task_input)
        for node_trace in state.node_traces:
            step = Step(id=self._new_id("step"), name=node_trace.name, status="running")
            run.steps.append(step)
            self._add_event(run.id, "node.started", f"{node_trace.name} started")

            step.status = "completed"
            step.output = node_trace.output
            step.completed_at = self._utc_now()
            self._add_event(run.id, "node.completed", f"{node_trace.name} completed")

        run.status = "completed"
        run.output = state.final_output
        run.completed_at = self._utc_now()
        self._add_event(run.id, "run.completed", "Run completed")

        return run

    def get_run(self, run_id: str) -> Run | None:
        return self._runs.get(run_id)

    def get_events(self, run_id: str) -> list[RunEvent] | None:
        events = self._events.get(run_id)
        if events is None:
            return None
        return list(events)

    def _add_event(self, run_id: str, event_type: str, message: str) -> None:
        self._events[run_id].append(RunEvent(type=event_type, message=message))

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)


run_store = RunStore()
