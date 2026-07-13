# Task state machine

智能体任务不是一句“已完成”的回复，而是一条可检查的状态链：

- `planned`：任务与计划已记录。
- `running`：正在执行受限工具。
- `verified`：结果已按可见证据检查。
- `completed`：验证通过后完成。
- `needs_attention` 或 `failed`：不能伪装成成功，必须保留原因和下一步。

任务账本只在本机持久化。代码写入仍需用户明确授权；状态机不扩大任何工具权限。

终态 `completed` 与 `failed` 不允许回退；需要再次执行时必须显式从 `needs_attention` 重试，或创建新任务。
