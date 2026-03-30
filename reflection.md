# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

For my initial design I identified four classes: `Pet`, `CareTask`, `Owner`, and `Scheduler`.

`Pet` is a simple data-holding class responsible for storing information about an individual animal — its name, species, and optional age. It doesn't make any decisions; it just represents the subject of all the care tasks.

`CareTask` is also a data class. Its responsibility is to describe a single care activity — what it is, how long it takes, and how urgent it is. I gave it a priority attribute with three levels (high, medium, low) so the scheduler would have something to rank tasks by.

`Owner` represents the person using the app. It holds the owner's name, how much time they have available in a day, and a list of their pets. I gave it an `add_pet()` method so pets can be registered to an owner rather than being standalone objects.

`Scheduler` is the most behaviorally complex class. Its responsibility is to take an owner and a list of tasks and produce a feasible daily plan. I gave it a `build_plan()` method to handle the selection and ordering logic, and an `explain_plan()` method to produce a human-readable summary of what was scheduled and what was skipped.

**b. Design changes**

Yes, my design changed after reviewing the skeleton before writing any logic.

The first change was adding a `pet` attribute to `CareTask`. In my original UML, tasks and pets were completely separate — a task had no idea which animal it belonged to. I realized that once you have multiple pets, the schedule output would be ambiguous. Linking a task back to a specific `Pet` makes it possible to say "Morning walk → Mochi" instead of just listing task titles.

The second change was adding priority validation. My original design used a plain string for `priority`, which meant anything could be passed in without error. I added a `VALID_PRIORITIES` constant and used `__post_init__` — a dataclass hook that runs right after the object is created — to raise a `ValueError` if the value isn't one of `"low"`, `"medium"`, or `"high"`. This prevents silent bugs where a misspelled priority would sort incorrectly in the scheduler.

The third change was adding a reset and a guard to `Scheduler`. I added `self.schedule = []` as the first line of `build_plan()` so that calling it multiple times doesn't stack results. I also added an early return in `explain_plan()` in case it gets called before `build_plan()` has run, which would otherwise produce a confusing empty output.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
