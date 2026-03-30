from dataclasses import dataclass, field
from typing import Optional


VALID_PRIORITIES = {"low", "medium", "high"}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"
    pet: Optional["Pet"] = None
    frequency: str = "daily"
    completed: bool = False

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of: {VALID_PRIORITIES}"
            )

    def __str__(self) -> str:
        pet_name = self.pet.name if self.pet else "No pet"
        status = "completed" if self.completed else "pending"
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority={self.priority}, pet={pet_name}, "
            f"frequency={self.frequency}, status={status})"
        )

    def mark_complete(self) -> None:
        self.completed = True

    def is_high_priority(self) -> bool:
        return self.priority == "high"


@dataclass
class Pet:
    name: str
    species: str
    age: Optional[int] = None
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        task.pet = self
        self.tasks.append(task)

    def get_pending_tasks(self) -> list:
        return [task for task in self.tasks if not task.completed]

    def __str__(self) -> str:
        age_str = f", age={self.age}" if self.age is not None else ""
        return (
            f"Pet(name={self.name}, species={self.species}{age_str}, "
            f"tasks={len(self.tasks)})"
        )


class Owner:
    def __init__(self, name: str, available_minutes: int):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def get_all_tasks(self) -> list:
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_all_pending_tasks(self) -> list:
        pending = []
        for pet in self.pets:
            pending.extend(pet.get_pending_tasks())
        return pending

    def __str__(self) -> str:
        return (
            f"Owner(name={self.name}, available_minutes={self.available_minutes}, "
            f"pets={len(self.pets)})"
        )


class Scheduler:
    PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}

    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: list[Task] = []

    def build_plan(self) -> None:
        self.schedule = []
        pending_tasks = self.owner.get_all_pending_tasks()
        sorted_tasks = sorted(
            pending_tasks,
            key=lambda t: self.PRIORITY_ORDER.get(t.priority, 99)
        )
        time_used = 0
        for task in sorted_tasks:
            if time_used + task.duration_minutes <= self.owner.available_minutes:
                self.schedule.append(task)
                time_used += task.duration_minutes

    def explain_plan(self) -> str:
        if not self.schedule:
            return "No plan built yet. Call build_plan() first."

        lines = [f"Scheduled plan for {self.owner.name}:"]
        total_time = 0
        for i, task in enumerate(self.schedule, start=1):
            pet_name = task.pet.name if task.pet else "No pet"
            lines.append(
                f"  {i}. {task.title} — {task.duration_minutes}min, "
                f"priority={task.priority}, pet={pet_name}, "
                f"frequency={task.frequency}"
            )
            total_time += task.duration_minutes

        lines.append(f"\nTotal time used: {total_time} min")

        all_pending = self.owner.get_all_pending_tasks()
        skipped = [t for t in all_pending if t not in self.schedule]
        if skipped:
            skipped_titles = ", ".join(t.title for t in skipped)
            lines.append(f"Skipped tasks (exceeded available time): {skipped_titles}")

        return "\n".join(lines)

    def get_tasks_by_priority(self, priority: str) -> list:
        return [task for task in self.schedule if task.priority == priority]
