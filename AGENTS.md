# AgentForge development

- Current direction: personal use first. Validate skill value on real user tasks before a minimal native-plugin experiment; see docs/implementation-plan.md and docs/decisions/0002-personal-skill-first.md.
- Freeze expansion of the custom runtime. Do not add commands, adapters, distribution services, dependencies or general-purpose evaluation infrastructure. Evidence-backed safety fixes or blockers of an agreed real task remain maintenance work; record the reason.
- Preserve the existing runtime and safety checks as a fallback. Do not delete or weaken them merely to reduce code size.
- The user explicitly paused remote push/publication. Do not push, publish, create releases/tags or change marketplace/host configuration as part of evaluation.
- Keep real-task inputs and raw outputs under .local/skill-evals/ (gitignored). Commit only sanitized aggregate findings. Never equate synthetic examples, author review or skill discovery with real-task efficacy.
- Use Python 3.12+ and one runtime. Runtime dependencies are locked in requirements.lock.
- Preserve user files. All destructive-behavior tests must use temporary directories.
- Validate schemas with Draft202012Validator; semantic checks are additional, not substitutes.
- Run `python -m unittest discover -s tests -v` and `python -m agentforge validate` after relevant changes.
- Keep core skills host independent. Generated Codex exports are not a second authored copy.
- Do not push, publish, install user-wide skills, or enable background updates without explicit authorization.
- Record actual validation and limitations in docs/validation-report.md. Never call file discovery proof of model invocation.
