---
sidebar_position: 4
---

# User Workflows

User workflows are custom Drona Workflows that enable researchers to create, customize, and deploy their own computational workflows within their personal workspace. These workflows provide complete isolation from system-wide workflows while maintaining full functionality and integration with the Drona Workflow Engine platform.

*[Image placeholder: User workflows appearing with blue highlighting in the workflow selection interface]*

## What are User Workflows?

User workflows are self-contained workflow definitions stored in your personal directory that follow the same architecture and structure as system workflows. Each user workflow represents a complete computational environment tailored to your specific research needs, allowing for experimental development, custom modifications, and specialized computational frameworks without requiring system-level permissions.

## Workflow Storage

User workflows are stored in your personal Drona directory under the `environments/` subdirectory. By default, this path is:

```
$SCRATCH/drona_composer/environments/
```

This default storage location can be configured through the [Drona User Configuration](./user-configuration) settings to match your preferred directory structure and workspace organization.

## Workflow Structure

Any directory within the `environments/` directory will be treated as a workflow environment. As long as the directory contains the necessary workflow files (schema.json, map.json, utils.py, and template files), it will function as a fully operational Drona Workflow.

User workflows appear with blue highlighting in the workflow selection interface, making them easily distinguishable from system-provided workflows and allowing for quick identification of custom environments.

---

**Texas A&M University High Performance Research Computing**