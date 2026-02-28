from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PlanStep:
    """Intermediate representation step for discourse planning."""
    role: str  # "anchor", "lead", "clause"
    text: str
    prefix: Optional[str] = None


@dataclass
class TemporalPlan:
    """Intermediate compiled plan for multi-sentence LTL translations."""
    steps: List[PlanStep] = field(default_factory=list)

    def add_anchor(self, text: str) -> None:
        self.steps.append(PlanStep(role="anchor", text=text))

    def add_lead(self, text: str) -> None:
        self.steps.append(PlanStep(role="lead", text=text))

    def add_clause(self, text: str, prefix: Optional[str] = None) -> None:
        self.steps.append(PlanStep(role="clause", text=text, prefix=prefix))
