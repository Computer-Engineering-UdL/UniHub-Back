from sqlalchemy.exc import IntegrityError


def extract_constraint_info(exc: IntegrityError) -> str:
    """Extract constraint violation info safely without leaking DB details."""
    error_msg = str(exc.orig).lower()

    if "unique constraint" in error_msg or "duplicate" in error_msg:
        if "email" in error_msg:
            return "Email already exists"
        elif "username" in error_msg:
            return "Username already taken"
        return "This value already exists"

    elif "foreign key constraint" in error_msg:
        return "Invalid reference to related resource"

    elif "not null constraint" in error_msg:
        return "Missing required field"

    elif "check constraint" in error_msg:
        return "Invalid field value"

    return "Database operation failed"
