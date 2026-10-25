# af-architecture-design：实施与验收记录

日期：2026-10-25。执行 ID：architecture-design。下述实施验收保留初始交付时的范围与状态；后续安装与交付记录单列在文末。依据用户两份交接材料、当前仓库规则和 [AF Skill Quality Loop](../skill-evaluation.md)。仅保存脱敏结论；全部输入是合成场景，不是真实项目样本。

## 实现与取舍

在唯一作者源新增 [af-architecture-design](../../skills/af-architecture-design/SKILL.md)，支持 design、review、selection、deep-design、evolution、validation。既有三技能面向产品方向、现有机制还原与技能建设；本技能填补正向架构决策的独立缺口。轻量 Skill Spec、一次性提示/扩展既有技能的替代比较与维护条件见 [ADR 0008](../decisions/0008-architecture-design.md)。

入口负责范围、模式、关键判断和停止条件；四份方法按需加载，模板可以裁剪。重要决定说明需求、最强可行替代、代价、验证与重评条件。模块、接口、数据所有权、异常及迁移边界应足以指导下一步，而不把图、技术名词或精确但无依据的数字当质量证据。

没有新增运行时、安装器、平台、插件包装、版本锁或自动同步；没有强制所有任务生成全套文档。新技能未安装到宿主，也未改写三个既有技能的正文、资源、场景或量表。

## 文件清单与用途

| 新增/修改 | 文件与用途 |
| --- | --- |
| 新增入口 | `skills/af-architecture-design/SKILL.md`：六模式、决策原则、证据与操作边界 |
| 新增方法 | `references/architecture-decision-method.md`、`system-decomposition.md`、`quality-attributes.md`、`architecture-validation.md`：候选比较、关键机制、质量目标、评审/演进/验证 |
| 新增模板与示例 | `templates/architecture-proposal.md`、`adr.md`；`examples/modular-monolith-design.md`：可选提案/决策记录及明确合成的实施示范 |
| 新增评估 | `evals/README.md`、`scenarios.json`、`rubric.md`、`results-20261025.md`；六份 fixtures 为 new-system、proposed-export、reliable-job、small-admin、migration、external-note |
| 新增材料回归 | `tests/test_architecture_design.py`：复用已有验证函数检查完整复制与原始输入路径；不测试模型行为，不改变通用检查器 |
| 新增仓库记录 | 本文件与 `docs/decisions/0008-architecture-design.md`：实施证据、职责取舍和轻量规格 |
| 更新现行入口 | `AGENTS.md`、`README.md`、`docs/usage.md`、`docs/authoring.md`、`docs/implementation-plan.md`、`docs/skill-evaluation.md`、`docs/validation-report.md`：技能清单、使用边界、专业评估入口及实际结果 |

共新增 21 个文件（其中技能内 18 个），修改 7 个现有文档。`docs/evidence/skill-creator-ab-20261025-summary.md` 与验证报告中的对应章节来自并行任务，保留其内容，不计入本任务新增清单或模型结果。

## 基线、条件与实际试跑

开始时工作区干净，分支 `codex/agentforge-mvp`，HEAD 为 `e67ed579dd952b709740bb5ad5be7ec38773ee81`。修改前冻结 93 个仓库文件及 SHA-256，实际运行文档检查通过（3 技能、73 Markdown、219 本地链接、38 场景），38 项单元测试通过。这是内容/结构基线；没有旧架构技能或旧行为输出，不构成改善对照。

冻结 17 个候选技能文件（尚不含事后结果索引），每例使用 `fork_turns=none` 新上下文显式读取入口及按需方法，执行者只收到 request、原始输入和操作范围，不提供 expected、量表、示例答案或另一例输出。全部 14 例实际执行并保存未经编辑的回答与执行元数据；六类核心及补充覆盖见 [场景级结果](../../skills/af-architecture-design/evals/results-20261025.md)。

执行方式是独立子代理、合成离线材料、会话/指定隔离目录交付；没有实际应用运行环境。未覆盖联网技术选型或真实系统。可核实的时间、读取路径与 SHA-256 记入元数据；精确模型构建、推理/采样设置、token 和费用不可得，记未知。宿主仍提供共同的技能简介环境，这不是“完全没有技能元信息”的模型条件。

执行完整性核对取得 14 份原始回答，63 个有效声明散列全部一致；另存每份原回答散列。散列和动作自述不能证明操作系统强制隔离或工具日志完备，不宣称双盲。architecture-review 的元数据最初把“被委派”误写为可见父级分析；执行者另写更正，确认未见父级分析/预期，原记录保留。实际调度参数为 `fork_turns=none`。

## 行为、质量与修正

六类核心与补充八例均已由两位未参与编写或执行的审查者按冻结 expected、十维量表与硬门槛逐项审查，14 例均为 `accepted`，范围仅为本次合成输出内容与行为，没有未处理硬失败或阻断项。评分只作分项诊断，不合并总分；N/A 注明原因，未知不计为零。详细逐项依据保存在 `reviews/core-review.*` 与 `reviews/boundary-review.*`。

信息不足场景的技术机制维度为 1：评论去重虽写了事务，但还需明确并发操作键的唯一约束或等效原子保护。该题仅要求整体条件方案，因此此建议不阻断本次接受；实施前须补齐，不能把事务本身等同去重保障。原回答与这一局限均保留。未把本题升级为完整 deep-design 或再加全局强制流程，因为技能方法已有具体原子去重规则，也没有证据支持普遍扩大任务范围。

独立实现审查发现一项非阻断的示例歧义：审批接口未定义幂等结果重放，但故障测试要求重放原结果。已补充审批操作键、同键载荷校验、原结果重放与状态/占用/结果的原子保存，并把测试明确限定为审批事务。审查者复核后确认修复，首轮发现和冻结旧示例保留。

14 例执行者均未声明读取 examples，因此本轮行为证据对应原冻结入口、references、templates 与输入/标准；这些文件没有变。最终只有示例相对候选修改，新增结果索引不冒充试跑输入。修正后的示例完成源码复核，未做独立模型试跑或应用测试；不把源码复核当行为复验。

## 结构、回归与集成

示例修正后实际运行：`python scripts/check_docs.py` 通过（4 个技能、93 份 Markdown、253 条本地链接、52 个场景）；`python -m unittest discover -s tests -v` 的 40 项通过；`git diff --check` 退出 0、无空白错误，仅提示 AGENTS.md 将按 Git 设置规范化换行。以上统计针对当时完整工作树，包含并行任务新增的报告，不全归因于本任务。没有失败测试、没有弱化或删除旧测试，通用检查器、原测试及 CI 未修改。原始输出保存为 `docs-check-final.txt`、`unit-tests-final.txt`、`diff-check-final.txt`；结果文档补齐后的复核另存 delivery 日志。

三个既有技能共 54 个文件与基线清单/散列一致。76 个既有技能/脚本/测试/CI/历史证据文件在保护范围内无本任务改动；并行任务新增的报告不在旧清单中。既有 38 个模型场景本轮 `not-run`：本次未改它们，不把材料保留或单元测试升级为模型行为回归通过。新技能的职责负例另有本轮实际试跑。

独立实现审查当前无未解决发现；主任务已核对场景级判定、实现版本及结构结果的对应关系。实现、结构和上述 14 次合成行为/产物质量在明确范围内 `accepted`，可以进入用户验收；这不是代替用户作最终批准。原始历史报告保持其日期与结论；并行工作对验证报告的新增内容已保护，未覆盖。

## 证据位置、限制与后续

本地证据根为 `.local/skill-evals/2026-10-25/architecture-design/`：`baseline*`、`candidate*` 定位内容；`runs/<id>/request.json`、fixtures、`response.md`、`metadata.json` 保存各例输入/未经编辑输出/加载记录；`reviews/` 保存独立内容及实现审查；`execution-integrity.json`、`example-fix.json` 与检查日志保存完整性、修正和执行证据。原始材料与详细审查未放入公开仓库。

| 项目 | 状态与限制 |
| --- | --- |
| 普通回答/有无技能对照 | `not-run`；没有可比基线，不能宣称 improved 或稳定净增益 |
| 真实任务价值与用户反馈 | `not-run`；尚未证明决策质量、实施效率或再使用意愿提升 |
| 宿主加载、自动触发、其他宿主兼容 | `not-run`；只验证作者源与显式代理读取，未安装副本 |
| 应用测试、性能、恢复与迁移实测 | `not-run`；模型产物中的测试均是计划，无法据此宣称生产正确性 |
| 修正后示例的模型行为 | `not-run`；已有源码复核，不扩大到试跑未加载的资源 |

建议下一次选一个真实项目，保存原需求、设计前判断与真实约束，按相同条件比较普通回答/技能回答，并记录后续实施返工、决策帮助和额外核查负担。没有这些证据前，保留当前技能供用户验收，不宣称真实价值已通过。本轮未提交、未推送、未安装、未改宿主配置或启用后台任务；已有历史授权不扩展到本次。

## 后续明确授权：安装与交付

2026-10-25，用户随后明确授权先备份、安装用户级副本、核对内容及宿主加载，再提交推送本次相关变更，并保护并行任务修改。本段记录新阶段，不追改上面的初始执行状态，也不扩大为自动更新授权。

安装前确认作者源 18 文件与上一轮交付清单及散列完全一致，用户级和已知项目级同名目标均未占用。备份 `.local/backups/architecture-install-20261025-180332/` 保存当时 115 个仓库文件、54 个既有用户级技能文件、工作区/暂存区补丁、Git 索引和历史 bundle；逐文件 SHA-256 与 bundle 校验通过，暂存区原为空。并行报告及共享验证报告的对应段落另存散列与原文，供隔离提交核对。

完整复制到用户主目录下的 `.agents/skills/af-architecture-design/` 后，18 个文件的清单和 SHA-256 与作者源一致，14 条内部文件链接有效，入口名称与目录一致；既有三个用户级技能的 54 个文件未改变。未创建另一个用户级别名或覆盖其他副本。

使用当前正在运行的桌面二进制 `0.164.0-alpha.11.1` 启动临时隐藏 stdio 进程，按照 [官方 App Server 接口](https://learn.chatgpt.com/docs/app-server) 调用 `skills/list`、`forceReload: true`。项目目录和用户目录均返回唯一的 af-architecture-design，路径为上述用户级 SKILL.md，scope=user、enabled=true，errors 为空；三个既有技能同时正常。关闭 stdin 后临时进程以 0 退出，未修改宿主配置或启动常驻服务。该项加载验证为 `accepted`；桌面 UI/当前会话刷新、自动触发及其他宿主兼容仍未实测，真实价值状态未改变。

本阶段私有证据位于 `.local/skill-evals/architecture-install-20261025-180332/`：preflight、install-verification、host-loader-verification、host-process-exit 记录备份、安装与加载；提交快照检查及远端交付结果另存同目录。提交仅纳入架构任务相关文件，共享验证报告只纳入本任务段落；并行技能创建器报告和其段落留在工作区，不混入本次提交。沿用此仓库此前将当前工作分支提交推送到 origin/main 的方式，推送前核对远端基线且不强推。
