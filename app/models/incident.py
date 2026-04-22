from app.extensions import db
from datetime import datetime, timezone
import enum


class StatusEnum(str, enum.Enum):
    PENDIENTE  = 'Pendiente'
    EN_PROCESO = 'En proceso'
    RESUELTO   = 'Resuelto'


class Incident(db.Model):
    __tablename__ = 'incidents'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status      = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.PENDIENTE)
    created_at  = db.Column(db.DateTime, nullable=False,
                            default=lambda: datetime.now(timezone.utc))
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Incident #{self.id} "{self.title}" [{self.status.value}]>'
