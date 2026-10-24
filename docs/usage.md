# 使用与退出码

所有命令从仓库根使用 `python -m agentforge`。默认范围是当前可识别的 Git 项目；没有 Git 项目时需要显式 `--project` 或 `--scope user`。显式项目目录必须已存在。`--scope user` 是写入用户级目录的明确选择，不会由项目检测失败触发。

| 命令 | 实际行为 |
| --- | --- |
| `--help` / `--version` | 显示已实现接口及运行时版本 |
| `validate --source .` | 校验所有 schema 本身、包元数据、入口/引用及依赖闭包 |
| `build --output dist/candidate` | 生成确定性 ZIP、摘要及本地候选目录，不上传 |
| `install ID --source SOURCE` | 安装一个内部插件并显示计划，缺少 ID 退出 2 |
| `skill install ID --source SOURCE` | 单技能安装，不重复注册共同技能 |
| `check --json` | 只读检查版本和冲突，不下载远程包体 |
| `check --locked` / `update --locked` | 验证源中仍存在精确锁定版本及摘要，缺失即失败 |
| `update [ID]` | 解析、核验并预览候选，可能在系统临时目录下载包体；不写目标 |
| `update [ID] --apply` | 应用预览同等规则；项目 pin 保持原版本 |
| `update ID --version V --update-lock --apply` | 显式改变项目锁；不绕过修改保护 |
| `update ... --channel preview` | 显式选择预览通道，受 pin 和精确版本规则约束 |
| `update ... --accept-permissions` | 审查后接受本次网络/输出权限扩大；不是后台授权 |
| `rollback --transaction ID [--apply]` | 整笔回滚当前事务，包括依赖闭包、账本与锁 |
| `rollback [PACKAGE] --to VERSION [--apply]` | 选择当前事务备份内的版本；依然恢复整笔事务 |
| `doctor` | 只读诊断目标、状态、修改、锁与未完成事务 |
| `recover --transaction ID [--apply]` | 校验归属/备份/现场后恢复之前有效状态 |

不支持对旧的非当前事务任意跳跃回滚；按逆序回滚，新事务记录仍保留。无项目 unpin CLI；项目始终 pinned。用户范围记录精确版本，但可以显式更新至同主版本 stable。依赖被两个根共同拥有且要求版本不同会失败，不自动重写另一根的 pin。

`--json` 输出一个 JSON 文档；文本安装模式先显示完整计划再执行。`check` 的 `updatesAvailable`、`pinned`、`conflicts`、`unsupported`、`errors`、`pendingTransactions` 区别状态；网络错误不是“没有更新”。JSON 不包含本机源路径，锁文件仅记录来源身份摘要；本机状态才保留绝对源路径。

| 退出码 | 意义 |
| --- | --- |
| 0 | 成功；检查发现可用更新仍为 0 |
| 2 | 参数、JSON Schema 或版本格式错误 |
| 3 | 用户文件、路径或 pin 冲突 |
| 4 | 网络、认证/访问或下载中断 |
| 5 | 来源、摘要、路径或不可信产物失败 |
| 6 | 兼容性、依赖、权限扩大或版本缺失 |
| 7 | 事务、锁、恢复或文件系统故障 |

本地候选目录中的 `artifact.url` 为安全相对路径。远程源格式为 `https://github.com/OWNER/REPO`，可追加 `#40位提交SHA` 固定 catalog；不固定时通过公开 GitHub API 解析 HEAD，再从固定提交读取目录。对固定 catalog 的安装不会自动看见后续 catalog 提交；这是选择固定来源的结果。
