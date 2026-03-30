# AgentShield Week 1 Panel apps/api 模块设计

> 版本：v1.0
> 日期：2026-03-30
> 范围：apps/api Panel Module Design

## 1. 模块目标

`apps/api` 需要承接两类职责：

- CLI 写接口：接收 init、baseline、run 上传并落库
- Web 读接口：查询项目总览、项目详情、latest run

## 2. 推荐目录

```text
apps/api/src/panel/
├── routes/
│   ├── register-project.ts
│   ├── upload-baselines.ts
│   ├── upload-run.ts
│   ├── get-projects.ts
│   ├── get-project-detail.ts
│   └── get-project-latest.ts
├── schemas/
│   ├── register-project.schema.ts
│   ├── upload-baselines.schema.ts
│   ├── upload-run.schema.ts
│   └── query-response.schema.ts
├── services/
│   ├── project-register-service.ts
│   ├── baseline-upload-service.ts
│   ├── run-upload-service.ts
│   ├── project-overview-query-service.ts
│   ├── project-detail-query-service.ts
│   └── latest-run-query-service.ts
├── repositories/
│   ├── project-repository.ts
│   ├── run-repository.ts
│   ├── module-repository.ts
│   ├── checker-result-repository.ts
│   └── baseline-repository.ts
├── mappers/
│   ├── request-to-entity.ts
│   └── entity-to-response.ts
└── db/
    ├── migrations/
    └── sqlite.ts
```

## 3. 分层职责

## 3.1 Route 层

职责：

- 接收 HTTP 请求
- 调用 schema 校验
- 调用 service
- 返回统一响应

不负责：

- 拼接 SQL
- 写业务聚合逻辑

## 3.2 Schema 层

职责：

- 校验请求体
- 校验 query/path 参数
- 保证字段类型完整

建议使用：

- Zod 或 Pydantic 对应方案

## 3.3 Service 层

职责：

- 实现业务流程
- 控制事务边界
- 处理幂等逻辑
- 组合多个 repository

例如：

- `run-upload-service.ts`
  - 找 project
  - upsert run
  - upsert modules snapshot
  - upsert checker results

## 3.4 Repository 层

职责：

- 单表 CRUD / upsert
- 屏蔽 SQLite 细节

原则：

- 一个 repository 只负责一张表
- 不在 repository 中写跨表业务逻辑

## 3.5 Mapper 层

职责：

- 把 API request 映射为内部 entity 输入
- 把数据库结果映射为 API response DTO

## 4. 写接口服务设计

## 4.1 ProjectRegisterService

输入：

- `POST /api/v1/panel/projects/register`

事务步骤：

1. upsert `panel_projects`
2. upsert `panel_modules`
3. 返回 `project_id` 和模块数

## 4.2 BaselineUploadService

输入：

- `POST /api/v1/panel/baselines`

事务步骤：

1. resolve `project_id`
2. resolve/create `module_id`
3. upsert `panel_baselines`
4. update `panel_modules.baseline_pct`

## 4.3 RunUploadService

输入：

- `POST /api/v1/panel/runs`

事务步骤：

1. resolve `project_id`
2. upsert `panel_runs`
3. upsert current `panel_modules`
4. upsert `panel_checker_results`
5. commit

## 5. 读接口服务设计

## 5.1 ProjectOverviewQueryService

返回：

- 项目总览列表

查询步骤：

1. 查 `panel_projects`
2. 查每个项目最新 run
3. 查模块数
4. 组装响应

## 5.2 ProjectDetailQueryService

返回：

- 项目详情

查询步骤：

1. 查项目
2. 查模块快照
3. 查最新 run
4. 查该 run 下 checker 结果
5. 组装响应

## 5.3 LatestRunQueryService

返回：

- 最近一次 run 明细

查询步骤：

1. 查最新 run
2. 查 run 对应 checker 结果
3. 查模块快照
4. 组装响应

## 6. 事务建议

写接口都应使用事务。

原因：

- 防止 `panel_runs` 写成功但 `panel_checker_results` 未写完
- 防止 baseline 表更新成功但模块快照未同步

建议：

- 每个写接口请求一个事务
- 失败即回滚

## 7. 日志建议

每次写接口记录：

- `project_key`
- `run_key`（如有）
- upsert 行数
- 请求耗时
- 错误码

## 8. 错误码建议

- `VALIDATION_ERROR`
- `PROJECT_NOT_FOUND`
- `MODULE_NOT_FOUND`
- `RUN_NOT_FOUND`
- `CONFLICT_ERROR`
- `INTERNAL_ERROR`

## 9. 最终建议

`apps/api` 的实现应遵循：

- route 薄
- service 负责事务和业务流程
- repository 只负责单表
- 所有写接口幂等
- 所有读接口只查 DB，不读本地文件
