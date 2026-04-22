from flask import render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app.dashboard import bp
from app.extensions import db
from app.models.incident import Incident, StatusEnum


@bp.route('/')
@login_required
def index():
    return render_template('dashboard/index.html')


@bp.route('/api/stats')
@login_required
def stats():
    query = db.session.query(Incident.status, func.count(Incident.id))

    if not current_user.is_admin:
        query = query.filter(Incident.user_id == current_user.id)

    results = query.group_by(Incident.status).all()

    counts = {s.value: 0 for s in StatusEnum}
    for status, count in results:
        counts[status.value] = count

    return jsonify({
        'labels': list(counts.keys()),
        'data':   list(counts.values()),
        'total':  sum(counts.values()),
    })
