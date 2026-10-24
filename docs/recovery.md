# 失败恢复与保留数据

先运行 `python -m agentforge doctor --project <项目>`。记录 pendingTransactions 的 ID/phase、writerLock、conflicts 和错误码。不要先删除 write.lock、candidate、backup、retired 或 journal；锁超时不是安全删除的依据。

可以把 `.agentforge/transactions/<id>/`、state.json 和 agentforge.lock.json 复制到自己选择的备份位置。分享诊断前脱敏 state 中的绝对路径和来源路径；无须提供 token、完整环境或研究材料。

```text
python -m agentforge recover --transaction <id> --project <项目>
python -m agentforge recover --transaction <id> --project <项目> --apply
```

恢复先校验事务 ID/目标、备份散列、state/lock、现场和原进程是否已退出。planned/staged 尚未切换，只结束事务；backed_up/switching/restoring 恢复完整之前状态；committed/rolled_back 若遗留锁，仅在现场一致且原进程已退出时释放锁。任何用户修改都停止恢复，不能用 --apply 绕过。

| 故障 | 处理 |
| --- | --- |
| Windows 文件占用 | 关闭目标宿主、编辑器及扫描器对目标的读取，确认原进程退出，再重试 recover |
| 备份损坏 | 保留全部现场；比较 retired、displaced 及独立备份；不要删活跃版本。手工复制到新项目验真后再切换 |
| 日志/锁损坏或 PID 重用 | 不自动接管；确认系统进程身份，保存完整快照后人工诊断；工具保守拒绝 |
| 恢复中再次退出 | 下次 recover 再校验现场；中间目录保留，重复恢复不会以时间判断删除 |
| 空间不足 | 变更前停止。扩容或把不受管文件移往已确认位置，再重新预览；不自动清理备份 |
| 下载中断/401/403/离线 | 原安装保持可用。修复网络/访问；公开源无权限时不要粘贴凭证到命令。也可显式使用已核实的本地候选 |
| 用户改动 | 保留现版，或将改动另存；在新目标进行合并与安装。没有强制覆盖选项 |

显式回滚：对当前 committed transaction 使用 `rollback --transaction <id>` 预览，`--apply` 整体恢复文件、依赖闭包、账本与 pin。不能只回退显示版本，也不能任意跳过后续事务。

## 卸载（本版没有 uninstall 命令）

先停止宿主，运行 doctor 确认没有待恢复事务。把导出目录、`.agentforge/` 和锁文件完整复制到独立备份位置。核对 state.exports 的名称和 owners；同一技能可能同时被插件和直接安装拥有，不能只删除其中一个逻辑根就假定其他根仍正常。

如果要移除本目标的**全部 AgentForge 安装**，在完成备份且确认真实绝对路径后，手工移走 state.exports 中列出的那些技能目录，再移走本工具的 state/事务目录和 agentforge.lock.json。保留 `.agents/skills` 内其他目录、用户文件、全局技能与宿主配置。不要递归删除整个 `.agents` 或项目目录。只卸载一个共同依赖根的操作未实现，改在新目标重建所需根。

恢复旧版完整安装时使用已校验的完整快照恢复同一目标；不要只复制 SKILL.md 后留下不一致账本。需要跨项目迁移时重新显式安装，原日志绑定原目标不允许直接改路径使用。
