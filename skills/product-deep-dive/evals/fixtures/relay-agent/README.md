# Relay Agent：合成源码输入

这是专为离线研究评估编写的虚构项目，不是公开产品、真实用户数据或生产实现。源码快照用文件 SHA-256 标识，不伪造远程仓库/commit。

项目说明：Relay Agent 把用户请求转换为工具步骤，保存进度，并在中断后继续执行。产品介绍使用“持久进度让工具任务可安全恢复”的表述。当前样本用预设 plan 代替模型响应，不包含模型客户端、调度服务或部署配置。

使用路径：调用 `Store.create(task_id, prompt, plan)`，再由 `run_task(store, task_id, tools)` 执行。plan 的每项包含 tool 名称与 args。tools 由调用方提供 Python 函数；sample 不访问外网。

可将整个目录复制到临时工作目录，用 `python -m unittest discover -s . -v` 运行已有测试。只使用标准库，测试的数据文件位于 TemporaryDirectory。允许追加局部实验，但原始输入文件保持不变。
