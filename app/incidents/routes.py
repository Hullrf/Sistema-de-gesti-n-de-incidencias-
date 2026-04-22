from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.incidents import bp
from app.incidents.forms import IncidentForm
from app.models.incident import Incident, StatusEnum
from app.extensions import db


@bp.route('/')
@login_required
def list():
    if current_user.is_admin:
        incidents = Incident.query.order_by(Incident.created_at.desc()).all()
    else:
        incidents = (Incident.query
                     .filter_by(user_id=current_user.id)
                     .order_by(Incident.created_at.desc())
                     .all())
    return render_template('incidents/list.html', incidents=incidents, StatusEnum=StatusEnum)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def create():
    form = IncidentForm()
    if form.validate_on_submit():
        incident = Incident(
            title=form.title.data,
            description=form.description.data,
            status=StatusEnum(form.status.data),
            user_id=current_user.id,
        )
        db.session.add(incident)
        db.session.commit()
        flash('Incidencia creada exitosamente.', 'success')
        return redirect(url_for('incidents.list'))
    return render_template('incidents/create.html', form=form)


@bp.route('/<int:id>')
@login_required
def detail(id):
    incident = db.session.get(Incident, id) or abort(404)
    if not current_user.is_admin and incident.user_id != current_user.id:
        abort(403)
    return render_template('incidents/detail.html', incident=incident)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    incident = db.session.get(Incident, id) or abort(404)
    if not current_user.is_admin and incident.user_id != current_user.id:
        abort(403)

    form = IncidentForm(obj=incident)
    if form.validate_on_submit():
        incident.title       = form.title.data
        incident.description = form.description.data
        incident.status      = StatusEnum(form.status.data)
        db.session.commit()
        flash('Incidencia actualizada.', 'success')
        return redirect(url_for('incidents.detail', id=incident.id))

    # Pre-select current status on GET
    if not form.is_submitted():
        form.status.data = incident.status.value

    return render_template('incidents/edit.html', form=form, incident=incident)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin:
        abort(403)
    incident = db.session.get(Incident, id) or abort(404)
    db.session.delete(incident)
    db.session.commit()
    flash('Incidencia eliminada.', 'warning')
    return redirect(url_for('incidents.list'))
