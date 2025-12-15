import subprocess
import sys


def main():
    """Check if model changes are accompanied by a migration file."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    staged_files = result.stdout

    model_changed = "app/models/" in staged_files
    migration_included = "migrations/versions/" in staged_files

    if model_changed and not migration_included:
        print("ERROR: Model files changed but no migration included!")
        print("Run: alembic revision --autogenerate -m 'your message'")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
