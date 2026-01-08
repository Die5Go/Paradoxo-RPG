import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_key_rpg'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rpg.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True)
    senha = db.Column(db.String(100))
    mestre = db.Column(db.Boolean, default=False)

class Personagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    imagem = db.Column(db.String(200), default='default.png')
    dados = db.Column(db.JSON)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    lista_usuarios = User.query.all()
    return render_template('login.html', users=lista_usuarios)

@app.route('/login/<int:user_id>')
def login_player(user_id):
    user = User.query.get(user_id)
    if not user.mestre:
        login_user(user)
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_mestre'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.mestre:
        personagens = Personagem.query.all()
    else:
        personagens = Personagem.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', personagens=personagens)

@app.route('/criar', methods=['GET', 'POST'])
@login_required
def criar():
    if request.method == 'POST':
        nome = request.form.get('nome')
        file = request.files.get('imagem')
        filename = 'default.png'
        if file:
            filename = secure_filename(file, filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        dados_ficha = {
            "atributos": {
                "forca": request.form.get('forca'),
                "destreza": request.form.get('destreza')
            },
            "itens": request.form.get('itens').split(',')
        }

        novo_personagem = Personagem(nome=nome, imagem=filename, user_id=current_user.id, dados=dados_ficha)
        db.session.add(novo_personagem)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('criar.html')

if __name__ == '__main__':
    app.run(debug=True, port=5153)