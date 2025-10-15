# mci-py

**MCI Python Adapter** - A lightweight, synchronous Python adapter for the Model Context Interface (MCI), enabling AI agents to execute tools defined in JSON schemas.

The Model Context Interface (MCI) is an open-source, platform-agnostic system for defining and executing AI agent tools through standardized JSON schemas. The `mci-py` Python adapter allows you to load tool definitions from JSON files and execute them synchronously with full control over authentication, templating, and error handling.

---

## Features

- 🚀 **Simple API** - Load and execute tools with just a few lines of Python code
- 📝 **JSON Schema-Based** - Define tools declaratively in JSON files
- 🔄 **Multiple Execution Types** - Support for HTTP, CLI, File, and Text execution
- 🔐 **Built-in Authentication** - API Key, Bearer Token, Basic Auth, and OAuth2 support
- 🎯 **Template Engine** - Dynamic value substitution for environment variables and properties
- ⚡ **Synchronous Execution** - Direct, predictable tool execution without async complexity
- 🔒 **Security First** - Environment-based secrets management
- 🎨 **Type Safe** - Full type hints and Pydantic validation
- 🧪 **Well Tested** - 90%+ test coverage with comprehensive test suite

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
