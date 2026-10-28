# Proofshot Context

Proofshot organizes indexed screenshots inside project directories. The CLI and optional Qt GUI are two interfaces over the same project files and services.

## Workspace and projects

**Workspace**:
A user-level discovery configuration containing ordered paths whose immediate child directories can be opened as projects. A workspace is navigation state, not the owner of project data.

**Discovery path**:
A directory configured in the workspace whose immediate child directories are listed as projects.

**Project**:
An independent directory containing screenshots and optional Proofshot configuration and manifest files. The project directory is the source of truth for project data.

**Project browser**:
The GUI view that lists projects discovered from configured discovery paths and supports project creation, initialization, and opening.

## Screenshot organization

**Column**:
A named project category, such as Form, Proof, or a custom category, used to organize screenshot indices and naming.

**Gallery**:
A project view that lists screenshot images and supports filtering, selection, preview, and navigation to image details.

**Image detail**:
The full-size view of one screenshot together with its current derived metadata, including filename, project, column, index or range, dimensions, file size, and manifest status.

**Manifest record**:
A content-linked record that maps an image hash to its filename, column, and index or range. It preserves screenshot identity when filenames change.

**Derived metadata**:
Information calculated from the image, project files, or manifest rather than user-authored fields. Captions are intentionally not part of this set yet.
