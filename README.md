# PawPal+

**PawPal+** is a Streamlit app that builds a realistic, priority-ordered daily care plan for pet owners. It fits tasks into an available-time budget, sorts them into a logical day order, flags scheduling conflicts before they become problems, and automatically reschedules recurring tasks so nothing falls through the cracks.

## Features

### Priority-based scheduling with backfill

`Scheduler.build_plan()` selects tasks in strict priority order (high → medium → low). After the first pass, a backfill loop re-scans skipped tasks to fill any remaining gaps with shorter items — so every available minute is used, not just the first tasks that fit.

```
High-priority tasks are always scheduled before medium or low ones.
Shorter low-priority tasks can fill leftover time that a longer task cannot.
```

### Chronological sorting by time of day

Every task carries a `preferred_time` field: `morning`, `afternoon`, `evening`, or `any`. After selecting which tasks fit the budget, the scheduler re-sorts the final plan in chronological slot order so the displayed schedule reads like a real day rather than a priority-ranked list.

```
morning → afternoon → evening → any
```

The same `sort_by_time()` method is available for ad-hoc sorting in the UI, keeping display logic out of the data model.

### Three recurrence modes

Completing a task via `Task.mark_complete()` automatically calculates the next due date using Python's `timedelta`:

| Frequency | Next due date |
| --- | --- |
| `daily` | today + 1 day |
| `weekly` | today + 7 days |
| `as needed` | none — task is not rescheduled |

`Scheduler.mark_task_complete()` wraps this and re-registers the follow-up task with the pet, so the next `build_plan()` call picks it up automatically.

### Three-tier conflict detection

Two checks run at the end of every `build_plan()` call. They append human-readable warnings to `scheduler.conflicts` without ever crashing the program:

| Tier | Condition | Severity |
| --- | --- | --- |
| Slot budget exceeded | A pet's combined task time in one slot exceeds that slot's share of the daily budget (morning 40 %, afternoon 35 %, evening 25 %) | Warning |
| Same-pet conflict | One pet has more than one task in the same named time slot | Error — a pet cannot do two things at once |
| Owner overlap | Different pets both need attention in the same slot | Warning — the owner cannot be in two places at once |

The UI surfaces each tier with a distinct visual treatment (`st.error` vs `st.warning`) and a plain-English fix suggestion.

### Focused schedule filtering

`Scheduler` exposes dedicated query methods so the UI never writes raw list comprehensions against internal state:

- `get_tasks_by_pet(pet_name)` — all scheduled tasks for one pet
- `get_tasks_by_status(completed)` — pending or completed tasks
- `filter_by_pet_and_status(pet_name, completed)` — combined filter
- `get_tasks_by_priority(priority)` — tasks at a given priority level

Time-slot filtering is the only filter applied in the UI directly, since no scheduler method exists for it.

### Streamlit UI with live conflict feedback

The app provides a form-driven workflow with real-time feedback:

- Three `st.metric` tiles (tasks scheduled, time used, time available) and a labeled progress bar replace the plain summary text.
- Each conflict is its own `st.error` or `st.warning` callout placed *above* the schedule table so the owner sees problems before scrolling.
- The schedule table uses emoji badges (🔴🟡🟢 for priority, 🌅☀️🌙 for time slot, ✅⏳ for status) for fast visual scanning.
- A collapsible "Skipped tasks" expander lists any due tasks that did not fit the time budget.
- A "Priority breakdown" expander shows a count and task list per priority level using `st.metric` and `st.caption`.

---

## Architecture

```
pawpal_system.py          Core data model and scheduling logic
├── Task                  A single care activity (title, duration, priority,
│                         frequency, preferred_time, recurrence dates)
├── Pet                   A pet and its list of tasks
├── Owner                 The pet owner, their time budget, and their pets
└── Scheduler             Builds and explains a daily care plan
    ├── build_plan()      Priority sort → backfill → time-slot sort → conflict checks
    ├── sort_by_time()    Chronological slot ordering
    ├── get_tasks_by_*()  Filtering helpers used by the UI
    └── explain_plan()    Human-readable plan summary with skipped tasks and conflicts

app.py                    Streamlit UI — form input, filter controls, display
tests/test_pawpal.py      14 pytest tests covering sorting, recurrence, and conflict detection
```

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

## Testing PawPal+

### Running the tests

Activate your virtual environment first, then run:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python3 -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Category | Tests | What is verified |
| --- | --- | --- |
| **Sorting correctness** | `test_sort_by_time_named_slots_are_chronological`, `test_sort_by_time_stable_when_all_same_slot`, `test_build_plan_display_order_is_by_time_slot` | Tasks are returned in chronological slot order (`morning → afternoon → evening → any`) both from `sort_by_time` directly and from `build_plan` end-to-end |
| **Recurrence logic** | `test_daily_task_recurs_next_day`, `test_weekly_task_recurs_in_seven_days`, `test_as_needed_task_returns_no_recurrence`, `test_future_due_date_excludes_task_from_todays_plan`, `test_completed_daily_task_returns_next_occurrence` | Completing a daily task produces a new task due tomorrow; weekly tasks recur in 7 days; `as needed` tasks return `None`; tasks with a future `next_due_date` are correctly excluded from today's plan |
| **Conflict detection** | `test_same_pet_same_slot_raises_conflict`, `test_different_pets_same_slot_raises_owner_overlap`, `test_any_time_tasks_never_cause_conflicts`, `test_no_conflict_when_slots_are_different` | Same-pet slot collisions and owner-overlap warnings are flagged; `any`-time tasks and tasks in separate slots produce no false positives |
| **Core model** | `test_mark_complete_changes_status`, `test_add_task_increases_pet_task_count` | Basic `Task` and `Pet` state changes work correctly |

**Total: 14 tests — 14 passing.**

### Known design constraint surfaced by testing

`Pet.add_task` deduplicates by title. When `Scheduler.mark_task_complete` registers the follow-up task, the original completed task (same title) is still in `pet.tasks`, causing the new task to be silently dropped. The return value of `mark_task_complete` is always correct — but the pet's task list is not automatically extended. See `test_completed_daily_task_returns_next_occurrence` for details.

### Confidence level

#### ★★★★☆ (4 / 5)

The core scheduling pipeline — priority selection, time-budget backfill, slot sorting, and all three conflict-detection tiers — is fully covered and passing. One star is withheld because the duplicate-title guard in `add_task` silently breaks automatic recurrence registration, and there is no coverage of the Streamlit UI layer or multi-day simulation scenarios.
