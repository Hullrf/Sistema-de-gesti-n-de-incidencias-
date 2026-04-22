from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

from app.dashboard import bp
from app.extensions import db
from app.models.incident import Incident, StatusEnum
from app.models.user import User


@bp.route('/')
@login_required
def index():
    # Admin puede filtrar por usuario via ?user_id=X
    filter_user_id = None
    filter_user = None
    users = []

    if current_user.is_admin:
        users = User.query.order_by(User.username).all()
        try:
            filter_user_id = int(request.args.get('user_id', 0)) or None
        except (ValueError, TypeError):
            filter_user_id = None
        if filter_user_id:
            filter_user = db.session.get(User, filter_user_id)

    # Últimas 5 incidencias (respetando filtro de rol/usuario)
    query = Incident.query
    if current_user.is_admin:
        if filter_user_id:
            query = query.filter(Incident.user_id == filter_user_id)
    else:
        query = query.filter(Incident.user_id == current_user.id)

    recent = query.order_by(Incident.created_at.desc()).limit(5).all()

    return render_template('dashboard/index.html',
                           recent=recent,
                           users=users,
                           filter_user_id=filter_user_id,
                           filter_user=filter_user,
                           StatusEnum=StatusEnum)


@bp.route('/api/stats')
@login_required
def stats():
    query = db.session.query(Incident.status, func.count(Incident.id))

    if current_user.is_admin:
        try:
            uid = int(request.args.get('user_id', 0)) or None
        except (ValueError, TypeError):
            uid = None
        if uid:
            query = query.filter(Incident.user_id == uid)
    else:
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
