"""Data model and scheduling logic for the PawPal+ pet care planner."""
from dataclasses import dataclass, field
from typing import Optional


VALID_PRIORITIES = {"low", "medium", "high"}


@dataclass
class Task:
    """Represents a single pet care activity with a duration and priority."""

    title: str
    duration_minutes: int
    priority: str = "medium"
    pet: Optional["Pet"] = None
    frequency: str = "daily"
    completed: bool = False

    def __post_init__(self):
        """Validate that priority is one of the allowed values."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of: {VALID_PRIORITIES}"
            )

    def __str__(self) -> str:
        """Return a readable string representation of the task."""
        pet_name = self.pet.name if self.pet else "No pet"
        status = "completed" if self.completed else "pending"
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority={self.priority}, pet={pet_name}, "
            f"frequency={self.frequency}, status={status})"
        )

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"


@dataclass
class Pet:
    """Represents a pet and the care tasks associated with it."""

    name: str
    species: str
    age: Optional[int] = None
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and append it to the task list."""
        task.pet = self
        self.tasks.append(task)

    def get_pending_tasks(self) -> list:
        """Return all tasks that have not yet been completed."""
        return [task for task in self.tasks if not task.completed]

    def __str__(self) -> str:
        """Return a readable string representation of the pet."""
        age_str = f", age={self.age}" if self.age is not None else ""
        return (
            f"Pet(name={self.name}, species={self.species}{age_str}, "
            f"tasks={len(self.tasks)})"
        )


class Owner:
    """Represents the pet owner, their available time, and their pets."""

    def __init__(self, name: str, available_minutes: int):
        """Initialize the owner with a name and daily time budget."""
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list:
        """Return every task across all of the owner's pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_all_pending_tasks(self) -> list:
        """Return all incomplete tasks across every pet."""
        pending = []
        for pet in self.pets:
            pending.extend(pet.get_pending_tasks())
        return pending

    def __str__(self) -> str:
        """Return a readable string representation of the owner."""
        return (
            f"Owner(name={self.name}, available_minutes={self.available_minutes}, "
            f"pets={len(self.pets)})"
        )


class Scheduler:
    """Builds and explains a priority-ordered daily care plan within a time budget."""

    PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}

    def __init__(self, owner: Owner):
        """Initialize the scheduler with an owner whose tasks will be planned."""
        self.owner = owner
        self.schedule: list[Task] = []

    def build_plan(self) -> None:
        """Select and order tasks by priority until the owner's time budget is filled."""
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
        """Return a human-readable summary of the scheduled tasks and any skipped ones."""
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
        """Return all scheduled tasks matching the given priority level."""
        return [task for task in self.schedule if task.priority == priority]
