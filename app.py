import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A daily care planner for your pet(s).")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "task_dicts" not in st.session_state:
    st.session_state.task_dicts = []
if "schedule_result" not in st.session_state:
    st.session_state.schedule_result = None

# --- Owner & Pet Setup ---
st.subheader("Owner & Pet")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input(
        "Available time today (minutes)", min_value=10, max_value=480, value=60, step=5
    )
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    pet_age = st.number_input("Pet age (years, optional)", min_value=0, max_value=30, value=3)

st.divider()

# --- Task Entry ---
st.subheader("Tasks")
with st.form("add_task_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["high", "medium", "low"])
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
    submitted = st.form_submit_button("Add task")

if submitted and task_title.strip():
    st.session_state.task_dicts.append(
        {
            "title": task_title.strip(),
            "duration_minutes": int(duration),
            "priority": priority,
            "frequency": frequency,
        }
    )
    st.session_state.schedule_result = None  # reset schedule on change

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
        # Build the object graph from current form values + task list
        pet = Pet(name=pet_name, species=species, age=pet_age if pet_age > 0 else None)
        owner = Owner(name=owner_name, available_minutes=int(available_minutes))
        owner.add_pet(pet)

        for td in st.session_state.task_dicts:
            task = Task(
                title=td["title"],
                duration_minutes=td["duration_minutes"],
                priority=td["priority"],
                frequency=td["frequency"],
            )
            pet.add_task(task)

        scheduler = Scheduler(owner)
        scheduler.build_plan()

        st.session_state.owner = owner
        st.session_state.schedule_result = scheduler

# --- Display Results ---
if st.session_state.schedule_result is not None:
    scheduler = st.session_state.schedule_result
    owner = st.session_state.owner

    if scheduler.schedule:
        st.success(f"Scheduled {len(scheduler.schedule)} task(s) for {owner.name}.")

        # Summary table
        rows = []
        for task in scheduler.schedule:
            rows.append(
                {
                    "Task": task.title,
                    "Pet": task.pet.name if task.pet else "—",
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority,
                    "Frequency": task.frequency,
                }
            )
        st.table(rows)

        # Time bar
        total = sum(t.duration_minutes for t in scheduler.schedule)
        pct = min(total / owner.available_minutes, 1.0)
        st.write(f"**Time used:** {total} / {owner.available_minutes} min")
        st.progress(pct)

        # Priority breakdown
        with st.expander("Priority breakdown"):
            for level in ["high", "medium", "low"]:
                tasks_at_level = scheduler.get_tasks_by_priority(level)
                if tasks_at_level:
                    st.write(
                        f"**{level.capitalize()}:** "
                        + ", ".join(t.title for t in tasks_at_level)
                    )

        # Full explanation
        with st.expander("Full plan explanation"):
            st.text(scheduler.explain_plan())
    else:
        st.error("No tasks fit within the available time. Try increasing available minutes or reducing task durations.")
