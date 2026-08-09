"""
Pipeline base class — the orchestrator abstraction used by every concrete
pipeline in :mod:`electpynasa.pipelines`.

A pipeline is a deterministic, ordered sequence of *steps*. Each step:

* has a unique label (used for logging / progress reporting);
* receives a mutable *context* dictionary;
* returns a :class:`~electpynasa.core.types.StepOutcome`;
* may raise :class:`~electpynasa.utils.exceptions.PipelineStepError` to abort
  the run.

Pipelines are designed to be:

* **Observable** — every step emits a structured log + progress update.
* **Resilient** — failures are wrapped in a typed exception with full context.
* **Composable** — a step can itself be a sub-pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from electpynasa.core.types import StepOutcome
from electpynasa.utils.exceptions import PipelineStepError
from electpynasa.utils.logging import ScientificLogger


# A step is any callable accepting a context dict and returning a StepOutcome.
StepCallable = Callable[[dict[str, Any]], StepOutcome]


class Pipeline(ABC):
    """Base class for every ElectPyNasa pipeline."""

    #: Human-readable name (used in log messages).
    name: str = "pipeline"

    def __init__(self) -> None:
        self._steps: list[tuple[str, StepCallable]] = []

    # ------------------------------------------------------------------
    # Registration API
    # ------------------------------------------------------------------
    def add_step(self, label: str, step: StepCallable) -> "Pipeline":
        """Append *step* to the pipeline. Returns ``self`` for chaining."""
        if not label:
            raise ValueError("Pipeline step label cannot be empty")
        self._steps.append((label, step))
        return self

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def run(self, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Execute every step in order, threading *context* through them.

        The method emits one structured log per step (with progress) and
        converts any unexpected exception into a :class:`PipelineStepError`.
        """
        ctx = dict(context or {})
        ctx.setdefault("pipeline", self.name)
        ctx.setdefault("outcomes", [])

        ScientificLogger.info(f"Pipeline '{self.name}' started.",
                              progress=0.0, extra={"steps": [s[0] for s in self._steps]})

        total = max(len(self._steps), 1)
        for index, (label, step) in enumerate(self._steps, start=1):
            progress = (index - 1) / total * 100.0
            ScientificLogger.info(f"Step {index}/{total}: {label}", progress=progress)
            try:
                outcome: StepOutcome = step(ctx)
            except PipelineStepError:
                raise
            except Exception as exc:  # noqa: BLE001 - wrap for stability
                ScientificLogger.error(
                    f"Step '{label}' raised {type(exc).__name__}: {exc}",
                    extra={"step": label, "error_type": type(exc).__name__},
                )
                raise PipelineStepError(label, str(exc)) from exc

            ctx["outcomes"].append(outcome)
            ScientificLogger.info(
                f"Step '{label}' completed.",
                progress=index / total * 100.0,
                extra={"notes": outcome.notes} if outcome.notes else None,
            )

        ScientificLogger.info(f"Pipeline '{self.name}' completed.", progress=100.0)
        return ctx

    # ------------------------------------------------------------------
    # Subclass hook
    # ------------------------------------------------------------------
    @abstractmethod
    def build(self) -> None:
        """Register all steps. Subclasses must implement this method."""
        raise NotImplementedError
