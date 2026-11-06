from dataclasses import dataclass, field

@dataclass
class Passage:
    id: str
    title: str
    text: str
    source: str
    score: float
    meta: dict = field(default_factory=dict)

@dataclass
class Retrieval:
    name: str
    passages: list = field(default_factory=list)
    gap: str | None = None
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.passages is None:
            self.passages = []
        if self.meta is None:
            self.meta = {}
