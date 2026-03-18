# Pipeline Status

Show the current state of all tasks in the manifest as a clean, scannable summary.

## Instructions

Read `manifest.yaml` and produce a status report. Your job is to present the information clearly — no interpretation, no recommendations unless something is clearly wrong.

### Step 1: Read the manifest

Read `manifest.yaml` in full.

### Step 2: Group tasks by state

Organise tasks into these groups (omit empty groups):

**In Progress** — tasks with status: specifying, designing, building, reviewing
**Ready** — tasks with status: ready_for_spec, ready_for_design, ready_for_dev, ready_for_review, ready_for_deploy (and no unresolved blockers)
**Blocked** — tasks in backlog or with a `blocked_by` field that references an incomplete dependency
**Recently Done** — tasks with status: done, sorted by completed_date descending, show last 3

### Step 3: Format the output

Use this format:

```
## Pipeline Status — [today's date]

### In Progress
| Task | Stage | Assigned |
|------|-------|----------|
| [task name] | [human-readable stage] | [assigned_to or —] |

### Ready to Start
| Task | Waiting for | Priority |
|------|-------------|----------|
| [task name] | [next agent: PM / architect / dev / reviewer / deploy] | [P0–P5] |

### Blocked
| Task | Blocked by |
|------|------------|
| [task name] | [reason — dependency task or blocked_by note] |

### Recently Shipped
| Task | Completed | Tag |
|------|-----------|-----|
| [task name] | [completed_date] | [tag if present] |

### Flags
[Only include this section if something needs attention:]
- [task] has been in [status] since [date] with no recent activity
- [task] depends on [other task] which is still in progress
```

### Stage labels (for In Progress column)

| Manifest status | Human label |
|---|---|
| specifying | Writing spec |
| designing | Designing |
| building | Building |
| reviewing | Under review |
| ready_for_deploy | Awaiting deploy |

### Step 4: Output only

Print the status report to the conversation. Do not write any files. Do not make any changes.
