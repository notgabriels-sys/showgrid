# Showgrid implementation plan

> **Implementation note:** Use test-first development on an isolated feature
> branch. Use generic examples only; do not use or claim verification against a
> real upcoming performance without a user-provided brief.

## Task 1: Models, parser, and plan validation

**Files:**

- Create: `pyproject.toml`
- Create: `src/showgrid/models.py`
- Create: `src/showgrid/parser.py`
- Create: `src/showgrid/validation.py`
- Create: `tests/test_parser.py`
- Create: `tests/test_validation.py`

1. Write failing tests for a valid plan and deterministic local validation
   errors.
2. Run the tests to demonstrate the missing-package failure.
3. Implement immutable models, TOML loading, time/date/timezone parsing, and
   declared-plan validation.
4. Re-run focused and complete tests, then commit.

## Task 2: Deterministic show documents

**Files:**

- Create: `src/showgrid/render.py`
- Create: `src/showgrid/build.py`
- Create: `tests/test_build.py`

1. Write failing tests for all five output files, declared-only wording,
   planned-clock calculations, and safe output creation.
2. Implement atomic output generation without absolute input paths.
3. Re-run focused and complete tests, then commit.

## Task 3: CLI, example, and docs

**Files:**

- Create: `src/showgrid/cli.py`
- Create: `tests/test_cli.py`
- Create: `examples/show-example.toml`
- Create: `README.md`
- Create: `LICENSE`

1. Write failing CLI tests for human and JSON checks, invalid plans, and builds.
2. Implement `check` and `build` without external actions.
3. Document the evidence boundary and included generic example.
4. Run the full suite, wheel/sdist build, and installed-command smoke test.
5. Commit the completed tool.

## Task 4: Publish and independently verify

1. Inspect the final diff and test evidence.
2. Create the GitHub repository, push the base and feature branches, and open
   a PR.
3. Confirm mergeability, merge it, and test a fresh remote clone.
4. Move to the next focused workflow tool after completion.
