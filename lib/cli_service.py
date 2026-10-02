"""Command-line definition and dispatch metadata for Proofshot."""

import argparse
from collections.abc import Callable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Operation:
    """A named operation, its argument predicate, and optional handler."""

    name: str
    predicate: Callable[[argparse.Namespace], bool]
    handler: Callable[..., object] | None = None


class CLIService:
    """Owns CLI arguments, operation registration, and argument combinations."""

    PROJECT_OPERATIONS = (
        "rename_column", "add_column", "remove_column", "add_screenshot",
        "remove_screenshot", "set_prefix", "set_suffix", "set_column_prefix",
        "set_column_suffix", "set_variable", "set_index_label", "show_config",
        "show_columns", "package", "upgrade_project",
    )

    def __init__(self, version: str):
        self.parser = argparse.ArgumentParser(
            prog="proofshot",
            description="Capture screenshots with automatic question numbering and proof tracking.",
            epilog="""Examples:
  proofshot -D ~/HTB/module         Set working directory
  proofshot -Q 5                    Capture question 5 (FORM default)
  proofshot -Q 5-7 --proof          Capture questions 5-7 as proof
  proofshot -P                      Shortcut for --proof
  proofshot -N                      Auto-increment by 1
  proofshot -N 2 -S                 Capture the complete next span
  proofshot --init ModuleName       Create folder, reset indices, persist
  proofshot -L                      List all indexed questions
  proofshot -V 5                    Open the image at index 5
  proofshot -W                      Show current working directory""",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._add_arguments(version)
        self._operations: list[Operation] = []
        self.register_operations(self.PROJECT_OPERATIONS)

    def _add_arguments(self, version: str) -> None:
        p = self.parser
        p.add_argument("--version", action="version", version=f"%(prog)s {version}")
        p.add_argument("--uninstall", action="store_true", help="Remove the installed proofshot command (keeps saved settings)")
        p.add_argument("--update", action="store_true", help="Download and install the latest GitHub release")
        p.add_argument("--provider", metavar="NAME", help="Set the screenshot provider (flameshot or gnome-screenshot)")
        p.add_argument("--install", action="store_true", help="Install dependencies for the selected screenshot provider")
        p.add_argument("--list-providers", action="store_true", help="List available screenshot providers")

        questions = p.add_argument_group("Question Parameters")
        questions.add_argument("-Q", "--question", metavar="NUM", help="Specify question number directly (e.g., '5' or '5-7')")
        questions.add_argument("-N", "--next", nargs="?", const=1, type=int, metavar="STEP", help="Auto-increment from last question")
        questions.add_argument("-S", "--span", action="store_true", help="Include all questions in a -N span")
        questions.add_argument("-I", "--index", type=int, metavar="NUMBER", help="Set or capture at the selected category index")
        questions.add_argument("-C", "--category", metavar="NAME_OR_COLUMN", help="Category name or zero-based column")
        questions.add_argument("--name", metavar="PREFIX", help="Custom filename prefix")
        questions.add_argument("--init", metavar="NAME", help="Create and initialize a project folder")

        project = p.add_argument_group("Project Parameters")
        project_ops = project.add_mutually_exclusive_group()
        project_ops.add_argument("--rename-column", nargs=2, metavar=("OLD", "NEW"))
        project_ops.add_argument("--add-column", metavar="NAME")
        project_ops.add_argument("--remove-column", metavar="NAME")
        project_ops.add_argument("--show-config", action="store_true")
        project_ops.add_argument("--show-columns", action="store_true")
        project_ops.add_argument("--set-prefix", metavar="TEMPLATE")
        project_ops.add_argument("--set-suffix", metavar="TEMPLATE")
        project_ops.add_argument("--set-column-prefix", nargs=2, metavar=("COLUMN", "TEMPLATE"))
        project_ops.add_argument("--set-column-suffix", nargs=2, metavar=("COLUMN", "TEMPLATE"))
        project_ops.add_argument("--set-variable", nargs=2, metavar=("NAME", "VALUE"))
        project_ops.add_argument("--set-index-label", metavar="LABEL")
        project_ops.add_argument("--package", action="store_true")
        project_ops.add_argument("--upgrade-project", action="store_true")
        project_ops.add_argument("--add-screenshot", metavar="PATH")
        project_ops.add_argument("--remove-screenshot", metavar="NAME")

        directory = p.add_argument_group("Directory Parameters")
        directory.add_argument("-D", "--dir", metavar="PATH")
        directory.add_argument("-W", "--where", action="store_true")
        directory.add_argument("-L", "--list", action="store_true")
        directory.add_argument("-V", "--view", type=int, metavar="NUMBER", help="Open the image at an index in the default image viewer")

        types = p.add_mutually_exclusive_group()
        types.add_argument("-p", "--proof", action="store_true")
        types.add_argument("-P", action="store_true", dest="proof_shortcut")
        types.add_argument("-f", "--form", action="store_true")
        p.add_argument("--force", action="store_true")
        p.add_argument("--quiet", action="store_true")

    def register_operation(self, name: str, predicate: Callable[[argparse.Namespace], bool], handler: Callable[..., object] | None = None) -> None:
        """Register a future operation without changing parser control flow."""
        self._operations.append(Operation(name, predicate, handler))

    def register_operations(self, names: Iterable[str]) -> None:
        for name in names:
            self.register_operation(name, lambda args, name=name: bool(getattr(args, name, False)))

    def parse_args(self, argv: list[str] | None = None) -> argparse.Namespace:
        args = self.parser.parse_args(argv)
        self.validate(args)
        return args

    def validate(self, args: argparse.Namespace) -> None:
        if args.span and args.next is None:
            self.parser.error("-S can only be used with -N")
        if args.index is not None and args.question is not None:
            self.parser.error("-I cannot be combined with -Q")
        if args.view is not None and args.view < 0:
            self.parser.error("-V NUMBER requires a non-negative index")

    def has_project_operation(self, args: argparse.Namespace) -> bool:
        return any(operation.predicate(args) for operation in self._operations)
