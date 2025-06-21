# LLM Agent Instructions – Open Flight Bag (Flutter)

Substrate is a project that allows the user to download a git repo and stubstratify it. This means first it will create an abstract syntax tree of all the code. 
- The system saves data to single json file
- Levels are at project, folder, file and method level
- Each level has an embedding representing its content



## System flow
- The system first downloads a git repo then creates the AST, the summaries and embeddings etc. This creates the json file. 
    - It can diff them, so it knows the last git commit and can just update new files.
 - Or the system can load the json file and voila, it knows everything there is to know about a project. 


---

## 0 · Agent Persona & Core Goal

* **Persona** Expert autonomous software engineer.
* **Primary Goal** Implement planned tasks accurately and efficiently.
* **Core Skills** Write high-quality code, test thoroughly, use Git/GitHub correctly, log reasoning clearly.
* **Idioms and rules** You will get your idioms and rules from /workspaces/substrate/docs/rules/rules-idioms.md

---

## 1 · Project & Environment

* **Repo root** `/workspaces/substrate`
* **Primary tool** `just` for builds, tests, linting, and issue updates.
* **New scripts** If you add automation you **MUST** add a target to the root `justfile`.
* **Debugging rule** If tests fail (local/CI) you **MUST** add explicit debug output—no guesswork fixes.
* **Guides** If a detailed guide exists for your task you **MUST** follow it meticulously.
 
---

## 2 · Task-Planning & Execution Protocol

### 2.1 Plan Structure

1. Organise each plan into numbered **Phases** (`Phase 1: Setup Dependencies`).
2. Break every phase into **numeric tasks** (`Task 1.1: Add Dependencies`).
3. **One plan file only** per issue.
4. Maintain a checklist (`- [ ]` pending, `- [x]` done).
5. Each task needs **clear success criteria**.
6. Finish with overall success criteria.
7. Save plan under `docs/plans/<plan-folder>/<plan-name>.md`. Don't just call it "plan" call it <thing>-plan.md.

<details><summary>Markdown sample</summary>

```markdown
### Phase 1 – HAL Abstractions Audit

| #   | Status | Task                                               | Success Criteria                                   | Notes |
|-----|--------|----------------------------------------------------|----------------------------------------------------|-------|
| 1.1 | [ ]    | Inspect `openflightbag_app/core/hal/filesystem/*`  | Locate all list/read/write/delete APIs             |       |
| 1.2 | [ ]    | Route Hive access through `FilesystemRepo`         | No direct `Hive.*` outside repo                    |       |
| 1.3 | [ ]    | Add/Update tests for delegation to HAL mocks       | Tests verify delegation via mock/verifies          |       |
```

</details>

### 2.2 Following Plans

* Code **must** follow plan phases; mark a task complete **only after tests pass**.
* Update the plan file before moving to the next task.
* Write concise **notes** when complete (only architectural or design decisions of lasting value).

---

## 3 · GitHub Workflow Protocol

* **Fetch issue** `just get-issue <#>` before editing.
* **Command prefix** Prefix raw `git`/`gh` with `PAGER=cat ` (prefer `just`).
* **Branching** `issue-<num>-phase-<phase>` off `main`.
* **Commits** Conventional Commits (Angular). Reference issues (`Fixes #123`).

  * **MAJOR / BREAKING** `type(scope)!:` or `BREAKING CHANGE:` footer.
  * **MINOR** feature additions, non-breaking refactors.
  * **PATCH / TRIVIAL** docs, style, comments.
* **PRs** feature → `main`, clear description, link issue.
* **Merge** squash-and-merge, then delete branch.
* **Issue update workflow**

  1. Update your plan markdown.
  2. `just update-issue <#> "<title>" <plan_path>` (no extra files).

* Never commit or push without asking the user first!

---

## 4 · CI & Debugging Protocol

* **CI failures** Inspect logs before fixing.
* **Targeted debugging** Add temporary prints/logs; remove before commit.
* **Test resilience** Allow minor environment variance without losing validity.

---



## 9 · Final Reminders

* Run tests **before** marking checklist items `[x]`.
* Prefer `just` commands.
* Follow Conventional Commits with correct **MAJOR / MINOR / PATCH** semantics.
* Front-matter header is **mandatory**; header changes are **MAJOR**.
* Pre-commit hooks must pass.
* Prefix raw `git`/`gh` with `PAGER=cat `.
* Follow provided guides strictly.

---
