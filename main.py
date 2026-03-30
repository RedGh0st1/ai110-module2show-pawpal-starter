"""Demo script: auto-recurrence, sorting, and filtering for PawPal+."""
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler

SEP  = "=" * 60
SEP2 = "-" * 60


def print_tasks(tasks: list, label: str) -> None:
    """Print a labelled table of tasks with time slot, pet, priority, and status."""
    print(f"\n{SEP2}")
    print(f"  {label}  ({len(tasks)} task(s))")
    print(SEP2)
    if not tasks:
        print("  (none)")
        return
    for t in tasks:
        pet_name = t.pet.name if t.pet else "—"
        status   = "DONE" if t.completed else "pending"
        due      = f"  next_due={t.next_due_date}" if t.next_due_date else ""
        print(
            f"  [{t.preferred_time:<9}] {t.title:<22}"
            f" | {pet_name:<6} | {t.priority:<6} | {status}{due}"
        )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

owner.add_pet(mochi)
owner.add_pet(luna)

# Tasks added intentionally out of time-slot order to demo sort_by_time()
mochi.add_task(Task(
    title="Evening walk", duration_minutes=20,
    priority="medium", frequency="daily", preferred_time="evening",
))
mochi.add_task(Task(
    title="Morning walk", duration_minutes=30,
    priority="high", frequency="daily", preferred_time="morning",
))
mochi.add_task(Task(
    title="Lunch feeding", duration_minutes=5,
    priority="high", frequency="daily", preferred_time="afternoon",
))
mochi.add_task(Task(
    title="Flea treatment", duration_minutes=10,
    priority="medium", frequency="weekly", preferred_time="morning",
))

luna.add_task(Task(
    title="Afternoon playtime", duration_minutes=15,
    priority="low", frequency="daily", preferred_time="afternoon",
))
luna.add_task(Task(
    title="Evening grooming", duration_minutes=10,
    priority="medium", frequency="daily", preferred_time="evening",
))
luna.add_task(Task(
    title="Breakfast feeding", duration_minutes=5,
    priority="high", frequency="daily", preferred_time="morning",
))
luna.add_task(Task(
    title="Vet checkup", duration_minutes=20,
    priority="medium", frequency="as needed", preferred_time="any",
))

# ---------------------------------------------------------------------------
# Build today's schedule
# ---------------------------------------------------------------------------
scheduler = Scheduler(owner)
scheduler.build_plan()

print(SEP)
print("  PHASE 1 — TODAY'S INITIAL SCHEDULE")
print(SEP)
print(scheduler.explain_plan())

# ---------------------------------------------------------------------------
# Sorting and filtering on the initial schedule
# ---------------------------------------------------------------------------
all_tasks = mochi.tasks + luna.tasks
print_tasks(scheduler.sort_by_time(all_tasks),              "ALL TASKS — sorted by time slot")
print_tasks(scheduler.get_tasks_by_pet("Mochi"),            "FILTER › pet = Mochi")
print_tasks(scheduler.get_tasks_by_pet("Luna"),             "FILTER › pet = Luna")
print_tasks(scheduler.get_tasks_by_status(completed=False), "FILTER › status = pending")

# ---------------------------------------------------------------------------
# Mark tasks complete via Scheduler.mark_task_complete()
#
# Internally calls task.mark_complete(), which uses timedelta:
#   "daily"  → today + timedelta(days=1)   # tomorrow
#   "weekly" → today + timedelta(days=7)   # 7 days from now
#   "as needed" → returns None (no recurrence)
# ---------------------------------------------------------------------------
today = date.today()

print(f"\n{SEP}")
print("  PHASE 2 — MARKING TASKS COMPLETE & AUTO-RECURRENCE")
print(SEP)

for task in scheduler.schedule:
    if task.title in ("Morning walk", "Breakfast feeding", "Flea treatment"):
        next_task = scheduler.mark_task_complete(task)
        if next_task:
            delta = "1" if task.frequency == "daily" else "7"
            print(
                f"  DONE: '{task.title}' ({task.frequency})"
                f"  →  next_due: {next_task.next_due_date}"
                f"  (today + timedelta(days={delta}))"
            )
        else:
            print(f"  DONE: '{task.title}' (as needed — no auto-recurrence)")

# ---------------------------------------------------------------------------
# Filters after marking complete
# ---------------------------------------------------------------------------
print_tasks(
    scheduler.get_tasks_by_status(completed=True),
    "FILTER › status = completed",
)
print_tasks(
    scheduler.get_tasks_by_status(completed=False),
    "FILTER › status = pending",
)
print_tasks(scheduler.filter_by_pet_and_status("Mochi", False), "FILTER › Mochi + pending")
print_tasks(scheduler.filter_by_pet_and_status("Luna",  False), "FILTER › Luna  + pending")

# ---------------------------------------------------------------------------
# Show next-occurrence Tasks registered on each pet
# ---------------------------------------------------------------------------
print(f"\n{SEP}")
print("  PHASE 3 — NEXT-OCCURRENCE TASKS REGISTERED ON EACH PET")
print(SEP)
tomorrow   = today + timedelta(days=1)
next_week  = today + timedelta(days=7)
print(f"  today={today}  |  tomorrow={tomorrow}  |  next_week={next_week}\n")

for pet in owner.pets:
    pending = pet.get_pending_tasks()
    print(f"  {pet.name}'s pending tasks ({len(pending)}):")
    for t in pending:
        due_label = f"next_due={t.next_due_date}" if t.next_due_date else "due today"
        print(f"    • {t.title:<22} | {t.frequency:<9} | {due_label}")

# ---------------------------------------------------------------------------
# Rebuild for today — recurrence tasks with future next_due_date are excluded
# ---------------------------------------------------------------------------
scheduler.build_plan()
print(f"\n{SEP}")
print("  PHASE 4 — REBUILT SCHEDULE FOR TODAY")
print(SEP)
print(scheduler.explain_plan())

if scheduler.conflicts:
    print(f"\n{SEP}")
    print("  CONFLICTS")
    print(SEP)
    for c in scheduler.conflicts:
        print(f"  ! {c}")
