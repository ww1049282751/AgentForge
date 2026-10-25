# UI 设计行为评估

场景及 fixtures 均为合成材料，不是用户项目或真实效果证据。AgentForge 维护采用仓库根目录 `docs/skill-evaluation.md` 的 AF Skill Quality Loop；复制技能后按目标项目规范与本页执行，不依赖仓库外文件。

## 执行方法

从 [scenarios.json](scenarios.json) 选题，运行前冻结请求、输入、技能、[量表](rubric.md) 与内容散列。执行者只接收 request、inputFiles 原始材料、候选入口及当前允许的工具/操作；不得读取 expected、量表、其他输出或评审。截图题只提供图片，不提供生成它的 HTML。材料存在不说明已经执行。

每例使用新上下文与隔离目录。记录模型/设置（不可得写未知）、日期、工具、权限、实际加载文件、耗时、可得 token 与成本。未编辑的公开输出、工具记录、截图、产物和前后清单在 AgentForge 放 `.local/skill-evals/<日期或任务ID>/`；内部推理不作为公开输出保存。评审在执行后读取 expected 和量表，逐项给原文/文件证据与限制；作者参与评审须披露。

普通组不读取技能正文或资源，技能组显式读取冻结入口。固定请求、输入、工具、权限、模型条件、输出要求及评审标准，使用互不可见的新上下文；记录宿主其他指令与自动加载污染。负例显式加载只验证克制，不证明自动触发正确。比较实际任务完成、错误、返工与负担，不能按篇幅、模板或自评分判断增益。

保留失败与无变化，先诊断输入/环境/技能/工具问题，再局部修正、冻结新快照并复验相关场景及必要回归。不得将失败输出覆盖成重跑结果，未跑回归不判 improved。

## 场景组织

- design：new-workbench-flow、visual-direction、interaction-failure；检查任务、方向与状态语义。
- improve：existing-system、responsive-real-content；检查继承与内容压力。
- review：review-screenshot、review-implementation；检查观察边界与定位。
- 条件运行：browser-feedback-loop；只有实际运行、看图、操作和复验才有运行结论。
- 深度与未知：small-ui-question、insufficient-context。
- 负例：product-discovery-only、backend-or-syntax-only。
- 权限：external-instruction、no-implementation-permission。

`fixtures/browser.html` 是无依赖、无外部请求的合成练习页，含待评审缺陷，不是推荐实现。运行题复制到隔离目录，通过仅绑定回环地址的临时静态服务访问；结束后停止服务。只允许修改副本，不能更新作者源 fixture 来消除失败。`review-screen.png` 是该页在 390×844 下的固定截图，仅作截图评审输入；生成环境与证据另记，不因它存在宣称行为已通过。

## 判定与限制

分别记录结构、行为、同题对照、真实任务价值。使用 not-run、blocked、failed、regression、inconclusive、no-change、improved、accepted，并限定 accepted 的验收范围。未执行为 not-run；确认缺环境/权限为 blocked 并写恢复条件；证据不能支持结论为 inconclusive。

截图与实际任务观察支持视觉/可用性判断；只有文档输出时只能评价设计推理，不能给真实 UI 视觉或体验通过结论。真实任务价值还需实际用户任务及反馈。合成运行、宿主显式加载和自动触发分别列出，不合并为“技能有效”。
