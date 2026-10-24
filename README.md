# AgentForge

个人使用优先的 Agent 技能库。首个能力 **product-intelligence 0.2.0** 用于产品发散性调研、深入分析、竞品分析、专家视角评审和认知补齐；通过分轮澄清对齐方向，形成有证据、有建设性的新理解与方案。当前优先验证它能否改善真实产品判断。

**当前阶段：真实任务效果验证。自建运行时冻结扩展，暂不推送或发布。** 已有安装、版本锁和恢复实现保留为备用，不作为本阶段验收中心。已有工程测试不证明技能价值；内部插件格式也不代表 Codex 原生插件已验证。

先读 [当前路线](docs/implementation-plan.md) 与 [真实任务评估方法](docs/skill-evaluation.md)。当前项目已经安装了技能，可在任务中显式使用 `$af-product-intelligence`；首批评估对照普通回答与技能回答，原始材料只保存在本地。效果评估形成结论后，才做 [最小原生插件验证](docs/native-plugin-validation.md)。

[首次真实项目材料试跑](docs/evidence/workbench-01-summary.md) 已完成：两组关键建议相近，技能的证据组织更细，但个人使用净收益尚未证明，待用户反馈。

用户新会话体验后的定位反馈已纳入 [0.2 调整](docs/decisions/0003-product-research-positioning.md)：完整研究可包含竞品机制、专业视角分歧、机会方向与图表，不再以最小行动简报作为所有任务的默认输出。旧试跑仅覆盖窄题，不能替代新版效果验收。

仓库身份与名称统一记录于 [manifest.json](manifest.json)。品牌、商标和注册表包名尚未全面核实。下面的安装与更新命令是已有实现的使用说明，不是继续扩展运行时的路线。

## 快速使用

需要 Python 3.12+。以下 PowerShell 命令在仓库根执行；项目虚拟环境不会修改系统 Python。

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock
.venv/Scripts/python.exe -m agentforge --help
.venv/Scripts/python.exe -m agentforge validate
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

安装到**已经存在**的目标项目（请把示例路径换成自己的路径）：

```powershell
.venv/Scripts/python.exe -m agentforge install af-product-intelligence --source . --project D:/projects/my-product --scope project --target codex
.venv/Scripts/python.exe -m agentforge check --project D:/projects/my-product --json
```

生成位置为目标项目的 `.agents/skills/af-product-intelligence/`；事务、备份与账本在 `.agentforge/`，项目版本锁在 `agentforge.lock.json`。不改动全局技能或宿主配置。新会话中可显式使用 `$af-product-intelligence`。如宿主未刷新，请重启该项目会话。

macOS/Linux 将 `.venv/Scripts/python.exe` 换成 `.venv/bin/python`。这些平台的 CI 已配置，本次本机验证只有 Windows。项目内 `python -m agentforge` 是必需验证的入口；可选 Python 包安装会提供 `af`，安装前应确认命令不冲突，不需要发布到 PyPI。

也可以仅安装技能，随后安装插件时复用同一导出并记录共同所有者：

```powershell
.venv/Scripts/python.exe -m agentforge skill install product-intelligence --source . --project D:/projects/my-product
```

## 检查、更新与恢复

```powershell
# 以下两条只读，不修改安装、项目锁或宿主配置
.venv/Scripts/python.exe -m agentforge check --project D:/projects/my-product --json
.venv/Scripts/python.exe -m agentforge update --project D:/projects/my-product

# 项目默认 pin；显式改变版本必须同时更新锁，来源必须包含此精确版本
.venv/Scripts/python.exe -m agentforge update af-product-intelligence --version 0.2.0 --update-lock --apply --project D:/projects/my-product

# 当前工作区包含技能/插件 0.2.0；运行时自身仍为 0.1.0
.venv/Scripts/python.exe -m agentforge update --locked --project D:/projects/my-product
.venv/Scripts/python.exe -m agentforge doctor --project D:/projects/my-product
```

每次成功变更都会输出 transaction ID。回滚/恢复默认预览，执行时追加 `--apply`：

```powershell
.venv/Scripts/python.exe -m agentforge rollback --transaction TRANSACTION_ID --project D:/projects/my-product
.venv/Scripts/python.exe -m agentforge recover --transaction TRANSACTION_ID --project D:/projects/my-product
```

发现本地新增、修改、删除或路径类型变化时停止应用。选择保留当前版本、把修改另存，或手工合并后安装到新目标；没有强制覆盖参数。切换前关闭正在读取该技能的宿主会话。两次重命名之间可能短暂没有目标目录，不是热更新或跨路径原子事务。

## 来源与发布状态

支持显式本地工作区、包含历史版本的本地候选目录，以及公开 HTTPS GitHub catalog。远程安装固定 catalog 提交与 source 提交，只接受同一仓库固定提交下的 raw 产物 URL；拒绝重定向。私有远程下载、GitHub Release CDN、发布签名与离线远程缓存尚未实现。私有源码可先用用户已有认证工具检出，再显式使用本地源。

仓库中的 stable/preview 发布目录目前为空。工作区里的 `channel: stable` 表示目标通道，**不代表已经发布**。本地候选可这样生成，输出目录必须不存在：

```powershell
.venv/Scripts/python.exe -m agentforge build --source . --output dist/candidate
```

## 文档

- [命令与状态模型](docs/usage.md)、[架构和原子性边界](docs/architecture.md)
- [新增与维护能力](docs/authoring.md)、[版本和发布步骤](docs/release.md)
- [恢复、备份和卸载](docs/recovery.md)、[安全与信任](docs/security.md)
- [兼容性](docs/compatibility.md)、[实际验证记录](docs/validation-report.md)
- [合成产品研究样例](examples/product-intelligence/decision-brief.md)、[技能场景与评分](tests/skill-evals/scenarios.json)

没有后台任务、遥测、包内执行钩子或自动应用更新。运行时升级由用户手工完成，不通过技能更新器替换运行中的代码。
