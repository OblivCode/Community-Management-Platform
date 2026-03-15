from flask import Blueprint, jsonify, render_template, redirect, request, flash

from ..auth import check_authentication
from ..models import Asset, AssetStatus, db

assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/assets', methods=['GET'])
@assets_bp.route('/assets/<id>', methods=['GET'])
def assets_get(id=None):
    if not check_authentication():
        return redirect("/login")
    
    if id:
        # Get specific asset
        asset = Asset.query.get(id)
        return jsonify({
            "id": asset.id,
            "name": asset.name,
            "location": asset.location,
            "status": asset.status,
            "count": asset.count
        })
    else:
        # Get all assets
        assets = Asset.query.all()
        asset_status_options = [status.value for status in AssetStatus]
        return render_template('assets.html', assets=assets, asset_status_options=asset_status_options)


@assets_bp.route('/assets/<operation>', methods=['POST'])
def assets_post(operation=None):
    if not check_authentication():
        return redirect("/login")
    
    # Import here to avoid circular imports
    from ..app import save_upload
    
    # "add", "update", "delete"
    if operation == "add":
        name = request.form.get("name")
        location = request.form.get("location")
        status_str = request.form.get("status")
        status = AssetStatus(status_str) if status_str else AssetStatus.FINE
        count = request.form.get("count")

        # Ensure name is unique
        existing_asset = Asset.query.filter_by(name=name).first()
        if existing_asset:
            flash("Asset with this name already exists.", "error")
        else:
            asset_image = request.files.get("asset_image")
            asset_filename = save_upload(asset_image) if asset_image and asset_image.filename else None
            new_asset = Asset(name=name, location=location, status=status, count=count, filename=asset_filename)
            db.session.add(new_asset)
            db.session.commit()
    elif operation == "update":
        id = request.form.get("id")
        asset = Asset.query.get(id)
        if asset:
            asset.name = request.form.get("name")
            # Ensure name is unique
            existing_asset = Asset.query.filter_by(name=asset.name).first()
            if existing_asset and existing_asset.id != asset.id:
                flash("Asset with this name already exists.", "error")
                return redirect("/assets")

            asset.location = request.form.get("location")
            status_str = request.form.get("status")
            asset.status = AssetStatus(status_str) if status_str else AssetStatus.FINE
            asset.count = request.form.get("count")
            asset_image = request.files.get("asset_image")
            if asset_image and asset_image.filename:
                saved = save_upload(asset_image)
                if saved:
                    asset.filename = saved
            db.session.commit()
        else:
            flash(f"Could not update asset with ID {id}: Asset not found", "error")
    elif operation == "delete":
        id = request.form.get("id")
        asset = Asset.query.get(id)
        if asset:
            db.session.delete(asset)
            db.session.commit()
        else:
            flash(f"Could not delete asset with ID {id}: Asset not found", "error")
    else:
        flash("Invalid operation.", "error")
    return redirect("/assets")
