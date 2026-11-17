# Classifier evaluation

100 stories labelled by an independent LLM, blind to Gemini's answer.
Gemini's labels: `predictions.csv`.

## Summary

| Metric | Value |
| --- | --- |
| Keyword filter precision (stories really about AI) | 100% (100/100) |
| Theme accuracy on AI stories | 69% (69/100) |
| 95% confidence interval (Wilson) | 59% – 77% |

## Per theme

| Theme | Reference labels | Gemini labels | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| models | 8 | 15 | 53% | 100% |
| agents | 8 | 9 | 67% | 75% |
| rag | 1 | 1 | 100% | 100% |
| dev-tools | 14 | 18 | 67% | 86% |
| security | 7 | 6 | 83% | 71% |
| research | 8 | 8 | 62% | 62% |
| business | 18 | 18 | 67% | 67% |
| regulation | 5 | 6 | 67% | 80% |
| other | 31 | 19 | 84% | 52% |

## Confusion matrix

Rows: reference label. Columns: Gemini's label.

| | models | agents | rag | dev-tools | security | research | business | regulation | other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **models** | **8** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **agents** | 0 | **6** | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| **rag** | 0 | 0 | **1** | 0 | 0 | 0 | 0 | 0 | 0 |
| **dev-tools** | 1 | 1 | 0 | **12** | 0 | 0 | 0 | 0 | 0 |
| **security** | 0 | 0 | 0 | 0 | **5** | 0 | 2 | 0 | 0 |
| **research** | 1 | 0 | 0 | 0 | 1 | **5** | 1 | 0 | 0 |
| **business** | 2 | 0 | 0 | 1 | 0 | 0 | **12** | 1 | 2 |
| **regulation** | 0 | 0 | 0 | 0 | 0 | 0 | 1 | **4** | 0 |
| **other** | 3 | 2 | 0 | 4 | 0 | 3 | 2 | 1 | **16** |

## Disagreements (31)

| Story | Reference | Gemini | Reference note |
| --- | --- | --- | --- |
| [Show HN: Copper-KiCad – MCP to design PCBs in KiCad better and cheaper](https://github.com/claynicholson/copper-kicad-mcp) | agents | dev-tools | MCP integration enables agents to design hardware |
| [What end-to-end AI systems mean for the future of automated driving](https://www.aptiv.com/en/insights/article/q-a-from-modular-software-to-end-to-end-ai) | agents | other | Autonomous driving system behavior is central |
| [SFT for professionals in software, AI, systems, science and others](https://app.outlier.ai/en/expert/referrals/link/3FKWhSGJnWvE8htqBdLKT9ZdU-w) | business | dev-tools | Domain suggests paid model training work |
| [Gemini Decision 1 is Free on Google AI Studio](https://aistudio.google.com/docs/decisions-api) | business | models | Free availability is the main announcement |
| [GLM Models Cut AI Coding Costs 90% for 2k Engineers](https://finance.biggo.com/news/71888475bad974d6) | business | models | Engineering cost savings rather than model capability benchmarks |
| [Ask HN: What do coding interviews look like in the age of AI?](https://news.ycombinator.com/item?id=50510540) | business | other | Hiring practices are the main subject |
| [Google AI Ultra Subscription Not Worth It](https://www.reddit.com/r/google_antigravity/comments/1xx9nl3/google_ai_ultra_subscription_not_worth_it/) | business | other | Subscription value and pricing are central |
| [Australian companies face 'AI washing' claims after wave of job cuts, offshoring](https://www.reuters.com/business/world-at-work/australian-companies-face-ai-washing-claims-after-wave-job-cuts-offshoring-2026-11-11/) | business | regulation |  |
| [An intention spec – workflow for the agentic dev cycle](https://djordjepuzic.com/blog/posts/2026-11-13-intention-spec/) | dev-tools | agents | Specification workflow for agent assisted software development |
| [Show HN: Claudette - Mistral models in Claude Code](https://github.com/raed667/claudette) | dev-tools | models |  |
| [Claude Code and Codex reverse engineered my 1994 Jeep's ECU over a $3 Arduino \[video\]](https://www.youtube.com/watch?v=WPj3aQ-xxpI) | other | agents | Hardware project completed with AI assistance |
| [What Picasso taught me about building AI Agents](https://claramap.com/blog/what-picasso-taught-me-about-building-ai-agents/) | other | agents | Personal essay about building agents |
| [Pundit Claims – Open-Source Register of AI Claims by Gary Marcus and Ed Zitron](https://punditclaims.ai/) | other | business |  |
| [Dario Amodei says AI will cure cancer, Alzheimer's, heart disease in 10 years](https://garymarcus.substack.com/p/breaking-eli-lilly-ceo-becomes-latest) | other | business | Commentary assessing predictions rather than reporting discoveries |
| [Claude Meetings](https://claude.com/resources/articles/claude-meetings) | other | dev-tools |  |
| [Jax Examples for Beginners (Dive into ML Fundamentals)](https://github.com/aymericdamien/JAX-Examples) | other | dev-tools | Educational examples rather than a new library |
| [Ask HN: What does building hardware with AI look like?](https://news.ycombinator.com/item?id=50508089) | other | dev-tools |  |
| [CopySpeech – AI text-to-speech for your clipboard](https://github.com/ilyaizen/CopySpeech) | other | dev-tools |  |
| [Show HN: OpenPocket – iOS app for running Qwen3.5, LFM and other LLMs offline](https://apps.apple.com/th/app/openpocket/id6833028114) | other | models |  |
| [Why Every AI Model Will Ship as a Torrent](https://pirateface.co/articles/every-ai-model-should-be-a-torrent) | other | models | Prediction about model distribution rather than a release |
| [A milestone in expanding access to AI](https://openai.com/index/expanding-access-to-ai-with-chatgpt-ads/) | other | models | Title does not identify a more specific subject |
| [New privacy rules for Google's Gemini Apps (updated November 16, 2026)](https://support.google.com/gemini/answer/13594961?hl=en) | other | regulation | Product privacy terms rather than government regulation |
| [We need more science in the judgment of AI](https://livingsystems.substack.com/p/we-need-more-science-in-the-judgment) | other | research |  |
| [The Fundamental Flaw in the Race to AGI](https://project507.substack.com/p/the-fundamental-flaw-in-the-race) | other | research |  |
| [A visual explanation of reinforcement learning](https://aatishb.com/myriad/how-brains-learn/) | other | research |  |
| [FAA tees up $875M AI tool to help manage air traffic congestion](https://arstechnica.com/ai/2026/09/faa-tees-up-875m-ai-tool-to-help-manage-air-traffic-congestion/) | regulation | business | Government deployment and spending are central |
| [AXI Framework: The Cure for the Cost Crisis in AI](https://zenodo.org/records/23958737) | research | business | Proposed framework rather than market pricing news |
| [Air-LLM: Broadcasting AI Weights for Edge LLM Inference via RF Computing](https://arxiv.org/abs/2610.00465) | research | models |  |
| [Preventing an AI catastrophe, a brief into to analysis by synthesis](https://shukla.io/blog/2026-11/analysis-by-synthesis.html) | research | security | Analysis by synthesis suggests a technical safety approach |
| [Anthropic says a key AI safety alarm has been triggered, days before its IPO](https://finance.yahoo.com/markets/article/anthropic-says-a-key-ai-safety-alarm-has-been-triggered-days-before-its-ipo-171519615.html) | security | business | Safety alarm is central despite IPO context |
| [NATO uses 300B OpenAI tokens a month for cyber defence](https://foxandlion.pub/news/nato-uses-300-billion-openai-tokens-a-month-for-cyber-defence) | security | business | Cyber defense application rather than token pricing |
