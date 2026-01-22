---
sidebar_position: 3
---

# Retriever Scripts

Retriever scripts dynamically populate form fields or display real-time information by executing shell scripts server-side. These scripts integrate with dynamic form components to provide context-aware interfaces that respond to user selections and system state.

## Overview

Retriever scripts enable workflows to present dynamic content based on user input, available resources, or system conditions. Scripts execute when fields initially render and re-execute automatically when referenced form values change.

## Schema Configuration

Link retrievers to form fields using the `retriever` property. Use `retrieverParams` to pass data to scripts and trigger re-execution when field values change.

### Basic Configuration

```json
{
  "partition": {
    "type": "select",
    "name": "partition",
    "options": [
      {"value": "gpu", "label": "GPU Partition"},
      {"value": "cpu", "label": "CPU Partition"}
    ]
  },
  "nodeCount": {
    "type": "text",
    "name": "nodeCount",
    "label": "Number of Nodes"
  },
  "nodeSelector": {
    "type": "autocompleteSelect",
    "retriever": "scripts/get_nodes.sh",
    "retrieverParams": {
      "PARTITION": "$partition",
      "NODE_COUNT": "$nodeCount",
      "ARCHITECTURE": "x86_64"
    },
    "placeholder": "Select node..."
  }
}
```

### Parameter Syntax

Parameters in `retrieverParams` support two modes:

- **Field References**: Use `$fieldName` to reference form field values (e.g., `"$partition"` gets the value from the `partition` field)
- **Static Values**: Pass literal values directly (e.g., `"x86_64"` passes the string "x86_64")

When referenced fields change, the script automatically re-executes with updated values passed as uppercase environment variables.

## Script Structure

Script output requirements depend on the consuming component type.

### Components Requiring JSON

These components need structured JSON output:
- **dynamicSelect**, **autocompleteSelect**: Array of `{value, label}` objects
- **dynamicCheckboxGroup**, **dynamicRadioGroup**: Array of option objects

```bash
#!/bin/bash
cat << EOF
[
  {"value": "node001", "label": "Node 001 (Available)"},
  {"value": "node002", "label": "Node 002 (Available)"}
]
EOF
```

### Components Accepting Plain Text

These components accept any text output:
- **staticText**: Displays text content directly
- **hidden**: Stores text value

```bash
#!/bin/bash
echo "Configuration valid for $PARTITION partition"
```

## Retriever Script Example

```bash
#!/bin/bash
# scripts/estimate_cost.sh

NODES=${NODE_COUNT:-1}
HOURS=${WALLTIME:-1}
PARTITION=${PARTITION:-cpu}

case $PARTITION in
  gpu) RATE=4.0 ;;
  bigmem) RATE=2.0 ;;
  *) RATE=1.0 ;;
esac

TOTAL=$(echo "$NODES * $HOURS * $RATE" | bc)

cat << EOF
{
  "message": "Estimated: $TOTAL Service Units",
  "severity": "$([ $(echo "$TOTAL > 1000" | bc) -eq 1 ] && echo "warning" || echo "info")"
}
EOF
```

## Environment Variables

Form field values from `retrieverParams` automatically pass to retrievers as environment variables. Scripts also receive default environment context:

- `DRONA_ENV_DIR`: Full path to current environment directory
- `DRONA_ENV_NAME`: Environment name (e.g., "Generic")
- `DRONA_RUNTIME_DIR`: Runtime directory path

Access these in your scripts:
```bash
#!/bin/bash
# Access form field values
SELECTED_PARTITION=${PARTITION:-cpu}
NODE_COUNT=${NODE_COUNT:-1}

# Access environment context
echo "Running in environment: $DRONA_ENV_NAME"
echo "Config directory: $DRONA_ENV_DIR/config"
```

## Best Practices

- Keep execution under 5 seconds for responsive interfaces
- Return meaningful errors with appropriate messages
- Cache expensive operations when possible

---
