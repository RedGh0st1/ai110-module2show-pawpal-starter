# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

PawPal+ goes beyond a basic to-do list with several algorithmic improvements built into `pawpal_system.py`:

**Sorting by time of day**
Tasks carry a `preferred_time` field (`morning`, `afternoon`, `evening`, or `any`). After selecting which tasks fit the daily budget, the scheduler sorts them into chronological slot order so the printed plan reads like a real day rather than a random list.

**Filtering by pet and status**
`Scheduler` exposes focused query methods — `get_tasks_by_pet()`, `get_tasks_by_status()`, and `filter_by_pet_and_status()` — so the UI and `main.py` can show exactly the slice of the schedule that is relevant (e.g. "Luna's pending tasks only").

**Recurring task handling**
`Task.mark_complete()` uses Python's `timedelta` to calculate the next due date automatically:
- `daily` → `today + timedelta(days=1)`
- `weekly` → `today + timedelta(days=7)`
- `as needed` → no automatic recurrence

`Scheduler.mark_task_complete()` calls this and re-registers the new Task with the pet, so the next `build_plan()` call picks it up without any manual setup.

**Conflict detection**
Two lightweight checks run at the end of every `build_plan()` call — they append warning strings to `scheduler.conflicts` and never crash the program:
- *Slot budget exceeded* — a pet's combined task time in one slot is larger than that slot's share of the daily budget.
- *Same-pet conflict* — one pet has more than one task assigned to the same named slot.
- *Owner overlap* — different pets both need attention in the same slot, leaving the owner no way to be in two places at once.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
