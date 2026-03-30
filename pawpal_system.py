from dataclasses import dataclass, field
from typing import Optional


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
        pass

    def explain_plan(self) -> str:
        pass
