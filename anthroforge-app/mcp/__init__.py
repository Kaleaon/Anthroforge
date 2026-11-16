"""AnthroForge MCP server package (stub).

Per APP_BLUEPRINT §4, the MCP server contains no logic of its own: it
is a thin client of the Core Service API, exactly like the GUI. This
package currently ships only the tool-surface catalogue
(:mod:`mcp.server`); the stdio transport and handlers land in Phase 1
(blueprint §15) once the Core Service methods they wrap exist.
"""
