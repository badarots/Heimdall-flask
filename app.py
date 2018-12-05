from flask import Flask, render_template, flash, redirect, url_for, session, logging, request, g
from wtforms import Form, StringField, PasswordField, validators
from passlib.hash import pbkdf2_sha256
import sqlite3
from functools import wraps
from flask_mqtt import Mqtt

# config sqlite
app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = 'server'
app.config['MQTT_PASSWORD'] = '1234'
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
mqtt = Mqtt(app)

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

# register class
class RegisterForm(Form):
    name = StringField("Nome", [validators.Length(min=1, max=50)])
    username = StringField("Usuário", [validators.Length(min=4, max=25)])
    email = StringField("E-mail", [validators.Length(min=6, max=50)])
    passwd = PasswordField("Senha", [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Senhas são diferentes')
    ])
    confirm = PasswordField('Confirme a senha')

# user register
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
        cur.execute("INSERT INTO users( name, email, username, passwd) VALUES(?, ?, ?, ?)", (name, email, username, passwd))
        # commit
        cur.commit()
        # fechando conexão
        cur.close()

        # mensagem
        flash('Você está registrado', 'success')

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


# user login
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
@is_logged_in
def logout():
    session.clear()
    flash('Você está desconectado', 'success')
    return redirect(url_for('login'))

# user dashboard
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


# Controlo do MQTT
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


if __name__ == "__main__":
    app.secret_key = 'eitalasqueiravixenoistudo'
    app.run(debug=True)
