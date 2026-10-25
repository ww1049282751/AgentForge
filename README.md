# AgentForge

供个人日常工作使用的技能集合。每个技能独立放在 `skills/<name>/`，围绕真实任务持续改进指令、分析方法和参考材料。

## 技能目录

| 技能 | 用途 | 入口 |
| --- | --- | --- |
| product-intelligence | 产品方向探索、需求挖掘、竞品与机制分析、专业视角评审和认知补齐 | [SKILL.md](skills/product-intelligence/SKILL.md) |

当前产品研究技能保留一个入口，按任务选择深度与参考资源。已有问题重构、需求取证、机制迁移和 [分析正反例](skills/product-intelligence/references/analysis-examples.md)，新增 [最强替代方案验证](skills/product-intelligence/references/strongest-alternative.md) 与 [认知增量和反证](skills/product-intelligence/references/learning-and-challenge.md)：沿同一任务检验替代，以真实输入为基准追踪证据、判断与选择变化。简单问题直接回答，复杂研究允许回退；这些方法尚未证明稳定增加真实使用价值。

[此前的行为试跑](docs/evidence/behavior-round-20261025-summary.md) 实际执行合成离线任务并据此修正研究范围偏移；该轮未覆盖联网竞品研究、真实用户收益或自动触发。

[真实项目联网对照](docs/evidence/online-ab-20261025-summary.md) 已比较普通组与显式技能组：首轮三个重点维度均相近，没有证明明显净提升；根据观察进一步校准认知增量与现有替代方案的分析。公开资料研究不等于产品实测或真实用户效果验证。

## 使用

本机个人使用统一选择 `$product-intelligence`。2026-10-25 按用户后续授权，分层研究修改已同步到用户级完整使用副本，22 个文件与作者源的清单和 SHA-256 一致；同步前已备份旧副本与仓库未提交改动。旧的项目级 `$af-product-intelligence` 别名仍保留在备份中。

在其他支持读取指令文件的助手中，可以明确指定本仓库的 `skills/product-intelligence/SKILL.md`，同时说明任务和已有材料。

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

新增或改进技能见 [编写说明](docs/authoring.md)，实际使用反馈见 [评估方法](docs/skill-evaluation.md)。运行轻量检查：

```powershell
python scripts/check_docs.py
python -m unittest discover -s tests -v
```

只需 Python 3.12+ 标准库，无需安装依赖。通用检查核对技能名称/简介、常见行内文件链接及行为场景输入；技能专属材料的约束放在相应测试中，不要求其他技能提供同样格式。测试不代表语义、模型行为或实际效果验证通过。

研究原始材料放在 `.local/skill-evals/`，可提交的只有脱敏结论。远端同步按用户明确授权执行；发布版本、创建 Release/tag 和后台更新仍需单独授权。

## 当前状态

仓库已按 [个人技能集合决定](docs/decisions/0004-personal-skill-collection.md) 移除安装器体系，保留技能、研究材料和历史证据。按用户后续授权统一个人入口并同步完整技能；使用副本不会随源码编辑自动更新。安装器的本地状态与构建产物保留在忽略的备份中。

[维护规则](AGENTS.md) · [当前路线](docs/implementation-plan.md) · [验证记录](docs/validation-report.md)
