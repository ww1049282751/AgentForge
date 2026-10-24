# AgentForge development

- Use Python 3.12+ and one runtime. Runtime dependencies are locked in requirements.lock.
- Preserve user files. All destructive-behavior tests must use temporary directories.
- Validate schemas with Draft202012Validator; semantic checks are additional, not substitutes.
- Run `python -m unittest discover -s tests -v` and `python -m agentforge validate` after relevant changes.
- Keep core skills host independent. Generated Codex exports are not a second authored copy.
- Do not push, publish, install user-wide skills, or enable background updates without explicit authorization.
- Record actual validation and limitations in docs/validation-report.md. Never call file discovery proof of model invocation.
