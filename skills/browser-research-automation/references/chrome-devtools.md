# Chrome DevTools MCP / CLI reference

Use this reference only when the task specifically depends on Chrome DevTools MCP/CLI or local browser debugging.

## Upstream

Official project: `ChromeDevTools/chrome-devtools-mcp` by the Google Chrome team.

Capabilities documented upstream include live Chrome automation, DOM/page inspection, console messages, network requests, screenshots, performance traces, and a terminal CLI. The MCP server uses browser automation under the hood and can start Chrome when a browser-requiring tool is first used.

## Installation assumptions

Do not install automatically unless the user has authorized installation in the current local environment.

Typical prerequisites are Node.js, npm, and a supported Google Chrome/Chrome for Testing installation. Prefer the upstream installation/configuration instructions because versions and flags can change.

For Codex/terminal work, first check whether an MCP connection or the `chrome-devtools` CLI already exists. Do not reinstall a working setup merely to standardize it.

## Basic MCP/CLI pattern

When available:

1. list pages/tabs;
2. target the correct page ID;
3. take a DOM/accessibility snapshot;
4. use stable element identifiers to click/fill;
5. inspect console/network around the failing action;
6. verify the final state.

Avoid coordinate clicking when a DOM-targeted action is available.

## Localhost

Chrome DevTools running on the user's machine can inspect `localhost` applications on that same machine. A cloud browser normally cannot reach the user's machine-local `localhost` unless a separate bridge/tunnel exists.

For this user's workflow, record the host machine as `CODEX_LAPTOP` or `CODEX_KIOM` when verified.

## Browser profiles and isolation

A persistent profile can retain browser state. Use isolated/temporary profiles for experiments when session separation matters. Do not assume the user's ordinary Chrome profile is the same profile used by Chrome DevTools MCP.

## Remote debugging

Connecting to an already-running Chrome instance may require a remote debugging endpoint. Treat this as a security-sensitive control channel. Do not expose it beyond the local machine unless the user deliberately configured a secure setup.

## Privacy

Chrome DevTools MCP can expose page content and browser state to its MCP client. Avoid unrelated sensitive tabs and redact secrets from logs. Browser automation should never be used as a reason to capture credentials or private data that are unnecessary for the requested task.

## Tool availability fallback

If Chrome DevTools MCP/CLI is unavailable:

- use another authorized browser/computer-use tool for interactive workflows;
- use public web search for public information retrieval;
- for localhost-only debugging, hand off to a local Codex/desktop environment rather than pretending cloud browsing can reach it.
