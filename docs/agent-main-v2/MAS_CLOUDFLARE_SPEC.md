# ASTRA — Connect Existing Backend MAS to Cloudflare

## Objective

Connect the existing ASTRA exam-generation Backend to the newly created Cloudflare MAS Worker and Gateway.

The Backend has already been designed by the team to generate, solve, review and validate examinations using a configured AI provider.

The owner confirms that exam generation previously worked when an API key was configured directly in the local .env file. That old local configuration is no longer available.

Do not reconstruct the old application or redesign the academic pipeline.

The objective is simply to provide the current Backend with working AI inference through Cloudflare instead of distributing an API key locally.

## 1. Inspect the existing Backend integration point

Continue from the actual current Agent V2 feature branch and worktree.

Read AGENTS.md, PROGRESS.md, NEXT_TASK.md and the existing Backend provider implementation.

Identify:

- Where the Backend currently receives its API configuration.
- The existing provider abstraction.
- The expected API protocol.
- Model configuration.
- Request and response formats.
- Structured-output parameters.
- Token limits and timeouts.
- How real generation is enabled instead of demo mode.

Use the current Backend source as the authoritative implementation.

Do not spend time attempting to recover the deleted local configuration.

If the model ID is not available in the current configuration, ask the owner only for that non-secret value.

## 2. Connect the existing Cloudflare infrastructure

The owner has already created:

- MAS Worker: astra-mas-proxy.
- MAS Gateway: astra-mas-gateway.
- Provider: Google AI Studio Gemini.
- Independent Gemini BYOK credential.

Expected Worker variables:

- ASTRA_MAS_GATEWAY_TOKEN
- ASTRA_MAS_GATEWAY_ACCOUNT_ID
- ASTRA_MAS_GATEWAY_ID
- ASTRA_MAS_GATEWAY_BYOK_ALIAS
- ASTRA_MAS_FORWARDING_ENABLED

Discover the actual Worker URL and verify the configured bindings without exposing credentials.

Do not create additional Workers or Gateways.

## 3. Implement the simplest compatible transport

The required inference path is:

Existing Backend MAS
→ astra-mas-proxy
→ astra-mas-gateway
→ Gemini
→ Existing Backend response parser.

Determine whether the current Backend uses Gemini native API or OpenAI-compatible Chat Completions.

Verify the appropriate Cloudflare endpoint and authentication mechanism against official documentation.

Prefer preserving the existing request and response protocol instead of introducing unnecessary schema conversions.

The Worker should:

- Forward supported academic inference requests to the configured provider.
- Attach Gateway authentication internally.
- Preserve the expected provider response format.
- Enforce fixed upstream destinations, model restrictions, bounded requests, persistent quotas and concurrency limits.
- Provide a forwarding kill switch and sanitized error reporting.
- Avoid duplicate retries or response caching.

Reuse existing Worker utilities where useful.

Do not build another academic orchestration or semantic interpretation system inside the Worker.

## 4. Preserve the Backend exactly where possible

Do not modify:

- Academic prompts.
- THPT and V-ACT formats.
- Existing generation schemas.
- Composer.
- Illustrator.
- Solver.
- Reviewer.
- RAG.
- Academic validation.
- Scoring.
- Existing generation and revision workflows.

Reuse the current provider interface and response parser.

The Backend already knows how to generate examinations. It only needs a functioning AI connection.

Do not apply Agent Chat schemas, token limits or deadlines to MAS.

Make the smallest changes necessary to enable the Worker-backed provider.

## 5. Preserve Agent Chat

Keep the existing Chat infrastructure unchanged:

- astra-ai-proxy.
- astra-gateway.
- Existing Chat provider and semantic workflow engine.

Chat and MAS must use their independent credentials and resource policies.

Teachers must remain able to chat while MAS generates an examination.

## 6. Security

Never expose Gemini API keys or Gateway Tokens in source code, frontend bundles, logs or distributed configuration.

Reuse the existing quota protection approach.

Do not expose an unrestricted anonymous academic completion proxy.

If caller authorization is required, use the simplest appropriate revocable mechanism for internal testing without Gmail login.

Keep forwarding disabled until the access policy and inference budget are approved.

Do not overengineer a new account or authentication system for this integration.

## 7. Deployment and actual acceptance

Complete the code and deploy it to the existing astra-mas-proxy Worker with forwarding disabled.

Preserve its configured Secrets and environment variables.

Perform focused checks of request compatibility, response parsing, access control and quota protection.

Do not repeat the full Backend academic test suite or conduct unnecessary standalone model experiments.

Start the actual ASTRA application.

Prepare real MAS generation using the new Worker connection.

Estimate and bound the inference calls required for one exam.

After owner approval, allow the owner to initiate one real exam-generation job through the existing UI.

Verify that:

- The Backend calls the new MAS Worker.
- Gemini returns actual academic responses.
- The existing Backend processes those responses normally.
- The generated exam is not demo data.
- Existing academic validation remains active.
- Chat continues working independently.

If a failure occurs, fix the actual transport or integration defect rather than rewriting academic logic.

Update PROGRESS.md and NEXT_TASK.md.

Provide the exact remaining configuration or activation steps.

Do not push, merge or deploy the ASTRA website.

## Final directive

Keep this task simple.

The Backend already contains the examination-generation intelligence and academic rules.

Do not rebuild what already exists.

Connect the AI provider through the new Cloudflare Worker, preserve the expected API behavior, and make real examination generation available through the existing application.