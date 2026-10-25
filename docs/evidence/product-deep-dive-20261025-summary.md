# product-deep-dive：实施与验证记录

日期：2026-10-25。范围：新增个人技能作者源及必要维护材料。开始时工作区干净，基线提交为 `eb807ec9c60aac4d7600852f1f2ea3cea5a7fad7`。原始任务、冻结技能、独立回答、执行日志与审查保存在忽略目录 `.local/skill-evals/product-deep-dive-20261025/`，不提交。

## 新增文件与职责

技能内共 22 个文件；不创建占位目录、包元数据、安装器或通用运行时。

| 文件 | 职责 |
| --- | --- |
| [SKILL.md](../../skills/af-product-deep-dive/SKILL.md) | 四种研究模式、资源选择、证据边界、交付与停止 |
| [research-protocol.md](../../skills/af-product-deep-dive/references/research-protocol.md) | 研究范围、问题/假设、区分证据、优先级、回退和停止 |
| [product-models.md](../../skills/af-product-deep-dive/references/product-models.md) | 用户任务、核心对象、业务状态和可观察交互 |
| [source-code-analysis.md](../../skills/af-product-deep-dive/references/source-code-analysis.md) | 入口、调用链、数据与控制流、架构取舍、错误和恢复、局部实验 |
| [evidence-and-validation.md](../../skills/af-product-deep-dive/references/evidence-and-validation.md) | E1–E5、引用与版本、冲突来源、实测和推断边界 |
| [design-pattern-extraction.md](../../skills/af-product-deep-dive/references/design-pattern-extraction.md) | 从机制提炼候选模式、条件、代价、反例和授权保存 |
| [product-overview.md](../../skills/af-product-deep-dive/templates/product-overview.md) | 快速扫描的可选输出提示 |
| [deep-dive-report.md](../../skills/af-product-deep-dive/templates/deep-dive-report.md) | 产品、业务、体验与实现的按需报告模块 |
| [architecture-report.md](../../skills/af-product-deep-dive/templates/architecture-report.md) | 技术链路、验证范围与设计取舍 |
| [evidence-ledger.md](../../skills/af-product-deep-dive/templates/evidence-ledger.md) | 重要主张与具体来源、范围、冲突及待验事项 |
| [design-pattern.md](../../skills/af-product-deep-dive/templates/design-pattern.md) | 候选模式的来源、机制、条件、失败与修订记录 |
| [agent-platform-analysis.md](../../skills/af-product-deep-dive/examples/agent-platform-analysis.md) | 明确标记的合成方法示范，不是试跑结果 |
| [evals/README.md](../../skills/af-product-deep-dive/evals/README.md)、[scenarios.json](../../skills/af-product-deep-dive/evals/scenarios.json)、[rubric.md](../../skills/af-product-deep-dive/evals/rubric.md) | 执行隔离、七个场景和事后 0–2 分量表 |
| [relay-agent/README.md](../../skills/af-product-deep-dive/evals/fixtures/relay-agent/README.md)、[runner.py](../../skills/af-product-deep-dive/evals/fixtures/relay-agent/runner.py)、[test_runner.py](../../skills/af-product-deep-dive/evals/fixtures/relay-agent/test_runner.py) | 合成 Agent 原始说明、可执行源码与已有局部测试 |
| [canvas-desk-pages.md](../../skills/af-product-deep-dive/evals/fixtures/canvas-desk-pages.md) | 仅页面的合成 SaaS 输入，含权限冲突和材料指令 |
| [stream-ledger.md](../../skills/af-product-deep-dive/evals/fixtures/stream-ledger.md) | 合成基础设施接口、数据流与恢复线索 |
| [approval-products.md](../../skills/af-product-deep-dive/evals/fixtures/approval-products.md) | 两种审批机制的合成比较输入 |
| [nova-loop.md](../../skills/af-product-deep-dive/evals/fixtures/nova-loop.md) | 无源码、无可核查原文的薄弱线索 |

另外新增 [专属材料测试](../../tests/test_product_deep_dive.py) 与 [ADR 0006](../decisions/0006-product-deep-dive.md)。测试检查完整技能复制后的资源可用性和执行输入不含评分/示范答案，不判断模型研究质量。

## 研究行为设计

入口按用户问题选择快速扫描、深度剖析、技术逆向或专项研究，不要求填表。先建立产品模型，再优先取能区分解释、改变结论的证据；模式扩展需说明理由。详细交互方法并入产品模型，技术架构并入源码分析，避免同一流程重复维护。

E1 是实际观察，E2 是实现证据，E3 是一手资料陈述，E4 是推断，E5 是待验证假设；类别不是质量排名。源码研究沿入口/调用者/配置追踪状态和数据，明确逻辑存在、路径可达、测试通过、运行观察和生产启用不能互相代替。

模式记录保留来源、版本、机制、必要条件、收益/代价、反例与未知；默认是候选知识。没有用户需要不强制迁移到其项目，没有授权不写全局知识库。

## 实际验证的口径

采用 skill-creator 建议的独立试跑：源码与页面任务分别使用新的、不继承主对话的执行上下文，显式加载冻结技能。执行者只获得请求、原始输入与相关技能资源，没有接收 expected、量表、示范答案或另一组输出。技能快照与作者源 22 个文件散列一致；该快照供本轮两个任务使用。

两个试跑均为合成离线输入上的实际模型执行；源码任务另运行了本地代码。它们不是公开真实产品研究，也不是普通组/技能组效果对照。模型精确版本、token 和费用不可得，记录为未知；没有宿主自动触发验证。输出由实施者按量表审查，不能称独立盲评。

## 实际检查与试跑结果

| 检查 | 本次结果及范围 |
| --- | --- |
| `python scripts/check_docs.py` | 通过；两个技能、合计 28 个场景的基础格式/输入路径和常见本地链接可解析，不核验联网来源或模型质量 |
| `python -m unittest discover -s tests -v` | 28 项通过，包含新增两项材料检查；所有会修改文件的测试使用临时目录 |
| skill-creator `quick_validate.py` | 两个技能入口均通过；本机使用 `python -X utf8`，未改变宿主配置 |
| `git diff --check` | 通过；没有用静态检查替代行为试跑 |
| 冻结快照与保留核对 | 新技能 22 个文件与执行快照一致；原有 35 个方法/材料/历史证据文件不变，product-intelligence 入口是唯一有意调整项 |

**源码任务 source-agent：** 实际读取冻结入口、源码分析、证据规则和架构模板四份资源。报告追到 `Store.create → run_task → execute → Store.save`，区分预设 plan 与真正模型规划、步骤索引与任务状态、再次调用与自动恢复。原样副本上的 3 个已有测试通过；另外 7 个定向实验的断言通过，覆盖部分失败续跑、副作用后异常、真实子进程退出、结果无法序列化、最终状态保存失败、错误记录保存失败和确定性重入交错。

实验复现了“副作用发生但进度未保存”后的重复执行；也确认最终状态保存失败时，已经提交的步骤不必重放。通过表示观察符合实验断言，多项断言专门复现限制，不表示可靠性目标达到。重入实验不是线程/跨进程压力测试，进程退出也不是断电耐久实验。报告明确区分实现、路径、实际测试与生产未知，未修改原始源码输入或为样本补修实现。

**页面任务 public-saas：** 实际读取冻结入口、研究协议、产品模型、证据规则和深度模板五份资源。报告沿 CSV 映射、预览排除、任务执行、部分失败、失败行重试和共享审阅还原流程；明确“外部编号匹配”不足以证明幂等，并保留角色指南与 FAQ 的编辑权限冲突。没有从排队/恢复文案编造数据库、队列或后台架构，没有登录、联网或真实产品操作，也未执行页面夹带的上传指令。

实施者审查两份未经改写的输出与源码/页面输入、实际实验日志：在适用维度达到本轮场景观察点，未发现上述硬性失败。源码 10 项适用维度均记 2，页面任务 9 项适用维度均记 2、源码实现可追溯记 N/A；分项理由与原文定位留在本地审查记录。分数只描述这两个刻意构造的小样本，不构成全面验收、净提升或真实价值证明。本轮未发现需据此修改技能的实质行为错误，因此未为凑迭代增加规则或重复执行。

## 维护文档与保留范围

README 增加技能目录、入口选择和本次未安装状态；使用说明提供作者源调用示例；路线记录能力与未覆盖项；AGENTS 及 ADR 澄清两个技能的边界。product-intelligence 仅调整 description 和边界说明，其余方法、模板、场景、示例和已有研究结论保持原样。authoring 与 skill-evaluation 的通用规范已足够，本次不修改。

对照开始时保存的 36 个文件散列，35 个文件保持不变，唯一变化是有意调整的 product-intelligence/SKILL.md。历史证据原文保留。此前个人副本同步记录仍表示当时状态，不改写为本次同步。

此次变更保留在工作区，未提交、推送、发布、创建 Release/tag、安装/覆盖用户级副本、改变宿主配置或启用后台任务。后续真实任务、联网/交互研究、复杂基础设施/双产品/薄弱证据场景、负例自动触发、用户反馈与净收益仍未验证。

后续用户已明确授权备份后全局安装、同步并提交推送，执行记录追加到 [验证报告](../validation-report.md)。上段为新增技能交付时的历史状态，后续安装与远端同步不会使未覆盖的行为自动变成已验证。
