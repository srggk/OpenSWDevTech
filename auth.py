from settings import *
from flask import Blueprint, flash, redirect, render_template, session, url_for
from forms import SignUpForm, LoginForm, LoginTwoFactorForm, ForgotPasswordForm, ChangePassword
from flask_login import login_user, current_user, logout_user, login_required
from db_models import User
import random

auth = Blueprint('auth', __name__, template_folder='templates')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('poke'))

    form = SignUpForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == form.email.data).first()
        if user:
            flash('Account with this email already exists.', 'error')
            return render_template('sign_up.html', form=form)

        user = User(name=form.name.data,
                    email=form.email.data,
                    password=form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('poke'))
        except Exception as e:
            db.session.rollback()
            print("ERROR DB: User failed to add\n", e)
            flash('Registration failed. Please try again later!', 'error')
    return render_template('sign_up.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('poke'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            code = random.randint(100000000, 999999999)
            print('CODE FOR LOGIN:', code)
            session['data_login'] = {'email': user.email, 'code': code}
            # send to email
            return redirect(url_for('auth.confirm_login'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html', form=form)


@auth.route('/confirm-login', methods=['GET', 'POST'])
def confirm_login():
    if current_user.is_authenticated:
        return redirect(url_for('poke'))
    
    form = LoginTwoFactorForm()
    if 'data_login' not in session:
        return redirect(url_for('auth.login'))
    if form.validate_on_submit():
        data_login = session['data_login']
        user = User.query.filter(User.email == data_login['email']).first()
        if user:
            if data_login['code'] == form.code.data:
                login_user(user)
                return redirect(url_for('poke'))
            else:
                flash('Confirmation code is incorrent.', 'error')
        else:
            flash('Unexpected error.', 'error')
    return render_template('login_two_factor.html', form=form)


@auth.route('/log-out')
@login_required
def log_out():
    if 'data_login' in session:
        session.pop('data_login')
    if 'data_to_change_password' in session:
        session.pop('data_to_change_password')
    logout_user()
    return redirect(url_for('poke'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('poke'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == form.email.data).first()
        if user:
            code = random.randint(100000000, 999999999)
            print('CODE FOR CHANGE PASSWORD:', code)
            session['data_to_change_password'] = {'email': user.email, 'code': code}
            # send to email
            return redirect(url_for('auth.change_password'))
        flash('Account with this email does not exist.', 'error')
    return render_template('forgot_password.html', form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if current_user.is_authenticated:
        return redirect(url_for('poke'))

    form = ChangePassword()
    if form.validate_on_submit():
        data_to_change_password = session['data_to_change_password']
        if form.code.data == data_to_change_password['code']:
            user = User.query.filter(User.email == data_to_change_password['email']).first()
            if user:
                user.password = user.get_password_hash(form.password.data)
                try:
                    db.session.commit()
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    db.session.rollback()
                    print("ERROR DB: User update password failed\n", e)
                    flash('Changing password failed. Please try again later!', 'error')
            else:
                flash('Unexpected error.', 'error')     
        flash('Confirmation code is incorrent.', 'error')
    return render_template('change_password.html', form=form)
