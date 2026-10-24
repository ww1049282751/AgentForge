# 验证报告（2026-10-24）

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

已提供一个全部显式标注为合成的研究样例，C01–C06 逐条映射原始材料，作者复核见 [样例评审](evidence/skill-author-review.md)。10 个固定行为场景和 rubric 已定义。引用映射测试只验证结构；独立语义评分、实际新会话模型调用、自动触发正负例尚未运行。

本次 Windows 文件符号链接创建不被 OS 允许，相关测试跳过；硬链接检测已执行，Windows 目录 junction 独立实测通过。macOS/Linux CI 尚未运行。真实远程包安装、签名、私有源认证、Release CDN、实际断电与真实宿主持锁未验证或未实现。

没有宣称严格原子切换：使用同卷重命名和日志恢复，可能短暂缺少目标目录，多路径观察者可能看到中间态。应用前关闭宿主读取。元数据 testedVersions 保持空，避免将“发现成功”夸大为完整宿主行为兼容。

## 本地交付与远程界限

源码位于当前仓库的 codex/agentforge-mvp 分支。候选由 build 命令生成到忽略的 dist 目录；归档与摘要不上传。仓库 stable/preview 发布目录仍为空。首次公开推送和正式发布须分别审查授权；没有开启自动化任务。

已实际安装到当前 AgentForge 项目的 `.agents/skills/af-product-intelligence/`，项目 pin 为 0.1.0。安装后的 check --locked 与 doctor 均无冲突、无待恢复事务，state/lock 一致。全局技能未改动。该本机安装、状态和备份均被 .gitignore 排除，不随源码提交。
