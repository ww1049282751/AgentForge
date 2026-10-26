# AgentForge

供个人日常工作使用的技能集合。每个技能独立放在 `skills/<name>/`，围绕真实任务持续改进指令、分析方法和参考材料。

## 技能目录

| 技能 | 用途 | 入口 |
| --- | --- | --- |
| af-product-intelligence | 产品方向探索、需求挖掘、竞品与机制分析、专业视角评审和认知补齐 | [SKILL.md](skills/af-product-intelligence/SKILL.md) |
| af-product-deep-dive | 具体产品深度剖析、工作流与机制还原、源码和架构追踪、设计取舍及候选模式提取 | [SKILL.md](skills/af-product-deep-dive/SKILL.md) |
| af-skill-creator | 技能化必要性判断、Skill Spec、创建、改进、审查、评估与维护 | [SKILL.md](skills/af-skill-creator/SKILL.md) |
| af-architecture-design | 软件架构设计、评审、技术选型、关键流程细化、兼容演进与验证计划 | [SKILL.md](skills/af-architecture-design/SKILL.md) |
| af-ui-design | 产品界面设计、改进与评审，涵盖视觉、交互状态、项目继承和实际观察 | [SKILL.md](skills/af-ui-design/SKILL.md) |

研究“这个产品如何工作、实现和取舍”优先选 af-product-deep-dive；研究“需求机会、方向或哪个方案适合我”优先选 af-product-intelligence。两者独立可用，混合任务复用有来源与边界的研究成果，不自动跨技能调度。职责依据见 [ADR 0006](docs/decisions/0006-product-deep-dive.md)。

af-product-deep-dive 按请求选择快速扫描、深度剖析、技术逆向或专项研究，详细方法按需加载。E1–E5 区分实际观察、实现证据、来源陈述、推断和假设；源码分析落到调用链与状态变化。提供模板、合成示范及五类正例和两类负例；实际检查与试跑范围见 [验证记录](docs/validation-report.md)，不把场景存在当作效果证明。

af-product-intelligence 保留问题重构、需求取证、机制迁移和 [分析正反例](skills/af-product-intelligence/references/analysis-examples.md)，以及 [最强替代方案验证](skills/af-product-intelligence/references/strongest-alternative.md) 与 [认知增量和反证](skills/af-product-intelligence/references/learning-and-challenge.md)：沿同一任务检验替代，以真实输入为基准追踪证据、判断与选择变化。简单问题直接回答，复杂研究允许回退；这些方法尚未证明稳定增加真实使用价值。

[此前的行为试跑](docs/evidence/behavior-round-20261025-summary.md) 实际执行合成离线任务并据此修正研究范围偏移；该轮未覆盖联网竞品研究、真实用户收益或自动触发。

[真实项目联网对照](docs/evidence/online-ab-20261025-summary.md) 已比较普通组与显式技能组：首轮三个重点维度均相近，没有证明明显净提升；根据观察进一步校准认知增量与现有替代方案的分析。公开资料研究不等于产品实测或真实用户效果验证。

af-skill-creator 在创建前比较复用与更简单的替代；按任务选择工作模式和必要资源，区分结构、行为、对照和真实任务价值验证。它独立使用，不要求两个产品技能存在，也不负责安装或发布。命名与边界见 [ADR 0007](docs/decisions/0007-af-prefix-and-skill-creator.md)。

## 使用

AF Next 第一阶段保持五个技能和独立入口，通过 [能力分流](docs/authoring.md)、[按需证据交接](docs/usage.md) 与 [既有质量协议](docs/skill-evaluation.md) 改进维护判断。治理取舍见 [ADR 0010](docs/decisions/0010-af-next-governance.md)，本轮实施、实际评估与未验证项见 [阶段证据](docs/evidence/af-next-phase1-summary.md)；文档治理完成不表示技能净收益已证明。

[Phase 2 对照与准入](docs/evidence/af-next-phase2-summary.md) 保留普通 Agent、既有技能及短提示的实际比较：本轮没有 trial-ready 候选，未增加技能；真实用户收益仍待验证。
[Phase 3 准入复核](docs/evidence/af-next-phase3-summary.md) 因证据不足而选择零试制，保留简单替代和重新准入条件，不建立占位技能。
[Phase 4 恢复对照](docs/evidence/af-next-phase4-summary.md) 在离线副本实际复现并修复状态重放，两种交接核心结果相同；保留知识失效与测试边界，不宣称真实用户或多 Agent 效率收益。

2026-10-26 经后续明确授权完成 [AF Next 用户副本同步](docs/evidence/af-next-sync-20261026-summary.md)：五个技能的 86 个文件与作者源一致，同版宿主加载器识别通过；现有桌面会话刷新与自动触发未实测。

af-ui-design 将既定任务与工程约束转为界面和交互，按 design / improve / review 工作；不接管方向研究、后端架构或技能建设。已有设计系统优先继承，小问题直接回答。2026-10-25 后续明确授权后，已备份并安装到用户级 `.agents/skills/af-ui-design/`：14 个文件及散列一致、8 条内部链接有效，同版加载器识别启用且无错误；桌面 UI/当前会话刷新与自动触发未实测。可用 `$af-ui-design`，也可显式读取作者源，例如“读取 `skills/af-ui-design/SKILL.md`，只评审这张截图，区分可见问题与待验证行为”。职责见 [ADR 0009](docs/decisions/0009-ui-design.md)，结构、模型试跑、对照与真实价值分别见 [实施报告](docs/evidence/ui-design-20261025-summary.md)，安装不改变行为效果的结论。

af-architecture-design 面向正向设计：把业务约束落到模块、接口、数据所有权、异常路径与可验证决策。按任务选择 design、review、selection、deep-design、evolution、validation；简单问题直接回答。它与产品方向研究、现有机制逆向及技能建设各自独立，不自动跨技能调用。职责取舍见 [ADR 0008](docs/decisions/0008-architecture-design.md)，实际验收范围见 [试跑摘要](skills/af-architecture-design/evals/results-20261025.md)。后续明确授权后，已备份并安装到用户级 `.agents/skills/af-architecture-design/`：18 个文件及散列一致、14 条内部链接有效，同版加载器在项目和用户目录均识别启用且无错误。可使用 `$af-architecture-design`；桌面 UI/当前会话刷新与自动触发未实测。以下三个技能的历史使用副本记录保留原范围。

仓库作者源和本机用户级 `.agents/skills/` 已统一使用 `$af-product-deep-dive`、`$af-product-intelligence` 和 `$af-skill-creator`。2026-10-25，按质量闭环后续同步授权，备份并保护本地内容后更新 5 个技能文件；三个完整副本共 54 个文件，清单与 SHA-256 均匹配本轮作者源，64 条内部链接有效。同版宿主加载器在项目和用户目录均识别三个技能、显示启用且无错误；桌面 UI/当前会话刷新和自动触发未实测。详见 [使用说明](docs/usage.md) 和 [验证记录](docs/validation-report.md)。

在支持读取指令文件的助手中，明确指定本仓库所选技能的 `SKILL.md`，同时说明任务和已有材料。例如：“使用 `skills/af-product-deep-dive/SKILL.md`，研究这个项目从任务提交到失败恢复的调用链，区分源码结论和实际验证。”

需要复制到某个宿主时，以该宿主支持的目录为准，先检查已有副本；仓库不提供安装器或自动同步。具体边界见 [使用说明](docs/usage.md)。

## 组织方式

```text
skills/<name>/
  SKILL.md             技能入口
  references/          按需读取的方法与参考材料
  templates/           可复用输出模板
  examples/            明确标注的演示材料
  evals/               行为场景与评价依据
docs/
  decisions/           重要决定及被替代的历史路线
  evidence/            脱敏研究结果与历史证据
scripts/check_docs.py   轻量格式与引用检查
tests/                 检查器回归与技能专属材料检查
.local/                私有任务材料与备份，不提交
```

除 `SKILL.md` 外的目录均按实际需要创建。技能目录是唯一编写源；不维护插件包装、包元数据或发布版本锁。

## 维护与检查

[AF Skill Quality Loop](docs/skill-evaluation.md) 是全仓库统一评估协议：从具体问题与假设出发，冻结基线后定向修改，执行对照与回归，再决定保留、继续修改、回滚或待验证。各技能保留专业量表；结构、行为、对照和真实价值分别判定，修改或分数提高不能代替价值证据。改进记录模板复用同一文档，不新增评估平台。

所有新技能必须使用 `af-` 前缀，frontmatter 的 `name` 与目录名完全一致。新增或改进技能见 [编写说明](docs/authoring.md)，实际使用反馈见 [评估方法](docs/skill-evaluation.md)。运行轻量检查：

```powershell
python scripts/check_docs.py
python -m unittest discover -s tests -v
```

只需 Python 3.12+ 标准库，无需安装依赖。通用检查核对技能名称/简介、常见行内文件链接及行为场景输入；技能专属材料的约束放在相应测试中，不要求其他技能提供同样格式。测试不代表语义、模型行为或实际效果验证通过。

研究原始材料放在 `.local/skill-evals/`，可提交的只有脱敏结论。远端同步按用户明确授权执行；发布版本、创建 Release/tag 和后台更新仍需单独授权。

## 当前状态

仓库已按 [个人技能集合决定](docs/decisions/0004-personal-skill-collection.md) 移除安装器体系，保留技能、研究材料和历史证据。af- 命名与此前宿主迁移记录保留；本轮完善统一质量闭环，实际检查及未执行项见验证记录，未证明三个技能的行为或真实价值已经改善。旧技能副本、安装器的本地状态与构建产物保留在忽略的备份中。

[维护规则](AGENTS.md) · [当前路线](docs/implementation-plan.md) · [验证记录](docs/validation-report.md)
