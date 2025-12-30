import re
import subprocess
import sys


def is_schema_change(diff_line: str) -> bool:
    """Check if a diff line represents a database schema change."""
    line = diff_line.strip()

    if not line.startswith(("+", "-")):
        return False

    line_content = line[1:].strip()

    if not line_content or line_content.startswith("#"):
        return False

    schema_patterns = [
        r"mapped_column\(",
        r"__tablename__\s*=",
        r"Mapped\[.*\]\s*=\s*mapped_column",
        r"ForeignKey\(",
        r"Index\(",
        r"UniqueConstraint\(",
        r"CheckConstraint\(",
        r"Column\(",
        r"Table\(",
    ]

    for pattern in schema_patterns:
        if re.search(pattern, line_content):
            return True

    return False


def main():
    """Check if model changes require a migration file."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    staged_files = result.stdout.strip().split("\n")

    model_files = [f for f in staged_files if f.startswith("app/models/") and f.endswith(".py")]

    if not model_files:
        sys.exit(0)

    result = subprocess.run(
        ["git", "diff", "--cached"] + model_files,
        capture_output=True,
        text=True,
        check=True,
    )
    diff_content = result.stdout

    has_schema_changes = any(is_schema_change(line) for line in diff_content.split("\n"))

    if has_schema_changes:
        migration_included = any(f.startswith("migrations/versions/") for f in staged_files)

        if not migration_included:
            print("ERROR: Model schema changes detected but no migration included!")
            print("Changes that require migrations:")
            print("  - New or modified mapped_column definitions")
            print("  - Table name changes")
            print("  - Foreign key changes")
            print("  - Index or constraint changes")
            print()
            print("Run: alembic revision --autogenerate -m 'your message'")
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
