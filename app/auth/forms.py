from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(3, 80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit   = SubmitField('Iniciar sesión')
