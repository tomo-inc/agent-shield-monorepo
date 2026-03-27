# QA Automation User Flow

## Primary Flow

```text
requested
  -> analyzed
  -> generated
  -> executed
  -> compared
  -> reported
```

## Failure Paths

- `analyzed -> failed`: 目标仓库无法识别语言或测试框架
- `generated -> failed`: 生成的测试无法通过静态校验
- `executed -> regressed`: baseline pass 但本次 fail
- `compared -> warning`: 覆盖率下降，但未到阻断阈值

## Success Standard

- 调用方在一次流水线里拿到结构化测试报告
- 报告至少包含通过数、失败数、回归结论、覆盖率变化
- 任何 baseline 更新都必须显式触发
