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

- `analyzed -> failed`: target repository language or test framework cannot be identified
- `generated -> failed`: generated tests fail static validation
- `executed -> regressed`: baseline passed but current run failed
- `compared -> warning`: coverage dropped but did not reach the blocking threshold

## Success Standard

- Caller receives a structured test report within a single pipeline run
- Report must include at minimum: pass count, fail count, regression verdict, coverage delta
- Any baseline update must be explicitly triggered
