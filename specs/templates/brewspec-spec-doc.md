# BrewSpec vX.Y

> **For the dev**: This template defines the required structure for the human-readable
> spec document (`brewspec-vX.Y.md`) that lives in the public brewspec repo alongside
> the JSON Schema. It is a separate artifact from the technical design in `specs/designs/`.
>
> Before writing this file:
> 1. Copy `brewspec-vX.(Y-1).md` → `versions/brewspec-vX.(Y-1).md` (archive previous version)
> 2. Write this file to the brewspec repo root as `brewspec-vX.Y.md`
>
> All sections marked **[Required]** must be present. Sections marked **[If applicable]**
> are included when relevant to the version.

---

## Overview [Required]

BrewSpec is an open standard for describing coffee brews as structured data. It defines a YAML/JSON format that tools can use to record, share, and analyse brew sessions — covering brew parameters, equipment, ingredients, and outcomes.

The schema is designed to be minimal and extensible. Tools may store only the fields they use; all fields except `brewspec_version`, `type`, and `brews` are optional.

**Current version:** X.Y
**Schema file:** `brewspec.schema.json`
**License:** [license]

---

## Field Reference [Required]

Complete reference for all fields in vX.Y. Every field in the JSON Schema must appear here.

### Top-Level Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `brewspec_version` | string | Yes | const: `"X.Y"` | Must be the literal string `"X.Y"`. Rejected if mismatched. |
| `type` | string | Yes | enum: [...] | Brew method category. |
| `brews` | array | Yes | minItems: 1 | Array of brew objects. At least one brew required. |

### Brew Object Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `date` | string | No | [pattern] | [description] |
| ... | | | | |

### [Nested Object] Fields

*Repeat for each nested object (e.g. coffee, water, equipment, result, ratings).*

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| ... | | | | |

---

## What Changed in vX.Y [Required]

### New Fields

- **`field_name`** (`type`, optional) — [description of the new field and where it lives]

### Breaking Changes

List any changes that will cause previously valid documents to fail validation under vX.Y.

- **`field_name` removed from [location]** — [what it became; migration path]
- **`field_name` changed from [old type] to [new type]** — [impact and migration path]

### Non-Breaking Changes

- **`field_name`** — [description of additive or constraint change]

---

## Validation [Required]

Tools implementing BrewSpec should validate documents at **storage time** — when a brew is saved or imported — not only at display time. Validating only on display allows corrupt or non-compliant documents to enter storage silently.

The reference validator uses the JSON Schema at `brewspec.schema.json` via the `jsonschema` library:

```python
import json
import yaml
import jsonschema

with open("brewspec.schema.json") as f:
    schema = json.load(f)

with open("brew.yaml") as f:
    document = yaml.safe_load(f)

jsonschema.validate(document, schema)  # raises ValidationError on failure
```

Invalid documents should be rejected with a clear error message. Do not silently coerce invalid values.

---

## Backward Compatibility [Required]

### Documents from vX.(Y-1)

*Describe whether old documents are valid under the new schema, and if not, what migration is required.*

**Breaking changes** in this version mean that vX.(Y-1) documents will fail validation under vX.Y if they contain:

- [List each breaking condition]

**Migration steps** for existing documents:

1. [Step 1]
2. [Step 2]

Tools that need to support both versions should check the `brewspec_version` field and apply version-specific parsing.

---

## Examples [If applicable]

Reference the examples in the `examples/` directory. Do not embed full examples here — link to them.

Valid examples:
- `examples/valid/pour_over.yaml` — [brief description]
- `examples/valid/espresso.yaml` — [brief description]

Invalid examples (for testing validators):
- `examples/invalid/invalid_[reason].yaml` — [what makes it invalid]

---

## Open Questions [If applicable]

Document any intentional deferral decisions or unresolved design questions for future versions.

- **[Topic]** — [Description of the open question and why it was deferred]
