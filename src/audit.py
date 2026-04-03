from flask import has_request_context, session
from sqlalchemy import event, inspect, insert
from datetime import datetime

from .models import ActionLog, Asset, Document, Transaction, User


# Helpers
def get_current_user_id():
    if not has_request_context() or not session.get("username"):
        return None

    user = User.query.filter_by(username=session.get("username")).first()
    if user:
        return user.id
    return None


def get_changed_fields(target) -> dict[str, list]:  # Returns field: (old_value, new_value)
    changes: dict[str, list] = {}

    inspector = inspect(target)
    fields = ["name", "location", "status", "count", "filename", "upload_date", "parent_id", "cost", "note", "timestamp", "category"]

    for field in fields:
        # 1. Check if field exists
        if not hasattr(target, field):
            continue
        # 2. Check if field has changed
        history = inspector.attrs.get(field).history

        # 3. If changed, get old and new values
        if history.has_changes():
            old_value = history.deleted[0] if history.deleted else None
            new_value = history.added[0] if history.added else None
            changes[field] = [old_value, new_value]
    return changes


# Audit logging
def log(connection, target, action):
    # 1. Get current user ID
    user_id = get_current_user_id()
    if not user_id:
        print(f"[AUDIT] Anonymous user performed '{action}' on record ID {target.id}.")
        return

    # 2. Prepare log entry
    table_name = target.__tablename__
    target_name = getattr(target, "name", str(target.id))
    print(f"[AUDIT] User '{user_id}' {action} on '{table_name}' for {target_name} (ID: {target.id})")

    # 3. Get changed fields for update action
    if action == "update":
        changes = get_changed_fields(target)
        details = f"Changed {target_name} (ID: {target.id}) on {table_name}s: "
        # Append each changed field
        for field in changes:
            values = changes[field]
            old, new = values
            details += f"{field} from '{old}' to '{new}'; "
    else:
        details = f"{action.capitalize()}d {target_name} (ID: {target.id}) on {table_name}s."

    # 4. Insert into ActionLog table
    stmt = insert(ActionLog).values(
        user_id=user_id,
        action_type=action,
        details=details,
        timestamp=datetime.now(),
    )
    connection.execute(stmt)


# Listeners
@event.listens_for(Asset, "after_insert")
@event.listens_for(Document, "after_insert")
@event.listens_for(Transaction, "after_insert")
def after_insert(mapper, connection, target):
    log(connection, target, "insert")


@event.listens_for(Asset, "after_update")
@event.listens_for(Document, "after_update")
@event.listens_for(Transaction, "after_update")
def after_update(mapper, connection, target):
    log(connection, target, "update")


@event.listens_for(Asset, "after_delete")
@event.listens_for(Document, "after_delete")
@event.listens_for(Transaction, "after_delete")
def after_delete(mapper, connection, target):
    log(connection, target, "delete")