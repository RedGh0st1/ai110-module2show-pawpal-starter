from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Existing tests ────────────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feeding", duration_minutes=5, priority="medium"))
    assert len(pet.tasks) == 1
    pet.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    assert len(pet.tasks) == 2


# ── Sorting Correctness ───────────────────────────────────────────────────────

def test_sort_by_time_named_slots_are_chronological():
    """sort_by_time must return morning → afternoon → evening → any."""
    tasks = [
        Task(title="Evening pill",   duration_minutes=5,  priority="medium", preferred_time="evening"),
        Task(title="Any-time task",  duration_minutes=10, priority="low",    preferred_time="any"),
        Task(title="Afternoon walk", duration_minutes=20, priority="high",   preferred_time="afternoon"),
        Task(title="Morning feed",   duration_minutes=15, priority="medium", preferred_time="morning"),
    ]
    owner = Owner(name="Alex", available_minutes=120)
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time(tasks)
    order = [t.preferred_time for t in sorted_tasks]

    assert order == ["morning", "afternoon", "evening", "any"]


def test_sort_by_time_stable_when_all_same_slot():
    """sort_by_time must not raise and must return all tasks when slots are identical."""
    tasks = [
        Task(title="Task A", duration_minutes=10, priority="high",   preferred_time="morning"),
        Task(title="Task B", duration_minutes=15, priority="medium", preferred_time="morning"),
        Task(title="Task C", duration_minutes=5,  priority="low",    preferred_time="morning"),
    ]
    owner = Owner(name="Alex", available_minutes=120)
    scheduler = Scheduler(owner)

    sorted_tasks = scheduler.sort_by_time(tasks)

    assert len(sorted_tasks) == 3
    assert all(t.preferred_time == "morning" for t in sorted_tasks)


def test_build_plan_display_order_is_by_time_slot():
    """After build_plan the schedule list must be ordered by preferred_time slot."""
    pet = Pet(name="Rex", species="dog")
    pet.add_task(Task(title="Evening brush", duration_minutes=10, priority="high",   preferred_time="evening"))
    pet.add_task(Task(title="Morning feed",  duration_minutes=10, priority="medium", preferred_time="morning"))
    pet.add_task(Task(title="Afternoon walk",duration_minutes=10, priority="low",    preferred_time="afternoon"))

    owner = Owner(name="Sam", available_minutes=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_plan()

    slots = [t.preferred_time for t in scheduler.schedule]
    assert slots == ["morning", "afternoon", "evening"]


# ── Recurrence Logic ──────────────────────────────────────────────────────────

def test_daily_task_recurs_next_day():
    """Completing a daily task must produce a new task due tomorrow."""
    task = Task(title="Feed", duration_minutes=10, priority="medium", frequency="daily")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.completed is False
    assert next_task.next_due_date == tomorrow


def test_weekly_task_recurs_in_seven_days():
    """Completing a weekly task must produce a new task due in exactly 7 days."""
    task = Task(title="Bath", duration_minutes=20, priority="low", frequency="weekly")
    in_seven = (date.today() + timedelta(days=7)).isoformat()

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.next_due_date == in_seven


def test_as_needed_task_returns_no_recurrence():
    """'as needed' tasks must return None from mark_complete — no auto-rescheduling."""
    task = Task(title="Vet visit", duration_minutes=60, priority="high", frequency="as needed")

    next_task = task.mark_complete()

    assert next_task is None


def test_future_due_date_excludes_task_from_todays_plan():
    """A task with next_due_date tomorrow must NOT appear in today's schedule."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task(
        title="Future groom",
        duration_minutes=15,
        priority="high",
        frequency="daily",
        next_due_date=tomorrow,
    ))

    owner = Owner(name="Sam", available_minutes=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert scheduler.schedule == []


def test_completed_daily_task_returns_next_occurrence():
    """mark_task_complete must return a new pending task dated for tomorrow.

    NOTE: add_task deduplicates by title, so the returned task is NOT added to
    the pet while the original (completed) task still sits in pet.tasks. This
    test verifies the return value is correct; the duplicate-guard behavior is a
    known design constraint documented here for visibility.
    """
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=20, priority="high", frequency="daily")
    pet.add_task(task)

    owner = Owner(name="Alex", available_minutes=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    next_task = scheduler.mark_task_complete(task)

    # The returned task must be a fresh, uncompleted task due tomorrow
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.next_due_date == tomorrow
    assert next_task.title == "Walk"


# ── Conflict Detection ────────────────────────────────────────────────────────

def test_same_pet_same_slot_raises_conflict():
    """Two tasks for the same pet in the same time slot must produce a same-pet conflict."""
    pet = Pet(name="Buddy", species="dog")
    pet.add_task(Task(title="Feed",  duration_minutes=10, priority="high",   preferred_time="morning"))
    pet.add_task(Task(title="Brush", duration_minutes=10, priority="medium", preferred_time="morning"))

    owner = Owner(name="Jordan", available_minutes=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_plan()

    same_pet_conflicts = [c for c in scheduler.conflicts if "[Same-pet conflict]" in c]
    assert len(same_pet_conflicts) >= 1


def test_different_pets_same_slot_raises_owner_overlap():
    """Tasks for two different pets in the same slot must trigger an owner-overlap warning."""
    dog = Pet(name="Rex", species="dog")
    dog.add_task(Task(title="Dog walk", duration_minutes=15, priority="high", preferred_time="morning"))

    cat = Pet(name="Whiskers", species="cat")
    cat.add_task(Task(title="Cat feed", duration_minutes=10, priority="high", preferred_time="morning"))

    owner = Owner(name="Taylor", available_minutes=120)
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    scheduler.build_plan()

    overlap_conflicts = [c for c in scheduler.conflicts if "[Owner overlap]" in c]
    assert len(overlap_conflicts) >= 1


def test_any_time_tasks_never_cause_conflicts():
    """Tasks with preferred_time='any' must not appear in any conflict message."""
    pet = Pet(name="Noodle", species="rabbit")
    pet.add_task(Task(title="Play A", duration_minutes=10, priority="medium", preferred_time="any"))
    pet.add_task(Task(title="Play B", duration_minutes=10, priority="medium", preferred_time="any"))

    owner = Owner(name="Kim", available_minutes=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert scheduler.conflicts == []


def test_no_conflict_when_slots_are_different():
    """Tasks spread across different slots must produce zero conflicts."""
    pet = Pet(name="Max", species="dog")
    pet.add_task(Task(title="Morning feed", duration_minutes=10, priority="high",   preferred_time="morning"))
    pet.add_task(Task(title="Evening walk", duration_minutes=20, priority="medium", preferred_time="evening"))

    owner = Owner(name="Chris", available_minutes=120)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert scheduler.conflicts == []
