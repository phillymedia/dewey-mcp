# Separate Runtime and Dev Dependencies

Dewey MCP keeps production dependencies minimal and separates local maintenance tooling into a dev dependency group. Runtime dependencies should cover MCP serving, Pydantic models/settings, and the active search provider SDKs; test, lint, formatting, and pre-commit tools belong in the dev group so the container image and production install path remain focused.
