# AI Agents: 12-Week Learning Plan

From **multi-agent builder** to **production agent engineer**, in 12 weeks, in public.

I am building agents the way they are built in production: measured, traced, secured and costed.
Every week ends with a pushed repo folder, a README with real numbers, and a written self-check.

> **The one shift this plan is about:** a Level 3 engineer says "my agent works".
> A Level 4 engineer shows it: "it succeeds 95% of the time on our test set, one run costs this much,
> and here is how it stays safe when someone attacks it."

---

## Where I am now

| | |
|---|---|
| **Current week** | Week 1: Agents from scratch |
| **Status** | All six days built. Left: fill the measured numbers in the Week 1 README, write the self-check, push |
| **Next up** | Week 2: Tools, context engineering and memory |

---

## Levels

| Level | What it means | Me |
|---|---|---|
| 1. LLM user | APIs, prompting, chatbots | Done |
| 2. Tool-using agent | ReAct, tools, RAG | Done (Travel Planner) |
| 3. Multi-agent builder | Several agents with a router or supervisor | Done (Octra, 5 agents) |
| **4. Production agent engineer** | **Evals, tracing, security, crash-resume, cost control** | **Target of this plan** |
| 5. Agent architect | Large system design, protocols, agents that run for hours | Later |

---

## Schedule

- **Weeks 1-8, full-time** (before joining): Mon-Sat, about 6 hours a day (about 36 h a week)
- **Weeks 9-12, part-time** (after joining, about mid-December): about 10-12 hours a week
- Suggested dates: start Mon 19 Oct 2026, week 8 ends Sun 13 Dec, week 12 ends Sun 10 Jan 2027

### Progress tracker

| Week | Dates | Mode | Theme | Key deliverable | Status |
|---|---|---|---|---|---|
| 1 | 19-25 Oct | Full-time | Agents from scratch | Agent loop and the 5 workflow patterns, with cost and latency numbers | **In progress** |
| 2 | 26 Oct-1 Nov | Full-time | Tools, context, memory | Long-task agent with compaction, memory assistant, agentic RAG comparison | Not started |
| 3 | 2-8 Nov | Full-time | MCP deep dive | Remote, OAuth-protected MCP server and my own MCP client | Not started |
| 4 | 9-15 Nov | Full-time | LangGraph 1.x in production | Migrated projects and Octra v2 with persistence and human approval | Not started |
| 5 | 16-22 Nov | Full-time | Multi-agent patterns | Pattern library and a three-way architecture bake-off | Not started |
| 6 | 23-29 Nov | Full-time | ADK, A2A, capstone design | ADK agent over A2A, capstone design doc and skeleton | Not started |
| 7 | 30 Nov-6 Dec | Full-time | Capstone build | Capstone v1 running locally with full tracing | Not started |
| 8 | 7-13 Dec | Full-time | Evals and observability | Eval suite, CI gate, before/after numbers | Not started |
| 9 | 14-20 Dec | Part-time | Security and guardrails | Threat model and an attack test suite in CI | Not started |
| 10 | 21-27 Dec | Part-time | Cost, reliability, deploy | Live deployment, dashboards, a cost report | Not started |
| 11 | 28 Dec-3 Jan | Part-time | Portfolio and visibility | README, demo video, blog post, updated resume | Not started |
| 12 | 4-10 Jan | Part-time | Review and next steps | 3 system designs, a work proposal, next-quarter plan | Not started |

**How the weeks connect:** Weeks 1-2 give the fundamentals that every framework hides. Weeks 3-6 add the
2026 standards (MCP, LangGraph 1.x, A2A) and the multi-agent patterns. Weeks 7-8 turn everything into one
capstone and prove it works with evals. Weeks 9-12 make it safe, cheap and visible, then point to what
comes next.

---

## Week 1 in detail (current)

Goal: understand exactly what happens inside an agent by building the loop, tool calling, structured output
and the five workflow patterns in plain Python. No LangChain this week.

| Day | What I built | Status |
|---|---|---|
| 1 | Logging wrapper for every model call (tokens, latency, cost) and a first raw tool call | Done |
| 2 | The agent loop with parallel tools, error recovery, timeouts, a hard step limit, and 3 real tools | Done |
| 3 | Structured output with validation and one retry, an invoice extractor scored on 10 inputs, streaming | Done |
| 4 | Prompt chaining with a gate, routing with an accuracy eval, parallelisation (sectioning and voting) | Built, numbers to fill |
| 5 | Orchestrator-workers, evaluator-optimizer, and a workflow vs agent comparison | Built, numbers to fill |
| 6 | Travel Planner rebuilt without LangChain (5 tools, re-planning when a tool fails) and the Week 1 README | Built, numbers to fill |

The pattern write-up, with diagrams and the numbers I measured, is in [`week_1/README.md`](week_1/README.md).

**Week 1 self-check, I am done when I can:**
- [ ] Write a tool-calling agent loop from memory in under 30 minutes
- [ ] Explain workflow vs agent with one example of each from my own code
- [ ] State my router's accuracy and the mistakes it made

---

## Ground rules

1. **Build more than I watch.** At least 60% of the hours go into code.
2. **A week is done only when** the repo is pushed with a README and the self-check is answered in writing.
3. **Measure from Day 1.** Log tokens, cost and latency for every model call.
4. **Cut scope, not the deliverable.** Ship a smaller version and move on.
5. **Never skip Week 8.** A smaller capstone with real evals beats a bigger one without them.
6. **Write in `LEARNINGS.md` every day:** what worked, what broke, what surprised me.
7. **Be honest in reports.** Report only measured numbers, and mention small samples.

### Daily rhythm (Weeks 1-8)

| Block | Time | What |
|---|---|---|
| Learn | 2 h | Read or watch the day's resources and take notes in my own words |
| Build | 3.5 h | Code the day's tasks, commit small and often |
| Log | 30 min | 5-10 lines in `LEARNINGS.md`, then push |

Day 6 of each week is also the buffer day. Day 7 is rest plus a 20-minute review of what slipped and a
quick look at the LangChain changelog, the MCP blog and the Anthropic Engineering blog.

---

## Capstone (Weeks 6-11): a multi-agent research assistant

One project ties the second half together. A lead agent clarifies the question and makes a plan that I
approve. Parallel researcher agents collect sourced findings, a writer drafts with inline citations, a
verifier checks every claim, and a localiser agent (built in Google ADK, called over A2A) produces Gujarati
or Hindi output.

**Must-have features**
- [ ] Clarify, plan, then human approval of the plan
- [ ] Lead agent and 3-5 parallel researchers, each with its own context and step/token limits
- [ ] Tools over MCP: web search, fetch/extract, document search
- [ ] One remote specialist over A2A
- [ ] Writer and verifier: every claim cited, unsupported claims flagged
- [ ] Durable execution: Postgres checkpointer, resume after a crash
- [ ] Budgets per run (steps, tokens, money, time) with graceful partial results
- [ ] Every run traced with cost and latency
- [ ] Evals: 50+ case golden set, validated LLM judge, CI gate, online evals
- [ ] Security: threat model, attack suite in CI, least privilege, outbound allow-list
- [ ] Deployed with dashboards and alerts
- [ ] README with demo GIF, diagram, eval table, cost per report and limitations

**Example targets (set my own in the design doc):** task success of 80% or more on the golden set,
citation accuracy of 90% or more, zero successful attacks in the security suite, p95 time per report under
5 minutes, and a fixed cost ceiling per report.

**Suggested stack:** Python 3.12, LangGraph/LangChain 1.x, Google ADK, MCP Python SDK v2, FastAPI,
Postgres, Qdrant, Langfuse, React or Streamlit, Docker, GitHub Actions, Kubernetes or a single VM.

---

## Repo layout

```
.
├── README.md              this file: the plan and my progress
├── LEARNINGS.md           daily notes: what worked, what broke, what surprised me
├── .env                   API keys (never committed, listed in .gitignore)
├── week_1/                agents from scratch
│   ├── README.md          pattern write-up with diagrams and measured numbers
│   └── Day-1 ... Day-6/   one folder per day
├── week_2/ ... week_12/   created as each week starts
└── capstone/              starts in Week 6
```

---

## Setup and conventions

- **Python 3.12** with **uv**, plus Docker and Git
- **Model access:** OpenRouter with `openai/gpt-4o-mini`, to keep experiments cheap. Strong models are for
  final runs and evals only.
- **Every call is logged** to `logs/calls.jsonl` (tokens, latency, cost). `cost_report.py` turns the log
  into totals and a latency graph.
- **Keep costs low:** hard monthly spending limits in the provider console, cached responses during
  development, and a weekly look at the running cost total.
- **Keep secrets safe:** `.env` is in `.gitignore`, and a secret scanner runs before every commit.

```bash
uv run python cost_report.py     # totals, INR cost and the latency graph
```

---

## Final checklist

Tick these off as I go. If every box is ticked by mid-January, the portfolio shows production agent
skills, not just demos.

- [ ] **W1** Agent loop and the 5 workflow patterns, with cost and latency numbers
- [ ] **W2** Context and memory experiments, each with a before/after number
- [ ] **W3** Remote, OAuth-protected MCP server on the 2026-07-28 spec, plus my own client
- [ ] **W4** Travel Planner and Octra migrated to LangGraph/LangChain 1.x
- [ ] **W5** Multi-agent bake-off report (single vs orchestrator-worker vs deep agent)
- [ ] **W6** ADK agent connected over A2A, and the capstone design doc
- [ ] **W7** Capstone v1 running locally with full tracing
- [ ] **W8** Eval suite with a CI gate and before/after numbers on my resume
- [ ] **W9** Threat model and attack suite running in CI
- [ ] **W10** Live deployment, dashboards and a cost report
- [ ] **W11** README, demo video, published blog post, updated resume
- [ ] **W12** Three system-design write-ups, a work proposal and my next-quarter plan

---

## If I fall behind

- Never skip Week 8.
- If work gets busy, merge Weeks 9 and 10, and keep the attack suite and the deployment.
- Drop optional items first: MCP Apps, the OpenAI Agents SDK skim, extra UI polish.

## Staying current after Week 12

- Every Sunday, 15 minutes on the LangChain changelog, the MCP blog and the Anthropic Engineering blog.
- Before trusting a tutorial, check its date and the library version it uses.
- Keep one small side project alive so there is always a place to try new ideas.

> When unsure what to do next, look at the traces. They tell me more than any new framework or course.

---

## Key references

- [Building Effective Agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents)
- [Demystifying evals for AI agents (Anthropic)](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Model Context Protocol, spec 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [A2A specification v1.0](https://a2a-protocol.org/latest/specification/)
- [LangChain changelog](https://docs.langchain.com/oss/python/releases/changelog)
- [Langfuse docs](https://langfuse.com/docs)
- [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications/)
- [Anthropic Engineering blog](https://www.anthropic.com/engineering)

The full day-by-day plan with every resource link is in the plan PDF (`AI_Agents_12_Week_Plan.pdf`).