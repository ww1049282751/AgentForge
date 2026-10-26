# AF Next：用户技能同步验证

日期：2026-10-26。用户在四阶段交付后明确授权“安装到用户技能，同步到远程仓库并合并主分支”。本记录覆盖本次用户副本同步；授权只适用于已交付的 AF Next 变更，不延伸到其他技能、Release/tag、部署、宿主配置或后台任务。

## 同步前核对与保护

- 仓库仍有此前交付的 14 份 Markdown 改动，逐文件散列与交付快照一致，没有新增用户修改。起点为 `c2c770babe10801dc5eeed197beb78440ba300fb`；抓取后本地与远端 main 相同。
- 五个既有用户副本均在 `~/.agents/skills/`。四个技能已与作者源完全一致；只有 af-skill-creator 的 `references/design-and-authoring.md` 和 `references/evaluation-and-maintenance.md` 落后于作者源，两份旧副本均逐字节等于起点 Git 内容，未发现额外用户编辑。
- 先备份当前仓库 137 个文件及五个用户技能的 86 个文件，逐文件核验 SHA-256。备份在忽略目录 `.local/backups/af-next-sync-20261026/`；没有删除原始评估、历史证据或其他技能。
- 沿用既有用户位置，仅同步两份差异文件。未向 `~/.codex/skills/` 创建重复副本，未使用远端旧版本替换本地已验证作者源。用户路径与 [OpenAI 本地技能文档](https://learn.chatgpt.com/docs/build-skills) 一致。

## 实际验证

| 检查 | 结果及边界 |
| --- | --- |
| 完整清单与内容散列 | 5 个技能、86 个文件全部与作者源一致；除同步的 2 文件外，其余 84 个文件保持原内容 |
| 相对资源引用 | 86 条内部链接、49 个场景输入引用有效，均位于各自技能目录，可随完整文件夹搬移 |
| 宿主加载 | 使用当前运行桌面应用同版二进制的临时 stdio 加载器，`skills/list` 强制重载；项目与用户两个工作目录均识别 5 个 user scope、enabled 技能，无加载错误 |
| 宿主设置 | 已记录的配置与全局规则文件散列不变；临时探针进程结束，没有启动模型任务或常驻服务 |
| 桌面会话刷新与自动触发 | not-run；加载器识别不能替代现有会话刷新、界面观察或自动选择验证 |
| 行为与真实价值 | 沿用四阶段报告的范围与限制，本次复制和加载不产生新的能力收益结论 |

本次宿主探针报告 `Codex Desktop/0.164.0-alpha.11.1`；只记录实测版本，不据此声称应用为最新版本。官方文档说明技能变更会自动发现；若下轮仍未出现更新，可重启应用，本次没有主动重启用户会话。

## 证据与后续

私有记录位于 `.local/skill-evals/af-next-sync-20261026/`：`preflight.json`、`install-verification.json`、`installed-manifest.json`、`host-loader-verification.json` 和临时进程退出记录。原始评估继续保留于前述四阶段目录，本次不改写既有结果。

仓库交付包括治理、质量协议、可选交接及四阶段证据，见 [第一阶段](af-next-phase1-summary.md)、[第二阶段](af-next-phase2-summary.md)、[第三阶段](af-next-phase3-summary.md)、[第四阶段](af-next-phase4-summary.md)。提交、远端 CI 与合并结果由本次 PR、Git 历史和私有完成记录关联，不以本地文件校验代替远端检查。

下一步仍优先收集真实中断任务与用户反馈；没有新增技能准入、运行时或平台建设。
