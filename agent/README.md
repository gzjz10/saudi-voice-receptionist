# agent/ — ElevenLabs agent config as code (Phase 0)

This folder is the `agents init` layout of the ElevenLabs CLI. It holds two minimal Arabic agents with no tools. Phase 0a (Windows, offline) only validates them. Phase 0b (Mac, with an API key) pushes them. See `reviews/plan-review.md` sections E–G.

| File | Purpose |
| --- | --- |
| `package.json`, `package-lock.json` | Pin `@elevenlabs/cli` **1.7.1** (devDependency). The lockfile includes the platform binaries for `darwin-arm64`, `darwin-x64`, `linux-*` and `win32-x64`. |
| `agents.json`, `tools.json`, `tests.json` | CLI registries. `tools` and `tests` are empty in Phase 0. |
| `agent_configs/sara.json` | Sara, the minimal persona agent. Its prompt is a verbatim copy of `prompts/system_v0.md`. |
| `agent_configs/sara_stt_probe.json` | STT gate probe. Same language, ASR and TTS settings; it answers only «تمام» (plan-review G.3). |
| `validate_configs.py` | Offline checker (stdlib only). Reads enums and ranges from the CLI's embedded OpenAPI spec. |
| `tool_configs/`, `test_configs/` | Empty until Phase 2. Git does not track empty folders; `agents init` recreates them. |

## Version and how it was checked (2026-10-27)

- `npm view @elevenlabs/cli version`: `1.7.1`, the `latest` tag (published 2026-10-22).
- `npx -y @elevenlabs/cli@1.7.1 --version` printed `elevenlabs 1.7.1`. The CLI is a native binary that ships as npm optional dependencies.
- The following were all run and read: `--help`, `agents --help`, `agents init --help`, `agents push --help`, `agents templates show minimal`, `auth --help`, `auth login --help`, `voices get_shared --help`, `agents conversations get --help`, `agents create --schema` and `agents create --spec`.
- `agents init .` created `agents.json`, `tools.json`, `tests.json`, `agent_configs/`, `tool_configs/`, `test_configs/`, `.gitignore` and `.env.example`.
  - The `agent/.env.example` it made was deleted. The repo-root `.env.example` is the only template.
  - The CLI walks up parent folders to find `.env`. This was checked with `voices accents get --dry-run`: a `.env` two levels up made the CLI attach the `xi-api-key` header. The repo-root `.env` therefore works from `agent/`.
- The configs are hand-written in the documented shape (`agents templates show minimal`), not generated with `agents add`. `agents add` uploads at once and has no `--skip-upload` option.

> **Warning.** Run `npm ci` in `agent/` before any `npx elevenlabs ...` command. Without the local install, `npx elevenlabs` downloads a different npm package called `elevenlabs` (1.59.0, an old JS SDK). That package is not this CLI.

## Settings and why

| Field | Value | Reason / source |
| --- | --- | --- |
| `agent.language` | `ar` | The language docs use short codes such as `en`/`fr` (https://elevenlabs.io/docs/eleven-agents/customization/voice/customization/language.md). The spec types it as a free string, so whether the server accepts `ar` is **UNVERIFIED until the first real push**. |
| `agent.prompt.llm` | `gemini-2.5-flash` | This is the schema default and the `minimal` template's choice. The LLM docs name no "fast tier" (https://elevenlabs.io/docs/eleven-agents/customization/llm), only "choose a low-latency model". Phase 2 compares it with `claude-haiku-4-5`, which is also in the spec's `LLM` enum, by measured latency. |
| `agent.prompt.temperature` | `0.0` | Schema default and template value. |
| `tts.model_id` | `eleven_v4_turbo` | The models page (https://elevenlabs.io/docs/overview/models) says Arabic is supported with "~100ms" latency and recommends it for Agents. It is also the schema default. Phase 0b compares it with `eleven_flash_v2_5` (Arabic, ~75 ms). The winner replaces it. |
| `tts.voice_id` | *absent* | Phase 0a writes no voice IDs. If the agent is pushed before the 0b winner is set, the platform default voice is used. That voice is not Arabic-specific. |
| `tts.stability` / `similarity_boost` / `speed` | 0.5 / 0.8 / 1.0 | These are the spec defaults (ranges 0–1, 0–1, 0.7–1.2). `phase0/tts_samples.py` reads these exact values, so the rated clips match the agent. The agent TTS config has no `style` field, so the samples use `style` 0. |
| `tts.text_normalisation_type` | `system_prompt` | This is the spec default. It keeps platform normalization from fighting the `*_spoken_ar` fields. |
| `asr.provider` / `quality` | `scribe_realtime` / `high` | These are the spec defaults, written out so `decision.md` can record them. The STT gate reruns once with `elevenlabs` or `scribe_v2_turbo`. |
| `conversation.max_duration_seconds` | 240 | Amendment 8. |
| `platform_settings.privacy.retention_days` | 30 | Amendment 8 / B5. |
| `platform_settings.call_limits` | `daily_limit` 20, `agent_concurrency_limit` 2 | Amendment 8. |

## Validate offline (any OS, no key)

```bash
cd agent && npm ci && cd ..
python agent/validate_configs.py          # exit 0 = OK (use python3 on the Mac if python is not 3.12)
(cd agent && npx elevenlabs agents push --dry-run)
```

Limits of the CLI's own checks in 1.7.1 were tested on purpose with broken copies:

- `agents push --dry-run` only parses the JSON. It accepted a bogus `model_id` and `speed: 9`, and it **exits 0 even when a config is invalid JSON**.
- `agents create --dry-run --json -` rejects unknown properties only.
- `validate_configs.py` adds the following checks, all read from the spec:
  - enums for `llm`, `tts.model_id`, `asr.provider` and `text_normalisation_type`
  - deprecated TTS models
  - TTS ranges and integer fields
  - `language == ar`, no tools, no `voice_id` (unless `--allow-voice-id`), and the prompt matching `prompts/system_v0.md`

  When `prompts/system_v0.md` changes, copy it into `sara.json` (`scripts/build_agent_config.py` takes over in Phase 2).

## On the Mac (Phase 0b): log in, push, test

```bash
cd ~/Desktop/saudi-voice-receptionist && git pull
cd agent && npm ci

# 1) Key: Ahmed puts it in the repo-root .env (git-ignored), copying names from .env.example:
#      ELEVENLABS_API_KEY=<his key>
#    The CLI reads ../.env from here. Alternatives: `npx elevenlabs auth login` (OAuth PKCE, browser,
#    stored in the macOS keychain) or `npx elevenlabs auth login --with-token` (reads the token on stdin).
npx elevenlabs user subscription get        # confirms the key works and shows the plan (Starter)

# 2) Validate, then push both agents
python3 validate_configs.py
npx elevenlabs agents push --dry-run
npx elevenlabs agents push --version-description "phase0 minimal arabic"
npx elevenlabs agents status                # should now show Agent IDs
git -C .. diff agent/agents.json            # whether push writes IDs here is UNVERIFIED; commit if it does

# 3) After the TTS gate: set the winner in agent_configs/sara.json (and sara_stt_probe.json)
#      "tts": {"model_id": "<winner model>", "voice_id": "<winner id from find_voices.py>", ...}
python3 validate_configs.py --allow-voice-id && npx elevenlabs agents pull && npx elevenlabs agents push

# 4) STT gate second run: edit sara_stt_probe.json "asr.provider" to "elevenlabs" or "scribe_v2_turbo", push again.
#    Transcripts (realtime ASR) for each test call:
npx elevenlabs agents conversations list --agent-id <probe agent id>
npx elevenlabs agents conversations get --conversation-id <id>      # GET /v1/convai/conversations/{id}
```

Rules from the review that apply here:

- The Mac is the only machine that pushes. The laptop only runs `--dry-run`.
- Run `agents pull` before `push` once anything has been pushed.
- If a dashboard change is ever made, pull it and commit it.

## UNVERIFIED (settle on the Mac with the key)

- Whether the server accepts `language: "ar"` together with `eleven_v4_turbo`.
  - The language docs say that adding languages in the dashboard moves the agent to the v2.5 multilingual model, and they do not mention v4.
- Whether `agents push` creates a new agent from a config with no ID. The dry-run prints "Would update agent", while `agents status` shows "Not created yet".
- Whether `push` writes agent IDs back into `agents.json`.
- Whether a shared-library voice must be added to "My Voices" before an agent can use it (`phase0/find_voices.py --add`).
- Which voice the agent uses while `voice_id` is absent. The spec default value would apply, but this has not been checked.
