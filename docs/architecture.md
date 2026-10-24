# 架构与一致性边界

核心层是 `skills/*/SKILL.md` 及相对引用。内部插件通过精确版本组合技能；plugin.json 是 AgentForge 格式，不直接交给宿主。`adapters/codex/adapter.json` 只声明已实现的名称转换、发现路径和基础能力。导出将核心 name 加 `af-` 前缀，正文与资源保持同源；不生成不必要的 openai.yaml。

根 schemas 是唯一作者源，安装包构建时复制到运行时包中。jsonschema 的 Draft202012Validator 执行完整结构校验，引用只从内置注册表加载，不联网解析 schema。SemVer、来源身份、依赖图、路径与宿主格式再做语义校验。`scripts/generate_schemas.py` 是 schema 定义的生成入口，生成 JSON 需一同提交。

数据流：显式 source → catalog/元数据 → 精确依赖闭包 → 有界 ZIP → 摘要与身份校验 → Codex 导出 → 事务。插件和技能共享一个导出，state.exports.owners 记录所有根。锁文件保存 sourceIdentity、catalogRevision、source revision、版本、归档摘要、adapter 摘要、闭包、host 和 pinned。workspace 来源身份由规范绝对路径散列，不在锁里泄露本机路径。

项目布局：

```text
project/
  .agents/skills/af-product-intelligence/  # 宿主实际加载目录
  agentforge.lock.json                    # 可审查的精确解析结果
  .agentforge/
    state.json                           # 本机路径、所有权与基线
    write.lock                           # 排他写锁：PID + transaction ID
    transactions/<id>/
      journal.json
      candidate/ backup/ retired/         # 均在目标同卷，宿主扫描区之外
```

事务阶段是 planned → staged → backed_up → switching → committed。异常进入 restoring → rolled_back 或 recovery_required。每个阶段先持久化日志；文件先 flush/fsync，JSON 临时文件替换；旧目录重命名到 retired，新目录重命名到宿主位置，随后更新账本与锁。操作系统文件互斥锁在进程退出时释放，持久 write.lock 保留事务身份；恢复锁也在核实原进程已退出且持有系统互斥锁后才接管。保留所有备份，不自动清理。

切换前二次比较基线与 state/lock；恢复前校验备份摘要、目标归属以及现场是否仍是旧或新版本。发现现场用户改动立即停止。恢复不靠锁年龄，必须验证日志并确认原 PID 已不存活。PID 重用可能保守拒绝恢复，需要人工诊断。

**可恢复不等于完全原子。** 目录、多个技能、state 与项目锁不是同一事务对象；两次目录重命名间有短暂缺口。禁止原位逐文件替换，也不承诺并行宿主读取一致性。应用前应关闭宿主读者，下次会话加载。单元测试覆盖进程突然退出；无法证明实际断电、磁盘控制器缓存或所有文件系统的持久性。Windows 无目录 fsync 的便携保证，极端断电仍需人工恢复和外部备份。

本地同用户恶意篡改整套日志/备份超出完整性散列的身份认证能力。工具不把 SHA-256 等同发布者签名，也不声称消除所有文件系统竞态。
