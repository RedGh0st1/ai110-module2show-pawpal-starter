"""Data model and scheduling logic for the PawPal+ pet care planner."""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


VALID_PRIORITIES = {"low", "medium", "high"}
VALID_TIMES = {"morning", "afternoon", "evening", "any"}

# Display order for time slots
TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "any": 3}

# Fraction of the daily budget allocated to each named slot (used for conflict detection)
SLOT_FRACTIONS = {"morning": 0.40, "afternoon": 0.35, "evening": 0.25}


@dataclass
class Task:
    """Represents a single pet care activity with a duration and priority."""

    title: str
    duration_minutes: int
    priority: str = "medium"
    pet: Optional["Pet"] = None
    frequency: str = "daily"
    completed: bool = False
    preferred_time: str = "any"
    last_scheduled_date: Optional[str] = None  # ISO format YYYY-MM-DD

    def __post_init__(self):
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of: {VALID_PRIORITIES}"
            )
        if self.preferred_time not in VALID_TIMES:
            raise ValueError(
                f"Invalid preferred_time '{self.preferred_time}'. Must be one of: {VALID_TIMES}"
            )

    def __str__(self) -> str:
        pet_name = self.pet.name if self.pet else "No pet"
        status = "completed" if self.completed else "pending"
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority={self.priority}, pet={pet_name}, "
            f"frequency={self.frequency}, time={self.preferred_time}, status={status})"
        )

    def mark_complete(self) -> None:
        """Mark this task as completed and record today's date for recurrence tracking."""
        self.completed = True
        self.last_scheduled_date = date.today().isoformat()

    def is_high_priority(self) -> bool:
        return self.priority == "high"

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule based on frequency."""
        if self.frequency in ("daily", "as needed"):
            return True
        if self.frequency == "weekly":
            if self.last_scheduled_date is None:
                return True
            last = date.fromisoformat(self.last_scheduled_date)
            return (date.today() - last).days >= 7
        return True


@dataclass
class Pet:
    """Represents a pet and the care tasks associated with it."""

    name: str
    species: str
    age: Optional[int] = None
    tasks: list = field(default_factory=list)

    def add_task(self, task: "Task") -> None:
        """Attach a task to this pet; silently skips duplicate titles."""
        if any(t.title == task.title for t in self.tasks):
            return
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
    """Represents the pet owner, their available time, and their pets."""

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
    """Builds and explains a priority-ordered daily care plan within a time budget."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner):
        self.owner = owner
        self.schedule: list[Task] = []
        self.conflicts: list[str] = []

    # ------------------------------------------------------------------
    # Plan building
    # ------------------------------------------------------------------

    def build_plan(self) -> None:
        """Select tasks by priority, filter by recurrence, fill leftover time, then sort by slot."""
        self.schedule = []
        self.conflicts = []

        # Only include tasks that are due today based on their frequency
        pending = [t for t in self.owner.get_all_pending_tasks() if t.is_due_today()]

        # Primary sort: priority; secondary: shorter duration fills gaps better
        sorted_tasks = sorted(
            pending,
            key=lambda t: (self.PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes),
        )

        # Backfill loop: keep scanning remaining tasks until nothing new fits
        time_used = 0
        remaining = list(sorted_tasks)
        while remaining:
            added_any = False
            next_remaining = []
            for task in remaining:
                if time_used + task.duration_minutes <= self.owner.available_minutes:
                    self.schedule.append(task)
                    time_used += task.duration_minutes
                    added_any = True
                else:
                    next_remaining.append(task)
            remaining = next_remaining
            if not added_any:
                break

        # Sort the final schedule by preferred_time slot for display
        self.schedule.sort(key=lambda t: TIME_ORDER.get(t.preferred_time, 3))

        self._detect_conflicts()

    def _detect_conflicts(self) -> None:
        """Flag (pet, time-slot) pairs whose total duration exceeds the slot's budget."""
        slot_budgets = {
            slot: int(self.owner.available_minutes * frac)
            for slot, frac in SLOT_FRACTIONS.items()
        }

        slot_map: dict[tuple, list[Task]] = defaultdict(list)
        for task in self.schedule:
            if task.preferred_time != "any" and task.pet:
                slot_map[(task.pet.name, task.preferred_time)].append(task)

        for (pet_name, slot), tasks in slot_map.items():
            total = sum(t.duration_minutes for t in tasks)
            budget = slot_budgets[slot]
            if total > budget:
                titles = ", ".join(t.title for t in tasks)
                self.conflicts.append(
                    f"{pet_name}'s {slot} tasks ({titles}) use {total} min "
                    f"but the {slot} slot budget is {budget} min."
                )

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def get_tasks_by_priority(self, priority: str) -> list:
        """Return scheduled tasks matching the given priority level."""
        return [t for t in self.schedule if t.priority == priority]

    def get_tasks_by_pet(self, pet_name: str) -> list:
        """Return scheduled tasks assigned to a specific pet."""
        return [t for t in self.schedule if t.pet and t.pet.name == pet_name]

    def get_tasks_by_status(self, completed: bool) -> list:
        """Return scheduled tasks filtered by completion status."""
        return [t for t in self.schedule if t.completed == completed]

    def get_tasks_sorted_by_time(self) -> list:
        """Return the schedule sorted by preferred_time slot."""
        return sorted(self.schedule, key=lambda t: TIME_ORDER.get(t.preferred_time, 3))

    def sort_by_time(self, tasks: list) -> list:
        """Sort Task objects by their preferred_time attribute.

        preferred_time can be:
          - A named slot: "morning", "afternoon", "evening", "any"
          - A clock string: "HH:MM"  (e.g. "09:00", "14:30")

        For "HH:MM" strings the lambda converts "09:00" → (9, 0) so that
        numeric ordering works correctly (e.g. "09:00" < "14:30").
        Named slots without an exact time fall back to TIME_ORDER bucket values
        so they sort after any explicit clock times.
        """
        def _sort_key(task: "Task"):
            t = task.preferred_time
            # "HH:MM" clock string — convert to (hours, minutes) tuple for numeric sort
            if len(t) == 5 and t[2] == ":":
                return tuple(int(x) for x in t.split(":"))
            # Named slot — map to a comparable tuple so it interleaves correctly
            slot_minutes = {"morning": (6, 0), "afternoon": (12, 0), "evening": (18, 0), "any": (99, 0)}
            return slot_minutes.get(t, (99, 0))

        return sorted(tasks, key=_sort_key)

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def explain_plan(self) -> str:
        """Return a human-readable summary of scheduled tasks, skipped tasks, and conflicts."""
        if not self.schedule:
            return "No plan built yet. Call build_plan() first."

        lines = [f"Scheduled plan for {self.owner.name}:"]
        total_time = 0
        for i, task in enumerate(self.schedule, start=1):
            pet_name = task.pet.name if task.pet else "No pet"
            time_label = f"[{task.preferred_time}] " if task.preferred_time != "any" else ""
            lines.append(
                f"  {i}. {time_label}{task.title} — {task.duration_minutes} min, "
                f"priority={task.priority}, pet={pet_name}, frequency={task.frequency}"
            )
            total_time += task.duration_minutes

        lines.append(f"\nTotal time used: {total_time} min")

        all_due = [t for t in self.owner.get_all_pending_tasks() if t.is_due_today()]
        skipped = [t for t in all_due if t not in self.schedule]
        if skipped:
            lines.append("Skipped (exceeded available time): " + ", ".join(t.title for t in skipped))

        if self.conflicts:
            lines.append("\nConflicts detected:")
            for c in self.conflicts:
                lines.append(f"  ! {c}")

        return "\n".join(lines)
