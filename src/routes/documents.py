import datetime
from flask import Blueprint, render_template, redirect, request, flash, session
from ..auth import check_authentication
from ..models import Document, User, db

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/documents', methods=['GET'])
def documents_get():
    if not check_authentication():
        return redirect("/login")
    
    documents = Document.query.all()
    return render_template('documents.html', documents=documents, username=session["username"])


@documents_bp.route('/documents/<int:id>', methods=['GET'])
def documents_get_view(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)
    if document:
        return render_template('view_document.html', document=document, username=session["username"])
    else:
        flash("Document not found.", "error")
        return redirect("/documents")


@documents_bp.route('/documents', methods=['POST'])
def documents_post():
    if not check_authentication():
        return redirect("/login")
    
    # Import here to avoid circular imports
    from ..app import save_upload
    
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
            flash("Invalid file type. Allowed: images (png, jpg, gif, webp) and PDF.", "error")
    else:
        flash("No file selected.", "error")
    return redirect("/documents")


@documents_bp.route('/documents/delete/<int:id>', methods=['POST'])
def documents_post_delete(id):
    if not check_authentication():
        return redirect("/login")

    document = Document.query.get(id)
    if document:
        db.session.delete(document)
        db.session.commit()
        flash("Document deleted successfully.", "success")
    else:
        flash("Document not found.", "error")
    return redirect("/documents")


@documents_bp.route('/documents/update/<id>', methods=['POST'])
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
