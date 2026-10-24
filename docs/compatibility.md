# 实际兼容性（2026-10-24）

`platforms` 声明计划支持范围，不是测试通过范围；metadata 中 `testedVersions: []` 保留未完成完整行为验收的状态。

| 对象 | 已运行证据 | 状态/边界 |
| --- | --- | --- |
| Windows 11 build 26200 / NTFS | Python 3.12.10；45 项回归、进程中断恢复、目录 junction 防护 | 44 通过，1 项文件符号链接测试因 OS 创建权限跳过 |
| macOS / Linux | 三平台 CI 已配置 | 尚未推送，CI 未运行，pending |
| Python 3.12 | 实际模块入口与临时 wheel 安装校验 | 通过；其他 Python 版本未实测 |
| Codex CLI 0.164.0 | app-server skills/list forceReload，在临时 Git 项目返回 repo 范围、enabled=true、正确路径 | 发现通过；模型调用和自动触发待验收 |
| Codex 桌面应用当前会话 | 本次实施工具环境 | 未作为新会话自动发现/调用验收；不推定与 CLI 相同 |
| Codex 原生插件目录 | 未生成官方插件格式 | 未验证，当前使用独立技能导出 |
| HTTPS GitHub 分发 | 固定提交/目录/包体/来源拒绝逻辑以离线网络替身测试 | 实际远程 catalog 尚未发布；端到端远程安装 pending |
| 私有源认证、Release CDN、签名、离线远程缓存 | 未实现 | 明确不支持；本地候选可离线使用 |

接入依据：[官方 Build skills](https://learn.chatgpt.com/docs/build-skills)，2026-10-24 查阅。使用 SKILL.md 的 name/description 和项目 `.agents/skills`；同名技能并非自动合并。可选 openai.yaml 本版不需要，故不生成。官方文档不是本机模型调用的替代证据。

人工调用验收：

1. 在目标项目安装后开启新的 Codex 会话，检查技能列表只有预期同名技能。
2. 显式请求 `$af-product-intelligence`，给出合成材料并要求离线研究；观察实际技能加载/调用及简报。
3. 用 tests/skill-evals/scenarios.json 逐例测试；负例应直接处理原任务，不进入产品研究。
4. 按 rubric.md 记录宿主版本、模型版本（可得时）、真实输出、工具调用和证据支持。不要把仅看到技能名称记作调用通过。

模拟 Windows rename 占用失败测试通过；真实第三方扫描器/宿主持锁、实际断电、网络盘和其他文件系统未覆盖。
