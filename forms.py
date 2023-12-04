from wtforms import StringField, SubmitField, TextAreaField,  BooleanField, PasswordField, EmailField, IntegerField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, InputRequired, EqualTo, Length


class SignUpForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=4, max=128)])
    email = EmailField('Email', validators=[DataRequired(), Email(message='Incorrent email address, try again')])
    password = PasswordField('Password', validators=[InputRequired(), DataRequired(), Length(min=8, max=64)])
    confirm  = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must equals')])
    submit = SubmitField('Sign up')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(message='Incorrent email address, try again')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class LoginTwoFactorForm(FlaskForm):
    code = IntegerField('Confirmation code from email to login', validators=[DataRequired()])
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(message='Incorrent email address, try again')])
    submit = SubmitField('Sent email to change password')

class ChangePassword(FlaskForm):
    code = IntegerField('Confirmation code from email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[InputRequired(), DataRequired(), Length(min=8, max=64)])
    confirm  = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must equals')])
    submit = SubmitField('Change password')
