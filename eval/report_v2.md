# Classifier evaluation

100 stories labelled by an independent LLM, blind to Gemini's answer.
Gemini's labels: `predictions_v2.csv`.

## Summary

| Metric | Value |
| --- | --- |
| Keyword filter precision (stories really about AI) | 97% (97/100) |
| Theme accuracy on AI stories | 79% (77/97) |
| 95% confidence interval (Wilson) | 70% – 86% |

## Per theme

| Theme | Reference labels | Gemini labels | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| models | 6 | 5 | 80% | 67% |
| agents | 11 | 12 | 75% | 82% |
| rag | 0 | 1 | 0% | – |
| dev-tools | 20 | 25 | 60% | 75% |
| security | 6 | 4 | 100% | 67% |
| research | 4 | 4 | 50% | 50% |
| business | 20 | 18 | 100% | 90% |
| regulation | 4 | 4 | 100% | 100% |
| other | 26 | 24 | 88% | 81% |

## Confusion matrix

Rows: reference label. Columns: Gemini's label.

| | models | agents | rag | dev-tools | security | research | business | regulation | other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **models** | **4** | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| **agents** | 0 | **9** | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| **rag** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **dev-tools** | 0 | 3 | 0 | **15** | 0 | 0 | 0 | 0 | 2 |
| **security** | 0 | 0 | 0 | 2 | **4** | 0 | 0 | 0 | 0 |
| **research** | 1 | 0 | 0 | 1 | 0 | **2** | 0 | 0 | 0 |
| **business** | 0 | 0 | 1 | 1 | 0 | 0 | **18** | 0 | 0 |
| **regulation** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **4** | 0 |
| **other** | 0 | 0 | 0 | 3 | 0 | 2 | 0 | 0 | **21** |

## Disagreements (20)

| Story | Reference | Gemini | Reference note |
| --- | --- | --- | --- |
| [Show HN: Agent skill and Claude/Codex plugins for Google Ads campaigns](https://github.com/adeptads/agent-skills) | agents | dev-tools |  |
| [MCP vs. CLI vs. Skills: What Each Costs in Context](https://openrouter.ai/blog/insights/mcp-vs-cli-vs-skills/) | agents | dev-tools | Comparison centers on agent tool access and context |
| [Databricks AI Index](https://developers.databricks.com/ai-index) | business | dev-tools | Index appears focused on enterprise AI adoption |
| [Discourse (forums) sees itself well positioned for the AI search era (vs Reddit)](https://blog.discourse.org/2026/11/reddit-vs-discourse-a-tale-of-two-incentive-models/) | business | rag | Forum positioning is central rather than search implementation |
| [In 1 in 6 repos with both files, Claude Code never loads the AGENTS.md](https://gethrbr.com/blog/claude-md-agents-md-github-study) | dev-tools | agents |  |
| [Show HN: Blobby – A design canvas that Claude, Cursor or Codex drives over MCP](https://useblobby.com/) | dev-tools | agents | Design tool controlled through AI integrations |
| [Show HN: Toolmaker Agent–Software project management for human and AI agent](https://toolmaker.io/) | dev-tools | agents | Project management tooling for humans and agents |
| [Show HN: Play SNES games while Claude is working](https://github.com/LaurentiuGabriel/retro-break) | dev-tools | other | Companion utility for an AI coding workflow |
| [Claude OAuth Failures](https://news.ycombinator.com/item?id=50480936) | dev-tools | other |  |
| [DeepSeek Ultrafast](https://github.com/basetenlabs/deepseek-ultrafast) | models | dev-tools | Title suggests a specific model variant |
| [I let LLMs play a 1988 detective gamebook 646 times](https://blog.mastykarz.nl/llms-play-detective-gamebook/) | models | other | Repeated game trials evaluate model capabilities |
| [Using LLMs outside of reflection is an anti-pattern](https://news.ycombinator.com/item?id=50489240) | other | dev-tools |  |
| [Inference Gateway Desktop, an AI client for any model provider](https://github.com/inference-gateway/desktop) | other | dev-tools | General AI client rather than developer infrastructure |
| [Everything You Wanted to Know About LLM Post-Training \[video\]](https://www.youtube.com/watch?v=LVXtFnEbNU0) | other | dev-tools | Educational overview rather than a new research result |
| [Orienting to 1 year AGI timelines](https://www.lesswrong.com/posts/biFHYdJnMSCmW9Xou/orienting-to-1-year-agi-timelines) | other | research | Timeline commentary rather than a scientific result |
| [Real: Reported Engagement with AI Level Framework](https://www.realgoodai.org/real-rating) | other | research | Framework for describing AI engagement |
| [Evolving Infra: Agent-Adaptive LLM Serving at Scale](https://arxiv.org/abs/2611.12304) | research | dev-tools | Paper proposes a serving technique |
| [I Tried Every LLM Architecture Change Since 2020](https://www.nikita-pavlichenko.com/blog/every-llm-architecture-change) | research | models | Architecture experimentation rather than named model comparison |
| [Show HN: Bright Lines – a fail-closed guard hook for Claude Code](https://github.com/LeriderTechnologies/bright-lines) | security | dev-tools | Safety guard functionality is central |
| [FlashVMM – jail your AI agent in a MicroVM that boots in 18 ms](https://flashvmm.com/) | security | dev-tools | Agent isolation is the primary purpose |

## Not about AI (3)

Stories the keyword filter let through.

- [The anti-marketing aspect of the Gemini network](https://ploum.net/2026-11-12-anti-marketing-gemini.html) (Gemini: other)
- [ML Modules for Mere Mortals](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/) (Gemini: research)
- [AI Race: an adaptation of Magical Athlete board game](https://ai-race.eamag.me/) (Gemini: other)
