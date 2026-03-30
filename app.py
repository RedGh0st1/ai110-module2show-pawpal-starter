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
        assigned_pet = st.selectbox("Assign to", [pet1_name, pet2_name])

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
    st.table(st.session_state.task_dicts)
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

        owner = Owner(name=owner_name, available_minutes=int(available_minutes))
        owner.add_pet(pet1)
        owner.add_pet(pet2)

        pet_lookup = {pet1_name: pet1, pet2_name: pet2}

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
if st.session_state.schedule_result is not None and st.session_state.owner is not None:
    scheduler = st.session_state.schedule_result
    owner = st.session_state.owner

    if scheduler.schedule:
        st.success(f"Scheduled {len(scheduler.schedule)} task(s) for {owner.name}.")

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

        # Apply filters
        displayed = scheduler.schedule
        if filter_pet != "All":
            displayed = [t for t in displayed if t.pet and t.pet.name == filter_pet]
        if filter_time != "All":
            displayed = [t for t in displayed if t.preferred_time == filter_time]
        if filter_status != "All":
            want_completed = filter_status == "completed"
            displayed = [t for t in displayed if t.completed == want_completed]

        rows = []
        for task in displayed:
            rows.append(
                {
                    "Task": task.title,
                    "Pet": task.pet.name if task.pet else "—",
                    "Time slot": task.preferred_time,
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority,
                    "Frequency": task.frequency,
                    "Status": "completed" if task.completed else "pending",
                }
            )

        if rows:
            st.table(rows)
        else:
            st.info("No tasks match the selected filters.")

        total = sum(t.duration_minutes for t in scheduler.schedule)
        pct = min(total / owner.available_minutes, 1.0)
        st.write(f"**Time used:** {total} / {owner.available_minutes} min")
        st.progress(pct)

        # --- Conflicts ---
        if scheduler.conflicts:
            st.error("Scheduling conflicts detected:")
            for c in scheduler.conflicts:
                st.write(f"- {c}")

        with st.expander("Priority breakdown"):
            for level in ["high", "medium", "low"]:
                tasks_at_level = scheduler.get_tasks_by_priority(level)
                if tasks_at_level:
                    st.write(
                        f"**{level.capitalize()}:** "
                        + ", ".join(
                            f"{t.title} ({t.pet.name if t.pet else '—'}, {t.preferred_time})"
                            for t in tasks_at_level
                        )
                    )

        with st.expander("Full plan explanation"):
            st.text(scheduler.explain_plan())
    else:
        st.error("No tasks fit within the available time. Try increasing available minutes or reducing task durations.")
