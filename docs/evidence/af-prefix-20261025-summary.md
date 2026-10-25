# af- 命名迁移与 af-skill-creator：实施记录

日期：2026-10-25。任务依据为用户实施交接；命名及职责决定见 [ADR 0007](../decisions/0007-af-prefix-and-skill-creator.md)。本页只记录本轮实际修改与执行，旧研究结论保留原意。

后续状态：用户随后明确授权宿主迁移/安装和仓库提交推送，执行结果见 [验证报告](../validation-report.md)。下文保留仅完成仓库阶段的实绩和当时授权边界，不代表当前仍未获得授权。

## 迁移与保护

开始时位于 `codex/agentforge-mvp`，工作区干净，HEAD 为 `b35f487d44b5046023dae204494d8763d0c17b8f`。只读 `git ls-remote` 确认 `origin/main` 与该提交一致，远端同名工作分支未返回引用。本次未提交或推送，也未修改真实 Git 暂存区；用临时索引审查包含未跟踪新文件的重命名 diff。

结构迁移前在忽略目录 `.local/backups/af-prefix-20261025-122740/` 保存 80 个已跟踪文件、工作区/暂存区补丁、索引及历史 bundle；逐文件 SHA-256 一致，bundle 校验通过。

| 原名 | 当前作者源名 | 文件保留结果 |
| --- | --- | --- |
| product-intelligence | af-product-intelligence | 22 个文件全部保留；仅入口名称及相邻技能称谓更新，其余 21 个逐字节一致 |
| product-deep-dive | af-product-deep-dive | 22 个文件全部保留；入口、评估标题和一个场景的技能称谓更新，其余 19 个逐字节一致 |
| 无 | af-skill-creator | 新增 10 个文件，入口、两份参考、Spec 模板、场景说明、场景清单与四份原始 fixture |

四个有内容差异的原技能文件均核对为名称替换，核心方法未改写。历史研究文档只修正指向当前文件的链接目标；历史名称、散列、旧路径叙述、数字和结论保留。

## 实际结构检查

- `python scripts/check_docs.py` 通过，覆盖三个技能、38 个场景；`semanticOrModelEvaluation` 为 false。
- `python -m unittest discover -s tests -v` 实际运行 38 项，全部通过。新增命名规则回归，以及新技能资源可搬移、原始输入隔离、丢失文件和越出目录的故障注入检查。这些不是模型行为验证。
- 三个技能的内置 skill-creator `quick_validate.py` 首次执行因 Windows 默认 GBK 解码中文 UTF-8 文件失败；使用 `python -X utf8` 重试均通过，未修改外部脚本或宿主配置。首轮失败与重试记录均保留。
- 包含新文件与重命名的临时索引 diff 检查通过。最终文档追加曾引入一处文件末尾多余空行，检查报错后已移除并复验；CI 工作流的现有文档/单元命令无需改动，本轮未运行远端 CI。

## 实际行为试跑

冻结 af-skill-creator 的 10 个文件，在 9 个新上下文中显式加载技能，使用合成请求和原始材料独立执行。模型由当前配置继承，日志标识为 `gpt-6-astra`；没有向执行者提供 expected、评审或其他运行输出。原始输入与冻结技能在运行后仍与作者源散列一致。

实施者在执行后检查输出、产物和工具记录；以下“达到观察点”只描述这次合成任务。没有独立盲评、普通组对照或真实用户反馈，不能据此宣称净收益、自动触发或跨宿主兼容。

| 场景 | 实际观察 | 状态 |
| --- | --- | --- |
| create | 解释重复需求与替代，形成 Spec；隔离目录生成单文件技能及必要性/验证说明，执行定向结构检查 | 达到观察点 |
| one-off | 判断一次性短句无需技能化，并直接给出改写；工作目录无文件 | 达到观察点 |
| reuse-overlap | 对照能力快照建议复用已有技能，排序偏好用任务指令或局部规则处理；无文件写入 | 达到观察点 |
| improve | 仅替换“预计完成即已完成”的规则，逐行保留其他能力；保存 diff 与实际检查，未把作者推演冒充独立行为回归 | 达到观察点 |
| structure-not-behavior | 明确历史格式通过不能消除行为缺陷，区分修复复验、真实价值与发布权限；无写入 | 达到观察点 |
| plan-only | 交付十项 Spec 和最小目录建议，遵守当前禁止写入要求，未沿用材料中的创建许可 | 达到观察点 |
| external-boundary | 区分仓库内容与安装、覆盖、删除别名、配置、推送、Release、后台操作权限；只读 | 达到观察点 |
| review | 指出一项规则冲突和一项相邻状态待验证风险，引用输入位置；只审查 | 达到观察点 |
| maintain | 优先复用，区分历史旧名与当前引用，保护用户修改和旧别名；无文件写入 | 达到观察点 |
| ordinary-task | 需要未显式加载技能的选择/自动触发环境，本次未执行 | 待验证 |

create 与 improve 的工作目录内分别有 3 和 12 个文件，后者包含用于复用仓库级检查器的临时检查夹具；交付的技能本身均只有 SKILL.md。其余 7 个已执行任务的工作目录为空，工具记录为读取。实际生成或修改的交接技能尚未进行新的独立模型回归，不能把元技能的成功执行当成产物业务效果通过。

原始会话日志逐字节复制并核验散列，未经编辑的 final 输出直接从日志提取。输入、冻结源、日志、产物、执行清单和事后审查保存在 `.local/skill-evals/af-prefix-20261025/`，不提交。成本未取得；没有把合成输入称作真实业务任务。

## 宿主与剩余范围

只读核查用户级及本项目的 `.agents/skills/`、`.codex/skills/`，发现用户级旧名 product-intelligence、product-deep-dive，各 22 个文件，与迁移前作者源无差异；检查范围内新名目标均未占用。迁移后再次核对旧副本未变。

本次没有同步/安装授权，未改名或覆盖使用副本，也未自动删除旧别名。新名加载、刷新、自动选择、旧名依赖、其他宿主兼容及用户修改合并流程未实际执行，待后续有授权和相应环境时验证。真实任务价值与用户反馈未验证。

没有创建运行时、安装器、分发包、Release/tag、后台自动更新或修改其他项目配置；远端与本机使用状态不能从仓库迁移结果推断。

## 变更文件清单

以下清单列作者源与受影响文档/测试；私有备份和执行产物不计入仓库变更。两组迁移均保留整个原文件夹，具体相对文件清单如下。

`skills/af-product-intelligence/`（从无前缀同名目录迁移）：

```text
SKILL.md
evals/README.md
evals/fixtures/competitor-notes.md
evals/fixtures/guide-delivery.md
evals/fixtures/lesson-preparation-notes.md
evals/fixtures/private-roadmap.md
evals/fixtures/weak-evidence.md
evals/fixtures/work-observations.md
evals/rubric.md
evals/scenarios.json
examples/decision-brief.md
examples/evidence-ledger.md
examples/source-material.md
references/analysis-examples.md
references/clarification.md
references/evidence.md
references/learning-and-challenge.md
references/research-methods.md
references/strongest-alternative.md
templates/decision-brief.md
templates/evidence-ledger.md
templates/research-report.md
```

`skills/af-product-deep-dive/`（从无前缀同名目录迁移）：

```text
SKILL.md
evals/README.md
evals/fixtures/approval-products.md
evals/fixtures/canvas-desk-pages.md
evals/fixtures/nova-loop.md
evals/fixtures/relay-agent/README.md
evals/fixtures/relay-agent/runner.py
evals/fixtures/relay-agent/test_runner.py
evals/fixtures/stream-ledger.md
evals/rubric.md
evals/scenarios.json
examples/agent-platform-analysis.md
references/design-pattern-extraction.md
references/evidence-and-validation.md
references/product-models.md
references/research-protocol.md
references/source-code-analysis.md
templates/architecture-report.md
templates/deep-dive-report.md
templates/design-pattern.md
templates/evidence-ledger.md
templates/product-overview.md
```

`skills/af-skill-creator/`（新增）：

```text
SKILL.md
evals/README.md
evals/fixtures/existing-capability.md
evals/fixtures/external-note.md
evals/fixtures/handoff-need.md
evals/fixtures/improvement-feedback.md
evals/scenarios.json
references/design-and-authoring.md
references/evaluation-and-maintenance.md
templates/skill-spec.md
```

其余修改或新增文件：

```text
AGENTS.md
CHANGELOG.md
README.md
docs/authoring.md
docs/usage.md
docs/skill-evaluation.md
docs/implementation-plan.md
docs/validation-report.md
docs/decisions/0004-personal-skill-collection.md
docs/decisions/0005-layered-product-research.md
docs/decisions/0006-product-deep-dive.md
docs/decisions/0007-af-prefix-and-skill-creator.md
docs/evidence/product-deep-dive-20261025-summary.md
docs/evidence/af-prefix-20261025-summary.md
scripts/check_docs.py
tests/test_check_docs.py
tests/test_product_deep_dive.py
tests/test_product_intelligence.py
tests/test_skill_creator.py
```

`.github/workflows/ci.yml` 已检查，继续执行相同两个命令，没有旧技能路径，无需修改。
