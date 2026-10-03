---
status: accepted
---

# Add an optional Qt GUI over shared Proofshot services

Proofshot 0.3.0 will provide an optional PySide6 GUI, available through both `proofshot --gui` and a desktop-friendly `proofshot-gui` executable with a desktop launcher. The GUI will use existing project directories, `.proofshot.json`, and `.manifest.json` as its source of truth, while a versioned user-level workspace file stores ordered discovery paths. GUI and CLI behavior will share service-layer operations rather than invoking each other as subprocesses. This preserves CLI compatibility, avoids a second project database, and gives the GUI a durable path for future metadata such as captions.

## Considered options

- Make the GUI mandatory: rejected because the current CLI installation should remain lightweight.
- Store projects in a GUI-owned registry/database: rejected because it would create a second source of truth and weaken portability.
- Have the GUI shell out to CLI commands: rejected because parsing human-readable output would be fragile and make shared behavior harder to test.

## Consequences

The 0.3.0 work must extract reusable operations from orchestration code where necessary. The workspace can discover projects, but project configuration and image metadata remain project-local. Reordering columns requires an explicit persisted order while retaining stable names and screenshot manifest records.
