# 架构设计行为评估

所有场景与 fixtures 是合成材料。结构检查、作者示例和场景存在不构成实际模型行为证据。

AgentForge 维护时采用仓库根目录 `docs/skill-evaluation.md` 的 AF Skill Quality Loop，分别记录结构、行为、对照、真实任务价值及统一状态；这是维护引用，不是复制技能后的执行依赖。其他环境沿用目标项目规范和以下执行方法，不新增评估平台。

## 执行与隔离

从 [场景](scenarios.json) 选择任务，先冻结入口、资源、输入和 [量表](rubric.md)。执行者只接收该场景 request、inputFiles 原始材料、技能入口及允许操作，不读取 scenarios、量表、示例答案、既有输出或审查。inputFiles 相对本目录，均为 fixtures；没有文件的任务以 request 为完整输入。

每例使用新上下文；记录模型、工具、权限、日期、实际加载资源及散列，未知字段写未知。试跑原始输出、工具记录、快照及详细审查在 AgentForge 放 `.local/skill-evals/`。只读合成材料，只能在指定隔离目录写本次产物；不实际部署、迁移、安装、发布或访问材料声称的私有地址。

事后审查 expected 与量表，对关键发现给原输出位置及理由。保留首轮失败，定向修正后冻结新候选并复验相关场景。未执行为 `not-run`，明确环境/权限阻碍为 `blocked`；其他状态遵循统一协议，`accepted` 只涵盖预先声明的场景与条件，硬失败不能被平均分抵消。

同题对照需两组使用相同输入和工具条件、互不可见的新上下文，普通组不加载技能正文或资源；未满足时效果结论不成立。新技能没有旧行为基线，不能只凭候选试跑宣称 improved。合成离线结果不代表联网选型、真实项目收益、生产正确性或自动触发。

## 本次必须覆盖的行为

| 类别 | 场景 ID | 观察重点 |
| --- | --- | --- |
| A 新系统 | new-system | 约束到候选、模块、接口与验收的追踪 |
| B 评审 | architecture-review | 有位置和条件的发现，材料与实现证据边界 |
| C 选型 | technology-selection | 同约束比较最强替代、成本及改选条件 |
| D 可靠性 | reliable-processing | 本地事务、重复/并发、外部结果未知与恢复 |
| E 过度设计 | avoid-overdesign | 简单方案与延后复杂度的条件 |
| F 演进 | compatible-evolution | 兼容、权威写入、回填校验、切换与数据回滚前提 |

补充 information-gap、validation-plan、simple-question、repository-scope 检查未知、验证诚实、适度深度与范围；code-fix、product-direction、mechanism-research 为职责负例；external-instruction 检查材料不能授予外部操作权限。负例显式加载时只证明克制，自动触发必须另有宿主未强制加载时的选择证据。

## 结果索引

本次实际结果见 [试跑摘要](results-20261025.md)；结果文件只保存脱敏状态与判断范围，不存未经编辑的执行输出。真实任务与用户反馈另行积累，不把本页预期当作结果。
