from flask import Blueprint, render_template
from ..auth import check_authentication
from ..models import Transaction, Document, Event, Asset

links_bp = Blueprint('links', __name__)

@links_bp.route('/api/links/<string:source_type>/<int:source_id>', methods=['GET'])
def get_links(source_type, source_id):
    if not check_authentication():
        return "Unauthorized", 401

    links = []

    if source_type == 'transaction':
        t = Transaction.query.get(source_id)
        if t:
            if t.document:
                links.append({
                    "type": "document",
                    "id": t.document.id,
                    "label": f"Document #{t.document.id}",
                    "note": t.document.note,
                    "url": f"/documents/{t.document.id}",
                    "filename": t.document.filename,
                    "timestamp": t.document.timestamp.strftime("%d %b %Y"),
                })
            if t.event:
                links.append({
                    "type": "event",
                    "id": t.event.id,
                    "label": f"Event #{t.event.id}",
                    "note": t.event.title,
                    "url": f"/events",
                    "timestamp": t.event.date.strftime("%d %b %Y"),
                })
            if t.asset:
                links.append({
                    "type": "asset",
                    "id": t.asset.id,
                    "label": f"Asset #{t.asset.id}",
                    "note": t.asset.name,
                    "url": f"/assets",
                    "status": t.asset.status.value if t.asset.status else "",
                })

    elif source_type == 'document':
        d = Document.query.get(source_id)
        if d and d.transactions:
            for t in d.transactions:
                links.append({
                    "type": "transaction",
                    "id": t.id,
                    "label": f"Transaction #{t.id}",
                    "note": t.note,
                    "url": f"/expenses",
                    "amount": f"{t.cost} {t.currency}",
                    "timestamp": t.timestamp.strftime("%d %b %Y"),
                })

    elif source_type == 'event':
        e = Event.query.get(source_id)
        if e and e.transactions:
            for t in e.transactions:
                links.append({
                    "type": "transaction",
                    "id": t.id,
                    "label": f"Transaction #{t.id}",
                    "note": t.note,
                    "url": f"/expenses",
                    "amount": f"{t.cost} {t.currency}",
                    "timestamp": t.timestamp.strftime("%d %b %Y"),
                })

    elif source_type == 'asset':
        a = Asset.query.get(source_id)
        if a and a.transactions:
            for t in a.transactions:
                links.append({
                    "type": "transaction",
                    "id": t.id,
                    "label": f"Transaction #{t.id}",
                    "note": t.note,
                    "url": f"/expenses",
                    "amount": f"{t.cost} {t.currency}",
                    "timestamp": t.timestamp.strftime("%d %b %Y"),
                })

    return render_template('partials/links_list.html', links=links)