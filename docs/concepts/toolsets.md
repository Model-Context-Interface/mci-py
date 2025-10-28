# MCI Toolsets Concept

Toolsets are collections of tools organized into reusable, shareable files. They provide a way to structure tools by domain, share them across projects, and apply filtering to control which tools are loaded.

## What are Toolsets?

A **toolset** is a separate MCI schema file that contains a collection of related tools. Unlike main entry files, toolsets:

- Are stored in a library directory (default: `./mci`)
- Contain only tool definitions (no top-level configuration)
- Can be shared across multiple projects
- Support schema-level filtering when loaded

## Toolsets vs Main Schema Files

### Main Entry File (mci.json)

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "My Application"
  },
  "libraryDir": "./mci",
  "directoryAllowList": ["/data"],
  "enableAnyPaths": false,
  "toolsets": [{ "name": "weather" }, { "name": "database" }],
  "tools": [
    {
      "name": "main_tool",
      "execution": {
        "type": "text",
        "text": "Main tool output"
      }
    }
  ]
}
```

**Can contain:**

- `schemaVersion` (required)
- `metadata` (optional)
- `tools` (optional)
- `toolsets` (optional)
- `mcp_servers` (optional)
- `libraryDir` (optional)
- `directoryAllowList` (optional)
- `enableAnyPaths` (optional)

### Toolset File (./mci/weather.mci.json)

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "Weather Toolset",
    "description": "Tools for weather information",
    "version": "1.0.0"
  },
  "tools": [
    {
      "name": "get_weather",
      "description": "Get current weather",
      "tags": ["weather", "read"],
      "execution": {
        "type": "http",
        "method": "GET",
        "url": "https://api.weather.com/current",
        "params": {
          "location": "{{props.location}}"
        }
      }
    },
    {
      "name": "get_forecast",
      "description": "Get weather forecast",
      "tags": ["weather", "read"],
      "execution": {
        "type": "http",
        "method": "GET",
        "url": "https://api.weather.com/forecast",
        "params": {
          "location": "{{props.location}}"
        }
      }
    }
  ]
}
```

**Can contain:**

- `schemaVersion` (required)
- `metadata` (optional - for documentation only)
- `tools` (required)

**Cannot contain:**

- `toolsets`
- `mcp_servers`
- `libraryDir`
- `directoryAllowList`
- `enableAnyPaths`

**Key Differences:**

| Feature                  | Main Entry File       | Toolset File              |
| ------------------------ | --------------------- | ------------------------- |
| Location                 | Project root          | `./mci` directory         |
| Purpose                  | Configure application | Define tool collection    |
| Can reference toolsets   | ✓ Yes                 | ✗ No                      |
| Can register MCP servers | ✓ Yes                 | ✗ No                      |
| Can set security config  | ✓ Yes                 | ✗ No                      |
| Metadata merged          | ✓ Yes                 | ✗ No (documentation only) |
| Tools required           | No                    | Yes                       |

## Creating Toolsets

### Basic Toolset

Create a file in your toolsets directory:

**./mci/github.mci.json:**

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "GitHub Tools",
    "description": "Tools for GitHub API integration",
    "version": "1.0.0",
    "authors": ["DevOps Team"]
  },
  "tools": [
    {
      "name": "create_issue",
      "description": "Create a GitHub issue",
      "tags": ["github", "write"],
      "inputSchema": {
        "type": "object",
        "properties": {
          "title": { "type": "string" },
          "body": { "type": "string" },
          "repo": { "type": "string" }
        },
        "required": ["title", "repo"]
      },
      "execution": {
        "type": "http",
        "method": "POST",
        "url": "https://api.github.com/repos/{{props.repo}}/issues",
        "auth": {
          "type": "bearer",
          "token": "{{env.GITHUB_TOKEN}}"
        },
        "headers": {
          "Accept": "application/vnd.github+json"
        },
        "body": {
          "type": "json",
          "content": {
            "title": "{{props.title}}",
            "body": "{{props.body}}"
          }
        }
      }
    },
    {
      "name": "list_repos",
      "description": "List user repositories",
      "tags": ["github", "read"],
      "execution": {
        "type": "http",
        "method": "GET",
        "url": "https://api.github.com/user/repos",
        "auth": {
          "type": "bearer",
          "token": "{{env.GITHUB_TOKEN}}"
        }
      }
    }
  ]
}
```

### Domain-Organized Toolsets

Organize toolsets by domain or purpose:

**./mci/database.mci.json:**

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "Database Tools"
  },
  "tools": [
    {
      "name": "query_users",
      "tags": ["database", "read"],
      "execution": {
        "type": "cli",
        "command": "psql",
        "args": ["-c", "SELECT * FROM users;"]
      }
    },
    {
      "name": "backup_database",
      "tags": ["database", "write", "admin"],
      "execution": {
        "type": "cli",
        "command": "pg_dump",
        "args": ["-f", "{{props.backup_file}}"]
      }
    }
  ]
}
```

## Loading Toolsets

Toolsets are loaded in the main schema file using the `toolsets` field.

### Basic Loading

```json
{
  "schemaVersion": "1.0",
  "toolsets": [
    { "name": "weather" },
    { "name": "github" },
    { "name": "database" }
  ]
}
```

### With Custom Library Directory

```json
{
  "schemaVersion": "1.0",
  "libraryDir": "./toolsets",
  "toolsets": [{ "name": "weather" }]
}
```

## Toolset Resolving

MCI resolves toolset names using a flexible system that supports both files and directories.

### Resolution Order

When you reference a toolset by name (e.g., `"weather"`), MCI looks for it in this order:

1. **Directory**: `{libraryDir}/weather/` - If found, loads all `.mci.json` files in the directory
2. **Direct File**: `{libraryDir}/weather`
3. **With Extension**: `{libraryDir}/weather.mci.json`
4. **YAML Files**: Also checks `.mci.yaml` and `.mci.yml`

### File-Based Toolset

```
mci/
└── weather.mci.json
```

Reference:

```json
{ "toolsets": [{ "name": "weather" }] }
```

Resolves to: `./mci/weather.mci.json`

### Directory-Based Toolset

```
mci/
└── github/
    ├── issues.mci.json
    ├── prs.mci.json
    └── repos.mci.json
```

Reference:

```json
{ "toolsets": [{ "name": "github" }] }
```

Resolves to: All `.mci.json` files in `./mci/github/`

**Result**: All tools from all files are loaded and merged.

### Nested Directories

```
mci/
└── apis/
    ├── github/
    │   ├── issues.mci.json
    │   └── prs.mci.json
    └── weather.mci.json
```

Reference:

```json
{
  "toolsets": [{ "name": "apis/github" }, { "name": "apis/weather" }]
}
```

### Multiple Files in Directory

When loading from a directory, all `.mci.json` files are loaded:

**./mci/monitoring/status.mci.json:**

```json
{
  "schemaVersion": "1.0",
  "tools": [
    {"name": "check_health", "execution": {...}}
  ]
}
```

**./mci/monitoring/metrics.mci.json:**

```json
{
  "schemaVersion": "1.0",
  "tools": [
    {"name": "get_metrics", "execution": {...}}
  ]
}
```

**Loading:**

```json
{ "toolsets": [{ "name": "monitoring" }] }
```

**Result**: Both `check_health` and `get_metrics` tools are loaded.

**Important Notes:**

- Only tools are merged from directory toolsets
- Metadata is NOT merged (used for documentation only)
- All files must use the same `schemaVersion`
- Schema version mismatch will raise an error

## Schema-Level Filtering

Apply filters when loading toolsets to control which tools are registered.

### Filter Types

| Filter Type   | Description                           | Example                       |
| ------------- | ------------------------------------- | ----------------------------- |
| `only`        | Include only specified tool names     | `"get_weather, get_forecast"` |
| `except`      | Exclude specified tool names          | `"delete_user, drop_table"`   |
| `tags`        | Include only tools with matching tags | `"read, search"`              |
| `withoutTags` | Exclude tools with matching tags      | `"write, delete"`             |

### Examples

**Include Only Specific Tools:**

```json
{
  "toolsets": [
    {
      "name": "weather",
      "filter": "only",
      "filterValue": "get_weather, get_forecast"
    }
  ]
}
```

Result: Only `get_weather` and `get_forecast` tools are loaded from the weather toolset.

**Exclude Dangerous Tools:**

```json
{
  "toolsets": [
    {
      "name": "database",
      "filter": "except",
      "filterValue": "drop_table, delete_all, truncate_table"
    }
  ]
}
```

Result: All database tools except the excluded ones are loaded.

**Filter by Tags (Include):**

```json
{
  "toolsets": [
    {
      "name": "github",
      "filter": "tags",
      "filterValue": "read, search"
    }
  ]
}
```

Result: Only tools tagged with `"read"` or `"search"` are loaded.

**Filter by Tags (Exclude):**

```json
{
  "toolsets": [
    {
      "name": "github",
      "filter": "withoutTags",
      "filterValue": "write, delete, admin"
    }
  ]
}
```

Result: All tools except those tagged with `"write"`, `"delete"`, or `"admin"` are loaded.

### Combining Multiple Toolsets with Different Filters

```json
{
  "schemaVersion": "1.0",
  "toolsets": [
    {
      "name": "weather",
      "filter": "only",
      "filterValue": "get_weather"
    },
    {
      "name": "github",
      "filter": "withoutTags",
      "filterValue": "admin"
    },
    {
      "name": "database",
      "filter": "tags",
      "filterValue": "read"
    },
    {
      "name": "utilities"
    }
  ]
}
```

## Sharing Toolsets

Toolsets are designed to be shared across projects and teams.

### Sharing Within Organization

**Project Structure:**

```
organization/
├── shared-toolsets/
│   ├── github.mci.json
│   ├── slack.mci.json
│   └── monitoring.mci.json
├── project-a/
│   ├── mci.json
│   └── mci/ -> ../shared-toolsets/
└── project-b/
    ├── mci.json
    └── mci/ -> ../shared-toolsets/
```

**Using Symlinks:**

```bash
# In project-a
ln -s ../shared-toolsets ./mci

# In project-b
ln -s ../shared-toolsets ./mci
```

### Sharing via Git Submodules

```bash
# Add shared toolsets as submodule
git submodule add https://github.com/org/mci-toolsets.git ./mci

# Update toolsets
git submodule update --remote
```

### Sharing via Package Manager

**npm Example:**

```bash
# Publish toolsets as npm package
npm publish @company/mci-toolsets

# Install in project
npm install @company/mci-toolsets
```

**In your schema:**

```json
{
  "libraryDir": "./node_modules/@company/mci-toolsets",
  "toolsets": [{ "name": "github" }, { "name": "slack" }]
}
```

## Best Practices

### 1. Organize by Domain

```
mci/
├── apis/
│   ├── github.mci.json
│   ├── slack.mci.json
│   └── weather.mci.json
├── databases/
│   ├── postgres.mci.json
│   └── redis.mci.json
└── utilities/
    ├── logging.mci.json
    └── monitoring.mci.json
```

### 2. Use Tags for Categorization

```json
{
  "tools": [
    {
      "name": "read_data",
      "tags": ["database", "read", "safe"]
    },
    {
      "name": "delete_data",
      "tags": ["database", "write", "destructive"]
    }
  ]
}
```

Then filter by tags:

```json
{
  "toolsets": [
    {
      "name": "database",
      "filter": "tags",
      "filterValue": "read, safe"
    }
  ]
}
```

### 3. Document Toolsets

```json
{
  "metadata": {
    "name": "GitHub API Tools",
    "description": "Complete GitHub API integration toolset. Requires GITHUB_TOKEN environment variable.",
    "version": "2.1.0",
    "authors": ["DevOps Team", "Platform Team"],
    "license": "MIT"
  }
}
```

### 4. Version Toolsets

Use semantic versioning in metadata:

```json
{
  "metadata": {
    "version": "2.1.0"
  }
}
```

### 5. Keep Toolsets Focused

Each toolset should focus on a single domain:

✓ Good:

- `github.mci.json` - GitHub API tools
- `slack.mci.json` - Slack API tools
- `monitoring.mci.json` - Monitoring tools

✗ Avoid:

- `misc.mci.json` - Mixed unrelated tools
- `everything.mci.json` - Too broad

## Examples

### Example 1: External APIs Toolset

**./mci/external-apis.mci.json:**

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "External APIs",
    "description": "Third-party API integrations"
  },
  "tools": [
    {
      "name": "fetch_weather",
      "tags": ["api", "weather", "read"],
      "execution": {
        "type": "http",
        "url": "https://api.weather.com/v1/current",
        "auth": {
          "type": "apiKey",
          "in": "header",
          "name": "X-API-Key",
          "value": "{{env.WEATHER_API_KEY}}"
        }
      }
    },
    {
      "name": "translate_text",
      "tags": ["api", "translation", "read"],
      "execution": {
        "type": "http",
        "url": "https://api.translate.com/v1/translate",
        "auth": {
          "type": "bearer",
          "token": "{{env.TRANSLATE_API_TOKEN}}"
        }
      }
    }
  ]
}
```

### Example 2: DevOps Toolset

**./mci/devops.mci.json:**

```json
{
  "schemaVersion": "1.0",
  "metadata": {
    "name": "DevOps Tools"
  },
  "tools": [
    {
      "name": "deploy_app",
      "tags": ["devops", "deploy", "write"],
      "execution": {
        "type": "cli",
        "command": "kubectl",
        "args": ["apply", "-f", "{{props.config_file}}"]
      }
    },
    {
      "name": "check_pods",
      "tags": ["devops", "monitoring", "read"],
      "execution": {
        "type": "cli",
        "command": "kubectl",
        "args": ["get", "pods"]
      }
    },
    {
      "name": "rollback_deployment",
      "tags": ["devops", "deploy", "write", "destructive"],
      "execution": {
        "type": "cli",
        "command": "kubectl",
        "args": ["rollout", "undo", "deployment/{{props.deployment_name}}"]
      }
    }
  ]
}
```

**Loading with Filters:**

```json
{
  "toolsets": [
    {
      "name": "devops",
      "filter": "withoutTags",
      "filterValue": "destructive"
    }
  ]
}
```

## Summary

- **Toolsets** organize tools into reusable collections
- **Main Schema Files** configure applications and reference toolsets
- **Toolset Files** contain only tool definitions
- **Resolving** supports both files and directories
- **Filtering** controls which tools are loaded from toolsets
- **Sharing** enables reuse across projects and teams

Toolsets make it easy to organize, maintain, and share tools across your organization.

## See Also

- [Structure Concept](structure.md) - Project organization and entry files
- [Tools Concept](tools.md) - Understanding tool execution types
- [MCP Servers Concept](mcp_servers.md) - Integrating MCP servers
- [Schema Reference](../schema_reference.md) - Complete schema documentation
