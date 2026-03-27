# QA Automation Test Spec

## Required Case Families

- 正向路径：目标代码存在，Analyzer 能产出可测试单元
- 异常路径：不支持的框架或无测试入口时，返回明确失败原因
- 边界路径：同一变更重复执行，不得产生重复副作用
- 回归路径：baseline pass -> current fail 必须阻断
- 覆盖率路径：覆盖率下降超过阈值时输出 warning

## Mandatory Assertions

- 输出结构必须稳定，可供 Agent 或 CI 直接消费
- 不允许把生成测试写入业务方测试目录
- 不允许在无显式确认时更新 baseline
- 结果必须区分 `failed`、`regressed`、`warning`
