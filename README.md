# mci-py

**MCI Python Adapter** - A lightweight, Python adapter for the Model Context Interface (MCI), enabling AI agents to execute tools defined in JSON schemas.

The **Model Context Interface (MCI)** is an open-source, platform-agnostic system for defining and executing AI agent tools through standardized JSON schemas.

Using the basic features that are supported in **every programming language**, MCI makes it easier to define collections of AI Tools, filter, execute and maintain. Making it a strong alternative or supplement of MCP, which lives right in your project repo and fits in single JSON file. (Check [example.mci.json](https://github.com/Model-Context-Interface/mci-py/blob/main/example.mci.json) & [example.py](https://github.com/Model-Context-Interface/mci-py/blob/main/example.py))

The `mci-py` Python adapter allows you to load tool definitions from JSON files and execute them with full control over authentication, templating, and error handling.

---

## Features

- 🚀 **Simple API** - Load and execute tools with just a few lines of Python code
- 📝 **JSON Schema-Based** - Define tools declaratively and statically in JSON files
- 🔄 **Multiple Execution Types** - Support for HTTP, CLI, File, and Text execution
- ✔️ **Easy to build** - Share MCI Schema reference and documentation of any REST API or CLI application to LLM to build your favorite tools in minute
- 🔐 **Built-in Authentication** - API Key, Bearer Token, Basic Auth, and OAuth2 support
- 🔁 **Easy to share** - All you need to move your toolset to another project, or share it to the world is a single JSON file.
- 🎯 **Template Engine** - Dynamic value substitution for environment variables and properties, as well as advanced templating directives like "@if", "@foreach", etc. to support complex prompting.
- 🔒 **Secure by design** - All you need is adapter and JSON file, which is easy to review, even by an LLM, compared to the whole servers. No more third-party code or servers accessing your data.
- 💔 **Flexible separation** - You can have one ".mci.json" file for whole project and filter tools out, or you can have 1 file per agent to include whole toolset of agent, or you can have 1 file per API wrapped, you can even have 10 files from different authors and use only 1 tool from each - you can do anything: it doesn't matter, it's not 10 MCP servers to initialize, it's just 10 files in your repo 🤷
- 🎨 **Type Safe** - Full type hints and Pydantic validation
- 🧪 **Well Tested** - 92%+ test coverage with comprehensive test suite

### Planned

- **Switch template engine** - Now `mci-py` have built-in basic template engine supporting variables, @if, @for & @foreach blocks. We are planning to add implement Jinja for more robust templating options and update JSON schema to define template engine
- **Include** - Add `@include("path/to/file.md")` directive to simplify reusing the prompt parts

---

## Usage example

```python
from mcipy import MCIClient

# Initialize with your schema file
client = MCIClient(
    json_file_path="my-tools.mci.json",
    env_vars={
        "API_KEY": "your-secret-key",
    }
)

# Get all tool objects
tools = client.tools()

# Execute the tool with properties
result = client.execute(
    tool_name="greet_user",
    properties={"username": "Alice"}
)

```

---

## Documentation

- [API Reference](docs/api_reference.md) - Comprehensive API documentation
- [Quickstart Guide](docs/quickstart.md) - Get started quickly with examples
- [Schema Reference](docs/schema_reference.md) - Complete JSON schema documentation

---

## Examples

Explore the [examples directory](./examples/) for comprehensive demonstrations:

- [HTTP Example](./examples/http_example.json) - HTTP API calls with authentication
- [CLI Example](./examples/cli_example.json) - Command-line tool execution
- [File Example](./examples/file_example.json) - File reading with templating
- [Text Example](./examples/text_example.json) - Text template generation
- [Mixed Example](./examples/mixed_example.json) - Combined execution types
- [Python Usage Example](./examples/example_usage.py) - Complete Python integration example

---

## Support

Need help or have questions?

- 📖 Check the [Documentation](#documentation) section above
- 🐛 [Open an issue](https://github.com/Model-Context-Interface/mci-py/issues) for bug reports
- 💬 [Start a discussion](https://github.com/Model-Context-Interface/mci-py/discussions) for questions and ideas
- 📧 Contact the maintainer: revaz.gh@gmail.com

---

## Contribution

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our coding standards
4. Run tests and linting (`make test && make lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

To quickly set up your development environment, run:

```shell
./setup_env.sh
```

This will install `uv`, Python, and all project dependencies automatically.

### Test Coverage

Run `make coverage` for coverage report

### Project Docs

For how to install uv and Python, see [installation.md](installation.md).

For development workflows, see [development.md](development.md).

For instructions on publishing to PyPI, see [publishing.md](publishing.md).

---

## Donation

**This project is not backed or funded in any way.** It was started by an individual developer and is maintained by the community. If you find this project useful, you can help in several ways:

- ⭐ Star the repository to show your support
- 🐛 Report bugs and suggest features
- 💻 Contribute code, documentation, or examples
- 📢 Spread the word and share the project
- 💝 Consider a donation to support ongoing development

Any kind of help is greatly appreciated! 🙏

---

## Credits

- **Author**: [MaestroError](https://github.com/MaestroError) (Revaz Ghambarashvili)
- **Contributors**: Thank you to all the amazing [contributors](https://github.com/Model-Context-Interface/mci-py/graphs/contributors) who have helped improve this project!
- **Template**: This project was built from [simple-modern-uv](https://github.com/jlevy/simple-modern-uv)
