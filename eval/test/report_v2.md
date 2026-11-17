# Classifier evaluation

100 stories labelled by GPT-6 Astra (OpenAI), blind to Gemini's answer.
Gemini's labels: `predictions_v2.csv`.

## Summary

| Metric | Value |
| --- | --- |
| Keyword filter precision (stories really about AI) | 100% (100/100) |
| Theme accuracy on AI stories | 73% (73/100) |
| 95% confidence interval (Wilson) | 64% – 81% |

## Per theme

| Theme | Reference labels | Gemini labels | Precision | Recall |
| --- | ---: | ---: | ---: | ---: |
| models | 8 | 9 | 78% | 88% |
| agents | 8 | 9 | 67% | 75% |
| rag | 1 | 1 | 100% | 100% |
| dev-tools | 14 | 16 | 75% | 86% |
| security | 7 | 4 | 100% | 57% |
| research | 8 | 8 | 75% | 75% |
| business | 18 | 17 | 65% | 61% |
| regulation | 5 | 6 | 50% | 60% |
| other | 31 | 30 | 77% | 74% |

## Confusion matrix

Rows: reference label. Columns: Gemini's label.

| | models | agents | rag | dev-tools | security | research | business | regulation | other |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **models** | **7** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| **agents** | 0 | **6** | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| **rag** | 0 | 0 | **1** | 0 | 0 | 0 | 0 | 0 | 0 |
| **dev-tools** | 0 | 2 | 0 | **12** | 0 | 0 | 0 | 0 | 0 |
| **security** | 0 | 0 | 0 | 1 | **4** | 0 | 2 | 0 | 0 |
| **research** | 0 | 0 | 0 | 1 | 0 | **6** | 0 | 1 | 0 |
| **business** | 2 | 0 | 0 | 0 | 0 | 0 | **11** | 1 | 4 |
| **regulation** | 0 | 0 | 0 | 0 | 0 | 0 | 1 | **3** | 1 |
| **other** | 0 | 1 | 0 | 1 | 0 | 2 | 3 | 1 | **23** |

## Disagreements (27)

| Story | Reference | Gemini | Reference note |
| --- | --- | --- | --- |
| [Show HN: Copper-KiCad – MCP to design PCBs in KiCad better and cheaper](https://github.com/claynicholson/copper-kicad-mcp) | agents | dev-tools | MCP integration enables agents to design hardware |
| [What end-to-end AI systems mean for the future of automated driving](https://www.aptiv.com/en/insights/article/q-a-from-modular-software-to-end-to-end-ai) | agents | other | Autonomous driving system behavior is central |
| [Gemini Decision 1 is Free on Google AI Studio](https://aistudio.google.com/docs/decisions-api) | business | models | Free availability is the main announcement |
| [GLM Models Cut AI Coding Costs 90% for 2k Engineers](https://finance.biggo.com/news/71888475bad974d6) | business | models | Engineering cost savings rather than model capability benchmarks |
| [The Wish Economy: Inside Starlight, the Bitcoin-Native AI App Store](https://starlight-ai.freemyip.com/sandbox/5de49786ace165eb6b29ca5ea3305b2c94be82784b8019010120ab42f31dc41f/) | business | other | Marketplace economics rather than a specific AI application |
| [SFT for professionals in software, AI, systems, science and others](https://app.outlier.ai/en/expert/referrals/link/3FKWhSGJnWvE8htqBdLKT9ZdU-w) | business | other | Domain suggests paid model training work |
| [Ask HN: What do coding interviews look like in the age of AI?](https://news.ycombinator.com/item?id=50510540) | business | other | Hiring practices are the main subject |
| [Google AI Ultra Subscription Not Worth It](https://www.reddit.com/r/google_antigravity/comments/1xx9nl3/google_ai_ultra_subscription_not_worth_it/) | business | other | Subscription value and pricing are central |
| [Australian companies face 'AI washing' claims after wave of job cuts, offshoring](https://www.reuters.com/business/world-at-work/australian-companies-face-ai-washing-claims-after-wave-job-cuts-offshoring-2026-11-11/) | business | regulation |  |
| [CodeGraphy v2.1: 11 MCP tools, interactive architecture graph, -85% LLM tokens](https://github.com/Vindettobkb/CodeGraphy-Desktop) | dev-tools | agents |  |
| [Brave Search API now accepts agentic payments via the x402 protocol](https://brave.com/blog/search-api-agentic-payments/) | dev-tools | agents | Search API feature for developers |
| [1 in 4 3rd Party AI Endpoints Underperform Their Advertised Models](https://hermes-ai.net/news/artificial-analysis-finds-1-in-4-ai-endpoints-quietly-underperform-their/) | models | other | Evaluation compares delivered and advertised model performance |
| [What Picasso taught me about building AI Agents](https://claramap.com/blog/what-picasso-taught-me-about-building-ai-agents/) | other | agents | Personal essay about building agents |
| [Dario Amodei says AI will cure cancer, Alzheimer's, heart disease in 10 years](https://garymarcus.substack.com/p/breaking-eli-lilly-ceo-becomes-latest) | other | business | Commentary assessing predictions rather than reporting discoveries |
| [Ask HN: What does building hardware with AI look like?](https://news.ycombinator.com/item?id=50508089) | other | business |  |
| [A milestone in expanding access to AI](https://openai.com/index/expanding-access-to-ai-with-chatgpt-ads/) | other | business | Title does not identify a more specific subject |
| [Jax Examples for Beginners (Dive into ML Fundamentals)](https://github.com/aymericdamien/JAX-Examples) | other | dev-tools | Educational examples rather than a new library |
| [New privacy rules for Google's Gemini Apps (updated November 16, 2026)](https://support.google.com/gemini/answer/13594961?hl=en) | other | regulation | Product privacy terms rather than government regulation |
| [We need more science in the judgment of AI](https://livingsystems.substack.com/p/we-need-more-science-in-the-judgment) | other | research |  |
| [A visual explanation of reinforcement learning](https://aatishb.com/myriad/how-brains-learn/) | other | research |  |
| [FAA tees up $875M AI tool to help manage air traffic congestion](https://arstechnica.com/ai/2026/09/faa-tees-up-875m-ai-tool-to-help-manage-air-traffic-congestion/) | regulation | business | Government deployment and spending are central |
| [Ask HN: Do I own the code I write with the help of AI?](https://news.ycombinator.com/item?id=50498553) | regulation | other |  |
| [Air-LLM: Broadcasting AI Weights for Edge LLM Inference via RF Computing](https://arxiv.org/abs/2610.00465) | research | dev-tools |  |
| [The Feasibility of a Hardwired Pause of Frontier AI Training](https://hardwired-pause.ai/) | research | regulation | Feasibility analysis of a technical safety mechanism |
| [Anthropic says a key AI safety alarm has been triggered, days before its IPO](https://finance.yahoo.com/markets/article/anthropic-says-a-key-ai-safety-alarm-has-been-triggered-days-before-its-ipo-171519615.html) | security | business | Safety alarm is central despite IPO context |
| [NATO uses 300B OpenAI tokens a month for cyber defence](https://foxandlion.pub/news/nato-uses-300-billion-openai-tokens-a-month-for-cyber-defence) | security | business | Cyber defense application rather than token pricing |
| [Running coding agents without handing them my credentials](https://blog.antonio.cx/running-agents-with-lend) | security | dev-tools |  |
