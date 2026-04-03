from flask import has_request_context, session
from sqlalchemy import event, inspect, insert
from datetime import datetime

from .models import ActionLog, Asset, Document, Transaction, User


# Helpers
def get_current_user_id():
    if not has_request_context() or not session.get("user_id"):
        return None

    return session.get("user_id")


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
    user_id = get_current_user_id()
    if not user_id:
        return
    
    table_name = target.__tablename__
    target_name = getattr(target, 'name', str(target.id))

    if action == "update":
        changes = get_changed_fields(target)
        details = f"Changed {target_name} (ID: {target.id}) on {table_name}s: "
        for field in changes:
            old, new = changes[field]
            details += f"{field} from '{old}' to '{new}'; "
    else:
        details = f"{action.capitalize()}d {target_name} (ID: {target.id}) on {table_name}s."
    
    # The new ORM-safe way to insert
    stmt = insert(ActionLog).values(
        user_id=user_id, 
        action_type=action, 
        details=details, 
        timestamp=datetime.now()
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