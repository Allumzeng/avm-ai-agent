import json
from dataclasses import dataclass, field


@dataclass
class WizardState:
    wizard_type: str          # "setup" | "diagnosis"
    current_step: int = 0
    collected_data: dict = field(default_factory=dict)
    is_complete: bool = False

    def to_json(self) -> str:
        return json.dumps(
            {
                "wizard_type": self.wizard_type,
                "current_step": self.current_step,
                "collected_data": self.collected_data,
                "is_complete": self.is_complete,
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def from_json(cls, data: str) -> "WizardState":
        d = json.loads(data)
        return cls(
            wizard_type=d["wizard_type"],
            current_step=d["current_step"],
            collected_data=d["collected_data"],
            is_complete=d["is_complete"],
        )
