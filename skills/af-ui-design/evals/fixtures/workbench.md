# 合成输入：运行任务的工作台

对象是维护者自己的六个日常自动化任务，不需要团队管理。维护者想查看最近一次任务、定位需要自己处理的事项，并确认结果是否可用。主要在桌面使用，偶尔用手机查看。

服务端返回 runId、title、status、updatedAt、artifactUrl、reviewStatus；任务 status 为 queued/running/succeeded/failed，reviewStatus 为 pending/accepted/rejected。任务可能执行成功却没有合格产物。连接由另一个 connected/disconnected 信号表示，断开后不能确定任务当前状态。

取消接口返回 202 仅表示收到了取消请求，目前没有“已取消”事件，也没有已停止的查询字段。失败重试会创建新的 runId；服务端尚未承诺幂等。人工点击“已验收”只更新 reviewStatus，不会执行任务。

内容例子：标题“季度中文资料整理与跨项目重复记录核对——等待维护者确认外部引用”；失败原因“部分资料已生成，附件索引尚未完成”。没有现成视觉规范，暂无截图。上述为已提供的合成事实，其他能力未知。
