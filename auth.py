from settings import *
from flask import Blueprint, flash, redirect, render_template, request, make_response, jsonify, abort, url_for
from forms import SignUpForm
from db_models import User

auth = Blueprint('auth', __name__, template_folder='templates')

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
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
