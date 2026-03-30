import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A daily care planner for your pet(s).")

# --- Session state initialization ---
if "task_dicts" not in st.session_state:
    st.session_state.task_dicts = []
if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None
if "owner" not in st.session_state:
    st.session_state.owner = None

# --- Owner Setup ---
st.subheader("Owner")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input(
        "Available time today (minutes)", min_value=10, max_value=480, value=90, step=5
    )

st.divider()

# --- Pet Setup ---
st.subheader("Pets")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Pet 1**")
    pet1_name = st.text_input("Name", value="Mochi", key="pet1_name")
    pet1_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="pet1_species")
    pet1_age = st.number_input("Age (years)", min_value=0, max_value=30, value=3, key="pet1_age")

with col2:
    st.markdown("**Pet 2**")
    pet2_name = st.text_input("Name", value="Luna", key="pet2_name")
    pet2_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], index=1, key="pet2_species")
    pet2_age = st.number_input("Age (years)", min_value=0, max_value=30, value=5, key="pet2_age")

col3, col4 = st.columns(2)

with col3:
    st.markdown("**Pet 3**")
    pet3_name = st.text_input("Name", value="Noodle", key="pet3_name")
    pet3_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], index=2, key="pet3_species")
    pet3_age = st.number_input("Age (years)", min_value=0, max_value=30, value=2, key="pet3_age")

with col4:
    st.markdown("**Pet 4**")
    pet4_name = st.text_input("Name", value="Buddy", key="pet4_name")
    pet4_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="pet4_species")
    pet4_age = st.number_input("Age (years)", min_value=0, max_value=30, value=7, key="pet4_age")

st.divider()

# --- Task Entry ---
st.subheader("Tasks")
with st.form("add_task_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        assigned_pet = st.selectbox("Assign to", [pet1_name, pet2_name, pet3_name, pet4_name])

    col4, col5, col6 = st.columns(3)
    with col4:
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
    with col6:
        preferred_time = st.selectbox("Time of day", ["any", "morning", "afternoon", "evening"])

    submitted = st.form_submit_button("Add task")

if submitted and task_title.strip():
    st.session_state.task_dicts.append(
        {
            "title": task_title.strip(),
            "duration_minutes": int(duration),
            "priority": priority,
            "frequency": frequency,
            "preferred_time": preferred_time,
            "pet": assigned_pet,
        }
    )
    st.session_state.schedule_result = None

# --- Warn if total task time already exceeds budget ---
if st.session_state.task_dicts:
    total_entered = sum(td["duration_minutes"] for td in st.session_state.task_dicts)
    if total_entered > available_minutes:
        st.warning(
            f"Total task time ({total_entered} min) exceeds your available time "
            f"({int(available_minutes)} min). Some tasks will be skipped."
        )

if st.session_state.task_dicts:
    st.write("**Current tasks:**")
    display_dicts = [
        {
            "Task": td["title"],
            "Pet": td["pet"],
            "Time slot": td["preferred_time"],
            "Duration (min)": td["duration_minutes"],
            "Priority": td["priority"],
            "Frequency": td["frequency"],
        }
        for td in st.session_state.task_dicts
    ]
    st.dataframe(display_dicts, use_container_width=True, hide_index=True)
    if st.button("Clear all tasks"):
        st.session_state.task_dicts = []
        st.session_state.schedule_result = None
        st.rerun()
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate Schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule", type="primary"):
    if not st.session_state.task_dicts:
        st.warning("Add at least one task before generating a schedule.")
    else:
        pet1 = Pet(name=pet1_name, species=pet1_species, age=pet1_age if pet1_age > 0 else None)
        pet2 = Pet(name=pet2_name, species=pet2_species, age=pet2_age if pet2_age > 0 else None)
        pet3 = Pet(name=pet3_name, species=pet3_species, age=pet3_age if pet3_age > 0 else None)
        pet4 = Pet(name=pet4_name, species=pet4_species, age=pet4_age if pet4_age > 0 else None)

        owner = Owner(name=owner_name, available_minutes=int(available_minutes))
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        owner.add_pet(pet3)
        owner.add_pet(pet4)

        pet_lookup = {pet1_name: pet1, pet2_name: pet2, pet3_name: pet3, pet4_name: pet4}

        for td in st.session_state.task_dicts:
            task = Task(
                title=td["title"],
                duration_minutes=td["duration_minutes"],
                priority=td["priority"],
                frequency=td["frequency"],
                preferred_time=td.get("preferred_time", "any"),
            )
            pet_lookup[td["pet"]].add_task(task)

        scheduler = Scheduler(owner)
        scheduler.build_plan()

        st.session_state.owner = owner
        st.session_state.schedule_result = scheduler

# --- Display Results ---
PRIORITY_BADGE = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
TIME_BADGE = {"morning": "🌅 Morning", "afternoon": "☀️ Afternoon", "evening": "🌙 Evening", "any": "🕐 Any"}

if st.session_state.schedule_result is not None and st.session_state.owner is not None:
    scheduler = st.session_state.schedule_result
    owner = st.session_state.owner

    if scheduler.schedule:
        # --- Summary metrics ---
        total = sum(t.duration_minutes for t in scheduler.schedule)
        pct = min(total / owner.available_minutes, 1.0)
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Tasks scheduled", len(scheduler.schedule))
        with col_m2:
            st.metric("Time used", f"{total} min")
        with col_m3:
            st.metric("Time available", f"{owner.available_minutes} min")
        st.progress(pct, text=f"{int(pct * 100)}% of daily budget used")

        # --- Conflict callouts (shown before the table so the owner sees them first) ---
        if scheduler.conflicts:
            same_pet = [c for c in scheduler.conflicts if "[Same-pet conflict]" in c]
            overlap  = [c for c in scheduler.conflicts if "[Owner overlap]" in c]
            budget   = [c for c in scheduler.conflicts if "[Same-pet conflict]" not in c
                                                        and "[Owner overlap]" not in c]
            for c in same_pet:
                detail = c.replace("[Same-pet conflict] ", "")
                st.error(
                    f"**Same-pet conflict** — {detail}\n\n"
                    f"**Fix:** Move one of these tasks to a different time slot "
                    f"(e.g. shift the shorter one to Afternoon or Evening)."
                )
            for c in overlap:
                detail = c.replace("[Owner overlap] ", "")
                st.warning(
                    f"**Owner overlap** — {detail}\n\n"
                    f"**Tip:** You cannot be in two places at once. "
                    f"Stagger these tasks across different time slots."
                )
            for c in budget:
                st.warning(
                    f"**Slot over budget** — {c}\n\n"
                    f"**Tip:** Shorten a task or move it to a less-loaded slot."
                )
        else:
            st.success(f"Plan ready for {owner.name} — no conflicts detected.")

        # --- Filters ---
        pet_names = list({t.pet.name for t in scheduler.schedule if t.pet})
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_pet = st.selectbox("Filter by pet", ["All"] + sorted(pet_names), key="filter_pet")
        with col_f2:
            filter_time = st.selectbox(
                "Filter by time slot",
                ["All", "morning", "afternoon", "evening", "any"],
                key="filter_time",
            )
        with col_f3:
            filter_status = st.selectbox(
                "Filter by status", ["All", "pending", "completed"], key="filter_status"
            )

        # Apply filters using Scheduler methods
        want_completed = filter_status == "completed" if filter_status != "All" else None

        if filter_pet != "All" and filter_status != "All":
            displayed = scheduler.filter_by_pet_and_status(filter_pet, want_completed)
        elif filter_pet != "All":
            displayed = scheduler.get_tasks_by_pet(filter_pet)
        elif filter_status != "All":
            displayed = scheduler.get_tasks_by_status(want_completed)
        else:
            displayed = list(scheduler.schedule)

        # Filter by time slot (no dedicated Scheduler method — applied after the above)
        if filter_time != "All":
            displayed = [t for t in displayed if t.preferred_time == filter_time]

        # Restore chronological slot order after filtering
        displayed = scheduler.sort_by_time(displayed)

        # --- Schedule table with visual badges ---
        rows = [
            {
                "Task": task.title,
                "Pet": task.pet.name if task.pet else "—",
                "Time": TIME_BADGE.get(task.preferred_time, task.preferred_time),
                "Duration": f"{task.duration_minutes} min",
                "Priority": PRIORITY_BADGE.get(task.priority, task.priority),
                "Frequency": task.frequency,
                "Status": "✅ Done" if task.completed else "⏳ Pending",
            }
            for task in displayed
        ]

        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No tasks match the selected filters.")

        # --- Skipped tasks ---
        skipped = [
            t for t in owner.get_all_pending_tasks()
            if t.is_due_today() and t not in scheduler.schedule
        ]
        if skipped:
            with st.expander(f"⚠️ {len(skipped)} task(s) skipped — not enough time today"):
                for t in skipped:
                    st.write(
                        f"- **{t.title}** — {t.pet.name if t.pet else '—'}, "
                        f"{t.duration_minutes} min, {t.priority} priority"
                    )

        # --- Priority breakdown ---
        with st.expander("Priority breakdown"):
            col_h, col_m, col_l = st.columns(3)
            for col, level, badge in [
                (col_h, "high",   "🔴"),
                (col_m, "medium", "🟡"),
                (col_l, "low",    "🟢"),
            ]:
                with col:
                    tasks_at_level = scheduler.get_tasks_by_priority(level)
                    st.metric(f"{badge} {level.capitalize()}", len(tasks_at_level))
                    for t in tasks_at_level:
                        st.caption(f"{t.title} — {t.pet.name if t.pet else '—'}, {t.preferred_time}")

        with st.expander("Full plan explanation"):
            st.text(scheduler.explain_plan())
    else:
        st.error(
            "No tasks fit within the available time. "
            "Try increasing your available minutes or reducing task durations."
        )
