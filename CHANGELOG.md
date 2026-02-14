# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-02-14

### Added
- Interactive prompt for missing endpoint variables in `oko endpoint run`.
- Runtime variable compact flag: `--vars key1=v1,key2=v2`.
- Request preview mode with `--dry-run` (resolve and display request without sending).
- Automatic API docs generator for `.oko/README.md`.
- Runtime variable history by endpoint, with default suggestions in prompts.

### Changed
- Improved prompt styling for missing variables using the current Rich theme.
- Endpoint request resolution was centralized via `prepare_endpoint_request(...)`.
- README was redesigned in Spanish with a full, consistent API example flow.

### Fixed
- Missing/unresolved variables are validated before request execution to avoid perceived hangs.
- Clear actionable error messages when variables are missing.

