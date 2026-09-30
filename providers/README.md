# Official provider templates

These configurations use official API endpoints and environment variables for
credentials. They are templates for the named study models, not evidence that
historical runs used these endpoints. No live API validation is included.

| Configuration | Model ID | Credential environment variable | Protocol |
| --- | --- | --- | --- |
| `deepseek-v4-flash.toml` | `deepseek-v4-flash` | `DEEPSEEK_API_KEY` | Chat Completions |
| `claude-sonnet.toml` | `claude-sonnet-5` | `ANTHROPIC_API_KEY` | Claude Code generator |
| `gemini-3.5-flash.toml` | `gemini-3.5-flash` | `GEMINI_API_KEY` | Google OpenAI-compatible Chat Completions |
| `grok-4.5.toml` | `grok-4.5` | `XAI_API_KEY` | Responses |
| `kimi-k2.6.toml` | `kimi-k2.6` | `MOONSHOT_API_KEY` | Chat Completions |
| `gpt-5.4.toml` | `gpt-5.4` | `OPENAI_API_KEY` | Responses |

DeepSeek uses the study's `deepseek-v4-flash` model ID and official endpoint.

The saved `claude-sonnet` provider configuration names `claude-sonnet-5`; this
file preserves that explicit model. The separate saved Claude CLI configuration
used the unpinned `sonnet` selector. Use the exact model from a study's recorded
response if that study used a different Sonnet version. The Anthropic template
selects the existing `claude-cli` candidate generator; the Codex execution bridge
has no native Anthropic Messages adapter.

Pass the configuration explicitly using `--generator-config`,
`--execution-config`, or `--provider-config`, as appropriate to the entry point.
The repository's implicit ModelConfig defaults are independent of these files.

Official documentation:

- [DeepSeek-V4-Flash](https://api-docs.deepseek.com/news/news260424/)
- [Claude Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview) and [Claude API](https://platform.claude.com/docs/en/api/overview)
- [Gemini 3.5 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash) and [OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai)
- [Grok 4.5](https://docs.x.ai/developers/models/grok-4.5) and [API quickstart](https://docs.x.ai/developers/quickstart)
- [Kimi K2.6](https://platform.kimi.ai/docs/guide/kimi-k2-6-quickstart)
- [GPT-5.4](https://developers.openai.com/api/docs/models/gpt-5.4)
