# UST OneDrive MCP Setup State

Updated: 2026-10-06

## Objective
Build a cloud-hosted MCP bridge so ChatGPT can access the UST OneDrive/SharePoint research workspace from web/mobile/company environments without requiring the user's PC to remain on.

## Canonical target workspace
- UST OneDrive/SharePoint workspace root: `LG_노트북/`
- Do not use the personal OneDrive account for this workflow.

## Cloud / repository
- MCP source repository: `kgene95/ust-onedrive-mcp`
- Hosting: Railway
- Railway public domain: `https://ust-onedrive-mcp-production.up.railway.app`

## Microsoft Entra setup
- App name: `UST Research MCP`
- Account type: UST single-tenant
- Microsoft Graph delegated permission: `Files.ReadWrite`
- Admin consent required: No
- Redirect URI:
  `https://ust-onedrive-mcp-production.up.railway.app/auth/callback`
- Client secret created and stored only in Railway environment variables.
- Never write secret values, access tokens, authorization codes, or passwords into GitHub/project memory.

## Railway environment variables
Configured variable names:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_REDIRECT_URI`
- `AZURE_CLIENT_SECRET`

Values are intentionally not recorded here.

## Validation completed
1. Microsoft Graph sign-in succeeded.
2. UST OneDrive root read succeeded.
3. `LG_노트북` folder was found.
4. Write test succeeded inside `LG_노트북`.
5. Temporary `MCP_TEST_<timestamp>` folder was created and then deleted successfully.
6. OAuth and Graph callback reported:
   - `oauth: success`
   - `graph: success`
   - `target: LG_노트북`
   - `write_test: success`
   - `cleanup: success`

## Architecture decision
Use a hybrid workflow:
- Personal/home PCs: normal OneDrive sync for full project folders and large files.
- Company / restricted environments: ChatGPT -> cloud MCP -> UST OneDrive.
- Railway should not be treated as the primary bulk-sync engine when direct OneDrive sync/web upload is available.

## Current implementation state
The Railway service currently contains an Express-based Microsoft Graph/OAuth test server. The Microsoft Graph connection is validated, but the service is not yet a complete production MCP protocol server.

## Next actions
1. Replace/extend the test Express server with an actual remote MCP server implementation.
2. Restrict MCP tools logically to `LG_노트북/`.
3. Implement file/folder tools needed for real work:
   - list/search
   - read/download
   - upload/create
   - update
   - move/rename
   - delete only with appropriate safeguards
4. Implement durable OAuth token handling/re-authentication.
5. Redeploy to Railway.
6. Connect the resulting remote MCP endpoint to ChatGPT.
7. Test from ChatGPT with a simple command such as listing `LG_노트북`.
8. Later review Railway usage/cost and migrate to another host if needed.

## DO NOT REPEAT
- Do not redo Graph Explorer read/write feasibility testing.
- Do not recreate the Entra app unless the current app is invalidated.
- Do not recreate Railway hosting unless migration is intentionally chosen.
- Do not store secrets in GitHub.
