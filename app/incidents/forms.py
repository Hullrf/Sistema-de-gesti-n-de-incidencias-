from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from app.models.incident import StatusEnum


class IncidentForm(FlaskForm):
    title       = StringField('Título',
                    validators=[DataRequired(), Length(3, 150)])
    description = TextAreaField('Descripción',
                    validators=[DataRequired(), Length(min=10)])
    status      = SelectField('Estado',
                    choices=[(s.value, s.value) for s in StatusEnum],
                    default=StatusEnum.PENDIENTE.value)
    submit      = SubmitField('Guardar')
