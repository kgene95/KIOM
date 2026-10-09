---
name: browser-research-automation
description: Inspect, debug, validate, and automate browser-based research and local web-app workflows. Use when ChatGPT needs to work with Chrome/Chrome DevTools MCP or CLI, inspect DOM/console/network/performance, test localhost or Streamlit apps, validate downloads/uploads and web forms, reproduce browser UI failures, or verify that a browser workflow completed correctly. Prefer direct browser inspection over screenshots when tooling is available, preserve privacy, and distinguish cloud-browser limits from local Codex/desktop access.
---

# Browser Research Automation

Use this skill as a thin orchestration layer for browser inspection and validation. Prefer the browser tool already available in the current environment; do not require Chrome DevTools MCP when another browser tool can satisfy the task reliably.

## Tool routing

1. If Chrome DevTools MCP is connected, use it for live Chrome inspection, console/network debugging, DOM-targeted automation, and performance analysis.
2. If the Chrome DevTools CLI is installed in a local Codex/terminal environment, use the CLI for repeatable local browser workflows and scriptable checks.
3. If neither is available but an authorized browser/computer-use tool exists, use that tool for UI workflows.
4. Use ordinary web search for public information retrieval when browser state, login, DOM, console, or localhost access is unnecessary.
5. Never claim access to localhost, a logged-in browser profile, DevTools, or local files unless the current environment actually exposes them.

Read `references/chrome-devtools.md` when Chrome DevTools MCP/CLI setup, privacy, localhost, or debugging details matter.

## Core workflow

### 1. Define the browser target

Identify:

- public URL, authenticated site, or localhost URL;
- expected page or workflow state;
- whether the task is read-only inspection or an authorized action;
- whether files will be uploaded/downloaded;
- whether console, network, DOM, or performance evidence is needed.

Do not ask for information already visible in the current browser context.

### 2. Inspect before acting

For debugging or UI validation:

- enumerate available pages/tabs when the tool supports it;
- select the exact target page;
- inspect the DOM/accessibility snapshot before coordinate-based clicking;
- capture console errors and failed network requests before changing state;
- preserve the original failure evidence when practical.

Prefer stable element identifiers/selectors over screen coordinates.

### 3. Reproduce narrowly

Reproduce the smallest failing workflow first. Examples:

- upload ZIP -> disease field not populated;
- click GO/KEGG plot -> no figure generated;
- login -> redirect loop;
- local Streamlit action -> exception in console/network;
- download button -> no file or wrong filename.

Avoid broad exploratory clicking when one deterministic path can test the hypothesis.

### 4. Diagnose with evidence

Separate observations from interpretations.

Useful evidence includes:

- visible UI state;
- DOM value/attribute/state;
- browser console messages;
- network status codes and response payload metadata;
- request/response timing;
- screenshot only when visual layout matters;
- downloaded file existence/name/size when available.

Do not infer a backend failure from a missing UI element without checking network/console evidence when those tools are available.

### 5. Act conservatively

For state-changing browser actions:

- follow the user's explicit authorization;
- avoid changing account/security settings unless requested;
- do not submit forms, delete data, publish content, or send messages merely to test a UI unless the user authorized that action;
- prefer test/local environments over production when both are available;
- after a write action, verify the resulting state rather than assuming success.

### 6. Validate the result

A browser task is complete only when the expected state is verified. Depending on the task, verify one or more of:

- target element state changed correctly;
- console has no new relevant error;
- expected network request succeeded;
- downloaded artifact exists and is plausible;
- localhost app remains responsive after the action;
- page reload preserves state when persistence is part of the requirement.

## Localhost and local-app rules

For `localhost`, Streamlit, Dash, Flask, local React/Vite, Cytoscape web UI, or similar apps:

- use a local Codex/desktop environment that can reach the user's machine;
- do not assume ChatGPT web/mobile cloud browsing can reach the user's `localhost`;
- if a terminal-launched server is required, record the launch command and port in the project checkpoint when the work is research-project relevant;
- keep long-running local servers separate from one-off test commands;
- when switching between `CODEX_LAPTOP` and `CODEX_KIOM`, record which machine hosted the app.

## Research workflow integration

Use browser automation to support, not replace, the scientific workflow.

Good uses include:

- validating NP web-app parsing and figure-generation behavior;
- checking public database pages when an API/export is unavailable;
- reproducing login/download workflows;
- inspecting Cytoscape/ChimeraX-adjacent browser interfaces;
- verifying manuscript submission forms without submitting unless authorized.

When browser work changes project state, hand the resulting facts, files, and unresolved issues to `research-project-memory`. Do not create a parallel project-memory system inside this skill.

## Privacy and security

- Treat a connected browser as potentially containing sensitive tabs, cookies, forms, and account data.
- Inspect only pages needed for the current task.
- Never expose passwords, session cookies, access tokens, API keys, or authorization headers in user-visible output or project memory.
- Do not record full sensitive request/response bodies when a status code, endpoint, or redacted excerpt is sufficient.
- Use isolated browser profiles for risky or experimental automation when supported.
- Remote debugging exposes browser control to clients that can reach the debugging endpoint; use it only when needed and close it after use.

## Evidence reporting

Report browser-debugging results compactly:

- **Target:** page/workflow tested
- **Observed:** reproducible behavior
- **Evidence:** console/network/DOM/file evidence
- **Cause:** confirmed or most likely cause, clearly labeled
- **Fix/next action:** minimum effective change
- **Validation:** what was retested
- **Gap:** anything not accessible or not verified

Do not present a hypothesis as a confirmed root cause.
