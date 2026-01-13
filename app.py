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
    fichas = db.relationship('Personagem', backref='proprietario', lazy=True)

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

@app.route('/login-mestre', methods=['GET', 'POST'])
def login_mestre():
    if request.method == 'POST':
        senha_digitada = request.form.get('senha')
        # Buscamos o usuário mestre no banco
        mestre = User.query.filter_by(mestre=True).first()
        
        if mestre and mestre.senha == senha_digitada:
            login_user(mestre)
            return redirect(url_for('dashboard'))
        else:
            flash("Senha incorreta!")
            
    return render_template('login_mestre.html')

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
        arquetipo = request.form.get('arquetipo')

        file = request.files.get('imagem')
        filename = 'default.png'
        if file and file.filename != '':
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        forca = int(request.form.get('a_força', 0))
        instinto = int(request.form.get('a_instinto', 0))
        resistencia = int(request.form.get('a_resistência', 0))
        autoridade = int(request.form.get('a_autoridade', 0))
        mente = int(request.form.get('a_mente', 0))

        pv_max = 10 + (resistencia * 3)
        fluxo_max = 3 + mente
        paradoxo = 0

        pericias = {k.replace('p_', ''): int(v) if v.isdigit() else v 
                    for k, v in request.form.items() if k.startswith('p_')}
        pericias['oficio_definicao'] = request.form.get('oficio_nome', '')

        dados_ficha = {
            "arquetipo": arquetipo,
            "atributos": {
                "forca": forca, "instinto": instinto, "resistencia": resistencia, 
                "autoridade": autoridade, "mente": mente
            },
            "status": {
                "pv_max": pv_max, "pv_atual": pv_max,
                "fluxo_max": fluxo_max, "fluxo_atual": fluxo_max,
                "paradoxo": paradoxo
            },
            "pericias": pericias,
            "habilidades": request.form.get('habilidades', ''),
            "itens": [i.strip() for i in request.form.get('itens', '').split(',') if i.strip()]
        }

        novo_personagem = Personagem(
            nome=nome, 
            imagem=filename, 
            user_id=current_user.id, 
            dados=dados_ficha
        )
        db.session.add(novo_personagem)
        db.session.commit()
        
        return redirect(url_for('dashboard'))
    
    return render_template('criar.html')

@app.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    char = Personagem.query.get_or_404(id)
    if current_user.mestre or char.user_id == current_user.id:
        db.session.delete(char)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/visualizar/<int:id>')
@login_required
def visualizar(id):
    char = Personagem.query.get_or_404(id)

    if not current_user.mestre and char.user_id != current_user.id:
        return redirect(url_for('dashboard'))
        
    return render_template('visualizar.html', char=char)

if __name__ == '__main__':
    app.run(debug=True, port=5153)