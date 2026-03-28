# QA Automation Test Spec

## Required Case Families

- Happy path: target code exists and Analyzer produces testable units
- Error path: unsupported framework or no test entry point returns a clear failure reason
- Boundary path: re-running the same change must not produce duplicate side effects
- Regression path: baseline pass -> current fail must be blocked
- Coverage path: coverage drop exceeding the threshold must emit a warning

## Mandatory Assertions

- Output structure must be stable and directly consumable by an Agent or CI pipeline
- Generated tests must not be written into the application's own test directories
- Baseline must not be updated without explicit confirmation
- Results must distinguish between `failed`, `regressed`, and `warning`
