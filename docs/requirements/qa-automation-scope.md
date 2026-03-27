# QA 自动化 Phase 1 范围

## 参考来源

- `docs/Ai Agent 友好型 开发指南.docx`
- `docs/AagentShield QA自动化功能 可行性调研.docx`

## 目标

把测试从依赖人工的独立阶段，变成可被开发者、CI、上层 Agent 直接调用的自动化能力。

## 要解决的问题

- 测试覆盖率低，人工补测成本高
- 回归测试边界不清，容易漏测
- AI Agent 改完代码没有自验证信号
- 测试风格不统一，维护成本高
- 新功能上线前测试准备周期长
- 覆盖率数字好看，但关键路径没被覆盖

## Phase 1 模块

- `Analyzer`：代码识别、覆盖率缺口识别、边界条件推断
- `Generator`：基于 few-shot 与项目风格的测试生成
- `Runner`：统一执行多框架测试并输出标准结果
- `Tracker`：baseline 管理与回归判定

## 当前不做

- 安全类 Agent Shield 深度能力建设
- 面向终端用户的 IDE 插件
- 重 UI 的 E2E 自动化平台

## 首批交付物

- Monorepo 模板
- 质量门禁模板
- OpenAPI 契约
- QA 自动化的契约文档
- API 与前端骨架
