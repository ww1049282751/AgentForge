# 新增或维护技能

当前优先依据真实任务反馈维护技能内容；自建运行时冻结扩展。下面是已有包结构的维护说明，不意味着现在需要增加更多插件、适配器或基础设施。见 [当前路线](implementation-plan.md)。

1. 在 `skills/<id>/` 编写 skill.json、SKILL.md 和必要 references/templates。name 与目录、元数据 ID 一致。核心不硬编码宿主工具、个人路径或账户。
2. 入口使用两行标量 frontmatter：name、description。本版采用受限、确定性的格式；不支持任意 YAML 或包内脚本。正文按实际触发条件和任务边界编写，引用使用技能内安全相对路径。
3. 在 `plugins/af-<id>/plugin.json` 组合技能，精确指定版本和路径。直接包含的技能不在 dependencies 重复列出。非直接依赖也只能精确版本，不接受范围。
4. 将包加入 `catalog/index.json`。metadata 和 source.path 指向同一目录，声明真实所需能力；web-research 在本技能中是可选能力，不能作为离线分析的硬依赖。
5. 修改 adapter 时核对宿主文档并记录摘要变化。当前仅支持 Codex 指令型技能；其他宿主应增加专门实现与测试，不仅改变 metadata。
6. 运行结构与回归检查，增加实际触发/不触发场景及证据样例。影响触发范围、输出契约或权限时必须更新版本与 changelog。
7. 准备本地候选，按发布文档确认后再公开。工程、设计等未实现能力不得作为可安装占位进入 catalog。

建议 PATCH 修正不改变契约的问题，MINOR 增加兼容能力，MAJOR 改变输入/输出、布局、权限或行为。0.x 同样遵守分类；插件仅升级引用技能也必须增加插件版本。已发布 id+version 的归档不能替换。

`kind: pack` 仅保留设计：未来可将多个插件组合为建议清单；MVP 没有 pack schema、求解或安装命令，不能把设计文档当可安装包。
