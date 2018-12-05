from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, g
from wtforms import Form, StringField, PasswordField, validators
from passlib.hash import pbkdf2_sha256
import sqlite3
from functools import wraps
from flask_mqtt import Mqtt
import sys

# Outros scripts
from email_token import generate_token, confirm_token


app = Flask(__name__)

# Configurando MQTT
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'server'
app.config['MQTT_PASSWORD'] = '1234'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
mqtt = Mqtt(app)

# Configurando bando de dados
DATABASE = 'fechadura.db'

# Abre banco de dados
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

# Pesquisa no banco de dados
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# inicializa banco de dados
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Index
@app.route('/')
def index():
    return render_template('home.html')

# Sobre
@app.route('/about')
def about():
    return render_template('about.html')

# Register class
class RegisterForm(Form):
    username = StringField("Usuário", [validators.Length(min=1, max=25)])
    name = StringField("Nome", [validators.Length(min=1, max=50)])
    email = StringField("E-mail", [validators.Length(min=1, max=50)])
    passwd = PasswordField("Senha", [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Senhas são diferentes'),
    ])
    confirm = PasswordField('Confirme a senha')


# User register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    print(form.validate())
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        passwd = pbkdf2_sha256.hash(str(form.passwd.data))

        # adcionando usuário ao banco de dados
        cur = get_db()
        try:
            cur.execute("INSERT INTO users( username, name, email, passwd ) VALUES(?, ?, ?, ?)", (username, name, email, passwd))
            # commit
            cur.commit()
        except Exception as e:
            flash('Erro: ' + str(e), 'danger')
        else:
            # mensagem
            # flash('Você está registrado', 'success')
            flash('O link de confirmção foi enviado para o seu e-mail', 'success')
            token = generate_token(email)
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('activate.html', confirm_url=confirm_url)
            subject = "HackerSpace.IFUSP: confirmação de e-mail"

            # return redirect(url_for('home'))
            return html

        # fechando conexão
        cur.close()
    elif request.method == 'POST':
        flash('Campos incorretor', 'danger')

    return render_template('register.html', form=form)


# Confirmação por email
@app.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('O link de confirmação é inválido ou expirou', 'danger')
        return render_template('404.html')

    else:
        user = query_db('SELECT * FROM users WHERE email=?', (email,), one=True)

        if user['confirmed']:
            flash('Conta já confirmada', 'success')
        else:
            cur = get_db()
            cur.execute('UPDATE users SET confirmed=1 WHERE email=?', (email,))
            # commit
            cur.commit()
            # fechando conexão
            cur.close()
            flash("Conta confirmada com sucesso", 'success')
        return redirect(url_for('login'))


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        passwd_cadidate = request.form['password']

        # get db
        result = query_db("SELECT * FROM users WHERE username=?", (username,), one=True)

        if result is not None:
            # get stored hash
            passwd = result['passwd']

            # comparando senhas
            if pbkdf2_sha256.verify(passwd_cadidate, passwd):
                # passou
                app.logger.info('SENHA CORRETA')
                session['logged_in'] = True
                session['username'] = username

                flash('Você está conectado', 'success')
                return redirect(url_for('dashboard'))
            else:
                app.logger.info('SENHA INCORRETA')
                error = 'Senha incorreta'
                return render_template('login.html', error=error)
        else:
            app.logger.info('USUÁRIO NÃO ENCONTRADO')
            error = 'Usuário não encontrado'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Nâo autorizado', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você está desconectado', 'success')
    return redirect(url_for('login'))

# User dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

# Abrir fechadura
@app.route('/open_door')
@is_logged_in
def open_door():
        # adcionando log de abertura
        cur = get_db()
        cur.execute("INSERT INTO log( msg ) VALUES(?)", ("Pedido de liberação: {}".format(session['username']),))
        # commit
        cur.commit()
        # fechando conexão
        cur.close()

        # mensagem
        flash('Porta liberada, seja livre!', 'success')

        # publica pedido de abertura da porta
        mqtt.publish('fechadura', 'liberar')

        return redirect(url_for('dashboard'))


# Controle do MQTT
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('server')

@mqtt.on_message()
def handle_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    app.logger.info('MENSAGEM -> {}: {}'.format(data['topic'], data['payload']))

    # adcionando log de abertura
    cur = get_db()
    cur.execute("INSERT INTO log( msg ) VALUES(?)", ("Porta liberada",))
    # commit
    cur.commit()
    # fechando conexão
    cur.close()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.errorhandler(404)
def page_not_found(e):
    #snip
    return render_template('404.html'), 404


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        db = sqlite3.connect(DATABASE)
        with open('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        print('Banco de dados criado')

    else:
        app.secret_key = 'eitalasqueiravixenoistudo'
        app.run(debug=True)
