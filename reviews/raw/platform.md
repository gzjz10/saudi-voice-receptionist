# Plan review: platform and tech-stack accuracy

Reviewer lens: platform and tech-stack accuracy. Reviewed `plan.md` (Technical Spec v1.0) and `CLAUDE.md` on 2026-10-27.

**Verdict: ready_with_fixes.** The architecture holds up: a hosted ElevenLabs voice loop, a FastAPI backend that owns the truth, and a QA loop. Most named platform features exist today. But the plan is not perfect. Several platform claims are stale or too vague to act on:

- The CLI has changed a lot in the last month.
- `agents add` needs an API key.
- Simulation tests are text-only.
- The widget needs a public agent.
- The quick-tunnel URL changes every run.
- The Vapi fallback would break the eval tooling.
- There is no `make` on the Windows laptop.

Phase 0 can't pass its gate on this laptop, because there is no API key and the gate itself was never written (§11 didn't export).

## How this was verified

- **CLI:** I installed `@elevenlabs/cli@1.7.1` (the latest on npm, published 2026-10-22) into a scratch folder and read the real `--help` and `--schema` output. I ran `agents init`, `agents templates show minimal` and `agents push --dry-run`. Nothing was sent to ElevenLabs and no key was used. The one call that reached the API (`agents add --dry-run`) was rejected with a 401.
- **Docs:** fetched from elevenlabs.io on 2026-10-27. The docs moved from `/docs/agents-platform/...` to `/docs/eleven-agents/...`, and the old paths now return 404.
- **Package versions:** read from the PyPI JSON API and `npm view` on 2026-10-27.
- **UNVERIFIED** marks anything that needs an API key or a docs page I couldn't confirm.

## Findings

### 1. [blocker] §11 and §14: the Phase 0 gate is undefined, and the laptop can't execute it

- **Problem:** §11 (the phase table and gates) is the unexported "[embedded content]" placeholder, so Phase 0 has no written acceptance check. Separately, every Phase 0 action that produces evidence needs an ElevenLabs API key, and this laptop has none:
  - listing library voices
  - synthesizing the 3 candidates
  - creating the agent
  - running the 10 STT utterances
- **Evidence:** `elevenlabs agents add sara --template minimal --dry-run` called the API anyway and returned `401 unauthorized: Neither authorization header nor xi-api-key received` (CLI 1.7.1). `voices get_shared` (the library search) also needs `xi-api-key`.
- **Fix:** Write the Phase 0 gate into the spec now, as measurable checks. Split Phase 0 into two parts:
  - **0a, offline, can be done today:** the agent config file, the voice-selection procedure, the STT test sheet, the scoring sheet and the budget.
  - **0b, needs a key, run on the Mac:** synthesis, listening scores, the STT run, then go/no-go.
- **Suggested gate (proposal, owner to confirm):**
  - Each of the 3 voices × 2 TTS models renders the same fixed 8-line script.
  - Ahmed plus one more Saudi listener each score dialect naturalness from 1 to 5. Go if at least one voice/model pair averages ≥ 4.0.
  - Across the 10 utterances spoken into the real agent, the product name or intent comes out correct in ≥ 8 of 10.
  - Record the minutes spent.
  - Docs/STATUS.md must say "Phase 0 gate: OPEN, waiting for API key". It must never say "passed".

### 2. [major] §4 and §14: the CLI is described with too few commands, and it isn't pinned

- **Problem:** The plan lists only `agents init/add/push` and installs with `npm install -g` (global and unpinned).
- **Evidence:**
  - **Release churn:** CLI 1.7.1 is the current version, and it ships very often: 1.4.0 on 2026-09-25, 1.5.0 on 10-13, 1.6.0 on 10-16, 1.7.0 on 10-20 and 1.7.1 on 10-22 (`npm view @elevenlabs/cli time`).
  - **Binary:** the binary is `elevenlabs`.
  - **Real `--help` output:**
    - `agents init [PATH]`: has `--override` and `--yes`.
    - `agents add [NAME]`: takes `--template default|minimal|voice-only|text-only|customer-service|assistant` plus `--from-file` and `--output-path`. It creates the config, uploads it and saves the ID. There is no `--skip-upload`, even though the docs page still lists one.
    - `agents push`: takes `--agent`, `--branch` and `--version-description`. The global `--dry-run` also works here.
    - Other subcommands: `agents pull`, `agents status`, `agents test <AGENT>`, `tools add <NAME> --type webhook|client`, `tools push`, `tests add <NAME> --template basic-llm|tool|conversation-flow|customer-service`, `tests push`, `agents widget embed`, `agents llm list`, `agents conversations list|get`.
  - **Install options in the docs:** `brew install elevenlabs/tap/elevenlabs` (macOS), Scoop (Windows), or npm.
  - **Docs URL:** https://elevenlabs.io/docs/agents-platform/operate/cli. The content is current, but the path is the legacy one.
- **Fix:**
  - Pin the CLI as a project devDependency in `package.json` (`"@elevenlabs/cli": "1.7.1"`) and call it with `npx elevenlabs ...` on both machines. Don't install it globally, and don't use brew on the Mac only, or the two machines will drift.
  - Document `tools push` and `tests push` too. In the init output, the push order is "agents push && tools push && tests push".

### 3. [major] §5: the agent config layout isn't specified

- **Problem:** The plan's `agent/` folder is just "CLI-managed". The real layout is fixed by `agents init`.
- **Evidence:** `elevenlabs agents init <path>` creates `agents.json`, `tools.json`, `tests.json`, `agent_configs/`, `tool_configs/`, `test_configs/`, `.env.example` and `.gitignore` (observed). Agent configs are JSON in the shape `{conversation_config:{agent:{language,prompt:{llm,prompt,temperature}},conversation:{text_only},tts:{model_id,voice_id}},name,platform_settings,tags}` (from `agents templates show minimal`). A hand-written `agent_configs/sara.json` registered in `agents.json` as `{"config": "agent_configs/sara.json"}` passes `agents push --dry-run` offline and shows "Agent ID: Not created yet". Whether a real `push` then creates the agent is **UNVERIFIED**, because it needs a key.
- **Fix:**
  - Run `npx elevenlabs agents init agent` and commit the generated layout.
  - Keep the prompt in `prompts/system_v1.md` and build it into `agent_configs/*.json` with a small script, so there is one source of truth.
  - Tests are attached through `platform_settings.testing.attached_tests` (from the init output and the schema).
  - Phase 0a can deliver this config offline, validated with `push --dry-run`.

### 4. [major] §4 and §12: the TTS model is never named, and the choice for Saudi dialect is undocumented

- **Problem:** The plan names a TTS model only in the fallback (`eleven_multilingual_v2`). It never says which model the agent itself uses, or which ones Phase 0 compares.
- **Evidence:**
  - The agent schema's `conversation_config.tts.model_id` enum is `eleven_turbo_v2, eleven_turbo_v2_5, eleven_flash_v2, eleven_flash_v2_5, eleven_multilingual_v2, eleven_v3_conversational, eleven_v4, eleven_v4_turbo` (CLI 1.7.1 `--schema`).
  - The CLI's minimal template now defaults to `eleven_v4_turbo`.
  - Per https://elevenlabs.io/docs/overview/models: `eleven_v4_turbo` handles 90+ languages including Arabic at about 100 ms and is listed for Agents. `eleven_flash_v2_5` supports Arabic at about 75 ms. `eleven_multilingual_v2` supports Arabic but has higher latency. `eleven_turbo_v2_5` is deprecated (replaced by flash v2.5). `eleven_v3_conversational` (about 280 ms) is not in the Agents model-selection guide but is in the agent enum.
  - No official page says which model sounds most Saudi or Gulf. That is **UNVERIFIED** and must be decided by listening.
- **Fix:**
  - Phase 0 compares `eleven_v4_turbo` and `eleven_flash_v2_5`, and optionally `eleven_v3_conversational`, on each of the 3 voices.
  - Record the winner and its latency.
  - Drop `turbo_v2_5`.
  - Note that `expressive_mode` and `suggested_audio_tags` apply only to v3 models.

### 5. [major] §4 and §12: the STT/ASR settings and Arabic accuracy aren't specified

- **Problem:** The plan treats STT as a black box. The agent's ASR has settings that directly target the "STT mishears product names" risk.
- **Evidence:**
  - Schema fields: `conversation_config.asr.provider` ∈ {`elevenlabs`, `scribe_realtime`, `scribe_v2_turbo`}, `asr.keywords` ("Keywords to boost prediction probability for"), and `conversation_config.agent.language` ("used for ASR and TTS").
  - https://elevenlabs.io/docs/capabilities/speech-to-text puts Arabic in the "Good (>10% to ≤20% WER)" tier, with no mention of dialects.
  - Whether `ar` covers Saudi dialect well is **UNVERIFIED**. There is no `ar-SA` locale in the agent config, only 2-letter codes.
- **Fix:**
  - Phase 0 sets `agent.language = "ar"`, tests at least 2 ASR providers on the same 10 utterances, and adds catalog product names to `asr.keywords`.
  - The STT sheet must be spoken into the real agent (voice), not run as batch `scribe_v2` file transcription, because the realtime ASR is a different model.
  - Read the results back through the transcript API (finding 10).

### 6. [major] §8 rule 9 and scenario E10: switching to English needs a system tool the plan doesn't mention

- **Problem:** "Caller speaks English → answer in English" won't work on an `ar` agent unless English is added as a supported language and the `language_detection` system tool is enabled. Without them, ASR and TTS stay on Arabic.
- **Evidence:** https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/language-detection.md says switchable languages "must be defined in the Agent settings", and the `language_detection` tool switches "voice and responses". The schema has `conversation_config.language_presets` and the built-in system tool `language_detection`.
- **Fix:**
  - Add `en` as a language preset.
  - Enable `language_detection` with a description that tells it to switch only on English-only speech and to stay in Arabic for mixed Arabic–English (scenario E11).
  - The English preset may need its own voice (`tts.supported_voices`).

### 7. [major] §9: simulation tests are text-only, so voice scenarios can't be tested that way

- **Problem:** §9 says "use the platform's built-in simulation where they fit", but never says which scenarios can't be simulated. These three are audio phenomena:
  - E7, barge-in during the read-back
  - E8, long silence
  - E9, unclear speech
- **Evidence:**
  - https://elevenlabs.io/docs/eleven-agents/customization/agent-testing.md lists three test types: Simulation (multi-turn, simulated user, success condition, max turns 1–50), Next Reply and Tool Call. Runs go through `elevenlabs agents test <agent>` or `POST /v1/convai/agents/{agent_id}/run-tests`, and `repeat_count` (2–20) gives pass rates. The page describes a generated text transcript.
  - The `simulate-conversation` endpoints are marked `[DEPRECATED]` in CLI 1.7.1 `agents --help`.
  - Whether tests consume call minutes or LLM credits is **UNVERIFIED**.
- **Fix:**
  - Tag each scenario `mode: sim | voice`. E7, E8 and E9, plus dialect naturalness, are `voice` only and go to the 10 real call cards.
  - Use platform Simulation tests with `repeat_count` instead of the deprecated simulate API.
  - E8 depends on `turn.turn_timeout` and `turn.silence_end_call_timeout`. Put those values in the agent config and the spec.
  - Use Tool Call tests for the "correct tool and arguments" metric.

### 8. [major] §4, §10 and D1: the widget needs a public, unauthenticated agent, which exposes cost

- **Problem:** The plan says "static demo/index.html, zero build step". It doesn't address three things:
  - **Public agent:** the widget only works on a public agent with authentication turned off.
  - **Public agent ID:** the repo is public, so the agent ID ends up in `agents.json` and `index.html`, where anyone can find it.
  - **Hosting:** `file://` has no origin. The plan never says where the page is hosted.
- **Evidence:**
  - https://elevenlabs.io/docs/eleven-agents/customization/widget.md says, "Widgets currently require public agents with authentication disabled". It also covers the Allowlist.
  - The snippet is `<elevenlabs-convai agent-id="..."></elevenlabs-convai>` with `<script src="https://unpkg.com/@elevenlabs/convai-widget-embed" async>`, which is unversioned.
  - The schema has `platform_settings.auth.allowlist`, `auth.require_origin_header`, `call_limits.daily_limit`, `call_limits.agent_concurrency_limit` and `conversation.max_duration_seconds`.
  - The widget package is at 0.21.5 (2026-10-26), with about 10 releases in October.
- **Fix:**
  - Host the page on GitHub Pages.
  - Set the allowlist to that host plus localhost, with `require_origin_header: true`, a low `daily_limit`, `max_duration_seconds` of about 180, and concurrency of 2.
  - Pin the script, e.g. `@elevenlabs/convai-widget-embed@0.19.1`, or whatever is at least two weeks old when it's built.
  - For local tests, serve with `python -m http.server`. Don't open the file directly.

### 9. [major] §4, §10 and §14: the cloudflared quick-tunnel URL changes on every run

- **Problem:** The plan treats the tunnel as a stable public URL. A quick tunnel gets a new `*.trycloudflare.com` hostname on every start, but the webhook tool URLs are baked into `tool_configs/*.json` on ElevenLabs. Every dev session would need its tools edited and re-pushed, and every committed URL is stale.
- **Evidence:** https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/:
  - The command is `cloudflared tunnel --url http://localhost:8080`.
  - "Quick Tunnels have no uptime guarantee".
  - There is a 200 in-flight request limit, and there's no SSE.
  - The URL stops working when the process stops.
  - Locally installed: `cloudflared version 2026.10.0`.
- **Fix:**
  - Choose one approach:
    - Script it: `make tunnel` captures the URL and rewrites `tool_configs/*.json` from a template with `TOOLS_BASE_URL`, then runs `tools push`.
    - Use a named tunnel. This needs a Cloudflare account and domain, so it's the owner's call.
  - The CLI has an `environment-variables` command ("workspace environment variables available to agents and tools"). Whether it can template tool URLs is **UNVERIFIED**. Check it before building the script.
  - On Windows, install with `winget install Cloudflare.cloudflared`, not brew.

### 10. [minor] §7 and §10: the webhook tool auth and conversation-ID wiring are vague but feasible

- **Problem:** `X-Tool-Secret` and `conversation_id?` are fine ideas. The plan doesn't say how ElevenLabs sends either one.
- **Evidence:**
  - In the tool schema (`agents tools create --schema`), `api_schema.request_headers` values can be a string, `{secret_id}` ("reference a secret from the agent's secret store") or `{variable_name}` (a dynamic variable).
  - Other fields that exist: `request_body_schema`, `response_timeout_secs`, `force_pre_tool_speech`, `pre_tool_speech`, `tool_call_sound`, `disable_interruptions`, `execution_mode`.
  - https://elevenlabs.io/docs/eleven-agents/customization/tools/server-tools.md says to store keys as a header of type Secret.
  - The system dynamic variables include `system__conversation_id` and `system__time` (https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables.md).
- **Fix:**
  - Store `TOOL_SECRET` as a workspace secret and reference it with `{secret_id}` in `request_headers`. Never write the literal value into `tool_configs`, which is public.
  - Bind `conversation_id` to `system__conversation_id`. Don't let the LLM fill it.
  - Consider `force_pre_tool_speech` or `tool_call_sound` instead of relying only on the prompted "لحظة أشيك لك".

### 11. [major] §4 fallback: "the eval suite stays unchanged" on Vapi is false

- **Problem:** `run_sims.py` uses ElevenLabs simulation tests, and `fetch_transcripts.py` uses `/v1/convai/conversations`. Neither exists on Vapi, and the tool-call payload format differs too. Also, `eleven_multilingual_v2` is the slowest Arabic-capable ElevenLabs model, which is a poor choice for a phone-latency fallback.
- **Evidence:**
  - Vapi's Azure transcriber lists `ar-SA` (https://docs.vapi.ai/providers/transcriber/azure).
  - Azure STT lists `ar-SA`, and Azure TTS has `ar-SA-HamedNeural` and `ar-SA-ZariyahNeural` (https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=stt).
  - So the fallback is still plausible.
  - Which ElevenLabs model IDs Vapi accepts today is **UNVERIFIED**.
  - The plan's only source is a Vapi community thread.
- **Fix:**
  - Reword the fallback: the backend and `scenarios.yaml`/rubric stay the same, but the runtime adapter, transcript fetcher and simulator get a Vapi variant, at an estimated +3–4 h.
  - Use `eleven_flash_v2_5` (or v4_turbo, if Vapi supports it) as the fallback TTS.
  - Keep Azure `ar-SA` voices as a second TTS fallback.

### 12. [major] §10: pricing — the 60-minute budget doesn't fit the Free plan

- **Problem:** The plan says to "check pricing", then budgets 60 call-minutes without naming a plan.
- **Evidence:** https://elevenlabs.io/pricing/agents (fetched 2026-10-27):
  - Free: 15 call-min/month.
  - Starter: $6/mo with 75 min. The page shows a $1 first-month promo.
  - Creator: $22/mo with 275 min.
  - Extra minutes cost $0.080/min on all plans, or $0.160 with burst.
  - Text messages cost $0.003 each.
  - LLM tokens are billed separately from the minutes.
  - Telephony is billed by Twilio.
  - Whether Free-tier keys can use shared library voices, and whether some library voices carry custom rates (`voices get_shared --include-custom-rates` exists), is **UNVERIFIED**.
- **Fix:**
  - State the decision: Starter (75 min) covers the 60-minute budget, or Free covers only the 10-minute Phase 0 spike.
  - Set `call_limits.daily_limit`.
  - Log `metadata.cost_fiat` and `call_duration_secs` from each conversation (finding 13) into the README usage table.
  - Exclude custom-rate voices from the 3 candidates.

### 13. [minor] §9: the transcript API is fine, but the plan never names the endpoint or fields

- **Problem:** `fetch_transcripts.py` is described only as "through the ElevenLabs API".
- **Evidence:**
  - `GET /v1/convai/conversations/{conversation_id}` returns `transcript[]` (`role`, `message`, `time_in_call_secs`, `tool_calls[]` with `tool_name` and `params_as_json`, `tool_results`) plus `metadata.call_duration_secs`, `metadata.cost_fiat` and `analysis` (https://elevenlabs.io/docs/api-reference/conversations/get).
  - The list call `GET /v1/convai/conversations` filters by `agent_id`, `call_start_after_unix`, `tool_names_errored` and more (CLI `agents conversations list --help`).
  - The Python SDK `elevenlabs` is at 2.74.1 (PyPI, 2026-10-20).
- **Fix:**
  - Name these endpoints in the spec, and pin the SDK, or use plain `httpx` with an `xi-api-key` header.
  - Because the transcript already includes tool calls and results, the backend's JSON log becomes a cross-check rather than the only tool record.
  - Consider the platform's `platform_settings.evaluation.criteria` as a free first-pass judge.

### 14. [minor] §4: the LLM choice is right but loose, and Realtime mode isn't mentioned

- **Evidence:**
  - Per https://elevenlabs.io/docs/eleven-agents/customization/llm.md, the agent LLM list includes Claude Haiku 4.5, the Gemini 3.x Flash and Flash-Lite variants, Gemini 2.5 Flash, GPT-5.4 Mini and Nano, ElevenLabs-hosted models, and a custom LLM option. LLM use is billed per token.
  - The CLI's minimal template defaults to `gemini-2.5-flash`. `npx elevenlabs agents llm list` returns the exact IDs.
  - A new "Realtime" voice mode (`eleven_realtime_v1_mini` / `eleven_realtime_v1_max`) replaces the separate LLM, TTS and ASR choices (https://elevenlabs.io/docs/eleven-agents/customization/realtime-models.md). Its Arabic support is **UNVERIFIED**.
- **Fix:**
  - Stay in Custom mode, because you need control of the TTS voice for the dialect test.
  - Shortlist 2 IDs from `agents llm list` (one Gemini Flash, one Claude Haiku 4.5) and pick by measured latency and Arabic quality in Phase 2.
  - Record the pick in the README.

### 15. [minor] §10: guardrails, data retention and number normalization are platform settings, not "where supported"

- **Evidence:** The schema has:
  - `platform_settings.guardrails.prompt_injection`, plus `content`, `focus` and `custom`
  - `platform_settings.privacy.record_voice`, `retention_days`, `delete_audio` and `zero_retention_mode`
  - `tts.text_normalisation_type` ∈ {`system_prompt`, `elevenlabs`}
  - `tts.pronunciation_dictionary_locators`
- **Fix:**
  - Turn on the `prompt_injection` guardrail in v1, so E13 measures prompt plus guardrail. Or turn it on in v2 as a CHANGELOG item.
  - Set a short `retention_days` for the family test calls.
  - Choose `text_normalisation_type` deliberately so it doesn't fight `spoken.py`. The `_spoken_ar` fields already handle numbers in the prompt, so `system_prompt` is the consistent choice. Verify by listening.

### 16. [major] §5 and §14: the Makefile and setup commands aren't cross-platform

- **Problem:** The owner starts on Windows, but the plan assumes macOS:
  - `make` isn't installed on this laptop (`make: command not found` in Git Bash).
  - `source .venv/bin/activate` is `.venv/Scripts/activate` on Windows.
  - `brew install cloudflared` doesn't apply on Windows.
  - `python3` on this laptop resolves to the WindowsApps stub. The real interpreter is Python 3.12.10 via `py`/`python`.
- **Fix:**
  - Either put all tasks in a cross-platform `scripts/` folder (bash scripts that run in Git Bash and on macOS, plus Python entry points), with an optional Makefile wrapper for the Mac, or document installing make with `winget install ezwinports.make`.
  - Add a `.python-version` file set to `3.12`, so Python matches on both machines.
  - Commit `requirements.txt` with exact pins.

### 17. [minor] §4: pin the Python packages, and reconsider LiteLLM

- **Evidence:** Latest on PyPI (2026-10-27):

  | Package | Version | Requires Python |
  | --- | --- | --- |
  | fastapi | 0.162.0 (10-23) | — |
  | pydantic | 2.14.1 | — |
  | rapidfuzz | 3.14.6 | ≥ 3.11, which matches the plan's "3.11+" |
  | uvicorn | 0.54.0 | — |
  | pytest | 9.1.1 | — |
  | litellm | 1.106.4 | — |

  LiteLLM had a PyPI supply-chain compromise on 2026-03-24 (malicious 1.82.7 and 1.82.8, with a `.pth` payload that runs whenever Python starts). See https://www.netspi.com/blog/executive-blog/ai-ml-pentesting/litellm-supply-chain-compromise/ and https://www.comet.com/site/blog/litellm-supply-chain-attack/. It's also a heavy dependency for a judge that calls one provider.
- **Fix:**
  - Pin exact versions, preferring releases at least 2 weeks old: fastapi 0.161.x if fastapi 0.162.0 is too fresh, pydantic 2.14.1, rapidfuzz 3.14.6, uvicorn 0.54.0, pytest 9.1.1.
  - Either call the judge provider's own SDK directly, or pin LiteLLM exactly and install with `--require-hashes`.
  - FastAPI, Pydantic v2, SQLite and rapidfuzz `token_set_ratio` are all sound choices.

### 18. [minor] §4: system tools — `transfer_to_number` doesn't work in the widget

- **Evidence:** "The `transfer_to_number` system tool is only available for phone calls and is not available in the chat widget". It needs Twilio or SIP (https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-human.md). The system tools present in the schema: `end_call`, `transfer_to_number`, `transfer_to_agent`, `language_detection`, `skip_turn`, `voicemail_detection` and `play_keypad_touch_tone`.
- **Fix:** Take "transfer tools" out of the "Why" column. Escalation stays as the `escalate_to_human` ticket webhook, which the plan already does. Enable `end_call` for E8 and the call close.

### 19. [minor] §4 and Sources: replace the third-party source and fix the naming

- **Problem:** The only platform source is mcpservers.org (third party). Also, the product docs now live under "ElevenAgents" (`/docs/eleven-agents/`), and the old `/docs/agents-platform/...` model pages return 404.
- **Fix:** Cite the official URLs used in this review. Point the README setup at the docs index https://elevenlabs.io/docs/llms.txt.

### 20. [minor] §2 and Phase 0: voice-library filtering isn't confirmed for "Saudi"

- **Evidence:**
  - `voices get_shared` takes `--language`, `--accent`, `--locale`, `--gender`, `--age`, `--use-cases`, `--search` and `--include-custom-rates` (CLI 1.7.1).
  - The valid accent values come from `voices accents get`, which needs a key. Whether "saudi" or "khaleeji" is an accepted value is **UNVERIFIED**.
  - Third-party catalogs list ElevenLabs Arabic voices tagged Saudi (e.g. https://www.famulor.io/voices/elevenlabs/languages/ar/accents/saudi). Those are not official labels.
  - Whether library voices must be added to "My Voices" before an agent can use them is **UNVERIFIED**.
- **Fix:**
  - Write the Phase 0 voice-selection procedure as follows:
    1. Run `voices accents get` and pick the Arabic accents.
    2. Run `voices get_shared --language ar --accent <value> --use-cases conversational`. Exclude custom-rate voices.
    3. Shortlist 5, listen, and keep 3.
  - Record the voice IDs only after a real API call returns them. Never copy them from third-party sites.

## What the plan gets right

- The core architecture: a hosted voice loop plus our own truth backend.
- Webhook tools carrying an auth header.
- The `end_call` system tool.
- The simulation tests, conversation transcript API and `<elevenlabs-convai>` widget all exist.
- The CLI package name `@elevenlabs/cli` and `agents init/add/push` are correct.
- An Azure `ar-SA` fallback via Vapi is real.
- The Python stack choices are sound.
