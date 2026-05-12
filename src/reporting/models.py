import json
from dataclasses import dataclass, field
from typing import Literal

ReportType = Literal["profitability", "capacity", "attribute", "value_object"]


@dataclass
class ReportState:
    report_type: ReportType
    source_data: dict
    report_text: str = ""
    anomalies: list[str] = field(default_factory=list)
    is_complete: bool = False

    def to_json(self) -> str:
        return json.dumps(
            {
                "report_type": self.report_type,
                "source_data": self.source_data,
                "report_text": self.report_text,
                "anomalies": self.anomalies,
                "is_complete": self.is_complete,
            },
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, data: str) -> "ReportState":
        d = json.loads(data)
        return cls(
            report_type=d["report_type"],
            source_data=d["source_data"],
            report_text=d["report_text"],
            anomalies=d["anomalies"],
            is_complete=d["is_complete"],
        )
