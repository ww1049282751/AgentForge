# AgentForge

供个人日常工作使用的技能集合。每个技能独立放在 `skills/<name>/`，围绕真实任务持续改进指令、分析方法和参考材料。

## 技能目录

| 技能 | 用途 | 入口 |
| --- | --- | --- |
| af-product-intelligence | 产品方向探索、需求挖掘、竞品与机制分析、专业视角评审和认知补齐 | [SKILL.md](skills/af-product-intelligence/SKILL.md) |
| af-product-deep-dive | 具体产品深度剖析、工作流与机制还原、源码和架构追踪、设计取舍及候选模式提取 | [SKILL.md](skills/af-product-deep-dive/SKILL.md) |
| af-skill-creator | 技能化必要性判断、Skill Spec、创建、改进、审查、评估与维护 | [SKILL.md](skills/af-skill-creator/SKILL.md) |

研究“这个产品如何工作、实现和取舍”优先选 af-product-deep-dive；研究“需求机会、方向或哪个方案适合我”优先选 af-product-intelligence。两者独立可用，混合任务复用有来源与边界的研究成果，不自动跨技能调度。职责依据见 [ADR 0006](docs/decisions/0006-product-deep-dive.md)。

af-product-deep-dive 按请求选择快速扫描、深度剖析、技术逆向或专项研究，详细方法按需加载。E1–E5 区分实际观察、实现证据、来源陈述、推断和假设；源码分析落到调用链与状态变化。提供模板、合成示范及五类正例和两类负例；实际检查与试跑范围见 [验证记录](docs/validation-report.md)，不把场景存在当作效果证明。

af-product-intelligence 保留问题重构、需求取证、机制迁移和 [分析正反例](skills/af-product-intelligence/references/analysis-examples.md)，以及 [最强替代方案验证](skills/af-product-intelligence/references/strongest-alternative.md) 与 [认知增量和反证](skills/af-product-intelligence/references/learning-and-challenge.md)：沿同一任务检验替代，以真实输入为基准追踪证据、判断与选择变化。简单问题直接回答，复杂研究允许回退；这些方法尚未证明稳定增加真实使用价值。

[此前的行为试跑](docs/evidence/behavior-round-20261025-summary.md) 实际执行合成离线任务并据此修正研究范围偏移；该轮未覆盖联网竞品研究、真实用户收益或自动触发。

[真实项目联网对照](docs/evidence/online-ab-20261025-summary.md) 已比较普通组与显式技能组：首轮三个重点维度均相近，没有证明明显净提升；根据观察进一步校准认知增量与现有替代方案的分析。公开资料研究不等于产品实测或真实用户效果验证。

af-skill-creator 在创建前比较复用与更简单的替代；按任务选择工作模式和必要资源，区分结构、行为和真实价值验证。它独立使用，不要求两个产品技能存在，也不负责安装或发布。命名与边界见 [ADR 0007](docs/decisions/0007-af-prefix-and-skill-creator.md)。

## 使用

仓库作者源和本机用户级 `.agents/skills/` 已统一使用 `$af-product-deep-dive`、`$af-product-intelligence` 和 `$af-skill-creator`。2026-10-25 按用户后续明确授权，先备份原副本及仓库改动，再迁移/安装；三个副本共 54 个文件，清单与 SHA-256 均匹配作者源。同版宿主加载器在项目及用户目录均识别三个新名、显示启用且无错误；桌面 UI 刷新和自动触发未实测。详见 [使用说明](docs/usage.md) 和 [本轮验证](docs/validation-report.md)。

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

所有新技能必须使用 `af-` 前缀，frontmatter 的 `name` 与目录名完全一致。新增或改进技能见 [编写说明](docs/authoring.md)，实际使用反馈见 [评估方法](docs/skill-evaluation.md)。运行轻量检查：

```powershell
python scripts/check_docs.py
python -m unittest discover -s tests -v
```

只需 Python 3.12+ 标准库，无需安装依赖。通用检查核对技能名称/简介、常见行内文件链接及行为场景输入；技能专属材料的约束放在相应测试中，不要求其他技能提供同样格式。测试不代表语义、模型行为或实际效果验证通过。

研究原始材料放在 `.local/skill-evals/`，可提交的只有脱敏结论。远端同步按用户明确授权执行；发布版本、创建 Release/tag 和后台更新仍需单独授权。

## 当前状态

仓库已按 [个人技能集合决定](docs/decisions/0004-personal-skill-collection.md) 移除安装器体系，保留技能、研究材料和历史证据。本次统一两个作者源的 af- 命名并新增 af-skill-creator，按后续授权完成宿主副本迁移/安装，仓库提交推送结果见验证记录。旧技能副本、安装器的本地状态与构建产物保留在忽略的备份中。

[维护规则](AGENTS.md) · [当前路线](docs/implementation-plan.md) · [验证记录](docs/validation-report.md)
