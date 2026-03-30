"""Demo: lightweight conflict detection for same-time and owner-overlap warnings."""
from pawpal_system import Task, Pet, Owner, Scheduler

SEP  = "=" * 60
SEP2 = "-" * 60


def print_tasks(tasks: list, label: str) -> None:
    """Print a labelled table of tasks."""
    print(f"\n{SEP2}")
    print(f"  {label}  ({len(tasks)} task(s))")
    print(SEP2)
    if not tasks:
        print("  (none)")
        return
    for task in tasks:
        pet_name = task.pet.name if task.pet else "—"
        status   = "DONE" if task.completed else "pending"
        print(
            f"  [{task.preferred_time:<9}] {task.title:<24}"
            f" | {pet_name:<6} | {task.priority:<6} | {status}"
        )


def print_conflicts(conflicts: list) -> None:
    """Print all conflict warnings with clear tier labels."""
    print(f"\n{SEP}")
    if not conflicts:
        print("  No conflicts detected.")
        print(SEP)
        return
    print(f"  CONFLICT WARNINGS  ({len(conflicts)} found)")
    print(SEP)
    for i, c in enumerate(conflicts, 1):
        print(f"  {i}. {c}")
    print(SEP)


# ---------------------------------------------------------------------------
# Setup — deliberately crafted to trigger both conflict tiers
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=180)

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Mochi: two tasks in "morning" → triggers Tier 1 (same-pet conflict) ---
mochi.add_task(Task(
    title="Morning walk", duration_minutes=30,
    priority="high", frequency="daily", preferred_time="morning",
))
mochi.add_task(Task(
    title="Flea treatment", duration_minutes=10,
    priority="medium", frequency="weekly", preferred_time="morning",  # same slot!
))

# --- Luna also in "morning" → triggers Tier 2 (owner overlap with Mochi) ---
luna.add_task(Task(
    title="Breakfast feeding", duration_minutes=5,
    priority="high", frequency="daily", preferred_time="morning",     # owner overlap!
))

# --- Afternoon tasks for both pets → Tier 2 owner overlap in afternoon ---
mochi.add_task(Task(
    title="Lunch feeding", duration_minutes=5,
    priority="high", frequency="daily", preferred_time="afternoon",
))
luna.add_task(Task(
    title="Afternoon playtime", duration_minutes=15,
    priority="low", frequency="daily", preferred_time="afternoon",    # owner overlap!
))

# --- Evening tasks with no conflict (one pet each) ---
mochi.add_task(Task(
    title="Evening walk", duration_minutes=20,
    priority="medium", frequency="daily", preferred_time="evening",
))
luna.add_task(Task(
    title="Evening grooming", duration_minutes=10,
    priority="medium", frequency="daily", preferred_time="evening",   # owner overlap!
))

# ---------------------------------------------------------------------------
# Build schedule — conflicts collected inside build_plan()
# ---------------------------------------------------------------------------
scheduler = Scheduler(owner)
scheduler.build_plan()

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
print(SEP)
print("  FULL SCHEDULE")
print(SEP)
print(scheduler.explain_plan())

print_tasks(scheduler.schedule, "SCHEDULE — sorted by time slot")

# Conflict warnings — lightweight: program keeps running, only warns
print_conflicts(scheduler.conflicts)

# Filters still work normally alongside conflict detection
print_tasks(scheduler.get_tasks_by_pet("Mochi"), "FILTER › pet = Mochi")
print_tasks(scheduler.get_tasks_by_pet("Luna"),  "FILTER › pet = Luna")
