# NightmareNet Agent Configuration

## Instructions

Read and follow, in this priority order:

1. `Prompt.md` — **Operating doctrine** (two parts).
   - **Part I — Execution doctrine:** elite engineering philosophy, self-improvement loop, research-first execution, validation standards.
   - **Part II — Consumer product improvement:** Analyze → Critique → Reimagine → Stress Test → Improve → Refine cycle; five user perspectives (first-time, daily, power, mobile, impatient); AI-native opportunities scan; delight engineering. *Applies after every implementation — never stop at "it works."*
2. `CLAUDE.md` — Project-specific conventions (Python 3.9 compat, Pydantic v2 + FastAPI rules, line length, ruff config).
3. The `.cursor/skills/` skills below auto-load when the description matches the task — they encode the doctrine in actionable form.

### Default execution loop

For ANY non-trivial task: **Research → Think → Plan → Build → Test → Verify → Validate → Reflect → Improve → Repeat.**
Never stop at first working implementation. Iterate until the solution feels elegant, scalable, intuitive, and genuinely delightful.

### Hard rules from doctrine

- Never patch symptoms; solve root causes.
- Never claim completion without proof (tests + UX walkthrough + edge cases + perf + accessibility).
- Never ship MVP-level when a feature ecosystem is possible — think in systems, not screens.
- Build for emotional satisfaction, not just functional correctness. "Would users love this?"
- After every correction or failure, update `tasks/lessons.md`. Never repeat the same mistake twice.

## Skills

The following skills are available and SHOULD be used when relevant:

### Superpowers (via ~/.agents/skills/superpowers/)

- **test-driven-development** — Use when writing any new feature or fixing bugs
- **systematic-debugging** — Use when investigating test failures or runtime errors
- **verification-before-completion** — Use before claiming ANY task is done
- **writing-plans** — Use when the task requires 3+ steps of implementation
- **executing-plans** — Use when executing a previously written plan

### Project Skills (via .claude/skills/)

- **ui-ux-pro-max** (`.claude/skills/ui-ux-pro-max/`) — Use for any frontend/UI work on the Next.js frontend
- **elite-execution-philosophy** (`.claude/skills/elite-execution-philosophy/`) — Core execution philosophy; applies to ALL tasks. Sets staff-engineer quality bar.
- **workflow-orchestration** (`.claude/skills/workflow-orchestration/`) — Plan-mode-first execution, task management via `tasks/todo.md`, self-improvement loop via `tasks/lessons.md`
- **verification-and-elegance** (`.claude/skills/verification-and-elegance/`) — Never mark work complete without proof. Demands elegant solutions over hacky/brittle code.
- **subagent-strategy** (`.claude/skills/subagent-strategy/`) — Aggressive subagent delegation for research, debugging, architecture, security, and verification.
- **research-first-execution** (`.claude/skills/research-first-execution/`) — Research competitors, benchmark patterns, analyze architecture before implementation.
- **ai-native-product-thinking** (`.claude/skills/ai-native-product-thinking/`) — AI-native product design, modern UX expectations, Linear/Vercel/Stripe-tier polish.
- **performance-security-devops** (`.claude/skills/performance-security-devops/`) — Performance engineering, security, RBAC, CI/CD, observability, deployment automation.

## Commands

Available slash commands in `.claude/commands/`:

- `/check` — Run full quality pipeline (lint + tests + frontend build)
- `/tdd <feature>` — Implement a feature with strict TDD
- `/commit` — Create a conventional commit with pre-flight checks
- `/debug <problem>` — Systematic debugging workflow
- `/prime` — Load project context for a new session

## Hooks

Configured in `.claude/settings.json`:

- **PostToolUse**: Python syntax check on `.py` file edits
- **Stop**: Ruff lint check before session ends

## Learned User Preferences

- Research-first execution: deep competitive landscape, market sizing, academic lit, GTM, personas, and architecture patterns before implementing; leverage Browser Use API for live web research/automation where applicable.
- Use subagents aggressively for parallel research, exploration, debugging, security review, and verification; one focused responsibility per subagent.
- **Subagents tend to fail sometimes** — always retry on error, investigate root cause before re-dispatch. Common failures: `[invalid_argument]`, `PING timed out`, interactive CLI prompts blocking. Mitigations: pass `--yes`/`-y` flags, pipe `echo Y |`, use non-interactive mode, keep prompts focused and under token limits. In this workspace, direct execution is often more reliable than subagent delegation.
- Linear/Vercel/Stripe-tier UI polish; feature-dense, information-heavy panels inspired by Linear/Vercel/DarkLead, Arc, Notion, Raycast — not minimal or sparse.
- Subtle UI sounds (Linear/Notion style clicks, success chimes, transition whooshes) — NOT immersive ambient/cyberpunk audio.
- Pipeline visualization preference: interactive node graph with 3D orbital elements (hybrid draggable nodes + orbital phase rotation around central model).
- Plan-mode-first for any non-trivial task (3+ steps or architectural decisions); generate full PRD/TRD/architecture/UX flows/API contracts/sprint plans as part of planning, not just task lists; re-plan if anything goes sideways.
- Track work via `tasks/todo.md` (checkable items) and corrections via `tasks/lessons.md` (self-improvement loop, append after every user correction).
- Verification before completion + autonomous bug fixing: tests, lint, type-check, UX validation, architecture integrity; investigate, trace root cause, fix, and validate without hand-holding; never claim done without staff-engineer-level proof and zero tolerance for shortcuts, lazy implementations, or fake completion.
- Demand elegance: pause and ask "Is there a more elegant solution?" before non-trivial implementations; reject hacky, repetitive, brittle, or tightly-coupled code.
- Git discipline: Conventional Commits, atomic per logical change; commit and push frequently to grow GitHub contribution history (clean atomic history naturally drives up commit count) — the user explicitly asks for this cadence.
- AI-native thinking: every feature considers AI copilots, semantic search, intelligent automation, conversational workflows; integrate Azure OpenAI (sole LLM backend — Bedrock removed), RAG pipelines, and vector databases as needed.
- Performance-first: sub-100ms UI, sub-500ms API, CUDA acceleration, mixed precision, quantization for ML; code splitting and lazy loading on the frontend.
- Security + DevOps: RBAC, secrets in vaults, rate limiting, audit logs, least-privilege, compliance readiness; CI/CD via GitHub Actions, Docker, Vercel/Railway, PostgreSQL/Redis, observability, rollback strategies, cost optimization.
- Spec-driven + repository intelligence: GitHub Spec Kit structured specs/ADRs/validation pipelines; use GitNexus for impact analysis before editing any symbol, and complement with `graphify` and `code-review-graph` for architecture and PR-review intelligence.
- Design skills installed: `npx impeccable skills install` (pbakaus/impeccable), `npx skills add Leonxlnx/taste-skill --skill "design-taste-frontend"`, `npx skills add emilkowalski/skill`. Skills install to `.cursor/skills/` via the `npx skills` CLI.
- **Stray lockfile trap**: If Next.js/Turbopack spawns excessive Node.js processes, check parent directories (up to user home `C:\Users\aditj\`) for stray `package.json`/`package-lock.json`/`node_modules`. Delete them — Turbopack walks up looking for workspace root. Root-level `package.json`, `package-lock.json`, and `node_modules/` must NEVER be committed to git (they were once tracked here and caused Turbopack multi-lockfile chaos).
- **Python .env loading**: uvicorn does NOT auto-load `.env` files. Always use `python-dotenv` with `load_dotenv()` at app entrypoint (guarded by `try/except ImportError`).
- **npm audit fix --force is dangerous**: it can DOWNGRADE packages and introduce MORE vulnerabilities. Prefer `npm install <pkg>@latest` for targeted fixes.
- GitHub contributions only count on the default branch (`main`); work on feature branches must be merged + pushed to main for profile activity.

## Learned Workspace Facts

- Next.js client uses same-origin `/api`; `frontend/next.config.ts` rewrites to `NEXT_API_REWRITE_URL` (backend base, no trailing slash). If `NEXT_PUBLIC_API_URL` is set, the browser calls that origin directly and rewrites are not used (configure API CORS for split-host).
- Health (`/api/v1/health`) optionally runs `pytest --collect-only` via `NIGHTMARENET_HEALTH_TEST_COUNT` (leave unset in production); pipeline runner registry capped by `NIGHTMARENET_MAX_PIPELINE_RUNNERS` (default 64, completed runs evicted first when over cap).
- Repo structure: OSS core in `nightmarenet/` (Apache 2.0), hosted platform in `nightmarenet_server/` (OAuth GitHub/Google + API keys, Celery workers, WebSocket fan-out, Alembic migrations; fully wired — app.py mounts OSS core, no additional integration needed), frontend in `frontend/` (Next.js 14 + Tailwind v4 + Framer Motion + GSAP).
- Dev GPU: RTX 3050 Ti (4 GB VRAM, CC 8.6); Python 3.12 + CUDA 12.1 venv at `.venv312/`. DistilBERT/DistilGPT-2 fit without issues; GPT-2 (124M) needs gradient checkpointing + FP16, batch size 4-8 max.
- 20-panel feature-dense dashboard lives at `/dashboard`, with `frontend/src/components/dashboard/` (AppShell, Cmd+K palette, 12 panels) and `frontend/src/components/ui/` (12 primitives); design inspiration is `C:\Users\aditj\New Projects\TR-104-DarkLead-main`. Current stats: 434+ tests, 13 API endpoints.
- OSS FastAPI app exposes WebSocket at `/ws/runs/{run_id}` for live pipeline streaming; PipelineLab frontend uses WebSocket-first with polling fallback.
- Strategic direction: hybrid open-source core (Apache 2.0) + hosted platform (paid). OSS = distortion engines, training loop, CLI. Paid = orchestration, compliance, multi-GPU, team features. Pricing: Community $0 (single-GPU, self-hosted) / Pro $49/seat/mo + compute (~1000 cycles/mo) / Enterprise $50K-$100K/yr (SSO, audit, compliance, on-prem, SLA, custom engines).
- Strategic execution plan at `.cursor/plans/nightmarenet_strategic_research_synthesis_9589248a.plan.md` (do not edit while executing); research synthesis artifact at `docs/solutions/nightmarenet-research-synthesis.md`; full deep-research workflows expect **parallel-cli** (or equivalent) available.
- Cyberpunk-neural design system: Void Black (#020617) backgrounds, Indigo Dream (#818CF8), Red Nightmare (#EF4444), Cyan Neural (#06B6D4), Amber Compress (#F59E0B); Inter (UI) + JetBrains Mono (code/metrics); Framer Motion spring-based 60fps motion.
- Academic positioning: closest prior art is PAD (Deperrois 2022, eLife) for sleep-inspired training; NightmareNet differentiates by targeting adversarial robustness (not representation learning) with integrated compression phase. Benchmark v1 headline: +14.49% relative robustness improvement on SST-2 (DistilBERT, 500 train / 200 val, seed 42), documented in `docs/research/benchmark-v1.md` and `docs/research/paper-draft.md`.
- Target market timing: EU AI Act Article 15 (robustness mandate) fully applicable August 2, 2026.
- CI integration: composite GitHub Action at `.github/actions/nightmarenet-robustness-check/` invokes `nightmarenet evaluate --json` to gate PRs on a robustness threshold; active development branch is `Frontend-with-Updated-backend`.
- 12 Cursor skills are committed at `.cursor/skills/` (auto-invoke; `.cursor/skills/` is exempted from the `.cursor/` gitignore). Continual-learning index lives at `.cursor/hooks/state/continual-learning-index.json` (NightmareNet-local; supersedes the prior AtomicPulse cross-workspace path).

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **NightmareNet** (4310 symbols, 7685 relationships, 161 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/NightmareNet/context` | Codebase overview, check index freshness |
| `gitnexus://repo/NightmareNet/clusters` | All functional areas |
| `gitnexus://repo/NightmareNet/processes` | All execution flows |
| `gitnexus://repo/NightmareNet/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
