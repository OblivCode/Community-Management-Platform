import datetime
from flask import Blueprint, render_template, redirect, request, session, flash
from ..auth import check_authentication
from ..models import Event, db

events_bp = Blueprint('events', __name__)

# Route to list all events
@events_bp.route('/events', methods=['GET'])
def events_get():
    # make sure they are logged in
    if not check_authentication():
        return redirect("/login")
    
    # grab all events and order them by date
    events = Event.query.order_by(Event.date.desc()).all()
    
    return render_template(
        'events.html', 
        events=events,
        username=session.get("username")
    )

# Route to handle adding a new event
@events_bp.route('/events', methods=['POST'])
def events_post():
    # security check
    if not check_authentication():
        return redirect("/login")
        
    title = request.form.get("title")
    description = request.form.get("description")
    date_str = request.form.get("date")
    
    # validate form data
    if not title or not date_str:
        flash("You need a title and a date to create an event!", "error")
        return redirect("/events")
        
    # parse the date from the form
    try:
        if 'T' in date_str:
            event_date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        else:
            event_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        flash("Oops, date format is wrong.", "error")
        return redirect("/events")
        
    # make a new event object and save it
    new_event = Event(
        title=title,
        description=description,
        date=event_date
    )
    db.session.add(new_event)
    db.session.commit()
    
    flash("Event added successfully!", "success")
    return redirect("/events")

@events_bp.route('/events/update', methods=['POST'])
def events_update():
    if not check_authentication():
        return redirect("/login")
        
    event_id = request.form.get("id")
    title = request.form.get("title")
    description = request.form.get("description")
    date_str = request.form.get("date")
    
    if not event_id or not title or not date_str:
        flash("Missing info for event update.", "error")
        return redirect("/events")
        
    event = db.session.get(Event, event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect("/events")
        
    try:
        if 'T' in date_str:
            event.date = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        else:
            event.date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format.", "error")
        return redirect("/events")
        
    event.title = title
    event.description = description
    db.session.commit()
    flash("Event updated successfully!", "success")
    return redirect("/events")

@events_bp.route('/events/delete', methods=['POST'])
def events_delete():
    if not check_authentication():
        return redirect("/login")
        
    event_id = request.form.get("id")
    if not event_id:
        return redirect("/events")
        
    event = db.session.get(Event, event_id)
    if event:
        db.session.delete(event)
        db.session.commit()
        flash("Event deleted successfully!", "success")
    
    return redirect("/events")