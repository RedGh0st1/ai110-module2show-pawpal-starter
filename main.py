from pawpal_system import Task, Pet, Owner, Scheduler

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Tasks for Mochi (dog) ---
mochi.add_task(Task(title="Morning walk",     duration_minutes=30, priority="high",   frequency="daily"))
mochi.add_task(Task(title="Breakfast feeding", duration_minutes=5,  priority="high",   frequency="daily"))
mochi.add_task(Task(title="Flea treatment",   duration_minutes=10, priority="medium", frequency="weekly"))

# --- Tasks for Luna (cat) ---
luna.add_task(Task(title="Breakfast feeding", duration_minutes=5,  priority="high",   frequency="daily"))
luna.add_task(Task(title="Litter box clean",  duration_minutes=10, priority="medium", frequency="daily"))
luna.add_task(Task(title="Brush coat",        duration_minutes=15, priority="low",    frequency="weekly"))

# --- Schedule ---
scheduler = Scheduler(owner)
scheduler.build_plan()

print("=" * 50)
print("         TODAY'S SCHEDULE")
print("=" * 50)
print(scheduler.explain_plan())
print("=" * 50)
