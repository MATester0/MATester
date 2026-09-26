# Issue Collection and Classification Dataset

This directory contains a step-by-step issue collection and classification dataset for multimodal agent (MAgent) systems, organized by three source types: **survey**, **GitHub**, and **conference**.

## Source Types

| Directory | Description |
|-----------|-------------|
| `survey/` | Issues from agent repositories identified in a systematic literature survey |
| `github/` | Issues from agent repositories discovered via GitHub search |
| `conference/` | Issues from agent repositories published at top AI/SE conferences |

Each source directory contains the same four-level subdirectory structure representing successive stages of collection and annotation.

---

## Directory Structure

```
data/
├── survey/
│   ├── raw_data/
│   ├── issue_related_data/
│   ├── functionality_issue_related_data/
│   └── functionality_issue_analysis_data/
├── github/
│   ├── raw_data/
│   ├── issue_related_data/
│   ├── functionality_issue_related_data/
│   └── functionality_issue_analysis_data/
├── conference/
│   ├── raw_data/
│   ├── issue_related_data/
│   ├── functionality_issue_related_data/
│   └── functionality_issue_analysis_data/
├── bug_types.txt
├── global_symptom.txt
├── module_symptom.txt
└── root_cause.txt
```

Each file is named `<agentID>_<owner>_<repo>.jsonl`, where `agentID` is the unique identifier assigned to the agent project.

---

## Step-by-Step Annotation Pipeline

### Step 1 — `raw_data/`

Raw issue reports and pull requests collected from GitHub, with no filtering applied. Each record contains basic metadata: `agent ID`, `type` (issue / pull request), `issue / pull request ID`, `url`, `status`, `title`, and `time`.

### Step 2 — `issue_related_data/`

Filtered subset of `raw_data`. Each record is annotated with `is_issue: true/false` to indicate whether the report corresponds to a genuine bug or problem (as opposed to feature requests, questions, or duplicates).

### Step 3 — `functionality_issue_related_data/`

Filtered subset of `issue_related_data` (only `is_issue: true` records). Each record is further annotated with `issue_type`, classifying the bug into one of the categories defined in [`bug_types.txt`](#bug-type-taxonomy). Records classified as `"functionality issue"` (i.e., bugs in agent-specific logic) are carried forward to the next step.

### Step 4 — `functionality_issue_analysis_data/`

Deep analysis of `"functionality issue"` records from Step 3. Each record contains an `analysis` array with one or more entries, each specifying:

| Field | Description |
|-------|-------------|
| `symptom` | Global symptom category (see [`global_symptom.txt`](#global-symptom-categories)) |
| `location` | Fine-grained module-level symptom in the agent pipeline (see [`module_symptom.txt`](#module-level-symptom-taxonomy)) |
| `root cause` | Root cause category ID or an object with ID and free-text explanation (see [`root_cause.txt`](#root-cause-categories)) |

---

## Taxonomy Files

### Bug Type Taxonomy (`bug_types.txt`)

Top-level classification of all issue reports:

**User Responsible Issues**
- `usage issue` — incorrect usage by the user
- `dependency issue` — missing or incompatible dependencies on the user side
- `configuration issue` — misconfiguration by the user

**Developer Responsible Issues**
- `import issue` — import errors in source code
- `dependency issue` — library/package problems in the codebase
- `functionality issue` — bugs in the agent's core functionality
- `functionality issue (not agent)` — bugs in non-agent components of the repository
- `version compatibility issue` — breakage due to version changes
- `cross-system compatibility issue` — platform-specific failures

**False Positive Issues**
- `not an issue` — reports that do not describe a real problem

---

### Global Symptom Categories (`global_symptom.txt`)

Observable failure modes at the system level:

| ID | Category |
|----|----------|
| 1 | crash |
| 2 | unrespond |
| 3 | incorrect behavior (misbehave) |
| 4 | mis-notify the exit (mis-signal) |
| 5 | inconsistent behavior under the same setting (diverge) |
| 6 | user interface provides wrong information (misinform) |

---

### Module-Level Symptom Taxonomy (`module_symptom.txt`)

Fine-grained location of the fault within the agent pipeline, organized by three core modules:

**1. Perception**
- `1.1 Wrong-S` — snapshot is wrong or incomplete vs. the environment
  - `1.1.1 SM` — same modality, different content
  - `1.1.2 DM` — different modalities, different content
- `1.2 Inconsistent-S` — two identical environments yield different snapshots
  - `1.2.1 SM` / `1.2.2 DM`
- `1.3 Malformed-S` — snapshot has wrong format
- `1.4 Missing-S` — snapshot does not exist
- `1.5 / 1.1.3 Mislabeled-S` — snapshot labels are wrong or incomplete

**2. Planner**
- `2.1 Conflict-P` — plan is internally contradictory
- `2.2 Inapplicable-P` — plan does not satisfy snapshot constraints
  - `2.2.1 SM` / `2.2.2 DM`
- `2.3 Irrelevant-P` — plan is unrelated to the task
  - `2.3.1 Wrong-Stop` — task is over but plan continues
  - `2.3.2 Wrong-Stop` — task is not over but plan stops
  - `2.3.3 Wrong-Step` — plan cannot advance the task
- `2.4 Malformed-P` — plan has wrong format
- `2.5 Inconsistent-P` — same inputs yield different plans and execution results
  - `2.5.1 SM` / `2.5.2 DM`
- `2.6 Missing-P` — model not loaded or plan does not exist
- `2.7 Wrong-PR` — prompts are not generated correctly

**3. Executor**
- `3.1 Wrong-A` — action differs from the plan
- `3.2 Inapplicable-A` — action is not applicable to the environment
  - `3.2.1 Wrong-P&A` — wrong plan propagated without checking
  - `3.2.2 Wrong-API` — action API is implemented incorrectly
- `3.3 Wrong-R` — reflection on action result is wrong
- `3.4 Missing-A` — action does not exist

---

### Root Cause Categories (`root_cause.txt`)

Underlying causes of functionality issues:

| ID | Category |
|----|----------|
| 1 | concurrency |
| 2 | corner case gaps |
| 3 | LLM's limitation |
| 4 | unsuitable LLM parameters (bad parameters) |
| 5 | error case gaps |
| 6 | lack of persistent memories for task execution experience (No persistent memory) |
| 7 | incorrect code semantics (incorrect semantics) |

When `root cause` is an object (e.g., `{"7": "snapshot only describes the first level children..."}`), the key is the category ID and the value provides a free-text explanation of the specific manifestation.
