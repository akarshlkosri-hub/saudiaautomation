# Saudia Automation — AI Agent Rules

## Project Context
This is the Saudia Airlines AlFursan Login Automation project.
- **BLUEPRINT:** Always read `C:\Users\ashus\SaudiaAutomation\BLUEPRINT.md` first for full technical context.
- **MILESTONES:** Read `C:\Users\ashus\SaudiaAutomation\MILESTONES.md` to see what's done and where we are.
- **TASKS:** Follow the task.md step-by-step checklist.

---

## Milestone Rule (IMPORTANT)

When the user types **`done-9335`**, it means the current task is CONFIRMED COMPLETE. You MUST:

1. **Update `MILESTONES.md`** — Add a new milestone entry with:
   - Date and time
   - What was built (files created/modified)
   - Problems faced and how they were solved
   - How it was tested/verified
   - What the next step is

2. **Update `task.md`** — Mark the completed items as `[x]`

3. **Confirm to user** — Print a brief summary of what was logged

If user types anything else with feedback (like "done-9335 but OTP was slow"), include that feedback in the milestone.

---

## Mid-Task Update Rule

If the user says the plan needs to change mid-task (new requirement, bug found, approach change):

1. **Update `BLUEPRINT.md`** — Modify the relevant section
2. **Update `task.md`** — Add/modify/reorder tasks as needed
3. **Add a note in `MILESTONES.md`** — Log what changed and why, like:
   ```
   ### UPDATE — [Brief description]
   - **Date:** ...
   - **What changed:** ...
   - **Why:** ...
   - **Impact on remaining tasks:** ...
   ```

---

## General Rules

- All code goes in `C:\Users\ashus\SaudiaAutomation\scripts\`
- Excel file is at `C:\Users\ashus\SaudiaAutomation\data\passengers.xlsx`
- Phone automation APK project is at `C:\Users\ashus\SaudiaAutomationWorker\` (DO NOT modify unless specifically asked)
- Old remote control script for reference: `C:\Users\ashus\PNR\remote_control.py`
- No emojis in Python print() statements (Windows terminal crashes)
- Test each component independently before combining
- Always use full absolute paths, never relative paths
