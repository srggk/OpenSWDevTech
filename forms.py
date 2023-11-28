from wtforms import StringField, SubmitField, TextAreaField,  BooleanField, PasswordField, EmailField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, InputRequired, EqualTo, Length


class SignUpForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=4, max=128)])
    email = EmailField('Email', validators=[DataRequired(), Email(message='Incorrent email address, try again')])
    password = PasswordField('Password', validators=[InputRequired(), DataRequired(), Length(min=8, max=64)])
    confirm  = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must equals')])
    submit = SubmitField('Sign Up')
