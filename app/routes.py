from flask import render_template, flash, redirect, url_for, request, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, LogPorta
from app.email import send_password_reset_email, send_activation_email
from app.mqtt import open_door_request
import os


# Home
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


# Sobre
@app.route('/about')
def about():
    return render_template('about.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuário ou senha incorreto', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    return render_template('login.html', form=form)


# Logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# Cadastro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Show, você está cadastrado!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Pedido de reformulação senha
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Um e-mail com sua nova senha foi enviado, cheque sua caixa de entrada', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', form=form)


# Resetando a senha
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_token('reset_password', token)
    if not user:
        flash('Pedido inválido, gere um novo pedido para alterar sua senha.', 'danger')
        return redirect(url_for('home'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Sua senha foi alterada.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


# Enviar email de ativação
@app.route('/send_activation')
@login_required
def send_activation():
    flash('E-mail de ativação enviado, verifique sua caixa de entrada', 'success')
    send_activation_email(current_user)
    return redirect(url_for('home'))


# Realiza ativação
@app.route('/activation/<token>')
def activation(token):
    if current_user.active:
        return redirect(url_for('home'))
    user = User.verify_token('activation', token)
    if not user:
        flash('Pedido inválido, gere um novo pedido para ativar sua conta.', 'danger')
        return redirect(url_for('home'))
    user.active = True
    db.session.commit()
    flash('Sua conta foi ativada com sucesso!', 'success')
    if not current_user.is_authenticated:
        login_user(user)
    return redirect(url_for('home'))


# Painel de controle
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.active:
        return render_template('dashboard.html', user=current_user)
    else:
        return render_template('send_activation.html')


# Liberar porta
@app.route('/open_door')
@login_required
def open_door():
    open_door_request()
    log = LogPorta(msg='Porta liberada', author=current_user)
    db.session.add(log)
    db.session.commit()
    flash('Porta liberada!', 'success')
    return redirect(url_for('dashboard'))

