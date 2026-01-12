# Test Case Template (TC)

Use this template for creating executable test cases that define HOW to test.

---
id: TC-XXX
level: verification
title: [Specific test scenario]
type: test-case
status: [draft|passed|failed|pending]
owner: [QA engineer]
created: [YYYY-MM-DD]
last_updated: [YYYY-MM-DD]
links:
  tests: [TRQ-XXX]
---

# TC-XXX: [Title]

## Test Description
[Brief description of what this test case validates.]

## Preconditions
- [Setup requirement 1]
- [Setup requirement 2]
- [Any data or environment setup needed]

## Test Steps
1. **Step description**
   - [Sub-step or detail]
   - [Expected behavior at this point]

2. **Step description**
   - [Sub-step or detail]

3. **Step description**

## Expected Results
- [Expected outcome 1]
- [Expected outcome 2]
- [How to verify success]

## Actual Results
[Fill in after test execution]

## Test Evidence
- [Log files location, e.g., `logs/tc-XXX-execution.log`]
- [Screenshots: `screenshots/tc-XXX-*.png`]
- [Test data: `test-data/tc-XXX-*.json`]

## Notes
[Any observations, issues, or follow-up items.]