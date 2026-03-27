# Skills Cloud

该文件沉淀跨项目可复用流程，当前先记录 AgentShield 的首批技能模板。

## qa-scope-review

- 输入：需求文档、优先级、阶段边界
- 输出：实现范围、明确的不做项、验收标准

## openapi-sync

- 输入：FastAPI 路由与 Pydantic 模型
- 输出：更新后的 `openapi/openapi.yaml` 与契约差异说明

## qa-regression-baseline

- 输入：本次测试结果、历史 baseline
- 输出：回归判定、覆盖率变化、是否允许更新 baseline

## test-style-alignment

- 输入：目标项目已有测试、Analyzer 输出、覆盖率缺口
- 输出：风格对齐的测试生成约束

## planner-generator-evaluator

- Planner：定义 contract、范围和成功标准
- Generator：在约束内实现
- Evaluator：验证行为、契约与测试，不改需求
