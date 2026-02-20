---
sidebar_position: 5
---

# Utility Functions

Utility functions let you add Python logic to a workflow. They are defined in `utils.py` and are primarily used by `map.json` to compute values that cannot be expressed as simple string substitutions.

## How `utils.py` Is Used

During map evaluation, Drona processes each mapping value in this order:

1. Replaces form references like `$fieldName` with submitted values.
2. Executes function calls written as `!functionName(...)`.
3. Uses the function return value as part of the final mapping string.

Example in `map.json`:

```json
{
  "mappings": {
    "RUN_COMMAND": "!build_run_command($mode, $partition)",
    "JOB_TAG": "project-$project_id"
  }
}
```

Example in environment `utils.py`:

```python
def build_run_command(mode, partition):
    if mode == "gpu":
        return f"sbatch --partition={partition} gpu.job"
    return f"sbatch --partition={partition} cpu.job"
```

## Function Call Syntax in `map.json`

Use `!` to call a function:

```json
"KEY": "!my_function($dynamic_value, 'static_value')"
```

- `$dynamic_value` comes from form input.
- `'static_value'` is passed literally.
- The function result is inserted back into the mapping.

This matches the HPRC workflow docs for creating mappings from input values to placeholders in `map.json`.

## Predefined Utility Functions

Drona includes shared helpers from `machine_driver_scripts/utils.py` (implemented in `packages/drona_utils/core.py`). These are available to environment utility logic:

| Function | Purpose |
|---|---|
| `drona_add_additional_file(additional_file, preview_name="", preview_order=0)` | Adds a file to the preview/output set by writing metadata to `/tmp/$USER.additional_files`. |
| `drona_add_mapping(key, evaluation_str)` | Adds or overrides a map entry by writing to `/tmp/$USER.map`. |
| `drona_add_message(msg_text, msg_type)` | Adds a UI message (`error`, `warning`, `note`) via `/tmp/$USER.messages`. |
| `drona_add_warning(warning)` | Convenience wrapper for `drona_add_message(..., "warning")`. |
| `drona_add_error(error)` | Convenience wrapper for `drona_add_message(..., "error")`. |
| `drona_add_note(note)` | Convenience wrapper for `drona_add_message(..., "note")`. |

### Naming Note (`drona_add_file`)

Some external HPRC documentation refers to a helper named `drona_add_file(...)`. In this repository, the equivalent helper is named:

```python
drona_add_additional_file(...)
```

Use `drona_add_additional_file` when authoring new environments in this codebase.

## Typical Pattern

Use a custom function for business logic, then optionally emit extra map values or messages:

```python
def configure_job(mode, walltime):
    if mode not in ["cpu", "gpu"]:
        drona_add_error("Invalid mode selected.")
        return ""

    drona_add_mapping("WALLTIME", walltime)
    drona_add_note(f"Configured mode: {mode}")
    return f"--mode={mode}"
```

Then in `map.json`:

```json
{
  "mappings": {
    "RUN_FLAGS": "!configure_job($mode, $walltime)"
  }
}
```

## Best Practices

- Keep utility functions deterministic and fast.
- Return strings for direct substitution into mappings.
- Use `drona_add_error`/`drona_add_warning` for user-facing feedback instead of embedding errors in scripts.
- Use `drona_add_mapping` when one function needs to populate multiple map variables.

---

**Texas A&M University High Performance Research Computing**
