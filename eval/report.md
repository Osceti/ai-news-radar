# Classifier evaluation

100 stories labelled by GPT-6 Astra (OpenAI), blind to Gemini's answer.
Gemini's labels: `predictions.csv`.

## Summary

| Metric | Value |
| --- | --- |
| Keyword filter precision (stories really about AI) | 97% (97/100) |
| Theme accuracy on AI stories | 77% (75/97) |
| 95% confidence interval (Wilson) | 68% – 85% |

## Per theme

| Theme | Reference labels | Gemini labels | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| models | 6 | 7 | 71% | 83% |
| agents | 11 | 11 | 82% | 82% |
| rag | 0 | 0 | – | – |
| dev-tools | 20 | 28 | 57% | 80% |
| security | 6 | 6 | 100% | 100% |
| research | 4 | 4 | 50% | 50% |
| business | 20 | 20 | 95% | 95% |
| regulation | 4 | 4 | 100% | 100% |
| other | 26 | 17 | 82% | 54% |

## Confusion matrix

Rows: reference label. Columns: Gemini's label.

| | models | agents | rag | dev-tools | security | research | business | regulation | other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **models** | **5** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| **agents** | 0 | **9** | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| **rag** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **dev-tools** | 1 | 2 | 0 | **16** | 0 | 0 | 0 | 0 | 1 |
| **security** | 0 | 0 | 0 | 0 | **6** | 0 | 0 | 0 | 0 |
| **research** | 0 | 0 | 0 | 1 | 0 | **2** | 0 | 0 | 1 |
| **business** | 0 | 0 | 0 | 0 | 0 | 1 | **19** | 0 | 0 |
| **regulation** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **4** | 0 |
| **other** | 1 | 0 | 0 | 9 | 0 | 1 | 1 | 0 | **14** |

## Disagreements (22)

| Story | Reference | Gemini | Reference note |
| --- | --- | --- | --- |
| [MCP vs. CLI vs. Skills: What Each Costs in Context](https://openrouter.ai/blog/insights/mcp-vs-cli-vs-skills/) | agents | dev-tools | Comparison centers on agent tool access and context |
| [Mac Health MCP – ask Claude why your Mac is slow](https://github.com/Swedishwizards/Mac-health-mcp) | agents | dev-tools |  |
| [Databricks AI Index](https://developers.databricks.com/ai-index) | business | research | Index appears focused on enterprise AI adoption |
| [In 1 in 6 repos with both files, Claude Code never loads the AGENTS.md](https://gethrbr.com/blog/claude-md-agents-md-github-study) | dev-tools | agents |  |
| [Show HN: Toolmaker Agent–Software project management for human and AI agent](https://toolmaker.io/) | dev-tools | agents | Project management tooling for humans and agents |
| [Llama.cpp v1 Is Out](https://huggingface.co/blog/ggml-org/llama-cpp-v1) | dev-tools | models |  |
| [Claude OAuth Failures](https://news.ycombinator.com/item?id=50480936) | dev-tools | other |  |
| [I let LLMs play a 1988 detective gamebook 646 times](https://blog.mastykarz.nl/llms-play-detective-gamebook/) | models | other | Repeated game trials evaluate model capabilities |
| [We handed our lives to closed software. AI is about to show us the cost](https://news.ycombinator.com/item?id=50509195) | other | business |  |
| [An AI-assisted RP2040 audio board that worked on first spin in 5 days](https://solderable.dev/blog/fluid) | other | dev-tools | AI assisted hardware project rather than an AI development tool |
| [The Hard Part of AI Coding Is the Second Change](https://brian.biz/blog/ai-agents-keep-it-working/) | other | dev-tools | Commentary on AI coding rather than a tool release |
| [Local AI chat for iPhone(test build), built on a custom engine](https://github.com/MiTLN/OwnOwl-iPhone) | other | dev-tools | Consumer chat application rather than developer infrastructure |
| [Ask HN: Has AI coding changed who builds your internal tools?](https://news.ycombinator.com/item?id=50473926) | other | dev-tools |  |
| [Show HN: AxiomStory – Keep stories consistent across AI text, images, video](https://axiomstory.com) | other | dev-tools |  |
| [Ask HN: Has AI coding changed who builds your internal tools?](https://news.ycombinator.com/item?id=50485228) | other | dev-tools |  |
| [Inference Gateway Desktop, an AI client for any model provider](https://github.com/inference-gateway/desktop) | other | dev-tools | General AI client rather than developer infrastructure |
| [Show HN: Minute – An Offline Meeting Notetaker Using Local LLMs](https://minutenotes.app/) | other | dev-tools |  |
| [Show HN: My OSS Claude Meetings alternative that works with any agent or call](https://github.com/wanderingstan/vibeconf-app/) | other | dev-tools | Meeting application with agent integration |
| [Everything You Wanted to Know About LLM Post-Training \[video\]](https://www.youtube.com/watch?v=LVXtFnEbNU0) | other | models | Educational overview rather than a new research result |
| [Orienting to 1 year AGI timelines](https://www.lesswrong.com/posts/biFHYdJnMSCmW9Xou/orienting-to-1-year-agi-timelines) | other | research | Timeline commentary rather than a scientific result |
| [Evolving Infra: Agent-Adaptive LLM Serving at Scale](https://arxiv.org/abs/2611.12304) | research | dev-tools | Paper proposes a serving technique |
| [We just found a new Dwarf Planet in our solar system with Claude and you can too](https://twitter.com/willdepue/status/2120632732107907471) | research | other | AI enabled scientific discovery |

## Not about AI (3)

Stories the keyword filter let through.

- [The anti-marketing aspect of the Gemini network](https://ploum.net/2026-11-12-anti-marketing-gemini.html) (Gemini: other)
- [ML Modules for Mere Mortals](https://thunderseethe.dev/posts/ml-modules-for-mere-mortals/intro/) (Gemini: dev-tools)
- [AI Race: an adaptation of Magical Athlete board game](https://ai-race.eamag.me/) (Gemini: other)
