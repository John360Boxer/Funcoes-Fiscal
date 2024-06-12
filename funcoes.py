from flask import Flask, jsonify, request
from models import db, Fiscal, Vaga
from datetime import datetime, timedelta
import locale

# Ajuste de locale para evitar problemas de codificação
try:
    locale.setlocale(locale.LC_CTYPE, 'Portuguese_Brazil.1252')
except locale.Error:
    print("Locale setting not supported. Using default locale.")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:brenodias@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from flask_cors import CORS
CORS(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print('Register Request JSON:', data)
    new_fiscal = Fiscal(
        cpf=data['cpf'],
        email=data['email'],
        senha=data['senha'],
        estado=data['estado'],
        cidade=data['cidade']
    )
    
    try:
        db.session.add(new_fiscal)
        db.session.commit()
        response = {'message': 'Fiscal registrado com sucesso!'}
        print('Register Response:', response)
        return jsonify(response), 201
    except Exception as e:
        error_response = {'message': 'Erro ao registrar fiscal.', 'error': str(e)}
        print('Register Error:', error_response)
        return jsonify(error_response), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print('Login Request JSON:', data)
    
    email = data['email']
    senha = data['senha']
    
    print('Login Email:', email, 'Senha:', senha)
    
    fiscal = Fiscal.query.filter_by(email=email).first()
    if not fiscal:
        return jsonify({'message': 'Email não encontrado no sistema.'}), 401
    
    if fiscal.senha != senha:
        return jsonify({'message': 'Senha incorreta.'}), 401
    
    response = {'message': 'Login realizado com sucesso!', 'cpf': fiscal.cpf}
    return jsonify(response)

@app.route('/fiscal_spot', methods=['POST'])
def get_fiscal_spots():
    data = request.get_json()
    cpf = data.get('cpf')
    nome_rua = data.get('nomeRua')

    if not cpf:
        return jsonify({'message': 'CPF do fiscal não fornecido.'}), 400

    if not nome_rua:
        return jsonify({'message': 'Nome da rua não fornecido.'}), 400

    fiscal = Fiscal.query.filter_by(cpf=cpf).first()
    if not fiscal:
        return jsonify({'message': 'Fiscal não encontrado.'}), 404

    current_time = datetime.now()

    # Consulta a rua pelo nome
    rua = Rua.query.filter_by(nome=nome_rua).first()
    if not rua:
        return jsonify({'message': 'Rua não encontrada.'}), 404

    # Consulta as vagas ativas na rua específica
    active_spots = Vaga.query.filter(
        Vaga.idrua == rua.id,
        Vaga.horasaida > current_time,
        Vaga.expirada == False
    ).all()

    if active_spots:
        response = [
            {
                'IDVaga': spot.idvaga,
                'horaEntrada': spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
                'horaSaida': spot.horasaida.strftime('%Y-%m-%d %H:%M:%S'),
                'placaDoCarro': spot.placadocarro
            } for spot in active_spots
        ]
        return jsonify(response), 200
    else:
        return jsonify({'message': 'Não há vagas ativas na rua especificada'}), 404
    
@app.route('/check_parking_state', methods=['POST'])
def check_parking_state():
    data = request.get_json()
    cpf = data.get('cpf')
    placa_do_carro = data.get('placaDoCarro')
    nome_rua = data.get('nomeRua')

    if not cpf:
        return jsonify({'message': 'CPF do fiscal não fornecido.'}), 400

    if not placa_do_carro:
        return jsonify({'message': 'Placa do carro não fornecida.'}), 400

    if not nome_rua:
        return jsonify({'message': 'Nome da rua não fornecido.'}), 400

    fiscal = Fiscal.query.filter_by(cpf=cpf).first()
    if not fiscal:
        return jsonify({'message': 'Fiscal não encontrado.'}), 404

    rua = Rua.query.filter_by(nome=nome_rua).first()
    if not rua:
        return jsonify({'message': 'Rua não encontrada.'}), 404

    current_time = datetime.now()

    # Consulta a vaga ativa para a placa fornecida
    active_spot = Vaga.query.filter(
        Vaga.placadocarro == placa_do_carro,
        Vaga.horasaida > current_time,
        Vaga.expirada == False
    ).first()

    if active_spot:
        # Verifica se a vaga ativa está na mesma rua
        if active_spot.idrua == rua.id:
            response = {
                'message': 'Veículo possui vaga ativa registrada nesta rua.',
                'vaga': {
                    'IDVaga': active_spot.idvaga,
                    'horaEntrada': active_spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
                    'horaSaida': active_spot.horasaida.strftime('%Y-%m-%d %H:%M:%S'),
                    'placaDoCarro': active_spot.placadocarro
                }
            }
        else:
            # Atualiza a rua da vaga ativa
            active_spot.idrua = rua.id
            db.session.commit()
            response = {
                'message': 'Veículo possuía vaga ativa em outra rua. Rua atualizada com sucesso.',
                'vaga': {
                    'IDVaga': active_spot.idvaga,
                    'horaEntrada': active_spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
                    'horaSaida': active_spot.horasaida.strftime('%Y-%m-%d %H:%M:%S'),
                    'placaDoCarro': active_spot.placadocarro
                }
            }
        return jsonify(response), 200
    else:
        # Consulta a vaga mais recente para a placa fornecida
        last_spot = Vaga.query.filter(
            Vaga.placadocarro == placa_do_carro
        ).order_by(Vaga.horasaida.desc()).first()

        tempo_max = last_spot.horaentrada + timedelta(minutes=15)

        if last_spot and last_spot.expirada == False:
            # Cria uma nova vaga com a opção expirada
            new_spot = Vaga(
                horaentrada=current_time,
                horasaida=None,
                idrua=rua.id,
                placadocarro=placa_do_carro,
                expirada=True
            )
            db.session.add(new_spot)
            db.session.commit()
            response = {
                'message': 'Veículo não possui vaga ativa. O proprietário tem 15 minutos para cadastrá-la, caso contrário você será solicitado para autuá-lo.',
                'vaga': {
                    'IDVaga': new_spot.idvaga,
                    'horaEntrada': new_spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
                    'horaSaida': new_spot.horasaida.strftime('%Y-%m-%d %H:%M:%S'),
                    'placaDoCarro': new_spot.placadocarro
                }
            }
            return jsonify(response), 200
        elif last_spot and last_spot.expirada == True:
            if current_time > tempo_max:
                return jsonify({'message': 'Proprietário não registrou uma vaga a tempo. Você está autorizado a autuá-lo.'}), 403
            else:
                mensagem = f'Autuação recusada. O proprietário tem até {tempo_max.strftime("%H:%M:%S")} para cadastrá-la.'
                return jsonify({'message': mensagem}), 403
        else:
            # Cliente não possuía uma vaga posteriormente. Cria uma nova vaga com a opção expirada
            new_spot = Vaga(
                horaentrada=current_time,
                horasaida=None,
                idrua=rua.id,
                placadocarro=placa_do_carro,
                expirada=True
            )
            db.session.add(new_spot)
            db.session.commit()
            response = {
                'message': 'Veículo não possui vaga ativa. O proprietário tem 15 minutos para cadastrá-la, caso contrário você será solicitado para autuá-lo.',
                'vaga': {
                    'IDVaga': new_spot.idvaga,
                    'horaEntrada': new_spot.horaentrada.strftime('%Y-%m-%d %H:%M:%S'),
                    'horaSaida': new_spot.horasaida.strftime('%Y-%m-%d %H:%M:%S'),
                    'placaDoCarro': new_spot.placadocarro
                }
            }
            return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)
