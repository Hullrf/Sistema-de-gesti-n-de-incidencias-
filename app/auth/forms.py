from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(3, 80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit   = SubmitField('Iniciar sesión')


class RegisterForm(FlaskForm):
    username  = StringField('Usuario', validators=[DataRequired(), Length(3, 80)])
    password  = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar contraseña',
                              validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden.')])
    submit    = SubmitField('Registrarse')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Ese nombre de usuario ya está en uso.')
