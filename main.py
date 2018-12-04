from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from bson import ObjectId
from flask_mail import Mail, Message
from datetime import datetime

app = Flask(__name__)

#CONFIGURAÇÃO DE BANCO DE DADOS (MONGODB)
app.config['MONGO_DBNAME'] = 'pad_db'
app.config["MONGO_URI"] = 'mongodb://localhost:27017/pad_db'

banco = PyMongo(app)

#CONFIGURAÇÃO DE EMAIL
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'thepadteam@gmail.com'
app.config['MAIL_PASSWORD'] = 'xxxxx'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

@app.route('/')
def init():
    return "..."

#LISTA TODOS OS AVALIADORES REGISTRADOS
@app.route('/appraisers/list', methods=['GET'])
def appraisers_list():
    appraisers = banco.db.appraisers
    output = []
    for appraiser in appraisers.find():
        output.append({
            'name':appraiser['name'], 
            'email':appraiser['email'],
        })
        if 'state' in appraiser:
            output[-1]['state'] = appraiser['state']
    return jsonify({'result':output})


#ADICIONA UM NOVA AVALIADOR
@app.route('/appraisers/add/<data>', methods=['GET'])
def appraisers_add(data):
    appraisers = banco.db.appraisers
    # data = request.data 
    try:
        appraiser_name, appraiser_email, appraiser_passwd = data.split('&')
        r = appraisers.find({'email':appraiser_email}, {'_id':0})
        rs = []
        for i in r:
            rs.append(i)
        if len(rs) == 0:
            appraisers.insert_one({
                'name':appraiser_name,
                'email':appraiser_email,
                'passwd':appraiser_passwd,
                'state':'deactivated'
            })
            mail = Mail(app)
            msg = Message(
                          'Verificação de Conta - PAD',
            	          sender='thepadteam@gmail.com',
            	          recipients=
                           [appraiser_email])
            msg.body = "Olá {}! Para ativar a sua conta, acesse: 127.0.0.1:5000/appraisers/activate/{}".format(appraiser_name, appraiser_email)
            mail.send(msg)
            return jsonify({'result': 'success' })
        else: 
            return jsonify({'result': 'Email is already in use'})
    except:
        return jsonify({'result': 'error'})


#ROTA PARA ATIVAR UMA CONTA DE AVALIADOR
@app.route('/appraisers/activate/<email>', methods=['GET'])
def appraiser_activate(email):
    try:
        appraisers = banco.db.appraisers
        appraisers.update_one({'email':email}, {'$set': {'state':'activated'}} )
        return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})


#ROTA PARA FAZER LOGIN COMO AVALIADOR
@app.route('/appraisers/login/<data>', methods=['GET'])
def appraiser_login(data):
    try:
        appraisers = banco.db.appraisers
        appraiser_email, appraiser_passwd = data.split('&')
        query = appraisers.find({'email':appraiser_email, 'passwd':appraiser_passwd, 'state':'activated'})
        array = []
        for i in query:
            array.append(i)
        if len(array) != 0:
            return jsonify({ 'result': {'_id':str(array[0]['_id']), 'name':array[0]['name'], 'email':appraiser_email} } )
        else:
           return jsonify({'result':'error'}) 
    except:
        return jsonify({'result':'error'})




#LISTA TODOS OS USUARIOS
@app.route('/users/list', methods=['GET'])
def users_list():
    users = banco.db.users
    try:
        output = []
        for user in users.find():
            output.append({
                '_id':str(user['_id']),
                'name':user['name'],
                'email':user['email']
            })
            if 'state' in user:
                output[-1]['state'] = user['state']
        return jsonify({'result':output})
    except:
        return jsonify({'result':'error'})


#ADICIONA UM NOVO USUARIO
@app.route('/users/add/<data>', methods=['GET'])
def users_add(data):
    users = banco.db.users
    user_name, user_email, user_passwd = data.split('&')
    q = []
    query = users.find_one({'email':user_email}, {'_id':0})
    try: 
        q = dict(query)['email']
        return jsonify({'result':'error'})
    except:
        users.insert_one({'name':user_name, 'email':user_email, 'passwd':user_passwd, 'state':'deactivated'})
        mail = Mail(app)
        msg = Message(
                      'Verificação de Conta - PAD',
        	          sender='thepadteam@gmail.com',
        	          recipients=
                       [user_email])
        msg.body = "Olá {}! Para ativar a sua conta, acesse: 127.0.0.1:5000/users/activate/{}".format(user_name, user_email)
        mail.send(msg)
        return jsonify({'result':'success'})


#ROTA PARA ATIVAR CONTA DE USUARIO
@app.route('/users/activate/<email>', methods=['GET'])
def user_activate(email):
    try:
        users = banco.db.users
        users.update_one({'email':email}, {'$set': {'state':'activated'}} )
        return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})


#ROTA PARA FAZER LOGIN COMO USUARIO
@app.route('/users/login/<data>', methods=['GET'])
def user_login(data):
    try:
        users = banco.db.users
        user_email, user_passwd = data.split('&')
        query = users.find({'email':user_email, 'passwd':user_passwd, 'state':'activated'})
        array = []
        for i in query:
            array.append(i)
        if len(array) != 0:
            return jsonify({ 'result': {'_id':str(array[0]['_id']), 'name':array[0]['name'], 'email':user_email} } )
        else:
           return jsonify({'result':'error'}) 
    except:
        return jsonify({'result':'error'})




#ROTA PARA LISTAR GRUPOS
@app.route('/groups/list', methods=['GET'])
def groups_list():
    try:
        groups = banco.db.groups
        appraisers = banco.db.appraisers
        output = []
        for group in groups.find():
            query = appraisers.find_one({'_id': ObjectId(group['appraiser'])})
            output.append({'group_id':str(group['_id']), 'name':group['name'], 'appraiser_id':group['appraiser'], 'appraiser_name':query['name']})
        return jsonify({'result':output})
    except:
        return jsonify({'result':'error'})


#ROTA PARA CRIAR GRUPOS
@app.route('/groups/add/<data>', methods=['GET'])
def groups_add(data):
    try:
        groups = banco.db.groups
        name, appraiser = data.split('&')
        groups.insert_one({'name':name, 'appraiser':appraiser})
        return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})


#ROTA PARA REMOVER GRUPOS
@app.route('/groups/del/<id>', methods=['GET'])
def groups_dell(id):
    try:
        groups = banco.db.groups
        groups.remove({'_id':ObjectId(id)})
        return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})




#ROTA PARA LISTAR MATRICULAS
@app.route('/groups/enrollments/list/<group>', methods=['GET'])
def groups_enrollments(group):
    enrollments = banco.db.enrollments
    users = banco.db.users
    output = []
    for enrollment in enrollments.find({'group':group}):
        user = users.find_one( {'_id':ObjectId(enrollment['user'])} )
        output.append( {'_id':str(enrollment['_id']), 'user_id':enrollment['user'], 'user_name':user['name']} )
    return jsonify({'result':output})


#ROTA PARA MATRICULAR-SE EM UM GRUPO
@app.route('/groups/apply/<data>', methods=['GET'])
def groups_apply(data):
    enrollments = banco.db.enrollments
    group_id, user_id = data.split('&')
    query = enrollments.find_one({'group':group_id, 'user':user_id}, {'_id':0})
    try:
        q = dict(query)['group']
        return jsonify({'result':'error'})
    except:
        enrollments.insert( { 'group':group_id, 'user':user_id } )
        return jsonify({'result':'success'})


#ROTA PARA REMOVER MATRICULA
@app.route('/groups/enrollments/del/<id>', methods=['GET'])
def enrollments_del(id):
    enrollments = banco.db.enrollments
    try:
        enrollments.remove({'_id':ObjectId(id)})
        return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})




#LISTA TODAS AS PROPOSTAS DO GRUPO
@app.route('/proposals/list', methods=['GET'])
def proposals_list():
    try:
        proposals = banco.db.proposals
        output = []
        for proposal in proposals.find():
            output.append({
                '_id': str(proposal['_id']),
                'group': proposal['group'],
                'format':proposal['format'],
                'deadline':proposal['deadline'],
                'name':proposal['name'],
                'description':proposal['description'],
                'creation_data':proposal['creation_data']
            })
        return jsonify({'result':output})
    except:
        return jsonify({'result':'error'})


#ADICIONA UMA NOVA PROPOSTA
@app.route('/proposals/add/<data>', methods=['GET'])
def proposals_add(data):
    try:
        proposals = banco.db.proposals
        group, format, deadline, name, description = data.split('&')
        actual_date = datetime.now().strftime("%Y-%m-%d")
        proposals.insert({
            'group':group,
            'format':format,
            'deadline':deadline,
            'name':name,
            'description':description,
            'creation_data':actual_date
            })
        return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})


#REMOVE UMA PROPOSTA
@app.route('/proposals/del/<id>', methods=['GET'])
def proposals_del(id):
    try:
        proposals = banco.db.proposals
        proposals.remove({'_id':ObjectId(id)})
        return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})




#RESPONDE UMA PROPOSTA
@app.route('/proposals/reply/<data>', methods=['GET'])
def proposals_reply(data):
    try:
        replies = banco.db.replies
        proposal_id, user_id, path = data.split('&')
        query = replies.find_one({
            'proposal':proposal_id,
            'user':user_id
            })
        try:
            q = dict(query)['user']
            return jsonify({'result':'error'})
        except:
            replies.insert({
                'proposal':proposal_id,
                'user':user_id,
                'file_path': path
            })
            return jsonify({'result':'success'})
    except:
        return jsonify({'result':'error'})



#CONFIGURAÇÕES BÁSICAS
if __name__ == '__main__':
    app.run(host='192.168.31.28', debug=True)
