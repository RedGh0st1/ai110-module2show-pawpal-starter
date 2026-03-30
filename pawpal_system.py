"""Data model and scheduling logic for the PawPal+ pet care planner."""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
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
    next_due_date: Optional[str] = None         # ISO format YYYY-MM-DD

    def __post_init__(self):
        """Validate priority and preferred_time against their allowed value sets."""
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of: {VALID_PRIORITIES}"
            )
        if self.preferred_time not in VALID_TIMES:
            raise ValueError(
                f"Invalid preferred_time '{self.preferred_time}'. Must be one of: {VALID_TIMES}"
            )

    def __str__(self) -> str:
        """Return a readable string representation of the task."""
        pet_name = self.pet.name if self.pet else "No pet"
        status = "completed" if self.completed else "pending"
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority={self.priority}, pet={pet_name}, "
            f"frequency={self.frequency}, time={self.preferred_time}, status={status})"
        )

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task done and return a new Task for the next occurrence.

        Uses timedelta to calculate the next due date:
          - "daily"  → today + timedelta(days=1)
          - "weekly" → today + timedelta(days=7)
          - "as needed" → no automatic recurrence; returns None

        The returned Task is a fresh instance (completed=False) with
        next_due_date pre-set so is_due_today() gates it correctly.
        """
        today = date.today()
        self.completed = True
        self.last_scheduled_date = today.isoformat()

        if self.frequency == "daily":
            next_due = today + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = today + timedelta(days=7)
        else:
            return None  # "as needed" tasks are not automatically rescheduled

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            preferred_time=self.preferred_time,
            next_due_date=next_due.isoformat(),
        )

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == "high"

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule.

        Checks next_due_date first (set by mark_complete recurrence).
        Falls back to frequency-based logic for tasks without an explicit date.
        """
        today = date.today()

        # If an explicit next due date was set, use it for the gate
        if self.next_due_date is not None:
            return date.fromisoformat(self.next_due_date) <= today

        # No explicit date — fall back to frequency rules
        if self.frequency in ("daily", "as needed"):
            return True
        if self.frequency == "weekly":
            if self.last_scheduled_date is None:
                return True
            last = date.fromisoformat(self.last_scheduled_date)
            return (today - last).days >= 7
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
        self._detect_time_overlaps()

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

    def _detect_time_overlaps(self) -> None:
        """Lightweight same-time conflict detection — appends warnings, never raises.

        Two conflict tiers are checked for every named time slot
        ("morning", "afternoon", "evening") in the schedule:

        1. Same-pet overlap — one pet has multiple tasks in the same slot.
           A pet can only do one thing at a time, so this is always a conflict.

        2. Owner overlap — different pets both need attention in the same slot.
           The owner can only be in one place, so this is flagged as a warning.

        Tasks with preferred_time="any" are flexible by design and are skipped.
        """
        # Group scheduled tasks by time slot, excluding flexible "any" tasks
        slot_map: dict[str, list[Task]] = defaultdict(list)
        for task in self.schedule:
            if task.preferred_time != "any":
                slot_map[task.preferred_time].append(task)

        for slot, tasks in slot_map.items():
            if len(tasks) < 2:
                continue

            # --- Tier 1: same-pet overlap ---
            pet_tasks: dict[str, list[Task]] = defaultdict(list)
            for task in tasks:
                if task.pet:
                    pet_tasks[task.pet.name].append(task)

            for pet_name, ptasks in pet_tasks.items():
                if len(ptasks) > 1:
                    titles = ", ".join(t.title for t in ptasks)
                    self.conflicts.append(
                        f"[Same-pet conflict] {pet_name} has {len(ptasks)} tasks "
                        f"in the '{slot}' slot: {titles}"
                    )

            # --- Tier 2: owner overlap across different pets ---
            pets_in_slot = {t.pet.name for t in tasks if t.pet}
            if len(pets_in_slot) > 1:
                summary = "; ".join(
                    f"{p}: "
                    + ", ".join(t.title for t in tasks if t.pet and t.pet.name == p)
                    for p in sorted(pets_in_slot)
                )
                self.conflicts.append(
                    f"[Owner overlap] Multiple pets need attention "
                    f"in the '{slot}' slot — {summary}"
                )

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a scheduled task done and auto-register the next occurrence with its pet.

        Calls task.mark_complete() which returns a new Task pre-dated with
        timedelta. That new Task is added back to the pet so the next
        build_plan() call picks it up automatically.

        Returns the new Task (or None for 'as needed' tasks).
        """
        next_task = task.mark_complete()
        if next_task is not None and task.pet is not None:
            task.pet.add_task(next_task)
        return next_task

    def get_tasks_by_priority(self, priority: str) -> list:
        """Return scheduled tasks matching the given priority level."""
        return [t for t in self.schedule if t.priority == priority]

    def get_tasks_by_pet(self, pet_name: str) -> list:
        """Return scheduled tasks assigned to a specific pet."""
        return [t for t in self.schedule if t.pet and t.pet.name == pet_name]

    def get_tasks_by_status(self, completed: bool) -> list:
        """Return scheduled tasks filtered by completion status."""
        return [t for t in self.schedule if t.completed == completed]

    def filter_by_pet_and_status(self, pet_name: str, completed: bool) -> list:
        """Return scheduled tasks matching both a specific pet name and completion status."""
        return [
            t for t in self.schedule
            if t.pet and t.pet.name == pet_name and t.completed == completed
        ]

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
            slot_minutes = {
                "morning": (6, 0), "afternoon": (12, 0),
                "evening": (18, 0), "any": (99, 0),
            }
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
            skipped_titles = ", ".join(t.title for t in skipped)
            lines.append(f"Skipped (exceeded available time): {skipped_titles}")

        if self.conflicts:
            lines.append("\nConflicts detected:")
            for c in self.conflicts:
                lines.append(f"  ! {c}")

        return "\n".join(lines)
