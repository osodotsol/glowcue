# GlowCue knowledge base

This is the shared source of truth for the owner, Claude Code and Antigravity. **Start with [PROJECT_STATUS.md](PROJECT_STATUS.md).**

| Area | Document | Purpose |
|---|---|---|
| Status | [PROJECT_STATUS.md](PROJECT_STATUS.md) | Live record: current phase, results, blockers, next action |
| Product | [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) | Strategy, differentiation, brand check, feature classification |
| | [PRD.md](PRD.md) | Requirements, functional spec, NFRs, MVP scope, definition of done |
| | [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Visual tokens, flow, screen-by-screen spec, assets |
| | [ASSETS.md](ASSETS.md) | Image and font register: product renders (cleared), temporary portraits (not cleared), replacement steps |
| | [decisions/ADR-005](decisions/ADR-005-demo-provider-and-redesign.md) | Demo analysis without the photo; Edition 2 implementation choices |
| | [decisions/ADR-006](decisions/ADR-006-live-youcam-analysis.md) | Live YouCam analysis: job polling, raw-body upload, 9 SD actions, safeguards |
| Technical | [ARCHITECTURE.md](ARCHITECTURE.md) | Stack, responsibilities, diagram, directory layout |
| | [API_CONTRACTS.md](API_CONTRACTS.md) | GlowCue HTTP endpoints (backend ↔ frontend) |
| | [DATA_MODEL.md](DATA_MODEL.md) | Shared data shapes |
| | [YOUCAM_API.md](YOUCAM_API.md) | Verified YouCam facts, unit costs, verification log |
| | [RECOMMENDATION_ENGINE.md](RECOMMENDATION_ENGINE.md) | Catalogue schema, engine logic, pseudocode, edge cases, claim rules |
| Quality | [TEST_PLAN.md](TEST_PLAN.md) | Test levels, tools and gates |
| | [SECURITY_PRIVACY.md](SECURITY_PRIVACY.md) | Controls, guardrails, permission model, incident response |
| Operations | [DEPLOYMENT.md](DEPLOYMENT.md) | Hosting choice and deploy steps |
| | [RUNBOOK.md](RUNBOOK.md) | How to run, operate, troubleshoot and release |
| Delivery | [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Timeline (§18), cut list and risk register (§19) are authoritative; §10 is the historical planning narrative |
| | [implementation/](implementation/README.md) | One gate document per phase (**authoritative** for acceptance checks) |
| | [prompts/](prompts/README.md) | One implementation prompt per task (**authoritative** for task instructions) |
| | [WORKFLOW.md](WORKFLOW.md) | How Claude Code and Antigravity share the work |
| | [decisions/](decisions/) | Architecture Decision Records |
| Submission | [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) | Verified hackathon rules and the final compliance checklist |
| | [submission/](submission/) | Devpost draft, demo storyboard, screenshot plan |
| Owner | [USER_CHECKLIST.md](USER_CHECKLIST.md) | Things only the owner can do |
| QA output | [qa/](qa/README.md) | Antigravity, design and security review reports |

Most design docs were derived from the planning blueprint written on 31 Oct 2026 and keep its section numbers (§1–§21), so cross-references stay valid.

## References
- Hackathon: [Overview](https://youcam-api-skin-ai-ecommerce.devpost.com/) · [Rules](https://youcam-api-skin-ai-ecommerce.devpost.com/rules) · [Dates](https://youcam-api-skin-ai-ecommerce.devpost.com/details/dates) · [Updates](https://youcam-api-skin-ai-ecommerce.devpost.com/updates) · [Judge-access thread](https://youcam-api-skin-ai-ecommerce.devpost.com/forum_topics/45693-judge-access-local-test-build-with-recorded-api-result-and-gated-fresh-inference) · [Perfect Corp release](https://www.perfectcorp.com/business/news/YouCam-API-Hackthon-eCommerce) · [Round-one gallery](https://youcam-api.devpost.com/project-gallery)
- YouCam docs: [Skin Analysis](https://docs.perfectcorp.com/reference/ai_skin_analysis.md) · [OpenAPI bundle](https://docs.perfectcorp.com/_bundle/reference/ai_skin_analysis.yaml) · [Quick start](https://docs.perfectcorp.com/develop/quick_start_guide.md) · [Rate limit](https://docs.perfectcorp.com/develop/rate_limit.md) · [Retention](https://docs.perfectcorp.com/develop/file_retention_period.md) · [Errors](https://docs.perfectcorp.com/develop/error_codes.md) · [FAQ](https://docs.perfectcorp.com/develop/faq.md) · [Changelog](https://docs.perfectcorp.com/release/changelog.md) · [Units](https://docs.perfectcorp.com/reference/unit_system.md) · [Task delete](https://docs.perfectcorp.com/reference/task_management.md) · [File API](https://docs.perfectcorp.com/reference/file.md)
- Claude Code: [Skills](https://code.claude.com/docs/en/skills) · [Subagents](https://code.claude.com/docs/en/sub-agents) · [Hooks](https://code.claude.com/docs/en/hooks) · [Settings](https://code.claude.com/docs/en/settings) · [Permissions](https://code.claude.com/docs/en/permissions) · [Memory & rules](https://code.claude.com/docs/en/memory)
- Antigravity: [Rules (AGENTS.md, .agents/rules)](https://antigravity.google/docs/rules)
- Market: [Perfect Corp auto product recommendation](https://www.businesswire.com/news/home/20240919987698/en/Perfect-Corp.-Introduces-Auto-Product-Recommendation-Tool-for-Skincare-Brands-and-Retailers-Powered-by-AI) · [WHO AFRO skin-bleaching fact sheet 2023](https://files.aho.afro.who.int/afahobckpcontainer/production/files/Skin_Bleaching_in_Africa_regional_fact_sheet_Nov23.pdf)
- Hosting: [Render pricing summary (third-party)](https://livemy.app/blog/render-pricing) · [Hugging Face Spaces](https://huggingface.co/docs/hub/en/spaces-overview)
