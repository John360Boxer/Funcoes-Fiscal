from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Cidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

class Rua(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    idcidade = db.Column(db.Integer, db.ForeignKey('cidade.id'), nullable=False)

class Cliente(db.Model):
    placadocarro = db.Column(db.String(10), primary_key=True)
    cpf = db.Column(db.String(11), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)

class Fiscal(db.Model):
    cpf = db.Column(db.String(11), primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)

class Vaga(db.Model):
    idvaga = db.Column(db.Integer, primary_key=True)
    horaentrada = db.Column(db.DateTime, nullable=False)
    horasaida = db.Column(db.DateTime)
    idrua = db.Column(db.Integer, db.ForeignKey('rua.id'), nullable=False)
    placadocarro = db.Column(db.String(10), db.ForeignKey('cliente.placadocarro'))
    expirada = db.Column(db.Boolean, nullable=False)
