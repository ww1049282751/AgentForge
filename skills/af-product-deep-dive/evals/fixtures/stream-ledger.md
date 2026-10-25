# Stream Ledger：合成基础设施材料

虚构项目的设计摘录与接口片段，无真实源码仓库、性能数据或生产日志。此文件是合成输入，不是实际评测报告。

## 设计摘录 D1

接收模块将事件追加到分片日志。协调器分配租约，worker 按 offset 读取并调用接收端，成功后提交 offset。租约过期后允许另一个 worker 领取分片。文档称其为“可恢复消费”；没有陈述所有业务副作用恰好一次。

## 接口定义 I1

```text
Lease = { partition, owner, epoch, expires_at }
Coordinator.acquire(partition) -> Lease
Log.read(partition, offset) -> Events
Sink.write(event_id, payload) -> Ack
Offsets.commit(partition, next_offset, epoch) -> Accepted | StaleEpoch
```

这是接口定义，未给出实现。Sink.write 参数没有 epoch；没有说明接收端是否按 event_id 去重。

## 测试说明 T1

测试设计文档列出“过期 epoch 的 commit 返回 StaleEpoch”和“重启后从已提交 offset 开始”。没有测试源文件、执行日志或退出状态。

## 未提供材料

租约时钟与续约、Sink 实现、分片重分配、压测及实际故障结果。当前任务可以提出实验，但不能把这些计划写作执行结果。
