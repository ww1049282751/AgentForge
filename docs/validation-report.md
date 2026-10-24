# 验证报告（2026-10-24）

当前路线已调整为个人使用与真实任务效果优先，自建运行时冻结扩展。以下 45 项工程回归与宿主发现是已有实现的历史验证，不能作为新阶段产品效果结论。真实任务首题为用户指定的“产研工作台”，评估状态单独记录；原生插件验证后置。见 [当前路线](implementation-plan.md)。

当前为本地 MVP 候选，未推送、未公开发布、未创建 Release/tag。远程仓库身份与 public 可见性已通过 GitHub CLI 只读核实；仓库 URL 见根 manifest。

## 已执行

| 项目 | 实际结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m agentforge validate` | 10 个 Draft 2020-12 schema 元校验通过；2 个包及依赖/入口/引用有效 |
| `.venv/Scripts/python.exe -m unittest discover -s tests -v` | 45 tests，44 通过、1 跳过；详见 [完整测试日志](evidence/runtime-tests.txt) |
| skill-creator 的 quick_validate.py | 核心技能通过 frontmatter/命名检查；不等于行为验收 |
| `python scripts/host_discovery_smoke.py`（项目虚拟环境） | Codex CLI 0.164.0 返回启用的 repo 技能，路径匹配，见 [发现证据](evidence/host-discovery.json) |
| `python scripts/check_docs.py` | 检查仓库内 Markdown 目标、6 条合成证据映射与 10 场景定义；结果见 evidence/docs-check.json |
| Python compileall | runtime、scripts、tests 语法编译通过 |
| Python wheel | 使用桌面应用已有构建工具生成 wheel；以 --no-deps 安装到 dist/wheel-probe，隔离导入后 10 schemas / 2 packages 校验通过；未安装全局 af |

测试全部在独立临时目录操作，用户级范围测试用假 home，不写真实全局技能。隔离宿主发现过程使用临时 Git 项目，结束后清理其技能文件。

## 安全行为证据

- 安装与重复安装、插件/技能共同所有权、只读 check/preview、stable/preview 排序、project pin、精确版本缺失、显式更新与全闭包回滚。
- 新增/修改/删除/目录类型变化保护；计划后与备份后的用户写入都会停止应用，保留原文件。
- 摘要/包版本/来源身份/通道错误、未知字段、非法版本、缺失依赖/循环/版本冲突、能力与平台不兼容、权限扩大、主版本升级限制。
- 同版本归档或 source revision 改写被拒绝；已有安装的 project/user scope 不能被另一范围静默接管。
- 401/403、超时、断流和重定向拒绝；check 网络替身确认没有获取包体；错误没有回显假凭证。
- 目录穿越、盘符、UNC、保留名、硬链接、归档链接/特殊文件、大小写冲突、ZIP 膨胀限制和 Windows junction 防护。
- 排他写锁、空间不足、备份损坏、模拟 rename 文件占用、陈旧计划、跨目标日志拒绝。
- 在 planned/staged/backed_up/switching/旧目录已移走/新目录已激活/state 已写入/committed 8 个位置强制结束子进程，然后用恢复命令验证旧态或已提交新态。
- 恢复过程在 restoring 再次强制退出，下一次恢复能识别已退出进程、处理遗留恢复锁并完成；连续两个更新可以逆序恢复。

## 技能质量与未完成验收

工程阶段提供了一个全部显式标注为合成的研究样例，C01–C06 逐条映射原始材料，作者复核见 [样例评审](evidence/skill-author-review.md)。10 个固定行为场景和 rubric 已定义。引用映射测试只验证结构，合成样例不计入真实业务样本。

路线调整后，首个真实项目材料对照已由两个独立子代理完成，另一个子代理进行了匿名内容审查；详见 [workbench-01 摘要](evidence/workbench-01-summary.md)。两组都获本题量表 10/10，关键建议相近；技能组证据组织更细，但用户价值和附加负担仍待反馈，未证明明显净增益。此次是离线、显式读取冻结技能的模型试跑，不代表原生插件加载、自动触发、联网研究或工作台模型回写闭环通过。精确模型版本、token 和费用未知。

本次 Windows 文件符号链接创建不被 OS 允许，相关测试跳过；硬链接检测已执行，Windows 目录 junction 独立实测通过。macOS/Linux CI 尚未运行。真实远程包安装、签名、私有源认证、Release CDN、实际断电与真实宿主持锁未验证或未实现。

没有宣称严格原子切换：使用同卷重命名和日志恢复，可能短暂缺少目标目录，多路径观察者可能看到中间态。应用前关闭宿主读取。元数据 testedVersions 保持空，避免将“发现成功”夸大为完整宿主行为兼容。

## 本地交付与远程界限

源码位于当前仓库的 codex/agentforge-mvp 分支。候选由 build 命令生成到忽略的 dist 目录；归档与摘要不上传。仓库 stable/preview 发布目录仍为空。首次公开推送和正式发布须分别审查授权；没有开启自动化任务。

首次安装到当前 AgentForge 项目的 `.agents/skills/af-product-intelligence/` 时，项目 pin 为 0.1.0；该版本的安装后检查通过。2026-10-24 已通过既有事务更新到 skill / 内部 plugin 0.2.0 并更新项目 lock，保留恢复备份。七个实际安装文件与受控评估冻结快照的 SHA-256 全部一致。更新后的 check --locked 与 doctor 均无冲突、无待恢复事务，state 有效。全局技能未改动。该本机安装、状态和备份均被 .gitignore 排除，不随源码提交。

## 0.2.0 定位反馈复核（2026-10-24）

按用户反馈扩展产品探索、深度分析、竞品与专业视角研究、认知补齐、分轮澄清和丰富表达。runtime 仍为 0.1.0，未扩展。两个独立受控试跑及主代理复核见 [research-02 摘要](evidence/research02-summary.md)：两轮脚本输入中继续追问关键未知；离线报告展开不同机制、反对意见、建设性方向和定性图表，明确区分模拟专业视角与真人评审。

本轮 validate 与 skill quick_validate 通过；完整运行时回归 45 项，44 通过、1 项因 Windows 文件符号链接权限跳过，见 [本轮测试日志](evidence/research02-runtime-tests.txt)。测试夹具固定历史起始版本，未修改运行时实现。Markdown 链接与场景结构另经 check_docs 检查。

这些结果仅支持受控行为符合新增要求；报告曾中断并恢复，不代表稳定响应时延。尚无用户对新版真实收益的验收，也未验证在线竞品研究、真实专家意见、自动触发或原生插件加载。源码与项目安装均仅本地更新，未推送或发布。
