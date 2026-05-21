# Rely on Infrastructure Access Control

Dewey MCP relies on deployment infrastructure for client access control in the first version instead of enforcing MCP client authentication inside the FastMCP app. The service should be deployed behind appropriate private networking, gateway, platform auth, or equivalent controls; app-level authentication can be added later if the deployment model requires it.
