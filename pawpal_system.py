from dataclasses import dataclass
from typing import Optional


VALID_PRIORITIES = {"low", "medium", "high"}


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None

    def __str__(self) -> str:
        pass


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str = "medium"
    pet: Optional[Pet] = None

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"Invalid priority '{self.priority}'. Must be one of: {VALID_PRIORITIES}")

    def __str__(self) -> str:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        pass

    def __str__(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: list[CareTask] = []
        self.schedule: list[CareTask] = []

    def add_task(self, task: CareTask) -> None:
        pass

    def build_plan(self) -> None:
        self.schedule = []  # reset on every call

    def explain_plan(self) -> str:
        if not self.schedule:
            return "No plan built yet. Call build_plan() first."
