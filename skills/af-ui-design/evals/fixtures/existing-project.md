# 合成输入：已有审批页面

现有 Vue 3 + TypeScript + Vite，Composition API；使用现有组件库，无 Tailwind。仓库约定复用 `src/components/AppDialog.vue`、`AsyncButton.vue`、`EmptyState.vue` 和 `src/styles/tokens.css`；tokens 为 `--space-2/4/6`、`--text-primary`、`--text-muted`、`--surface`、`--danger`、`--focus-ring`。系统已有深浅主题。这里只提供上下文摘录，未提供完整项目或可启动环境。

`src/views/ApprovalList.vue` 已用原生表格表达申请人、标题、提交时间与审批状态。维护者未提交修改包括将详情面板宽度改为 520px 和新增退回原因字段；必须保留。UI 库已处理对话框焦点管理，禁止再引入一套对话框。

附带的 `ReviewPanel.vue` 是待审查的合成片段。`api.approve(id)` 返回 `{accepted: true}` 表示排队接收，最终审批状态由独立刷新获取；该片段没有接入最终状态刷新。不存在“已批准”同步返回契约。网络失败抛异常。调用副作用不允许在真实服务执行。
