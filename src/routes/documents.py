import datetime
import os

from flask import Blueprint, flash, redirect, render_template, request, session

from ..auth import check_authentication
from ..models import Document, Transaction, User, db
from ..utils.config import UPLOAD_FOLDER

documents_bp = Blueprint("documents", __name__)


@documents_bp.route("/documents", methods=["GET"])
def documents_get():
    if not check_authentication():
        return redirect("/login")

    documents = Document.query.all()
    # Count linked transactions for each document
    doc_transaction_counts = {
        doc.id: Transaction.query.filter_by(document_id=doc.id).count()
        for doc in documents
    }
    return render_template(
        "documents.html",
        documents=documents,
        doc_transaction_counts=doc_transaction_counts,
        username=session["username"],
    )


@documents_bp.route("/documents/<int:id>", methods=["GET"])
def documents_get_view(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)
    if document:
        return render_template(
            "view_document.html", document=document, username=session["username"]
        )
    else:
        flash("Document not found.", "error")
        return redirect("/documents")


@documents_bp.route("/documents", methods=["POST"])
def documents_post():
    if not check_authentication():
        return redirect("/login")

    from ..utils import save_upload

    # Get form data
    file = request.files.get("document_file")
    note = request.form.get("document_note") or (file.filename if file else "")
    timestamp = datetime.datetime.now()
    uploader = User.query.filter_by(username=session["username"]).first()

    if file and file.filename != "":
        saved_name = save_upload(file)
        if saved_name:
            new_document = Document(
                note=note,
                timestamp=timestamp,
                filename=saved_name,
                uploaded_by=uploader.id,
            )
            db.session.add(new_document)
            db.session.commit()
            flash("Document uploaded successfully.", "success")
        else:
            flash(
                "Invalid file type. Allowed: images (png, jpg, gif, webp) and PDF.",
                "error",
            )
    else:
        flash("No file selected.", "error")
    return redirect("/documents")


@documents_bp.route("/documents/delete/<int:id>", methods=["POST"])
def documents_post_delete(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)
    if document:
        # Clear document_id from any linked transactions
        Transaction.query.filter_by(document_id=id).update({"document_id": None})

        # Store filename before deleting row
        filename = document.filename

        db.session.delete(document)
        db.session.commit()

        # NOTE: Deleting a Document also deletes its file from uploads/
        if filename:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        flash("Document deleted successfully. Linked transactions updated.", "success")
    else:
        flash("Document not found.", "error")
    return redirect("/documents")


@documents_bp.route("/documents/update/<id>", methods=["POST"])
def documents_post_update(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)

    if document:
        document.note = request.form.get("document_note")
        db.session.commit()
        flash("Document updated successfully.", "success")
    else:
        flash("Document not found.", "error")
    return redirect(f"/documents/{id}")
