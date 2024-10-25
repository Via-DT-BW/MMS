#Modificações da atualização 2.0
#Botaõ a atualizar com java script parte do armazem
#MRP edição massiva
#Transports edição massiva

#Inicio de APP
from flask import Flask, render_template, request, flash, redirect, url_for, session, g, Response, jsonify, make_response,send_file
from datetime import datetime, date,timedelta
import pyodbc
import settings
#email
from flask_mail import Mail, Message

from flask_toastr import Toastr
from fpdf import FPDF
import socket
import pandas as pd

try:
    string_conexao=settings.string_conexao()
    conn=pyodbc.connect(string_conexao)
except Exception as e:
  print("Falha de ligacao LMS DB")

app = Flask(__name__)

#Configurações email
app.config['MAIL_SERVER']='viasmtp.borgwarner.net'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = 'lms@borgwarner.com'

mail = Mail(app)
toastr = Toastr(app)
app.secret_key = 'secret_key_for_transport'


@app.route('/')
def index():
  conn=pyodbc.connect(string_conexao)
  cursor = conn.cursor()
  sp_supervisors = "Exec dbo.[CreateUserSupervisor]"
  cursor.execute(sp_supervisors)
  supervisors = cursor.fetchall()

  today = date.today()
  year = today.strftime("%Y")

  return render_template('index.html',supervisors=supervisors,year=year)

#LOGINS
#TRANSPORTS
@app.route('/login_transport', methods=['GET', 'POST'])
def login_transport():
    try:
        conn=pyodbc.connect(string_conexao)
    except Exception as e:
        print("falha de ligação")
    
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        
        cursor = conn.cursor()
        cursor.execute('SELECT * from dbo.Users WHERE username = ? AND password = ?', (username, password))
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            session['username'] = account[1]
            session['password'] = account[2]
            session['email'] = account[3] 
            session['workernumber'] = account[4]
            session['accesslevel'] = account[5]
            if account[5] < 7:
              
              conn.close()
              return redirect(url_for('status_transport_standard'))
              
              #return redirect(url_for('status_transport'))
            else:
              flash('Não tem permissões suficientes',category='warning')
              conn.close()
              return redirect(url_for('index'))
        else:
            flash('Erro com as Credenciais',category='error')
            return redirect(url_for('index'))

@app.route('/login_vigilant', methods=['GET', 'POST'])
def login_vigilant():
    try:
        conn=pyodbc.connect(string_conexao)
    except Exception as e:
        print("falha de ligação")
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = conn.cursor()
        cursor.execute('SELECT * from dbo.Users WHERE username = ? AND password = ?', (username, password))
        account = cursor.fetchone()
        if account:
            session['username'] = account[1]
            session['password'] = account[2]
            session['email'] = account[3] 
            session['workernumber'] = account[4]
            session['accesslevel'] = account[5]
            if account[5] > 7 and account[5] < 30:
              conn.close()
              return redirect(url_for('status_portaria'))
            else:
              flash('Não tem permissões suficientes',category='warning')
              conn.close()
              return redirect(url_for('index'))
        else:
            flash('Erro com as Credenciais',category='error')
            return render_template('index.html')

@app.route('/login_cargas_descargas', methods=['GET', 'POST'])
def login_cargas_descargas():
    try:
        conn=pyodbc.connect(string_conexao)
    except Exception as e:
        print("falha de ligação")
    
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        
        cursor = conn.cursor()
        cursor.execute('SELECT * from dbo.Users WHERE username = ? AND password = ?', (username, password))
        account = cursor.fetchone()
 
        # If account exists in accounts table in out database
        if account:
            session['username'] = account[1]
            session['password'] = account[2]
            session['email'] = account[3] 
            session['workernumber'] = account[4]
            session['accesslevel'] = account[5]
            if account[5] > 30 and account[5] < 40:
              conn.close()
              return redirect(url_for('status_armazem'))
            else:
              flash('Não tem permissões suficientes', category='warning')
              conn.close()
              return redirect(url_for('index'))
        else:
            flash('Erro com as credenciais', category='error')
            return redirect(url_for('index'))

#LOGINS MRP
@app.route('/login_mrp', methods=['GET', 'POST'])
def login_mrp():
    try:
        conn=pyodbc.connect(string_conexao)
    except Exception as e:
        print("falha de ligação")
    
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        
        cursor = conn.cursor()
        cursor.execute('SELECT * from dbo.Users WHERE username = ? AND password = ?', (username, password))
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            session['username'] = account[1]
            session['password'] = account[2]
            session['email'] = account[3] 
            session['workernumber'] = account[4]
            session['accesslevel'] = account[5]
            if account[5] > 2:
              conn.close()
              return redirect(url_for('status_mrp'))
            else:
              flash('Não tem permissões suficientes',category='warning')
              conn.close()
              return redirect(url_for('index'))
        else:
            flash('Erro com as Credenciais',category='error')
            return redirect(url_for('index'))

###REGISTO MRPS
@app.route('/register_mrp', methods=['GET', 'POST'])
def register_mrp():
  conn=pyodbc.connect(string_conexao)
  if request.method == 'POST':
    email = request.form['email']
    password1 = request.form['password1']
    password2 = request.form['password2']
    workernumber = request.form['workernumber']
   
    if password1 != password2:
      flash('The passwords are different!',category='error')
      return redirect(url_for('index'))
    else:
      cursor = conn.cursor()
      cursor.execute("SELECT email FROM [dbo].[users] where email =?",email)
      account_validation = cursor.fetchall()
      if account_validation:
        flash('Email is already registered. Please contact the system administrator.', category='error')
        return redirect(url_for('index'))
      else:
        username = email.split("@")[0]
        sp_insert_user = "Exec dbo.[CreateUserMRP] @Username=?,@Password=?,@Email=?,@WorkerNumber=?"
        cursor.execute(sp_insert_user,username,password1,email,workernumber)
        cursor.commit()
        flash('Account created successfully, you can now log in', category='success')
        return redirect(url_for('index')) 
      flash('Account created successfully. You can now log in!', category='success')
      return redirect(url_for('index')) 
  return render_template('index.html', category='sucess')  


###REGISTO UNIFORMS
@app.route('/register_uniforms', methods=['GET', 'POST'])
def register_uniforms():
  conn=pyodbc.connect(string_conexao)
  if request.method == 'POST':
    email = request.form['email']
    password1 = request.form['password1']
    password2 = request.form['password2']
    supervisor = request.form['supervisor']
    workernumber = request.form['workernumber']
   
    if password1 != password2:
      flash('The passwords are different!',category='error')
      return redirect(url_for('index'))
    else:
      cursor = conn.cursor()
      cursor.execute("SELECT email FROM [dbo].[users] where email =?",email)
      account_validation = cursor.fetchall()
      if account_validation:
        flash('Email is already registered. Please contact the system administrator.', category='error')
        return redirect(url_for('index'))
      else:
        username = email.split("@")[0]
        sp_insert_user = "Exec dbo.[CreateUserUMS] @Username=?,@Password=?,@Supervisor=?,@Email=?,@WorkerNumber=?"
        cursor.execute(sp_insert_user,username,password1,supervisor,email,workernumber)
        cursor.commit()
        flash('Account created successfully, you can now log in', category='success')
        return redirect(url_for('index')) 
      flash('Account created successfully. You can now log in!', category='success')
      return redirect(url_for('index')) 
  return render_template('index.html', category='sucess')   


###REGISTO TRANSPORTS
@app.route('/register_transports', methods=['GET', 'POST'])
def register_transports():
  conn=pyodbc.connect(string_conexao)
  if request.method == 'POST':
    email = request.form['email']
    password1 = request.form['password1']
    password2 = request.form['password2']
   
    if password1 != password2: # verificação password 
      flash('As passwords não são iguais!',category='error')
      return redirect(url_for('index'))
    else:
      #account_validation='teste'
      cursor = conn.cursor()
      cursor.execute("SELECT email FROM [dbo].[users] where email =?",email)
      account_validation = cursor.fetchall()
      if account_validation:
        flash('Esse email já está registado, fale com o adminsitrador do sistema', category='error')
        return redirect(url_for('index'))
      else:
        username = email.split("@")[0]
        cursor.execute("INSERT INTO [users](username,password,email,access_level ) values(?, ?, ?, ?)",(username, password1, email,1))
        conn.commit()
        conn.close()
        flash('Conta criada com sucesso, pode fazer login!', category='success')
        return redirect(url_for('index')) 
      flash('Conta criada com sucesso, pode fazer login!', category='success')
      return redirect(url_for('index')) 
  return render_template('index.html', category='sucess')       
###LOGOUT
@app.route('/logout')
def logout():

   session.pop('username', None)
   session.pop('password', None)
   session.pop('email', None)
   session.pop('workernumber', None)
   session.pop('accesslevel', None)
   session.clear()
   return redirect(url_for('index'))

#####
#HOMEPAGE
####
@app.route('/home')
def home():
  return render_template('home.html')

@app.route('/home_portaria')
def home_portaria():
  return render_template('home_portaria.html')

@app.route('/portaria_dashboard',methods=['GET', 'POST'])
def portaria_dashboard():
  today = date.today()
  ano = today.year
  username=session['username']
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  dashboard_portaria = "Exec dbo.[homepage_vigilantes] @estado = ?"
  cursor.execute(dashboard_portaria,0)
  pendentes_armazem = cursor.fetchall()

  cursor.execute(dashboard_portaria,1)
  pendentes_armazem_registo = cursor.fetchall()

  cursor.execute(dashboard_portaria,2)
  em_trabalho = cursor.fetchall()

  cursor.execute(dashboard_portaria,3)
  estado_cais = cursor.fetchall()

  cursor.execute(dashboard_portaria,4)
  recusado_portaria = cursor.fetchall()

  cursor.execute(dashboard_portaria,5)
  contagem_acessos = cursor.fetchall()

  cursor.execute(dashboard_portaria,6)
  contagem_dashboard = cursor.fetchall()

  cursor.execute(dashboard_portaria,7)
  contagem_lugares_servicos = cursor.fetchall()

  cursor.execute(dashboard_portaria,8)
  chaves_chaveiro_principal = cursor.fetchall()

  cursor.execute(dashboard_portaria,9)
  chaves_chaveiro_copias = cursor.fetchall()

  cursor.execute(dashboard_portaria,10)
  contagem_cartoes = cursor.fetchall()

  cursor.execute(dashboard_portaria,11)
  contagem_cais = cursor.fetchall()

  dashboard_armazem_em_trabalho = "Exec dbo.[homepage_armazem] @estado=?"
  cursor.execute(dashboard_armazem_em_trabalho,3)
  dashboard_armazem_estado_cais = cursor.fetchall()

  dashboard_tabela_cartoes = "Exec dbo.[VisitGetCardsDashboard] @Filtro=?"
  cursor.execute(dashboard_tabela_cartoes,'Serviços')
  dashboard_lista_cartoes_servicos = cursor.fetchall()

  cursor.execute(dashboard_tabela_cartoes,'Visitas')
  dashboard_lista_cartoes_visitas = cursor.fetchall()

  cursor.execute(dashboard_tabela_cartoes,'Temporário')
  dashboard_lista_cartoes_temporario = cursor.fetchall()

  return render_template('portaria_dashboard.html',contagem_cais=contagem_cais,dashboard_lista_cartoes_temporario=dashboard_lista_cartoes_temporario,dashboard_lista_cartoes_visitas=dashboard_lista_cartoes_visitas,dashboard_lista_cartoes_servicos=dashboard_lista_cartoes_servicos,contagem_cartoes=contagem_cartoes,chaves_chaveiro_copias=chaves_chaveiro_copias,chaves_chaveiro_principal=chaves_chaveiro_principal,ano=ano,contagem_lugares_servicos=contagem_lugares_servicos,contagem_dashboard=contagem_dashboard,dashboard_armazem_estado_cais=dashboard_armazem_estado_cais,pendentes_armazem_registo=pendentes_armazem_registo,contagem_acessos=contagem_acessos,pendentes_armazem=pendentes_armazem,em_trabalho=em_trabalho,estado_cais=estado_cais,recusado_portaria=recusado_portaria)

@app.route('/home_armazem')
def home_armazem():

  return render_template('home_armazem.html')

@app.route('/homepage')
def homepage():
  try:
    username=session['username']

    return render_template('homepage.html')
  except Exception as e:
        flash('Login Error')
  return redirect(url_for('index'))

@app.route('/homepage_portaria',methods=['GET', 'POST'])
def homepage_portaria():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    dashboard_portaria = "Exec dbo.[homepage_vigilantes] @estado = ?"
    cursor.execute(dashboard_portaria,0)
    pendentes_armazem = cursor.fetchall()

    cursor.execute(dashboard_portaria,1)
    pendentes_armazem_registo = cursor.fetchall()

    cursor.execute(dashboard_portaria,2)
    em_trabalho = cursor.fetchall()

    cursor.execute(dashboard_portaria,3)
    estado_cais = cursor.fetchall()

    cursor.execute(dashboard_portaria,4)
    recusado_portaria = cursor.fetchall()

    cursor.execute(dashboard_portaria,5)
    contagem_acessos = cursor.fetchall()

    cursor.execute(dashboard_portaria,6)
    contagem_dashboard = cursor.fetchall()

    cursor.execute(dashboard_portaria,7)
    contagem_lugares_servicos = cursor.fetchall()

    dashboard_armazem_em_trabalho = "Exec dbo.[homepage_armazem] @estado=?"
    cursor.execute(dashboard_armazem_em_trabalho,3)
    dashboard_armazem_estado_cais = cursor.fetchall()


    return render_template('homepage_portaria.html',contagem_lugares_servicos=contagem_lugares_servicos,contagem_dashboard=contagem_dashboard,dashboard_armazem_estado_cais=dashboard_armazem_estado_cais,pendentes_armazem_registo=pendentes_armazem_registo,contagem_acessos=contagem_acessos,pendentes_armazem=pendentes_armazem,em_trabalho=em_trabalho,estado_cais=estado_cais,recusado_portaria=recusado_portaria)
  except Exception as e:
        flash('Login Error')
  return redirect(url_for('index'))


@app.route('/homepage_portaria_new',methods=['GET', 'POST'])
def homepage_portaria_new():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    dashboard_portaria = "Exec dbo.[homepage_vigilantes] @estado = ?"
    cursor.execute(dashboard_portaria,0)
    pendentes_armazem = cursor.fetchall()

    cursor.execute(dashboard_portaria,1)
    pendentes_armazem_registo = cursor.fetchall()

    cursor.execute(dashboard_portaria,2)
    em_trabalho = cursor.fetchall()

    cursor.execute(dashboard_portaria,3)
    estado_cais = cursor.fetchall()

    cursor.execute(dashboard_portaria,4)
    recusado_portaria = cursor.fetchall()

    cursor.execute(dashboard_portaria,5)
    contagem_acessos = cursor.fetchall()

    cursor.execute(dashboard_portaria,6)
    contagem_dashboard = cursor.fetchall()

    cursor.execute(dashboard_portaria,7)
    contagem_lugares_servicos = cursor.fetchall()

    dashboard_armazem_em_trabalho = "Exec dbo.[homepage_armazem] @estado=?"
    cursor.execute(dashboard_armazem_em_trabalho,3)
    dashboard_armazem_estado_cais = cursor.fetchall()


    return render_template('portaria/homepage_portaria_new.html',contagem_lugares_servicos=contagem_lugares_servicos,contagem_dashboard=contagem_dashboard,dashboard_armazem_estado_cais=dashboard_armazem_estado_cais,pendentes_armazem_registo=pendentes_armazem_registo,contagem_acessos=contagem_acessos,pendentes_armazem=pendentes_armazem,em_trabalho=em_trabalho,estado_cais=estado_cais,recusado_portaria=recusado_portaria)
  except Exception as e:
        flash('Login Error',category='error')
  return redirect(url_for('index'))


@app.route('/homepage_armazem',methods=['GET', 'POST'])
def homepage_armazem():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    dashboard_armazem_em_trabalho = "Exec dbo.[homepage_armazem] @estado=?"
    cursor.execute(dashboard_armazem_em_trabalho,0)
    dashboard_armazem_aguarda_portaria_data = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,1)
    dashboard_armazem_aguarda_registo_armazem = cursor.fetchall()


    cursor.execute(dashboard_armazem_em_trabalho,2)
    dashboard_armazem_em_trabalho_data = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,3)
    dashboard_armazem_estado_cais = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,4)
    dashboard_armazem_recusas = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,5)
    dashboard_armazem_contagem = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,6)
    dashboard_nivel_6 = cursor.fetchall()
    

    contagem_cargas_descargas = "Exec dbo.[contagem_cargas_descargas] @valor=?"
    cursor.execute(contagem_cargas_descargas,0)
    valor = cursor.fetchall()
    teste='Borgwarner'
    valor_para_real=valor[0][0]
    valor_para_atualizar=valor[0][1]
    if valor_para_atualizar > valor_para_real:
      
      flash("Existe um novo registo nas cargas e descargas", 'info')

      cursor.execute(contagem_cargas_descargas,1)
      cursor.commit()
      cursor.close()
    return render_template('/armazem/homepage_armazem.html',dashboard_nivel_6=dashboard_nivel_6,dashboard_armazem_recusas=dashboard_armazem_recusas,dashboard_armazem_aguarda_registo_armazem=dashboard_armazem_aguarda_registo_armazem,dashboard_armazem_contagem=dashboard_armazem_contagem,dashboard_armazem_estado_cais=dashboard_armazem_estado_cais,dashboard_armazem_aguarda_portaria_data=dashboard_armazem_aguarda_portaria_data,dashboard_armazem_em_trabalho_data=dashboard_armazem_em_trabalho_data)
  except Exception as e:
        flash('Login Error')
  return redirect(url_for('index'))


@app.route('/dashboard_armazem_bw',methods=['GET', 'POST'])
def dashboard_armazem_bw():
  try:
    
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    dashboard_armazem_em_trabalho = "Exec dbo.[homepage_armazem] @estado=?"
    cursor.execute(dashboard_armazem_em_trabalho,0)
    dashboard_armazem_aguarda_portaria_data = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,1)
    dashboard_armazem_aguarda_registo_armazem = cursor.fetchall()


    cursor.execute(dashboard_armazem_em_trabalho,2)
    dashboard_armazem_em_trabalho_data = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,3)
    dashboard_armazem_estado_cais = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,4)
    dashboard_armazem_recusas = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,5)
    dashboard_armazem_contagem = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,6)
    dashboard_nivel_6 = cursor.fetchall()

    cursor.execute(dashboard_armazem_em_trabalho,7)
    dashboard_nivel_7 = cursor.fetchall()
    

    return render_template('/armazem/dashboard_armazem_bw.html',dashboard_nivel_7=dashboard_nivel_7,dashboard_nivel_6=dashboard_nivel_6,dashboard_armazem_recusas=dashboard_armazem_recusas,dashboard_armazem_aguarda_registo_armazem=dashboard_armazem_aguarda_registo_armazem,dashboard_armazem_contagem=dashboard_armazem_contagem,dashboard_armazem_estado_cais=dashboard_armazem_estado_cais,dashboard_armazem_aguarda_portaria_data=dashboard_armazem_aguarda_portaria_data,dashboard_armazem_em_trabalho_data=dashboard_armazem_em_trabalho_data)
  except Exception as e:
        flash('Login Error')
  return redirect(url_for('index'))
########################################################################################################################################################################
#PORTARIA
######################################################################################################################################################################## 
#
#CHAVEIRO PRINCIPAL
#
#####
@app.route('/portaria_chaves_principal')
def portaria_chaves_principal():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    sp_RegistoChavesConfiguracoesChaveiro = "Exec dbo.[RegistoChavesConfiguracoesChaveiro] @estado=?"
    cursor.execute(sp_RegistoChavesConfiguracoesChaveiro,0)
    chaves_principal = cursor.fetchall()
    return render_template('settings/portaria_chaves_principal.html',chaves_principal=chaves_principal)
  except Exception as e:
        flash('Login Error',category="error")
  return redirect(url_for('index'))
#ADD CHAVEIRO PRINCIPAL
@app.route('/add_chaveiro_principal',methods=['GET', 'POST'])
def add_chaveiro_principal():
  try:
    codigo=request.form['var_1']
    designacao=request.form['var_2']
    quantidade=request.form['var_3']
    codigo_nome=request.form['var_4']
    observacoes=request.form['var_5']
    cursor=conn.cursor()
    Store_procedure_PortariaChaveiroPrincipalAdd = "Exec dbo.PortariaChaveiroPrincipalAdd @Codigo = ?,@Designacao = ?,@Quantidade = ?,@CodigoChave = ?,@Observacoes= ?"
    cursor.execute(Store_procedure_PortariaChaveiroPrincipalAdd,codigo,designacao,quantidade,codigo_nome,observacoes)
    cursor.commit()

    flash('Chave criada com sucesso',category="success")
    return redirect(url_for('portaria_chaves_principal'))
  except Exception as e:
        flash('Login Error',category="error")
  return redirect(url_for('index'))
# EDIT CHAVEIRO PRINCIPAL
@app.route('/edit_chaveiro_principal/<int:id>',methods=['GET', 'POST'])
def edit_chaveiro_principal(id):
  try:
    codigo=request.form['var_1']
    designacao=request.form['var_2']
    quantidade=request.form['var_3']
    codigo_nome=request.form['var_4']
    observacoes=request.form['var_5']
    cursor=conn.cursor()
    Store_procedure_PortariaChaveiroPrincipalUpdate = "Exec dbo.PortariaChaveiroPrincipalUpdate @id=?,@Codigo = ?,@Designacao = ?,@Quantidade = ?,@CodigoChave = ?,@Observacoes= ?"
    cursor.execute(Store_procedure_PortariaChaveiroPrincipalUpdate,id,codigo,designacao,quantidade,codigo_nome,observacoes)
    cursor.commit()

    flash('Chave editada com sucesso',category="success")
    return redirect(url_for('portaria_chaves_principal'))
  except Exception as e:
        flash('Login Error',category="error")
  return redirect(url_for('index'))
# DELETE CHAVEIRO PRINCIPAL
@app.route('/delete_chaveiro_principal/<int:id>', methods=['POST', 'GET'])
def delete_chaveiro_principal(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_delete_key = "Exec dbo.PortariaChaveiroPrincipalDelete @id = ?"
    cursor.execute(storeproc_delete_key,id)
    conn.commit()
    flash('Registo eliminado com sucesso.', category='success')
    return redirect(url_for('portaria_chaves_principal'))
  except Exception as e:
        flash('Login Error',category="error")
  return redirect(url_for('index'))
#
#CHAVEIRO COPIAS
#
#####
@app.route('/portaria_chaves_copias')
def portaria_chaves_copias():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    sp_RegistoChavesConfiguracoesChaveiro = "Exec dbo.[RegistoChavesConfiguracoesChaveiro] @estado=?"
    cursor.execute(sp_RegistoChavesConfiguracoesChaveiro,1)
    chaves_copias = cursor.fetchall()

    return render_template('settings/portaria_chaves_copias.html',chaves_copias=chaves_copias)
  except Exception as e:
        flash('Login Error',category="success")
  return redirect(url_for('index'))
#ADD CHAVEIRO COPIAS
@app.route('/add_chaveiro_copias',methods=['GET', 'POST'])
def add_chaveiro_copias():
  try:
    codigo=request.form['var_1']
    designacao=request.form['var_2']
    quantidade=request.form['var_3']
    codigo_nome=request.form['var_4']
    observacoes=request.form['var_5']
    cursor=conn.cursor()
    PortariaChaveiroCopiasAdd = "Exec dbo.PortariaChaveiroCopiasAdd @Codigo = ?,@Designacao = ?,@Quantidade = ?,@CodigoChave = ?,@Observacoes= ?"
    cursor.execute(PortariaChaveiroCopiasAdd,codigo,designacao,quantidade,codigo_nome,observacoes)
    cursor.commit()

    flash('Chave criada com sucesso',category="success")
    return redirect(url_for('portaria_chaves_copias'))
  except Exception as e:
        flash('Login Error',category="error")
  return redirect(url_for('index'))
# EDIT CHAVEIRO COPIAS
@app.route('/edit_chaveiro_copias/<int:id>',methods=['GET', 'POST'])
def edit_chaveiro_copias(id):
  try:
    codigo=request.form['var_1']
    designacao=request.form['var_2']
    quantidade=request.form['var_3']
    codigo_nome=request.form['var_4']
    observacoes=request.form['var_5']
    cursor=conn.cursor()
    Store_procedure_PortariaChaveiroCopiasUpdate = "Exec dbo.PortariaChaveiroCopiasUpdate @id=?,@Codigo = ?,@Designacao = ?,@Quantidade = ?,@CodigoChave = ?,@Observacoes= ?"
    cursor.execute(Store_procedure_PortariaChaveiroCopiasUpdate,id,codigo,designacao,quantidade,codigo_nome,observacoes)
    cursor.commit()

    flash('Chave editada com sucesso',category="success")
    return redirect(url_for('portaria_chaves_copias'))
  except Exception as e:
        flash('Login Error',category="error")
  return redirect(url_for('index'))
# DELETE CHAVEIRO COPIAS
@app.route('/delete_chaveiro_copias/<int:id>', methods=['POST', 'GET'])
def delete_chaveiro_copias(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_delete_key = "Exec dbo.PortariaChaveiroCopiasDelete @id = ?"
    cursor.execute(storeproc_delete_key,id)
    conn.commit()
    flash('Registo eliminado com sucesso.', category='success')
    return redirect(url_for('portaria_chaves_copias'))
  except Exception as e:
        flash('Login Error',category="error")
  return redirect(url_for('index'))
#


#TRANSPORTS
@app.route('/homepage_transports')
def homepage_transports():
  return render_template('transports/homepage_transports.html')
#Requisitions
@app.route('/all_requisitions_transport_pendent')
def all_requisitions_transport_pendent():
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  all_requisitions_transport_pendent = "Exec dbo.[all_requisitions_transport_pendent]"
  cursor.execute(all_requisitions_transport_pendent)
  all_requisitions_transport_pendent_data = cursor.fetchall()
  return render_template('/transports/all_requisitions_transport_pendent.html',all_requisitions_transport_pendent_data=all_requisitions_transport_pendent_data)


#ADD REQUISITON standard
@app.route('/add_standard_requisition_new',methods=['GET', 'POST'])
def add_standard_requisition_new():
  try:
    username=session['username']
    if request.method == 'POST':
      username=session['username']
      owner_email=str(username)+str('@borgwarner.com')
      #Criacao novo internal_code
      UT = 'STR'
      today = date.today()
      format ="%y"
      year = today.strftime(format)
      ##########
      #Verifica o ultimo internal code
      ##########
      cursor=conn.cursor()
      cursor.execute("SELECT [InternalCode] FROM [StandardTransportRequests] ORDER BY id DESC")
      dados_ultimo_id = cursor.fetchone()

      last_internal_code_value=str(dados_ultimo_id[0])
      last_internal_code_value_number=last_internal_code_value[6::]
      last_internal_code_value_year=last_internal_code_value[3:5]

      if last_internal_code_value_year == year:
        #acrecentar 1 ao internal code
        new_number = int(last_internal_code_value_number) + 1
        internal_code= str(UT)+str(year)+str('-')+str(new_number).zfill(4)
      else:
        #Começa o ano novo
        new_number =  1
        internal_code= str(UT)+str(year)+str('-')+str(new_number).zfill(4)
        
      ##########

      var_1=request.form['var_1']
      var_2=request.form['var_2']
      var_3=request.form['var_3']
      var_4=request.form['var_4']
      var_5=request.form['var_5']
      var_6=request.form['var_6']
      var_7=request.form['var_7']
      var_8=request.form['var_8']
      var_9=request.form['var_9']
      
      var_10=request.form['var_10']
      var_11=request.form['var_11']
      var_12=request.form['var_12']
      var_13=request.form['var_13']
      var_14=request.form['var_14']
      var_15=request.form['var_15']
      var_16=request.form['var_16']
      var_17=request.form['var_17']
      var_18=request.form['var_18']

      
      insystem=request.form['insystem']
      SFE=request.form['SFE']
      sosa=request.form['sosa']
      var_31=request.form['var_31']

      var_empty=""
      totalvalue=request.form['totalvalue']
      cursor=conn.cursor()
      sp_CreateStandardRequisitionNew = "Exec dbo.[CreateStandardRequisitionNew] @InternalCode = ?,@Username=?,@PickupCompany=?, @PickupAddress=?, @PickupCountry=?, @PickupZip=?, @PickupCity=?, @PickupDate=?, @PickupContactName=?, @PickupContactEmail=?, @PickupContactPhone=?, @DeliveryCompany=?, @DeliveryAddress=?, @DeliveryCountry=?, @DeliveryZip=?, @DeliveryCity=?, @DeliveryDate=?, @DeliveryContactName=?, @DeliveryContactEmail=?, @DeliveryContactPhone=?, @InSystem=?, @SFENumber=?, @SOSANumber=?, @TotalValue=?, @Observations=?"
      cursor.execute(sp_CreateStandardRequisitionNew,internal_code,username, var_1, var_2, var_3,var_4,var_5,var_6,var_7,var_8,var_9,var_10,var_11,var_12,var_13,var_14,var_15,var_16,var_17,var_18,insystem,SFE,sosa,totalvalue,var_31)
      dados_ultimo_id = cursor.fetchone()

      id_request=dados_ultimo_id[0]

      var_19 = request.form.getlist('var_19[]')
      var_20 = request.form.getlist('var_20[]')
      var_21 = request.form.getlist('var_21[]')
      var_22 = request.form.getlist('var_22[]')
      var_23 = request.form.getlist('var_23[]')
      var_24 = request.form.getlist('var_24[]')
      var_25 = request.form.getlist('var_25[]')
      var_26 = request.form.getlist('var_26[]')
      var_27 = request.form.getlist('var_27[]')
      var_28 = request.form.getlist('var_28[]')
      var_30 = request.form.getlist('var_30[]')
      str_html = f'''Olá,<br> Foi criado uma nova requisição com o Código: <b>{internal_code} </b> que se encontra disponível na Plataforma LMS (<a href='http://10.30.64.11:6600/'>LMS</a>).<br><br>
      <b>Remetente:</b><br>
      <b>Data recolha: </b>{var_6}<br><b>Empresa: </b>{var_1}<br><b>Rua/Lugar recolha: 
      </b>{var_2}<br><b>Cidade recolha: </b> {var_5}<br><b>Zip: </b>{var_4}<br><b>Pais recolha: </b>{var_3}<br>
      <b>Expedidor:</b> {var_7} - <b>Contacto:</b> {var_9} - <b>Email:</b> {var_8}<br>
      <br>
      <b>Destinatário:</b><br>
      <b>Data entrega: </b>{var_15}<br><b>Empresa: </b>{var_10}<br><b>Rua/Lugar entrega: 
      </b>{var_11}<br><b>Cidade entrega: </b> {var_14}<br><b>Zip: </b>{var_13}<br><b>Pais entrega: </b>{var_12}<br>
      <b>Pessoa de Contacto:</b> {var_16} - <b>Contacto:</b> {var_18} - <b>Email:</b> {var_17} <br>
      <br>
      <br>
      <b>Observações: </b>{var_31}<br>
      <br>
      <br>
      <table style="border-collapse: collapse;">
          <tr>
            <th  style="border: 0.5px solid black;"> Referencia </th>
            <th style="border: 0.5px solid black;"> Nº Pallets </th>
            <th style="border: 0.5px solid black;"> Comp. </th>
            <th style="border: 0.5px solid black;"> Larg. </th>
            <th style="border: 0.5px solid black;"> Alt. </th>
            <th style="border: 0.5px solid black;"> Peso Kgs </th>
            <th style="border: 0.5px solid black;"> Qtd. Parts </th>
            <th style="border: 0.5px solid black;"> Volume </th>
            <th style="border: 0.5px solid black;"> Sobreponível </th>
            <th style="border: 0.5px solid black;"> Imputável </th>
            <th style="border: 0.5px solid black;"> Linha </th>
          </tr>
          <tr>'''
      for index, row in enumerate(var_19):
        #index = var_19.index(row)
        volume_value = (float(var_20[index]) * float(var_21[index]) * float(var_22[index]) * float(var_23[index])) / 1000000
        volume=round(volume_value,4)
        straux = f'''
              <td style="border: 0.5px solid black; text-align:center">{var_19[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_20[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_21[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_22[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_23[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_24[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_25[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{volume}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_26[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_27[index]}</td>
              <td style="border: 0.5px solid black;text-align:center">{var_30[index]}</td>
            </tr>
        '''
        str_html = str_html + straux
        sp_CreateStandardRequisitionDetails = "Exec dbo.[CreateStandardRequisitionDetails] @idRequest=?,@Reference=?,@PalletType=?,@PalletQty=?,@PalletLenght=?,@PalletWidth=?,@PalletHeight=?,@TotalWeight=?,@PartsQty=?,@Stackable=?,@Imputable=?,@SupplierClient=?,@TransportType=?,@ProdLine=?,@TotalVolume=?"
        cursor.execute(sp_CreateStandardRequisitionDetails,id_request,var_19[index],"",var_20[index],var_21[index],var_22[index],var_23[index],var_24[index],var_25[index],var_26[index],var_27[index],var_28[index],"",var_30[index],volume)
        conn.commit()
        Subject='Requisição ' + internal_code
        #msg = Message(Subject, recipients = ['cafilipe@borgwarner.com'])
        msg = Message(Subject, recipients = ['drebelo@borgwarner.com','befernandes@borgwarner.com','vprado@borgwarner.com'],cc=[owner_email])    
      
      str_html += '</table>'
      str_html_final =f'<h4>Mensagem enviada pela conta de: {username}</h4>'
      msg.html = str_html + str_html_final
      mail.send(msg) 
      flash('Requisition Created', category='success')
      return redirect(url_for('request_standard_transport_final'))
    else:
      flash('Error with the fields!', category='error')
      return redirect(url_for('request_standard_transport_final'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

#ADD REQUISITON
@app.route('/add_requisition',methods=['GET', 'POST'])
def add_requisition():
  if request.method == 'POST':
    username=session['username']
    owner_email=str(username)+str('@borgwarner.com')
    #Criacao novo internal_code
    UT = 'UT'
    today = date.today()
    format ="%y-"
    year = today.strftime(format)

    vendor=request.form['var_1']
    vendor_details=request.form['var_111']


    delivery_vendor=request.form['var_2']
    delivery_details=request.form['var_222']

    data_recolha=request.form['var_7']
    data_entrega=request.form['var_8']

    #########
    cursor=conn.cursor()
    add_requisition_info = "Exec dbo.[add_requisition_info] @vendor = ?"
    cursor.execute(add_requisition_info,vendor)
    add_requisition_info_data = cursor.fetchall()

    cursor=conn.cursor()
    add_requisition_info_delivery = "Exec dbo.[add_requisition_info] @vendor = ?"
    cursor.execute(add_requisition_info_delivery,delivery_vendor)
    add_requisition_info_data_delivery = cursor.fetchall()
    #########

    vendor_name=add_requisition_info_data[0][0]
    vendor_country=add_requisition_info_data[0][1]
    vendor_street=add_requisition_info_data[0][2]
    vendor_city=add_requisition_info_data[0][3]
    vendor_zip=add_requisition_info_data[0][4]


    delivery_name=add_requisition_info_data_delivery[0][0]
    delivery_country=add_requisition_info_data_delivery[0][1]
    delivery_street=add_requisition_info_data_delivery[0][2]
    delivery_city=add_requisition_info_data_delivery[0][3]
    delivery_zip=add_requisition_info_data_delivery[0][4]


    #########
    internal_code_var=add_requisition_info_data[0][5]

    last_number_ut=internal_code_var[-4:].zfill(4)
    new_number = int(last_number_ut) + 1
    internal_code= str(UT)+str(year)+str(new_number).zfill(4)
    #########
    #########
    #nº Paletes
    n_pallets=request.form['var_9']
    comprimento=request.form['var_10']
    largura=request.form['var_11']
    altura=request.form['var_12']
    peso=request.form['var_13']
    empilhavel=request.form['var_133']

    #Volume é a multiplcação de n_palets, comprimento,largura e altura.
    volume = (float(n_pallets) * float(comprimento) * float(largura) * float(altura)) / 1000000
    #referencias
    referencia_1=request.form['var_15']
    referencia_2=request.form['var_16']
    referencia_3=request.form['var_17']

    imputavel=request.form['var_18']
    fornecedor_cliente=request.form['var_19']

    prod_line=request.form['var_20']
    cost_center=''
    urgente=''

    var_root_cause=request.form['var_root_cause']
    var_corrective_Action=request.form['var_corrective_Action']
    var_impact=request.form['var_impact']
    
    justification=request.form['var_23']
    nome_contato=request.form['var_24']
    email_contato=request.form['var_242']
    numero_contato=request.form['var_243']
    #category=request.form['var_255']

    tipo_transport=request.form['var_25']
    Store_procedure_create_ut = "Exec dbo.create_ut @internal_code = ? , @creation_date = ?,@pickup_address = ?,@pickup_company = ?,@pickup_country = ?, @delivery_address = ?,@delivery_company = ?,@delivery_country = ? , @pickup_date = ?,@delivery_date = ?,@pallet_qty=?,@pallet_lenght=?,@pallet_width=?,@pallet_height=?,@total_weight=?,@total_volume=?,@reference_1=?,@reference_2=?,@reference_3=?,@imputable=?,@supplier_client =?,@prod_line=?,@cost_center =?,@urgent=?,@justify =?,@owner=?,@request_state=?,@transport_type=?,@contact_name=?,@contact_email=?,@contact_number=?,@vendor_details=?,@delivery_details=?,@pickup_zip=?,@pickup_city=?,@delivery_zip=?,@delivery_city=?,@stackable=?,@root_cause=?,@corrective_action=?,@impact=?"
    cursor.execute(Store_procedure_create_ut,internal_code,today,vendor_street,vendor_name,vendor_city,delivery_street,delivery_name,delivery_city,data_recolha,data_entrega,n_pallets,comprimento,largura,altura,peso,volume,referencia_1,referencia_2,referencia_3,imputavel,fornecedor_cliente,prod_line,cost_center,urgente,justification,username,1,tipo_transport,nome_contato,email_contato,numero_contato,vendor_details,delivery_details,delivery_zip,delivery_city,vendor_zip,vendor_city,empilhavel,var_root_cause,var_corrective_Action,var_impact)
    cursor.commit()
    
    Subject='Requisição ' + internal_code
    #alterar o recipients para valtransports
    #vprado@borgwarner.com
    #befernandes@borgwarner.com
    #drebelo@borgwarner.com

    msg = Message(Subject, recipients = ['drebelo@borgwarner.com','befernandes@borgwarner.com','vprado@borgwarner.com'],cc=[owner_email])
    #msg.body = message
    #str_html = f''
    msg.html =  "Olá,<br><br> Foi criado uma nova requisição com o Código: <b>"+ internal_code +"</b> que se encontra disponível na Plataforma LMS (<a href='http://10.30.64.11:6600/'>LMS</a>). <br><br><b>Data recolha: </b>"+data_recolha+"<br><br><b>Morada recolha: </b>"+vendor_name+"<br><b>Rua/Lugar recolha: </b>"+vendor_street+"<br><b>Cidade recolha: </b> "+vendor_city+"<br><b>Zip: </b>"+vendor_zip + "<br><b>Pais recolha:</b> " +  vendor_country +"<br><b>Info. adicional:</b> " +  vendor_details + "<br><br><b>Data Entrega: </b> "+data_entrega+"<br><br><b>Morada entrega: </b>"+delivery_name+"<br><b>Rua/Lugar entrega: </b>"+delivery_street +"<br><b>Cidade entrega:</b> "+delivery_city+"<br><b>Zip:</b> "+delivery_zip + "<br><b>Pais entrega:</b> " + delivery_country +"<br><b>Info. adicional:</b> " + delivery_details+" <br><br><br><b>Contato</b><br><b>Nome: </b>"+ nome_contato+"<br><b>Email: </b>"+ email_contato+"<br><b>Informações Contato: </b>"+ numero_contato+"<br><br><br><b>Dados Volumes:</b><br><br><b>Paletes:</b> "+n_pallets+"<br><b>Dimensões: </b>"+comprimento+"x"+largura+"x"+altura+"<br><b>Peso: </b>"+peso+"Kgs <br><b>Sobreponível: </b> " + empilhavel +  "<br><b>Tipo Transporte: "+tipo_transport+" </hb> <h4>Mensagem enviada pela conta de: "+ username+"</h4>"
    mail.send(msg)
    #criar funcao email no inicio da requisição
    
    flash('Requisição criada', category='success')
    
    #return render_template('request_transport.html')
    return redirect(url_for('request_transport'))


#editqtd pallets
@app.route('/requisition_edit/<int:id>',methods=['GET', 'POST'])
def requisition_edit(id):

  username=session['username']
  owner_email=str(username)+str('@borgwarner.com')
  id_var=id
  #nº Paletes
  internal_code=request.form['var_0']
  n_pallets=request.form['var_1']
  comprimento=request.form['var_2']
  largura=request.form['var_3']
  altura=request.form['var_4']
  peso=request.form['var_5']
  empilhavel=request.form['var_7']
  volume = (float(n_pallets) * float(comprimento) * float(largura) * float(altura)) / 1000000
  #Colocar SP update
  cursor=conn.cursor()
  Store_procedure_ut_requisition_edit = "Exec dbo.ut_requisition_edit @id=?,@pallet_qty = ?,@pallet_lenght = ?,@pallet_width = ?,@pallet_height = ?,@total_weight= ?, @total_volume = ?,@stackable = ?,@request_state = ?"
  cursor.execute(Store_procedure_ut_requisition_edit,id_var,n_pallets,comprimento,largura,altura,peso,volume,empilhavel,1)
  cursor.commit()

  Subject='Requisição ' + internal_code
  #alterar o recipients para valtransports
  msg = Message(Subject, recipients = ['drebelo@borgwarner.com','befernandes@borgwarner.com','vprado@borgwarner.com'],cc=[owner_email])
  #msg.body = message
  msg.html =  "Olá,<br><br> A requisição com o Código: <b>"+ internal_code +"</b> foi alterada, e encontra-se disponível para consulta na Plataforma LMS (<a href='http://10.30.64.11:6600/'>LMS</a>). <br><br><br><b>Dados Volumes:</b><br><br><b>Paletes:</b> "+n_pallets+"<br><b>Dimensões: </b>"+comprimento+"x"+largura+"x"+altura+"<br><b>Peso: </b>"+peso+"Kgs <br><b>Sobreponível: </b>"+empilhavel+"<br><br><h4>Mensagem enviada por: "+ username+"</h4> <h5>Não responda a este email!</h5>"
  mail.send(msg)
  #criar funcao email no inicio da requisição
  flash('Requisição enviada', category='success')
  
  return redirect(url_for('status_transport'))


@app.route('/option_selection/<int:id>',methods=['GET', 'POST'])
def option_selection(id):

  username=session['username']
  id_var=id
  option = request.form['option_var']
  internal_code = request.form['internal_code']
  status_requisition=3

  owner_email=str(username)+ str('@borgwarner.com')

  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  option_selection_supervisor = "Exec dbo.[user_option_select_supervisor] @option_id=?,@requester = ?, @id = ?"
  cursor.execute(option_selection_supervisor,option,username,id_var)
  option_selection_supervisor_data = cursor.fetchall()
  supervisor_1=option_selection_supervisor_data[0][0]
  supervisor_2=option_selection_supervisor_data[0][1]
  supervisor_3=option_selection_supervisor_data[0][2]

  supervisor_1_email=str(supervisor_1)+ str('@borgwarner.com')
  
  if supervisor_2 !='':
    supervisor_2_email=str(supervisor_2)+ str('@borgwarner.com')
  else:
    supervisor_2_email=''

  if supervisor_3 !='':
    supervisor_3_email=str(supervisor_3)+ str('@borgwarner.com')
  else:
    supervisor_3_email=''

  #storedprocedure para inserir na tabela ut_request_validate todos os supervisores do request
  cursor=conn.cursor()
  option_selection = "Exec dbo.[user_option_select] @option_id=?,@status_requisition = ?, @id = ?,@supervisor_1=?,@supervisor_2=?,@supervisor_3=?"
  cursor.execute(option_selection,option,status_requisition,id_var,supervisor_1,supervisor_2,supervisor_3)
  cursor.commit()
    
  approval_requests_info = "Exec dbo.[approval_requests_info] @id=?"
  cursor.execute(approval_requests_info,id_var)
  approval_requests_info_data = cursor.fetchall()
  pickup_country=approval_requests_info_data[0][3]
  delivery_country=approval_requests_info_data[0][4]
  root_cause=approval_requests_info_data[0][5]
  corrective_action=approval_requests_info_data[0][6]
  impact=approval_requests_info_data[0][7]
  imputable=approval_requests_info_data[0][8]
  dash="/"

  Subject='Request - option selected: ' + internal_code
  msg = Message(Subject, recipients = [supervisor_1_email],cc=[owner_email,'drebelo@borgwarner.com','befernandes@borgwarner.com','vprado@borgwarner.com'])
  msg.html =  "Olá,<br><br> A requisição com o  Internal Code: <b>"+ internal_code +"</b> está pendente da sua aprovação..<br><br>Pickup/Delivery: "+str(pickup_country+dash)+str(delivery_country)+"<br>Root Cause: "+str(root_cause)+"<br>Corrective Action: "+str(corrective_action)+"<br>Impact: "+str(impact)+"<br>Imputable: "+str(imputable)+"<br><br><h4>Message sent by : "+ username+"@borgwarner.com</h4> <h5>Não responda a este email.</h5>"
  mail.send(msg)
  flash('Requisição enviada', category='success')
  return redirect(url_for('status_transport'))

@app.route('/request_transport')
def request_transport():

  cursor=conn.cursor()
  cursor.execute("SELECT * from CustomersVendors")
  morada_fornecedores = cursor.fetchall()

  cursor.execute("SELECT * FROM [LMS].[dbo].[cost_center] where mrp is not null order by name asc")
  cost_center = cursor.fetchall()

  return render_template('/transports/request_transport.html',morada_fornecedores=morada_fornecedores,cost_center=cost_center)


@app.route('/request_standard_transport')
def request_standard_transport():

  cursor=conn.cursor()
  cursor.execute("SELECT * from CustomersVendors")
  morada_fornecedores = cursor.fetchall()

  cursor.execute("SELECT * FROM [LMS].[dbo].[cost_center] where mrp is not null order by name asc")
  cost_center = cursor.fetchall()

  return render_template('/transports/request_standard_transport.html',morada_fornecedores=morada_fornecedores,cost_center=cost_center)


@app.route('/request_standard_transport_final')
def request_standard_transport_final():
  try:
    username=session['username']
    cursor=conn.cursor()
    cursor.execute("SELECT * from CustomersVendors")
    morada_fornecedores = cursor.fetchall()

    cursor.execute("SELECT * FROM [LMS].[dbo].[cost_center] where mrp is not null order by name asc")
    cost_center = cursor.fetchall()

    return render_template('/transports/request_standard_transport_final.html',morada_fornecedores=morada_fornecedores,cost_center=cost_center)
  except Exception as e:
        flash('Tem que efetuar login!', category='warning')
  return redirect(url_for('index'))







#Transportes
@app.route('/transports_requests')
def transports_requests():
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  transports_request = "Exec dbo.[requisitions]"
  cursor.execute(transports_request)
  transports_request_data = cursor.fetchall()

  cursor.execute("SELECT * FROM [LMS].[dbo].[cost_center] where financial='yes' order by name asc")
  cost_center_financial = cursor.fetchall()

  cursor.execute("SELECT * FROM [LMS].[dbo].[ut_category] order by name asc")
  category = cursor.fetchall()

  return render_template('/transports/transports_requests.html',transports_request_data=transports_request_data,cost_center_financial=cost_center_financial,category=category)

@app.route('/transports_requests_in_progress')
def transports_requests_in_progress():
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  transports_request = "Exec dbo.[requisitions_in_progress]"
  cursor.execute(transports_request)
  transports_request_data = cursor.fetchall()
  return render_template('/transports/transports_requests_in_progress.html',transports_request_data=transports_request_data)

@app.route('/transports_requests_closed')
def transports_requests_closed():
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  transports_request = "Exec dbo.[requisitions_closed]"
  cursor.execute(transports_request)
  transports_request_data = cursor.fetchall()
  return render_template('/transports/transports_requests_closed.html',transports_request_data=transports_request_data)

@app.route('/transports_requests_finished')
def transports_requests_finished():
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  transports_request = "Exec dbo.[requisitions_aproved]"
  cursor.execute(transports_request)
  transports_request_data = cursor.fetchall()
  return render_template('transports_requests_finished.html',transports_request_data=transports_request_data)

@app.route('/option_add/<int:id>',methods=['GET', 'POST'])
def option_add(id):
  
  owner=session['username']
  id_var=id
  status_requisition=2

  owner_email=str(owner)+str('@borgwarner.com')

  requester = request.form['requester']
  internal_code = request.form['internal_code']
  requester_email = str(requester)+str('@borgwarner.com')

  option_1_desc = request.form['option_1_name']
  option_1_cost = request.form['option_1_price']
  option_1_date = request.form['option_1_date']

  option_2_desc = request.form['option_2_name']
  option_2_cost = request.form['option_2_price']
  option_2_date = request.form['option_2_date']

  classificacao_transport = request.form['classificacao_transport']
  centro_custo_financial = request.form['centro_custo_financial']
  urgent = request.form['var_22']

  
  Subject='Requisição ' + internal_code + '- Opções '
  msg = Message(Subject, recipients = [requester_email],cc=['drebelo@borgwarner.com','befernandes@borgwarner.com','vprado@borgwarner.com'])
  msg.html =  "Olá,<br><br> As opções selecionadas para o seu pedido com o Internal Code  <b>"+ internal_code +"</b> <br><br><b>Opção 1: </b>"+option_1_desc+"<br><b>Custo:</b> " + option_1_cost +  "€ <br><b>Tempo Transito:</b> " + option_1_date +  "<br><br><b>Opção 2:</b> " + option_2_desc +  "<br><b>Custo:</b> " + option_2_cost +  "€ <br> <b>Tempo Transito :</b> " + option_2_date +  "<br> <h4>Mensagem enviada pela conta de  : "+ owner+"</h4> <h5>Não responda a este email!</h5>"
  mail.send(msg)
  

  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  option_add = "Exec dbo.[transport_option_add] @id = ?,@status_requisition=?,@owner=?,@option_1_desc=?,@option_1_date=?,@option_1_cost=?,@option_2_desc=?,@option_2_date=?,@option_2_cost=?,@classificacao_transport=?,@category_cost_center=?,@urgent=?"
  cursor.execute(option_add,id_var,status_requisition,owner,option_1_desc,option_1_date,option_1_cost,option_2_desc,option_2_date,option_2_cost,classificacao_transport,centro_custo_financial,urgent)
  cursor.commit()
  flash('Opções selecionadas e enviadas', category='success')

  return redirect(url_for('transports_requests'))

@app.route('/option_edit/<int:id>',methods=['GET', 'POST'])
def option_edit(id):
  
  owner=session['username']
  id_var=id
  status_requisition=2

  owner_email=str(owner)+str('@borgwarner.com')

  #requester = request.form['requester']
  #internal_code = request.form['internal_code']
  

  internal_code = request.form['var_0']
  requester = request.form['var_01']
  requester_email = str(requester)+str('@borgwarner.com')
  option_1_desc = request.form['var_1']
  option_1_date = request.form['var_2']
  option_1_cost = request.form['var_3']
  
  option_2_desc = request.form['var_4']
  option_2_date = request.form['var_5']
  option_2_cost = request.form['var_6']
  
  #classificacao_transport = request.form['classificacao_transport']
  #centro_custo_financial = request.form['centro_custo_financial']
  
  Subject='Requisição ' + internal_code + '- alterada! '
  msg = Message(Subject, recipients = [requester_email],cc=[owner_email,'drebelo@borgwarner.com','befernandes@borgwarner.com','vprado@borgwarner.com'])
  msg.html =  "Olá,<br><br> As opções selecionadas para o seu pedido com o Internal Code  <b>"+ internal_code +"</b> foram alteradas. <br><br><b>Option 1: </b>"+option_1_desc+"<br><b>Custo:</b> " + option_1_cost +  "€ <br><b>Tempo Transito:</b> " + option_1_date +  "<br><br><b>Option 2:</b> " + option_2_desc +  "<br><b>Custo:</b> " + option_2_cost +  "€ <br> <b>Tempo Transito :</b> " + option_2_date +  "<br> <h4>Mensagem enviada pela conta de  : "+ owner+"</h4> <h5>Não responda a este email!</h5>"
  mail.send(msg)
  
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  option_edit = "Exec dbo.[transport_option_edit] @id = ?,@status_requisition=?,@owner=?,@option_1_desc=?,@option_1_date=?,@option_1_cost=?,@option_2_desc=?,@option_2_date=?,@option_2_cost=?"
  cursor.execute(option_edit,id_var,status_requisition,owner,option_1_desc,option_1_date,option_1_cost,option_2_desc,option_2_date,option_2_cost)
  cursor.commit()
  flash('Options updated successfully', category='success')
  
  return redirect(url_for('transports_requests_in_progress'))


@app.route('/option_edit_after_finish/<int:id>',methods=['GET', 'POST'])
def option_edit_after_finish(id):
  
  owner=session['username']
  id_var=id
  status_requisition=2

  owner_email=str(owner)+str('@borgwarner.com')

  #requester = request.form['requester']
  #internal_code = request.form['internal_code']
  

  internal_code = request.form['var_0']
  requester = request.form['var_01']
  requester_email = str(requester)+str('@borgwarner.com')
  option_1_desc = request.form['var_1']
  option_1_date = request.form['var_2']
  option_1_cost = request.form['var_3']
  
  option_2_desc = request.form['var_4']
  option_2_date = request.form['var_5']
  option_2_cost = request.form['var_6']


  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  option_edit = "Exec dbo.[transport_option_edit_after_finish] @id = ?,@status_requisition=?,@owner=?,@option_1_desc=?,@option_1_date=?,@option_1_cost=?,@option_2_desc=?,@option_2_date=?,@option_2_cost=?,@internal_code=?"
  cursor.execute(option_edit,id_var,status_requisition,owner,option_1_desc,option_1_date,option_1_cost,option_2_desc,option_2_date,option_2_cost,internal_code)
  supervisor=cursor.fetchall()
  cursor.commit()
  supervisor_1=supervisor[0][0]

  supervisor_1_email = str(supervisor_1)+str('@borgwarner.com')
  
  #classificacao_transport = request.form['classificacao_transport']
  #centro_custo_financial = request.form['centro_custo_financial']
  
  Subject='Requisição ' + internal_code + '- alterada! '
  msg = Message(Subject, recipients = [requester_email,supervisor_1_email],cc=[owner_email,'drebelo@borgwarner.com','befernandes@borgwarner.com','vprado@borgwarner.com'])
  msg.html =  "Olá,<br><br> As opções selecionadas para o seu pedido com o Internal Code  <b>"+ internal_code +"</b> foram alteradas e precisam da sua aprovação. <br><br><b>Option 1: </b>"+option_1_desc+"<br><b>Custo:</b> " + option_1_cost +  "€ <br><b>Tempo Transito:</b> " + option_1_date +  "<br><br><b>Option 2:</b> " + option_2_desc +  "<br><b>Custo:</b> " + option_2_cost +  "€ <br> <b>Tempo Transito :</b> " + option_2_date +  "<br> <h4>Mensagem enviada pela conta de  : "+ owner+"</h4> <h5>Não responda a este email!</h5>"
  mail.send(msg)
  
  flash('Options updated successfully', category='success')
  
  return redirect(url_for('transports_requests_closed'))



@app.route('/status_transport')
def status_transport():
  username= session['username']
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  transports_request = "Exec dbo.[user_requisitions] @username=?"
  cursor.execute(transports_request,username)
  transports_request_data = cursor.fetchall()

  return render_template('/transports/status_transport.html',transports_request_data=transports_request_data)

@app.route('/status_transport_standard')
def status_transport_standard():
  try:
    username= session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    standard_transports_request = "Exec dbo.[StandardTransportRequestByUserFinal] @username=?"
    cursor.execute(standard_transports_request,username)
    transports_request_data = cursor.fetchall()

    return render_template('/transports/status_transport_standard.html',transports_request_data=transports_request_data)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))

"""
#New Standard Transport Final
@app.route('/status_transport_standard_final')
def status_transport_standard_final():
  try:
    username= session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    standard_transports_request = "Exec dbo.[StandardTransportRequestByUserFinal] @username=?"
    cursor.execute(standard_transports_request,username)
    transports_request_data = cursor.fetchall()

    return render_template('/transports/status_transport_standard_final.html',transports_request_data=transports_request_data)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))
"""

#Approval Requests
@app.route('/approval_requests_pendent')
def approval_requests_pendent():
  username=session['username']
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  #approval_requests = "Exec dbo.[approval_requests] @requester=?"
  approval_requests = "Exec dbo.[approval_requests_pendent] @requester=?"
  cursor.execute(approval_requests,username)
  approval_requests_data = cursor.fetchall()
  return render_template('transports/approval_requests_pendent.html',approval_requests_data=approval_requests_data)

@app.route('/approval_requests_done')
def approval_requests_done():
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  approval_requests_done = "Exec dbo.[approval_requests_done]"
  cursor.execute(approval_requests_done)
  approval_requests_done = cursor.fetchall()
  return render_template('transports/approval_requests_done.html',approval_requests_done=approval_requests_done)

#acoes arpovação REQUESTS
@app.route('/aprovar_requisicao/<int:id>',methods=['GET', 'POST'])
def aprovar_requisicao(id):
  
  approval_owner=session['username']
  approval_owner_email=str(approval_owner) + str('@borgwarner.com')
  id_var=id
  
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  approvar_requisicao = "Exec dbo.[approve_request_final] @id = ?,@approval_owner=?"
  cursor.execute(approvar_requisicao,id_var,approval_owner)
  cursor.commit()

  cursor=conn.cursor()
  approval_requests_info = "Exec dbo.[approval_requests_info] @id=?"
  cursor.execute(approval_requests_info,id_var)
  approval_requests_info_data = cursor.fetchall()

  requester = approval_requests_info_data[0][0]
  transport_requester = approval_requests_info_data[0][1]
  internal_code = approval_requests_info_data[0][2]
  requester_email=str(requester) + str('@borgwarner.com')
  transport_requester_email=str(transport_requester) + str('@borgwarner.com')

  cursor=conn.cursor()
  cursor.execute("SELECT top(1) supervisor FROM [LMS].[dbo].[ut_request_validate] where id_request=? and status =0 order by id",id_var)
  supervisor=cursor.fetchall()
  if supervisor:
    new_supervisor=str(supervisor[0][0])+"@borgwarner.com"
    Subject='Aguarda aprovação: ' + internal_code
    msg = Message(Subject, recipients = [requester_email],cc=[approval_owner_email,transport_requester_email,new_supervisor])
    msg.html =  "Olá,<br><br> O seu pedido de requisição com  o código: <b>"+ internal_code +"</b> foi <b>ACEITE</b> pelo "+str(approval_owner)+".<br><br> Aguarda aprovação de "+str(supervisor[0][0])+".<br><br> <h4>Mensagem enviada por : "+ approval_owner+"@borgwarner.com</h4> <h5>Atenção email automático. Não responda a este email!</h5>"
    mail.send(msg)
    flash('Aceite com sucesso',category='success')
    return redirect(url_for('approval_requests_pendent'))

  else:
    cursor.execute("UPDATE [ut_request] set approval_status= 'Closed', approval_date_final=getdate() where id=?",id_var)
    cursor.commit()
    
    Subject='Pedido Aceite: ' + internal_code
    msg = Message(Subject, recipients = [requester_email],cc=[approval_owner_email,transport_requester_email])
    msg.html =  "Olá,<br><br> O seu pedido de requisição com  o código: <b>"+ internal_code +"</b> foi <b>ACEITE</b> pelos seus supervisores. <h5>Atenção email automático. Não responda a este email!</h5>"
    mail.send(msg)
    flash('Aceite com sucesso',category='success')
    return redirect(url_for('approval_requests_pendent'))

@app.route('/recusar_requisicao/<int:id>',methods=['GET', 'POST'])
def recusar_requisicao(id):
  
  approval_owner=session['username']
  approval_owner_email=str(approval_owner) + str('@borgwarner.com')
  id_var=id
  status_requisition=4
  justificacao = request.form['justificacao']
  status_approve='REJECTED'

  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  recusar_requisicao = "Exec dbo.[refuse_request_final] @id = ?,@approval_owner=?,@justification=?"
  cursor.execute(recusar_requisicao,id_var,approval_owner,justificacao)
  cursor.commit()

  approval_requests_info = "Exec dbo.[approval_requests_info] @id=?"
  cursor.execute(approval_requests_info,id_var)
  approval_requests_info_data = cursor.fetchall()
  requester = approval_requests_info_data[0][0]
  transport_requester = approval_requests_info_data[0][1]
  internal_code = approval_requests_info_data[0][2]
  requester_email=str(requester) + str('@borgwarner.com')
  transport_requester_email=str(transport_requester) + str('@borgwarner.com')

  #recusar_requisicao = "Exec dbo.[refuse_request] @id = ?,@status_requisition=?,@approval_owner=?,@status_aprove=?,@justification=?"
  #cursor.execute(recusar_requisicao,id_var,status_requisition,approval_owner,status_approve,justificacao)
  #cursor.commit()

  Subject='Pedido Recusado: ' + internal_code
  msg = Message(Subject, recipients = [requester_email],cc=[approval_owner_email,transport_requester_email])
  msg.html =  "Olá,<br><br> O seu pedido de requisição com  o Código: <b>"+ internal_code +"</b> foi <b>RECUSADO</b> pelo seu supervisor. <br> <br> <h4>Mensagem enviada por : "+ approval_owner+"@borgwarner.com</h4> <h5>Atenção email automático. Não responda a este email!</h5>"
  mail.send(msg)
  flash('Requisição recusada com sucesso.',category='success')

  return redirect(url_for('approval_requests_pendent'))

#history
@app.route('/history_all')
def history_all():
  username= session['username']
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  all_transports_request = "Exec dbo.[all_requisitions]"
  cursor.execute(all_transports_request)
  transports_request_data = cursor.fetchall()

  return render_template('/transports/history_all.html',transports_request_data=transports_request_data)


@app.route('/history_all_standard_transports')
def history_all_standard_transports():
  username= session['username']
  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  all_transports_request = "Exec dbo.[AllStandardRequests]"
  cursor.execute(all_transports_request)
  transports_request_data = cursor.fetchall()

  return render_template('/transports/history_all_standard_transports.html',transports_request_data=transports_request_data)

########################################################################################################################################################################

@app.route('/status_portaria',methods=['GET', 'POST'])
def status_portaria():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    visitas = "Exec dbo.[visitas]"
    cursor.execute(visitas)
    visitas_data = cursor.fetchall()

    SP_estacionamento_disponivel = "Exec dbo.[ocupacao_estacionamento_servicos]"
    cursor.execute(SP_estacionamento_disponivel)
    estacionamento_disponivel = cursor.fetchall()

    gestao_stock = "Exec dbo.[gestao_stock_epi]"
    cursor.execute(gestao_stock)
    gestao_stock_data = cursor.fetchall()
    var_2=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    sp_cartoes = "Exec dbo.[VisitGetCards]"
    cursor.execute(sp_cartoes)
    cartoes_data = cursor.fetchall()

    sp_empresas = "Exec dbo.[VisitGetCompany]"
    cursor.execute(sp_empresas)
    empresas_data = cursor.fetchall()

    return render_template('/portaria/status_portaria.html',empresas_data=empresas_data,cartoes_data=cartoes_data,estacionamento_disponivel=estacionamento_disponivel,visitas_data=visitas_data,gestao_stock_data=gestao_stock_data)
  except Exception as e:
        flash('Erro de Login', category='error')
  return redirect(url_for('index'))

########################################################################
@app.route('/status_portaria_temporarios',methods=['GET', 'POST'])
def status_portaria_temporarios():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    visitas = "Exec dbo.[visitasCartoesTemporarios]"
    cursor.execute(visitas)
    visitas_data = cursor.fetchall()

    gestao_stock = "Exec dbo.[gestao_stock_epi]"
    cursor.execute(gestao_stock)
    gestao_stock_data = cursor.fetchall()
    var_2=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    sp_cartoes = "Exec dbo.[VisitGetCardsTemporary]"
    cursor.execute(sp_cartoes)
    cartoes_data = cursor.fetchall()

    return render_template('/portaria/status_portaria_temporarios.html',cartoes_data=cartoes_data,visitas_data=visitas_data,gestao_stock_data=gestao_stock_data)
  except Exception as e:
        flash('Erro de Login', category='error')
  return redirect(url_for('index'))
  
@app.route('/add_card',methods=['GET', 'POST'])
def add_card():
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']
      cartao=request.form['cartao']
      tipocartao=request.form['type']

      create_AddCard = "Exec dbo.[AddCard] @Nome=?,@Type=?"
      cursor.execute(create_AddCard,cartao,tipocartao)
      cursor.commit()
      flash('Registo de entrada Concluído', category='success')
      return redirect(url_for('estado_cartoes'))



@app.route('/add_visit_temp',methods=['GET', 'POST'])
def add_visit_temp():
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']
      nome=request.form['nome']
      numero=request.form['numero']
      cartao=request.form['cartao']
      create_AddVisitTemp = "Exec dbo.AddVisitTemp @Nome=?,@Numero=?,@Cartao=?,@Username=?"
      cursor.execute(create_AddVisitTemp,nome,numero,cartao,username)
      cursor.commit()
      flash('Registo de entrada Concluído', category='success')
      return redirect(url_for('status_portaria_temporarios'))


@app.route('/delete_visit_temp/<int:id>', methods=['POST', 'GET'])
def delete_visit_temp(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_DeleteVisitTemp = "Exec dbo.[DeleteVisitTemp] @id = ?"
    cursor.execute(storeproc_DeleteVisitTemp,id)
    conn.commit()
    flash('Registo eliminado', category='warning')
    return redirect(url_for('status_portaria_temporarios'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/edit_visit_temp/<int:id>', methods=['POST', 'GET'])
def edit_visit_temp(id):
  try:
    if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']
      nome=request.form['nome']
      numero=request.form['numero']
      cartao=request.form['cartao']
      storeproc_editVisitTemp = "Exec dbo.[editVisitTemp] @id = ?,@Cartao=?,@Nome=?,@Numero=?"
      cursor.execute(storeproc_editVisitTemp,id,cartao,nome,numero)
      conn.commit()
      flash('Registo Editado', category='warning')
      return redirect(url_for('status_portaria_temporarios'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/registar_saida_visit_temp/<int:id>', methods=['POST', 'GET'])
def registar_saida_visit_temp(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    datetime_var=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    storeproc_AddVisitTempExit = "Exec dbo.[AddVisitTempExit] @id = ?,@RegDate=?,@Username=?"
    cursor.execute(storeproc_AddVisitTempExit,id,datetime_var,username)
    conn.commit()
    flash('Registado com sucesso', category='success')
    return redirect(url_for('status_portaria_temporarios'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


#estado do estacionamento servicos
@app.route('/estado_estacionamento_servicos',methods=['GET', 'POST'])
def estado_estacionamento_servicos():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    SP_estado_estacionamento_servicos = "Exec dbo.[settings_estado_estacionamento_servicos]"
    cursor.execute(SP_estado_estacionamento_servicos)
    estado_estacionamento_servicos = cursor.fetchall()
    return render_template('/portaria/estado_estacionamento_servicos.html',estado_estacionamento_servicos=estado_estacionamento_servicos)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

########################################################################

@app.route('/status_empresas',methods=['GET', 'POST'])
def status_empresas():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    sp_RegVisitsCompanies = "Exec dbo.[RegVisitsCompanies]"
    cursor.execute(sp_RegVisitsCompanies)
    companies_data = cursor.fetchall()
    return render_template('/portaria/status_empresas.html',companies_data=companies_data)
  except Exception as e:
        flash('Erro de Login', category='error')
  return redirect(url_for('index'))

@app.route('/delete_company/<int:id>', methods=['POST', 'GET'])
def delete_company(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_DeleteCompany = "Exec dbo.[DeleteCompany] @id = ?"
    cursor.execute(storeproc_DeleteCompany,id)
    conn.commit()
    flash('Registo eliminado', category='warning')
    return redirect(url_for('status_empresas'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/add_company',methods=['GET', 'POST'])
def add_company():
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()

      nome=request.form['nome']
      create_AddCompany = "Exec dbo.AddCompany @Nome=?"
      cursor.execute(create_AddCompany,nome)
      cursor.commit()
      flash('Registo de Empresa Concluído', category='success')
      return redirect(url_for('status_empresas'))

@app.route('/edit_company/<int:id>', methods=['POST', 'GET'])
def edit_company(id):
  try:
    if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      nome=request.form['nome']
      storeproc_EditCompany = "Exec dbo.[EditCompany] @id = ?,@Nome=?"
      cursor.execute(storeproc_EditCompany,id,nome)
      conn.commit()
      flash('Registo Editado', category='warning')
      return redirect(url_for('status_empresas'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

########################################################################
@app.route('/alterar_estado_estacionamento_servicos/<int:id>', methods=['POST', 'GET'])
def alterar_estado_estacionamento_servicos(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_settings_alterar_estado_estacionamento_servicos = "Exec dbo.[settings_alterar_estado_estacionamento_servicos] @id = ?"
    cursor.execute(storeproc_settings_alterar_estado_estacionamento_servicos,id)
    conn.commit()
    flash('Estacionamento libertado', category='success')
    return redirect(url_for('estado_estacionamento_servicos'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


##
#estado do estacionamento servicos
@app.route('/estado_cartoes',methods=['GET', 'POST'])
def estado_cartoes():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    SP_SettingsCartoes = "Exec dbo.[SettingsCartoes]"
    cursor.execute(SP_SettingsCartoes)
    cartoes_data = cursor.fetchall()
    SP_SettingsCartoesFollowUp = "Exec dbo.[SettingsCartoesFollowup]"
    cursor.execute(SP_SettingsCartoesFollowUp)
    cartoes_data_followup = cursor.fetchall()

    return render_template('/portaria/estado_cartoes.html',cartoes_data=cartoes_data,cartoes_data_followup=cartoes_data_followup)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


#Anular cartao
@app.route('/bloquear_cartao/<int:id>',methods=['GET', 'POST'])
def bloquear_cartao(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      motivo=request.form['var_1']
      username=session['username']
      Store_procedure_anular_cartao = "Exec dbo.CartoesBloquear @id = ?,@motivo = ?,@username=?"
      cursor.execute(Store_procedure_anular_cartao,id_var,motivo,username)
      cursor.commit()
      flash('Cartão Bloqueado com sucesso!', category='success')
      return redirect(url_for('estado_cartoes'))

#Anular cartao
@app.route('/desbloquear_cartao/<int:id>',methods=['GET', 'POST'])
def desbloquear_cartao(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    id_var=id
    Store_procedure_desbloquear = "Exec dbo.[CartoesDesbloquear] @id = ?"
    cursor.execute(Store_procedure_desbloquear,id_var)
    cursor.commit()
    flash('Cartão desbloqueado com sucesso!', category='success')
    return redirect(url_for('estado_cartoes'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/libertar_cartao/<int:id>',methods=['GET', 'POST'])
def libertar_cartao(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    id_var=id
    Store_procedure_desbloquear = "Exec dbo.[CartoesDesbloquear] @id = ?"
    cursor.execute(Store_procedure_desbloquear,id_var)
    cursor.commit()
    print ('just do it')
    flash('Cartão desbloqueado com sucesso!', category='success')
    return redirect(url_for('estado_cartoes'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))



@app.route('/get_info_estado_cartoes', methods=['GET'])
def get_info_estado_cartoes():
    id = request.args.get('id')
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    cursor.execute("SELECT [Identification],[CardType] FROM [CartoesEntrada]  where id = ?",(id))
    identification = cursor.fetchall()
    card_id=identification[0][0]
    card_type=identification[0][1]
    #print (card_id)
    #print (card_type)
    cursor.execute("SELECT [CreationDate],[Motive],[Owner],[CardId],[Type] FROM [CartoesEntradaFollowUp]  where CardId = ? and Type =?",(card_id,card_type))
    data = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    # Convertendo os resultados para uma lista de dicionários
    result_list = []
    for row in data:
        result_dict = dict(zip(column_names, row))
        result_list.append(result_dict)  
    return jsonify(result_list)


#anular req_visit
@app.route('/anular_regito_req_visit/<int:id>',methods=['GET', 'POST'])
def anular_regito_req_visit(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      motivo=request.form['var_1']
      username=session['username']
      Store_procedure_anular_registo_portaria_req_visita = "Exec dbo.anular_registo_portaria_req_visita_new @id = ?,@motivo = ?,@username=?"
      #Store_procedure_anular_registo_portaria_req_visita = "Exec dbo.anular_registo_portaria_req_visita @id = ?,@motivo = ?,@username=?"
      cursor.execute(Store_procedure_anular_registo_portaria_req_visita,id_var,motivo,username)
      cursor.commit()
      flash('Registo anulado com sucesso!', category='success')
      
      return redirect(url_for('status_portaria'))
@app.route('/anular_regito_req_visit_2/<int:id>',methods=['GET', 'POST'])
def anular_regito_req_visit_2(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      motivo=request.form['var_1']
      username=session['username']
      Store_procedure_anular_registo_portaria_req_visita_2 = "Exec dbo.anular_registo_portaria_req_visita_2_new @id = ?,@motivo = ?,@username=?"
      #Store_procedure_anular_registo_portaria_req_visita_2 = "Exec dbo.anular_registo_portaria_req_visita_2 @id = ?,@motivo = ?,@username=?"
      cursor.execute(Store_procedure_anular_registo_portaria_req_visita_2,id_var,motivo,username)
      cursor.commit()
      flash('Registo anulado com sucesso!', category='success')
      
      return redirect(url_for('status_portaria'))


#editar req_visit
@app.route('/update_registo_vigilantes_req_visit/<int:id>',methods=['GET', 'POST'])
def update_registo_vigilantes_req_visit(id):
  try:
    username=session['username']
    if request.method == 'POST':
      id_var=id
      nome=request.form['var_1']
      empresa=request.form['var_2']
      identificacao=request.form['var_3']
      contato=request.form['var_4']
      matricula=request.form['var_5']
      oculos=request.form['var_6']
      bata=request.form['var_7']
      sapatos=request.form['var_8']
      cartao=request.form['var_9']
      obs=request.form['var_10']
      responsable=request.form['var_11']
      var_lugar=request.form['var_lugar']


      cursor=conn.cursor()
      Store_procedure_alterar_registo_vigilantes_req_visitas = "Exec dbo.PortariaAlterarRegistoVisita @id = ?,@nome=?,@empresa=?,@identificacao=?,@matricula=?,@contato=?,@glasses=?,@uniform=?,@shoes=?,@cartao=?,@lugar=?,@obs=?,@responsable=?"
      cursor.execute(Store_procedure_alterar_registo_vigilantes_req_visitas,id_var,nome,empresa,identificacao,matricula,contato,oculos,bata,sapatos,cartao,var_lugar,obs,responsable)
      cursor.commit()
      flash('Registo alterado com sucesso!', category='success')
      
      return redirect(url_for('status_portaria'))
  except Exception as e:
        flash('Erro ao alterar o registo', category='error')
  return redirect(url_for('index'))

#voltar a entrar
@app.route('/voltar_entrar_req_visit/<int:id>',methods=['GET', 'POST'])
def voltar_entrar_req_visit(id):
  try:
    username=session['username']
    if request.method == 'POST':
      lugar=request.form['var_lugar']
      id_var=id
      cursor=conn.cursor()
      Store_procedure_create_second_entry_reg_visit = "Exec dbo.create_second_entry_reg_visit_new @id = ?,@username=?, @lugar=?"
      #Store_procedure_create_second_entry_reg_visit = "Exec dbo.create_second_entry_reg_visit @id = ?,@username=?"
      cursor.execute(Store_procedure_create_second_entry_reg_visit,id_var,username,lugar)
      cursor.commit()
      flash('Registo alterado com sucesso!', category='success')
      
      return redirect(url_for('status_portaria'))
  except Exception as e:
        flash('Erro ao alterar o registo', category='error')
  return redirect(url_for('index'))


@app.route('/status_epis',methods=['GET', 'POST'])
def status_epis():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    epis = "Exec dbo.[epis]"
    cursor.execute(epis)
    epis_data = cursor.fetchall()
    return render_template('status_epis.html',epis_data=epis_data)
  except Exception as e:
        flash('Erro de Login', category='error')
  return redirect(url_for('index'))

#registo de Visitas
def send_file_to_ip_printer(printer_ip, printer_port, file_path):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
        pcl_command_set_a5 = b'\x1B&l26A'
        # Combine the PCL command with the file content
        combined_content = pcl_command_set_a5 + file_content
        a5_command = b'\x1B%-12345X@PJL SET PAPER=A5\r\n'
        data = a5_command + file_content

        # Establish a socket connection to the printer
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((printer_ip, printer_port))
            print("Connected to the printer.")

            # Send the file content to the printer
            sock.sendall(file_content)
            print("File sent to the printer successfully.")

    except FileNotFoundError:
        print("File not found.")
    except ConnectionRefusedError:
        print("Connection to the printer failed.")
    except Exception as e:
        print(f"An error occurred: {e}")
# Para 1 pessoa
@app.route('/add_visit',methods=['GET', 'POST'])
def add_visit():
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']

      nome=request.form['var_1']
      identificacao=request.form['var_2']
      empresa=request.form['var_3']
      contato=request.form['var_4']
      matricula=request.form['var_5']
      cartaobw=request.form['var_6']
      motivo=request.form['var_7']

      destino=request.form['var_8']
      var_lugar=request.form['var_lugar']
      oculos=request.form['var_9']
      uniforme=request.form['var_10']
      sapatos=request.form['var_11']
      bw_responsable=request.form['var_12']
      obs=request.form['var_13']
      
      create_reg_visit_new_with_print = "Exec dbo.create_reg_visit_new_with_print @nome = ? , @identificacao = ?,@empresa = ?,@contato = ?, @matricula = ? , @cartaobw = ?,@motivo = ?,@destino=?,@oculos=?,@uniforme=?,@sapatos=?,@username=?,@bw_responsable=?,@obs=?,@lugar=?"
      cursor.execute(create_reg_visit_new_with_print,nome,identificacao,empresa,contato,matricula,cartaobw,motivo,destino,oculos,uniforme,sapatos,username,bw_responsable,obs,var_lugar)
      id_var=cursor.fetchone()[0]
      
      cursor.commit()
      day=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
      day_texto=datetime.today().strftime('%Y-%m')
      
      class PDF(FPDF):
          def header(self):
              self.image('static/content/borgwarner_blue.png',130,10,55,5)
              self.set_font('helvetica','B',12)
              self.cell(80, 5, 'LIVRE TRÂNSITO Nº '+ str(id_var)+ str('-') + str(day_texto), align='L')
              self.ln(7)
              self.set_font('helvetica','B',8)
              self.cell(170, 5, 'VIANA DO CASTELO - PORTUGAL', align='R')
              self.ln(10)

          def footer(self):
                # Go to 1.5 cm from bottom
              self.set_y(-10)
              # Select Arial italic 8
              self.set_font('Arial', 'I', 6)
              # Print centered page number
              self.cell(0, 10, 'Version 1.0 - Facilities - 2023', 0, 0, 'C')

      pdf = PDF(orientation="L", unit="mm", format="A5")
      pdf.add_page()

      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(30, 8, 'Nome/Name:', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.multi_cell(60, 6, str(nome), border=0)
      pdf.set_font("Helvetica",'B', size = 11)
      pdf.cell(10, 6, str(''), border=0)
      pdf.cell(80, -20, str('Atenção:'), border=0)
      pdf.ln(6)
      pdf.set_font("Helvetica", size = 6)
      pdf.cell(100, 5, str(''), border=0)
      pdf.cell(80, -20, str('- Durante a visita deve transportar de forma visível o cartão que lhe foi entregue.'), border=0)
      pdf.ln(2)
      pdf.cell(100, 5, str(''), border=0)
      pdf.cell(80, -20, str('- A visita é restrita aos departamentos especificados.'), border=0)
      pdf.ln(2)
      pdf.cell(100, 5, str(''), border=0)
      pdf.cell(80, -20, str('- É proibido efectuar qualquer registo de som ou imagem. Câmaras ou outros equipamentos de'), border=0)
      pdf.ln(2)
      pdf.cell(100, 5, str(''), border=0)
      pdf.cell(80, -20, str('registo de imagem não podem ser utilizadas, excepto em casos devidamente autorizados.'), border=0)
      pdf.ln(2)
      pdf.cell(100, 5, str(''), border=0)
      pdf.cell(80, -20, str('- Informações que lhe forem fornecidas durante a visita têm de ser tratadas confidencialmente.'), border=0)
      pdf.ln(2)
      pdf.cell(100, 5, str(''), border=0)
      pdf.cell(80, -20, str('- À saída terá de devolver este documento devidamente assinado pela pessoa a quem se dirigiu.'), border=0)
      pdf.ln(5)
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(35, 10, 'Empresa/Company:', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(65, 10, str(empresa), border=0)
      pdf.set_font("Helvetica",'B', size = 11)
      pdf.cell(80, -10, str('Please Note:'), border=0)
      pdf.ln(6)
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(40, -16, 'Nº Telef./Phone Number: ', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(70, -16, str(contato), border=0)
      pdf.ln(2)
      pdf.set_font("Helvetica", size = 6)
      pdf.cell(100, -15, str(''), border=0)
      pdf.cell(80, -15, str('- During the visit, the badge given to you by the secuirity is to be worn visibly.'), border=0)
      pdf.ln(2)
      pdf.cell(100, -15, str(''), border=0)
      pdf.cell(80, -15, str('- The visit is restricted to the specified departments.'), border=0)
      pdf.ln(2)
      pdf.cell(100, -15, str(''), border=0)
      pdf.cell(80, -15, str('- Cameras and other visual or sound recording equipment are forbidden unless a'), border=0)
      pdf.ln(2)
      pdf.cell(100, -15, str(''), border=0)
      pdf.cell(80, -15, str('specific permission was given to you.'), border=0)
      pdf.ln(2)
      pdf.cell(100, -15, str(''), border=0)
      pdf.cell(80, -15, str('- Information made available to you during the visit are to be treated confidentially.'), border=0)
      pdf.ln(2)
      pdf.cell(100, -15, str(''), border=0)
      pdf.cell(80, -15, str('- When leaving, pleease make sure you return this document, after signature.'), border=0)
      pdf.ln(2)
     
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(45, -36, 'Matrícula/ Registration no. : ', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(55, -36, str(matricula), border=0)
      pdf.set_font("Helvetica",'U', size = 8)
      pdf.ln(1)
      pdf.cell(50, -15, '____________________________________________________', border=0)
      pdf.ln(3)
      pdf.cell(70, -15, 'Assinatura do Visitante/Visitor Signature', border=0)
      pdf.ln(1)
      pdf.set_font("Helvetica", size = 5)
      #pdf.cell(190, -5, '_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _', border=0)
      pdf.ln(3)

      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(30, 8, str('Vigilante:'), border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(70, 8, str(username), border=0)
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(40, 8, str('Anfitrião BW / Host: '), border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(40, 8, str(bw_responsable), border=0)
      pdf.ln(5)

      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(30, 8, 'Cartão visitante nº: ', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(80, 8, str(cartaobw), border=0)
              
      pdf.ln(3)
      
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(30, 8, 'Data entrada:', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(70, 8, str(day), border=0)
      pdf.cell(60, -16, '__________________________________________________', border=0)
      pdf.ln(5)
      pdf.set_font("Helvetica",'BU', size = 9)
      pdf.cell(60, 10, str('ENTREGA EPI:'), border=0)
      pdf.ln(5)
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(20, 8, 'Calçado:', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(10, 8, str(sapatos), border=0)
      pdf.cell(70, 1, '')
      pdf.cell(70, 8, '_________________________', border=0)
      pdf.cell(80, 8, '______', border=0)
      pdf.ln(5)
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(20, 8, 'Óculo:', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(10, 8, str(oculos), border=0)
      pdf.cell(70, 5, '')
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(70, 8, 'Data e Hora / Date and Time', border=0)
      pdf.cell(70, 8, 'Nº WD', border=0)
      pdf.ln(5)
      pdf.set_font("Helvetica",'B', size = 9)
      pdf.cell(20, 8, 'Bata:', border=0)
      pdf.set_font("Helvetica", size = 8)
      pdf.cell(10, 8, str(uniforme), border=0)
      pdf.cell(80, 5, '')
      pdf.ln(5)
              
      pdf.output(name='imprimir.pdf',dest='S')
      printer_ip = "10.30.67.21"
      printer_port = 9100          # Replace with the printer's port (usually 9100 for Raw Socket Printing)
      file_path = "imprimir.pdf"
      send_file_to_ip_printer(printer_ip, printer_port, file_path)
      
      flash('Registo de entrada feito', category='success')
      return redirect(url_for('status_portaria'))

# até 3 pessoas
@app.route('/add_visit_3',methods=['GET', 'POST'])
def add_visit_3():
  try:
    if request.method == 'POST':
        conn=pyodbc.connect(string_conexao)
        cursor=conn.cursor()
        username=session['username']

        empresa=request.form['var_1']
        matricula=request.form['var_2']
        motivo=request.form['var_3']
        destino=request.form['var_4']

        nome_1=request.form['var_5']
        cartao_1=request.form['var_6']
        contacto_1=request.form['var_7']
        cc_1=request.form['var_8']
        oculos_1=request.form['var_9']
        bata_1=request.form['var_10']
        sapatos_1=request.form['var_11']

        nome_2=request.form['var_12']
        cartao_2=request.form['var_13']
        contacto_2=request.form['var_14']
        cc_2=request.form['var_15']
        oculos_2=request.form['var_16']
        bata_2=request.form['var_17']
        sapatos_2=request.form['var_18']
        var_lugar=request.form['var_lugar']
        nome_3=request.form['var_19']
        cartao_3=request.form['var_20']
        contacto_3=request.form['var_21']
        cc_3=request.form['var_22']
        oculos_3=request.form['var_23']
        bata_3=request.form['var_24']
        sapatos_3=request.form['var_25']
        obs=request.form['var_26']
        responsavel=request.form['var_27']
        
        create_reg_visit_3_new_with_print = "Exec dbo.create_reg_visit_3_new_with_print @empresa = ?, @matricula = ?,@motivo = ?,@destino = ?,@nome_1 = ?,@cartaobw_1 = ?,@cc_1 = ?,@contacto_1=?,@oculos_1=?,@uniforme_1=?,@sapatos_1=?,@nome_2 = ?,@cartaobw_2 = ?,@cc_2 = ?,@contacto_2=?,@oculos_2=?,@uniforme_2=?,@sapatos_2=?,@nome_3 = ?,@cartaobw_3 = ?,@cc_3 = ?,@contacto_3=?,@oculos_3=?,@uniforme_3=?,@sapatos_3=?,@username=?,@responsavel=?,@obs=?,@lugar=?"
        cursor.execute(create_reg_visit_3_new_with_print,empresa,matricula,motivo,destino,nome_1,cartao_1,cc_1,contacto_1,oculos_1,bata_1,sapatos_1,nome_2,cartao_2,cc_2,contacto_2,oculos_2,bata_2,sapatos_2,nome_3,cartao_3,contacto_3,cc_3,oculos_3,bata_3,sapatos_3,username,responsavel,obs,var_lugar)
        id_var=cursor.fetchone()[0]
        
        cursor.commit()
        day=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        day_texto=datetime.today().strftime('%Y-%m')
       
        class PDF(FPDF):
          def header(self):
              self.image('static/content/borgwarner_blue.png',130,10,55,5)
              self.set_font('helvetica','B',12)
              self.cell(80, 5, 'LIVRE TRÂNSITO Nº '+ str(id_var)+ str('-') + str(day_texto), align='L')
              self.ln(7)
              self.set_font('helvetica','B',8)
              self.cell(170, 5, 'VIANA DO CASTELO - PORTUGAL', align='R')
              self.ln(10)

          def footer(self):
                # Go to 1.5 cm from bottom
              self.set_y(-10)
              # Select Arial italic 8
              self.set_font('Arial', 'I', 6)
              # Print centered page number
              self.cell(0, 10, 'Version 1.0 - Facilities - 2023', 0, 0, 'C')

        pdf = PDF(orientation="L", unit="mm", format="A5")
        pdf.add_page()

        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, 'Nome/Name:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.multi_cell(60, 6, str(nome_1) +str(', ')+ str(nome_2)+str(', ')+str(nome_3), border=0)
        pdf.set_font("Helvetica",'B', size = 11)
        pdf.cell(10, 6, str(''), border=0)
        pdf.cell(80, -20, str('Atenção:'), border=0)
        pdf.ln(6)
        pdf.set_font("Helvetica", size = 6)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- Durante a visita deve transportar de forma visível o cartão que lhe foi entregue.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- A visita é restrita aos departamentos especificados.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- É proibido efectuar qualquer registo de som ou imagem. Câmaras ou outros equipamentos de'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('registo de imagem não podem ser utilizadas, excepto em casos devidamente autorizados.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- Informações que lhe forem fornecidas durante a visita têm de ser tratadas confidencialmente.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- À saída terá de devolver este documento devidamente assinado pela pessoa a quem se dirigiu.'), border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(35, 10, 'Empresa/Company:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(65, 10, str(empresa), border=0)
        pdf.set_font("Helvetica",'B', size = 11)
        pdf.cell(80, -10, str('Please Note:'), border=0)
        pdf.ln(6)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(40, -16, 'Nº Telef./Phone Number: ', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(70, -16, str(contacto_1), border=0)
        pdf.ln(2)
        pdf.set_font("Helvetica", size = 6)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- During the visit, the badge given to you by the secuirity is to be worn visibly.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- The visit is restricted to the specified departments.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- Cameras and other visual or sound recording equipment are forbidden unless a'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('specific permission was given to you.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- Information made available to you during the visit are to be treated confidentially.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- When leaving, pleease make sure you return this document, after signature.'), border=0)
        pdf.ln(2)
       
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(45, -36, 'Matrícula/ Registration no. : ', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(55, -36, str(matricula), border=0)
        pdf.set_font("Helvetica",'U', size = 8)
        pdf.ln(1)
        pdf.cell(50, -15, '____________________________________________________', border=0)
        pdf.ln(3)
        pdf.cell(70, -15, 'Assinatura do Visitante/Visitor Signature', border=0)
        pdf.ln(1)
        pdf.set_font("Helvetica", size = 5)
        #pdf.cell(190, -5, '_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _', border=0)
        pdf.ln(3)

        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, str('Vigilante:'), border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(70, 8, str(username), border=0)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(40, 8, str('Anfitrião BW / Host: '), border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(40, 8, str(responsavel), border=0)
        pdf.ln(5)

        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, 'Cartão visitante nº: ', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(80, 8, str(cartao_1)+str(',') + str(cartao_2)+str(',')+str(cartao_3), border=0)
                
        pdf.ln(3)
        
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, 'Data entrada:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(70, 8, str(day), border=0)
        pdf.cell(60, -16, '__________________________________________________', border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'BU', size = 9)
        pdf.cell(60, 10, str('ENTREGA EPI:'), border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(20, 8, 'Calçado:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(10, 8, str(sapatos_1), border=0)
        pdf.cell(70, 1, '')
        pdf.cell(70, 8, '_________________________', border=0)
        pdf.cell(80, 8, '______', border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(20, 8, 'Óculo:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(10, 8, str(oculos_1), border=0)
        pdf.cell(70, 5, '')
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(70, 8, 'Data e Hora / Date and Time', border=0)
        pdf.cell(70, 8, 'Nº WD', border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(20, 8, 'Bata:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(10, 8, str(bata_1), border=0)
        pdf.cell(80, 5, '')
        pdf.ln(5)
                  
        pdf.output(name='imprimir3.pdf',dest='S')
        printer_ip = "10.30.67.21"
        printer_port = 9100          # Replace with the printer's port (usually 9100 for Raw Socket Printing)
        file_path = "imprimir3.pdf"
        send_file_to_ip_printer(printer_ip, printer_port, file_path)

        flash('Registo de entrada feito', category='success')
        return redirect(url_for('status_portaria'))
  except Exception as e:
      flash('Erro no Registo, confirme os valores', category='error')
  return redirect(url_for('status_portaria'))

# até 3 pessoas
@app.route('/add_visit_5',methods=['GET', 'POST'])
def add_visit_5():
  try:
    if request.method == 'POST':
        conn=pyodbc.connect(string_conexao)
        cursor=conn.cursor()
        username=session['username']

        empresa=request.form['var_1']
        matricula=request.form['var_2']
        motivo=request.form['var_3']
        destino=request.form['var_4']

        nome_1=request.form['var_5']
        cartao_1=request.form['var_6']
        contacto_1=request.form['var_7']
        cc_1=request.form['var_8']
        oculos_1=request.form['var_9']
        bata_1=request.form['var_10']
        sapatos_1=request.form['var_11']

        nome_2=request.form['var_12']
        cartao_2=request.form['var_13']
        contacto_2=request.form['var_14']
        cc_2=request.form['var_15']
        oculos_2=request.form['var_16']
        bata_2=request.form['var_17']
        sapatos_2=request.form['var_18']

        nome_3=request.form['var_19']
        cartao_3=request.form['var_20']
        contacto_3=request.form['var_21']
        cc_3=request.form['var_22']
        oculos_3=request.form['var_23']
        bata_3=request.form['var_24']
        sapatos_3=request.form['var_25']

        nome_4=request.form['var_26']
        cartao_4=request.form['var_27']
        contacto_4=request.form['var_28']
        cc_4=request.form['var_29']
        oculos_4=request.form['var_30']
        bata_4=request.form['var_31']
        sapatos_4=request.form['var_32']

        nome_5=request.form['var_33']
        cartao_5=request.form['var_34']
        contacto_5=request.form['var_35']
        cc_5=request.form['var_36']
        oculos_5=request.form['var_37']
        bata_5=request.form['var_38']
        sapatos_5=request.form['var_39']
        responsavel=request.form['var_41']
        obs=request.form['var_40']
        var_lugar=request.form['var_lugar']
        
        create_reg_visit_5_new_with_print = "Exec dbo.create_reg_visit_5_new_with_print @empresa = ?, @matricula = ?,@motivo = ?,@destino = ?,@nome_1 = ?,@cartaobw_1 = ?,@cc_1 = ?,@contacto_1=?,@oculos_1=?,@uniforme_1=?,@sapatos_1=?,@nome_2 = ?,@cartaobw_2 = ?,@cc_2 = ?,@contacto_2=?,@oculos_2=?,@uniforme_2=?,@sapatos_2=?,@nome_3 = ?,@cartaobw_3 = ?,@cc_3 = ?,@contacto_3=?,@oculos_3=?,@uniforme_3=?,@sapatos_3=?,@nome_4 = ?,@cartaobw_4 = ?,@cc_4 = ?,@contacto_4=?,@oculos_4=?,@uniforme_4=?,@sapatos_4=?,@nome_5 = ?,@cartaobw_5 = ?,@cc_5 = ?,@contacto_5=?,@oculos_5=?,@uniforme_5=?,@sapatos_5=?,@username=?,@responsavel=?,@obs=?,@lugar=?"
        cursor.execute(create_reg_visit_5_new_with_print,empresa,matricula,motivo,destino,nome_1,cartao_1,cc_1,contacto_1,oculos_1,bata_1,sapatos_1,nome_2,cartao_2,cc_2,contacto_2,oculos_2,bata_2,sapatos_2,nome_3,cartao_3,cc_3,contacto_3,oculos_3,bata_3,sapatos_3,nome_4,cartao_4,cc_4,contacto_4,oculos_4,bata_4,sapatos_4,nome_5,cartao_5,cc_5,contacto_5,oculos_5,bata_5,sapatos_5,username,responsavel,obs,var_lugar)
        id_var=cursor.fetchone()[0]
        #id_var='8480-2023-12'
        cursor.commit()
        day=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        day_texto=datetime.today().strftime('%Y-%m')
       
        class PDF(FPDF):
          def header(self):
              self.image('static/content/borgwarner_blue.png',130,10,55,5)
              self.set_font('helvetica','B',12)
              self.cell(80, 5, 'LIVRE TRÂNSITO Nº '+ str(id_var)+ str('-') + str(day_texto), align='L')
              self.ln(7)
              self.set_font('helvetica','B',8)
              self.cell(170, 5, 'VIANA DO CASTELO - PORTUGAL', align='R')
              self.ln(10)

          def footer(self):
                # Go to 1.5 cm from bottom
              self.set_y(-10)
              # Select Arial italic 8
              self.set_font('Arial', 'I', 6)
              # Print centered page number
              self.cell(0, 10, 'Version 1.0 - Facilities - 2023', 0, 0, 'C')

        pdf = PDF(orientation="L", unit="mm", format="A5")
        pdf.add_page()

        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, 'Nome/Name:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.multi_cell(60, 6, str(nome_1) +str(', ')+ str(nome_2)+str(', ')+str(nome_3)+str(', ')+str(nome_4)+str(', ')+str(nome_5), border=0)
        pdf.set_font("Helvetica",'B', size = 11)
        pdf.cell(10, 6, str(''), border=0)
        pdf.cell(80, -20, str('Atenção:'), border=0)
        pdf.ln(6)
        pdf.set_font("Helvetica", size = 6)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- Durante a visita deve transportar de forma visível o cartão que lhe foi entregue.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- A visita é restrita aos departamentos especificados.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- É proibido efectuar qualquer registo de som ou imagem. Câmaras ou outros equipamentos de'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('registo de imagem não podem ser utilizadas, excepto em casos devidamente autorizados.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- Informações que lhe forem fornecidas durante a visita têm de ser tratadas confidencialmente.'), border=0)
        pdf.ln(2)
        pdf.cell(100, 5, str(''), border=0)
        pdf.cell(80, -20, str('- À saída terá de devolver este documento devidamente assinado pela pessoa a quem se dirigiu.'), border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(35, 10, 'Empresa/Company:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(65, 10, str(empresa), border=0)
        pdf.set_font("Helvetica",'B', size = 11)
        pdf.cell(80, -10, str('Please Note:'), border=0)
        pdf.ln(6)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(40, -16, 'Nº Telef./Phone Number: ', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(70, -16, str(contacto_1), border=0)
        pdf.ln(2)
        pdf.set_font("Helvetica", size = 6)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- During the visit, the badge given to you by the secuirity is to be worn visibly.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- The visit is restricted to the specified departments.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- Cameras and other visual or sound recording equipment are forbidden unless a'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('specific permission was given to you.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- Information made available to you during the visit are to be treated confidentially.'), border=0)
        pdf.ln(2)
        pdf.cell(100, -15, str(''), border=0)
        pdf.cell(80, -15, str('- When leaving, pleease make sure you return this document, after signature.'), border=0)
        pdf.ln(2)
       
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(45, -36, 'Matrícula/ Registration no. : ', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(55, -36, str(matricula), border=0)
        pdf.set_font("Helvetica",'U', size = 8)
        pdf.ln(1)
        pdf.cell(50, -15, '____________________________________________________', border=0)
        pdf.ln(3)
        pdf.cell(70, -15, 'Assinatura do Visitante/Visitor Signature', border=0)
        pdf.ln(1)
        pdf.set_font("Helvetica", size = 5)
        #pdf.cell(190, -5, '_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _', border=0)
        pdf.ln(3)

        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, str('Vigilante:'), border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(70, 8, str(username), border=0)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(40, 8, str('Anfitrião BW / Host: '), border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(40, 8, str(responsavel), border=0)
        pdf.ln(5)

        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, 'Cartão visitante nº: ', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(80, 8, str(cartao_1)+str(',') + str(cartao_2)+str(',')+str(cartao_3)+str(',')+str(cartao_4)+str(',') + str(cartao_5), border=0)
                
        pdf.ln(3)
        
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(30, 8, 'Data entrada:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(70, 8, str(day), border=0)
        pdf.cell(60, -16, '__________________________________________________', border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'BU', size = 9)
        pdf.cell(60, 10, str('ENTREGA EPI:'), border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(20, 8, 'Calçado:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(10, 8, str(sapatos_1), border=0)
        pdf.cell(70, 1, '')
        pdf.cell(70, 8, '_________________________', border=0)
        pdf.cell(80, 8, '______', border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(20, 8, 'Óculo:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(10, 8, str(oculos_1), border=0)
        pdf.cell(70, 5, '')
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(70, 8, 'Data e Hora / Date and Time', border=0)
        pdf.cell(70, 8, 'Nº WD', border=0)
        pdf.ln(5)
        pdf.set_font("Helvetica",'B', size = 9)
        pdf.cell(20, 8, 'Bata:', border=0)
        pdf.set_font("Helvetica", size = 8)
        pdf.cell(10, 8, str(bata_1), border=0)
        pdf.cell(80, 5, '')
        pdf.ln(5)
                  
        pdf.output(name='imprimir5.pdf',dest='S')
        printer_ip = "10.30.67.21" 
        printer_port = 9100          # Replace with the printer's port (usually 9100 for Raw Socket Printing)
        file_path = "imprimir5.pdf"
        send_file_to_ip_printer(printer_ip, printer_port, file_path)

        flash('Registo de entrada feito', category='success')
        return redirect(url_for('status_portaria'))
  except Exception as e:
        flash('Erro no Registo, confirme os valores', category='error')
  return redirect(url_for('status_portaria'))

#download pdf by id visit
@app.route('/download_pdf_visit/<id>',methods=['GET', 'POST'])
def download_pdf_visit(id):

  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  SP_all_reg_visit = "Exec dbo.[all_reg_visit] @id = ?"
  cursor.execute(SP_all_reg_visit,id)
  all_reg_visit = cursor.fetchall()

  id_var=all_reg_visit[0][0]
  nome=all_reg_visit[0][3]
  identificacao=all_reg_visit[0][4]
  empresa=all_reg_visit[0][5]
  contato=all_reg_visit[0][6]
  matricula=all_reg_visit[0][7]
  cartaobw=all_reg_visit[0][8]
  oculos=all_reg_visit[0][9]
  uniforme=all_reg_visit[0][10]
  sapatos=all_reg_visit[0][11]
  username=all_reg_visit[0][14]
  bw_responsable=all_reg_visit[0][17]

  day=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
  day_texto=datetime.today().strftime('%Y-%m')
  class PDF(FPDF):
        def header(self):
            self.image('static/content/borgwarner_blue.png',130,10,55,5)
            self.set_font('helvetica','B',12)
            self.cell(80, 5, 'LIVRE TRÂNSITO Nº '+ str(id_var)+ str('-') + str(day_texto), align='L')
            self.ln(7)
            self.set_font('helvetica','B',8)
            self.cell(170, 5, 'VIANA DO CASTELO - PORTUGAL', align='R')
            self.ln(10)

        def footer(self):
              # Go to 1.5 cm from bottom
            self.set_y(-10)
            # Select Arial italic 8
            self.set_font('Arial', 'I', 6)
            # Print centered page number
            self.cell(0, 10, 'Version 1.0 - Facilities - 2023', 0, 0, 'C')

  pdf = PDF(orientation="L", unit="mm", format="A5")
  pdf.add_page()
  pdf.set_font("Helvetica",'B', size = 9)
  pdf.cell(30, 8, 'Nome/Name:', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(80, 8, str(nome), border=0)
  pdf.set_font("Helvetica",'B', size = 11)
  pdf.cell(80, 8, str('Atenção:'), border=0)
  pdf.ln(6)
  pdf.set_font("Helvetica",'B', size = 9)
  pdf.cell(30, 8, 'C.C/ Id. Card:', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(80, 8, str(identificacao), border=0)
  pdf.set_font("Helvetica", size = 5)
  pdf.multi_cell(80, 3, str('- Durante a visita deve transportar de forma visível o cartão que lhe foi entregue.\n - A visita é restrita aos departamentos especificados.\n - É proibido efectuar qualquer registo de som ou imagem. Câmaras ou outros equipamentos de registo de imagem não podem ser utilizadas, excepto em casos devidamente autorizados.\n - Informações que lhe forem fornecidas durante a visita têm de ser tratadas confidencialmente. \n - À saída terá de devolver este documento devidamente assinado pela pessoa a quem se dirigiu.'), border=0)

  pdf.ln(2)
  pdf.set_font("Helvetica",'B', size = 9)
  pdf.cell(35, -10, 'Empresa/Company:', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(75, -10, str(empresa), border=0)
  pdf.set_font("Helvetica",'B', size = 11)
  pdf.cell(80, 8, str('Please Note:'), border=0)
  pdf.ln(6)
  pdf.set_font("Helvetica",'B', size = 9)
  pdf.cell(40, -10, 'Nº Telef./Phone Number: ', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(70, -10, str(contato), border=0)
  pdf.set_font("Helvetica", size = 5)
  pdf.multi_cell(70, 3, str('- During the visit, the badge given to you by the secuirity is to be worn visibly.\n - The visit is restricted to the specified departments.\n - Cameras and other visual or sound recording equipment are forbidden unless a specific permission was given to you.\n - Information made available to you during the visit are to be treated confidentially.\n - When leaving, pleease make sure you return this document, after signature.'), border=0)

  pdf.ln(2)
  pdf.set_font("Helvetica",'B', size = 9)
  pdf.cell(45, -30, 'Matrícula/ Registration no. : ', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(55, -30, str(matricula), border=0)

  pdf.set_font("Helvetica",'U', size = 8)
  pdf.ln(1)
  pdf.cell(50, -15, '____________________________________________________', border=0)
  pdf.ln(3)
  pdf.cell(70, -15, 'Assinatura do Visitante/Visitor Signature', border=0)
  pdf.ln(1)
  pdf.set_font("Helvetica", size = 5)
  pdf.cell(190, -5, '_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _', border=0)
  pdf.ln(1)

  pdf.set_font("Helvetica",'B', size = 9)
  pdf.cell(30, 8, str('Segurança:'), border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(80, 8, str(username), border=0)
  pdf.set_font("Helvetica",'B', size = 9)
  pdf.cell(100, 8, str('Anfitrião BW / Host:'), border=0)
  pdf.ln(5)

  pdf.set_font("Helvetica",'B', size = 8)
  pdf.cell(30, 8, 'Cartão visitante nº: ', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(80, 8, str(cartaobw), border=0)
  pdf.cell(100, 8, str(bw_responsable), border=0)
  pdf.ln(5)
  pdf.set_font("Helvetica",'B', size = 8)
  pdf.cell(30, 8, 'Data entrada:', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(80, 8, str(day), border=0)
  pdf.cell(80, 8, '____________________________________________________', border=0)
  pdf.ln(5)
  pdf.set_font("Helvetica",'BU', size = 10)
  pdf.cell(60, 10, str('ENTREGA EPI:'), border=0)
  pdf.ln(6)
  pdf.set_font("Helvetica",'B', size = 8)
  pdf.cell(20, 8, 'Calçado:', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(10, 8, str(sapatos), border=0)
  pdf.cell(80, 5, '')
  pdf.cell(70, 8, '_______________________', border=0)
  pdf.cell(80, 8, '______', border=0)
  pdf.ln(5)
  pdf.set_font("Helvetica",'B', size = 8)
  pdf.cell(20, 8, 'Óculo:', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(10, 8, str(oculos), border=0)
  pdf.cell(80, 5, '')
  pdf.set_font("Helvetica",'B', size = 8)
  pdf.cell(70, 5, 'Data e Hora / Date and Time', border=0)
  pdf.cell(80, 5, 'Nº WD', border=0)
  pdf.ln(5)
  pdf.set_font("Helvetica",'B', size = 8)
  pdf.cell(20, 8, 'Bata:', border=0)
  pdf.set_font("Helvetica", size = 8)
  pdf.cell(10, 8, str(uniforme), border=0)
  pdf.cell(80, 5, '')
  pdf.ln(5)
  return Response (bytes(pdf.output(dest='S')), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=LivreTransitoNº '+str(id_var)+ str('-') + str(day_texto)+'.pdf'})


@app.route('/download_pdf_req_standard/<id>',methods=['GET', 'POST'])
def download_pdf_req_standard(id):

  conn=pyodbc.connect(string_conexao)
  cursor=conn.cursor()
  SP_all_standard_req = "Exec dbo.[AllStandardRequisitionsById] @id = ?"
  cursor.execute(SP_all_standard_req,id)
  all_standard_req = cursor.fetchall()

  day=datetime.today().strftime('%Y-%m-%d %H:%M:%S')
  year=datetime.today().strftime('%Y')
  day_texto=datetime.today().strftime('%Y-%m')
  
  class PDF(FPDF):
        def header(self):
            self.image('static/content/borgwarner_blue.png',150,10,55,5)
            self.set_font('helvetica','B',16)
            self.cell(80, 5, 'Standard Requisition ', align='L')
            self.ln(10)
            self.set_font('helvetica','B',16)
            self.cell(200, 5, 'VIANA DO CASTELO - PORTUGAL', align='R')
            self.ln(20)

        def footer(self):
              # Go to 1.5 cm from bottom
            self.set_y(-10)
            # Select Arial italic 8
            self.set_font('Arial', 'I', 8)
            # Print centered page number
            self.cell(0, 10, 'Version 1.0 - Digital Transformation - Transport - Warehouse - '+str(year), 0, 0, 'C')

  pdf = PDF(orientation="L", unit="mm", format="A5")
  pdf.add_page()
  pdf.set_font("Helvetica",'B', size = 30)
  pdf.cell(75, 8, str('Internal Code: '), border=0)
  pdf.set_font("Helvetica", size = 30)
  pdf.cell(90, 8, str(all_standard_req[0][1]), border=0)
  pdf.ln(20)
  pdf.set_font("Helvetica",'B', size = 30)
  pdf.cell(30, 8, 'Date: ', border=0)
  pdf.set_font("Helvetica", size = 30)
  pdf.cell(120, 8, str(all_standard_req[0][2]), border=0)
  pdf.ln(20)
  
  pdf.set_font("Helvetica",'B', size = 30)
  pdf.cell(60, 8, str('Requester: ') , border=0)
  pdf.set_font("Helvetica", size = 30)
  pdf.cell(90, 8, str(all_standard_req[0][3]), border=0)
  pdf.ln(20)
  pdf.set_font("Helvetica",'B', size = 16)
  pdf.cell(50, 8, str('Pick Up Contact: '), border=0)
  pdf.set_font("Helvetica", size = 16)
  pdf.cell(90, 8, str(all_standard_req[0][10])+ str(' - ')+str(all_standard_req[0][12]), border=0)
  pdf.ln(20)
  pdf.set_font("Helvetica",'B', size = 16)
  pdf.cell(50, 8, str('Delivery Contact: '), border=0)
  pdf.set_font("Helvetica", size = 16)
  pdf.cell(90, 8, str(all_standard_req[0][19]) + str(' - ')+str(all_standard_req[0][21]), border=0)
  pdf.ln(20)

  return Response (bytes(pdf.output(dest='S')), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=Standard Requisition Nº '+ str(all_standard_req[0][1])+' .pdf'})

@app.route('/get_info', methods=['GET'])
def get_info():
    id = request.args.get('id')
    
    cursor=conn.cursor()
    cursor = conn.cursor()
    cursor.execute("SELECT [Reference],[PalletQty],[PalletLenght],[PalletWidth],[PalletHeight],[TotalWeight],[Stackable],[Imputable],[SupplierClient],[ProdLine],[TotalVolume] FROM [StandardTransportRequestReference]  where idRequest = ?",(id))
    data = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]

    # Convertendo os resultados para uma lista de dicionários
    result_list = []
    for row in data:
        result_dict = dict(zip(column_names, row))
        result_list.append(result_dict)
        
    return jsonify(result_list)
    
@app.route('/add_epis',methods=['GET', 'POST'])
def add_epis():
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']

      nome=request.form['var_1']
      identificacao=request.form['var_2']
      cartaobw=request.form['var_3']
      oculos=request.form['var_4']
      uniforme=request.form['var_5']
      sapatos=request.form['var_6']
      cartao_id=request.form['var_7']

      Store_procedure_create_reg_epis = "Exec dbo.create_reg_epis @nome = ? , @identificacao = ?,@cartaobw = ?,@oculos=?,@uniforme=?,@sapatos=?,@username=?,@cartao_id=?"
      cursor.execute(Store_procedure_create_reg_epis,nome,identificacao,cartaobw,oculos,uniforme,sapatos,username,cartao_id)
      cursor.commit()
      flash('Registo de entrada feito', category='success')
      return redirect(url_for('status_epis'))
 

@app.route('/registar_saida/<int:id>',methods=['GET', 'POST'])
def registar_saida(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      
      observacao_saida=request.form['var_7']
      pausa_almoco=request.form['var_8']
      username=session['username']

      #Store_procedure_create_reg_saida = "Exec dbo.create_reg_saida @id = ?,@obs_saida = ?,@username=?"
      Store_procedure_create_reg_saida = "Exec dbo.create_reg_saida @id = ?,@obs_saida = ?,@username=?,@PausaAlmoco=?"
      cursor.execute(Store_procedure_create_reg_saida,id_var,observacao_saida,username,pausa_almoco)
      cursor.commit()
      flash('Registo de entrada feito', category='success')
      return redirect(url_for('status_portaria'))

@app.route('/registar_saida_2/<int:id>',methods=['GET', 'POST'])
def registar_saida_2(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      username=session['username']
      #Store_procedure_create_reg_saida_2 = "Exec dbo.create_reg_saida_2 @id = ?,@username=?"
      Store_procedure_create_reg_saida_2 = "Exec dbo.create_reg_saida_2_new @id = ?,@username=?"
      cursor.execute(Store_procedure_create_reg_saida_2,id_var,username)
      cursor.commit()
      flash('Registo de entrada feito', category='success')
      return redirect(url_for('status_portaria'))


#REGISTO SAIDA CARGAS/DESCARAS PORTARIA
@app.route('/registo_saida_portaria/<int:id>',methods=['GET', 'POST'])
def registo_saida_portaria(id):

    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    id_var=id
      
    username=session['username']

    Store_procedure_registo_saida_portaria_cargas_descargas = "Exec dbo.registo_saida_portaria_cargas_descargas @id = ?,@username=?"
    cursor.execute(Store_procedure_registo_saida_portaria_cargas_descargas,id_var,username)
    cursor.commit()
    flash('Registo de entrada feito', category='success')
    return redirect(url_for('status_cargas_descargas'))

@app.route('/validar_entrada/<int:id>',methods=['GET', 'POST'])
def validar_entrada(id):
  
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    id_var=id
    estado_var=1
    username=session['username']

    Store_procedure_validar_entrada = "Exec dbo.validar_entrada @id = ?,@estado_var = ?,@username=?"
    cursor.execute(Store_procedure_validar_entrada,id_var,estado_var,username)
    cursor.commit()
    flash('Validação concluída com sucesso!', category='success')
    return redirect(url_for('status_cargas_descargas'))

@app.route('/registar_saida_epi/<int:id>',methods=['GET', 'POST'])
def registar_saida_epi(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      
      observacao_saida_epi=request.form['var_3']
      username=session['username']

      Store_procedure_create_reg_saida_epi = "Exec dbo.create_reg_saida_epi @id = ?,@obs_saida = ?,@username=?"
      cursor.execute(Store_procedure_create_reg_saida_epi,id_var,observacao_saida_epi,username)
      cursor.commit()
      flash('Registo de saída feito!', category='success')
      return redirect(url_for('status_epis'))

##### Pre regito Cargas (Dentro da PORTARIA)
@app.route('/status_cargas_descargas',methods=['GET', 'POST'])
def status_cargas_descargas():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    all_cargas_descargas = "Exec dbo.[all_cargas_descargas]"
    cursor.execute(all_cargas_descargas)
    all_cargas_descargas_data = cursor.fetchall()
    return render_template('status_cargas_descargas.html',all_cargas_descargas_data=all_cargas_descargas_data)
  except Exception as e:
        flash('Erro de credenciais', category='error')
  return redirect(url_for('index'))

@app.route('/update_registo_vigilantes/<int:id>',methods=['GET', 'POST'])
def update_registo_vigilantes(id):
  try:
    username=session['username']
    if request.method == 'POST':
      id_var=id
      motorista=request.form['var_3']
      identificacao=request.form['var_4']
      contato=request.form['var_5']
      empresa=request.form['var_6']
      matricula=request.form['var_7']
      matricula_reboque=request.form['var_8']
      tipo=request.form['var_9']

      cliente=request.form['var_10']
      codigo_carga=request.form['var_11']
      notas_vigilante=request.form['var_12']
      
      cursor=conn.cursor()
      Store_procedure_alterar_registo_vigilantes = "Exec dbo.alterar_registo_vigilantes @id = ?,@username = ?,@motorista=?,@identificacao=?,@contato=?,@empresa=?,@matricula=?,@matricula_reboque=?,@tipo=?,@cliente=?,@codigo_carga=?,@notas_vigilante=?"
      cursor.execute(Store_procedure_alterar_registo_vigilantes,id_var,username,motorista,identificacao,contato,empresa,matricula,matricula_reboque,tipo,cliente,codigo_carga,notas_vigilante)
      cursor.commit()
      flash('Registo alterado com sucesso!', category='success')
      
      return redirect(url_for('status_cargas_descargas'))
  except Exception as e:
        flash('Erro ao alterar o registo', category='error')
  return redirect(url_for('index'))

@app.route('/notificar_armazem_tempo_espera/<int:id>',methods=['GET', 'POST'])
def notificar_armazem_tempo_espera(id):
  try:
    username=session['username']
    flash('Registo alterado com sucesso!', category='success')
      
    return redirect(url_for('status_cargas_descargas'))
  except Exception as e:
        flash('Erro ao alterar o registo', category='error')
  return redirect(url_for('index'))

@app.route('/add_carga_descarga',methods=['GET', 'POST'])
def add_carga_descarga():
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']

      nome=request.form['var_1']
      identificacao=request.form['var_2']
      empresa=request.form['var_3']
      contato=request.form['var_4']
      
      matricula=request.form['var_5']
      matricula_reboque=request.form['var_6']

      tipo_veiculo=request.form['var_7']

      epi=request.form['var_8']

      tipo_carga=request.form['var_9']

      

      destino=request.form['var_10']
      cliente=request.form['var_11']
      codigo_carga=request.form['var_12']
      notas_vigilante=request.form['var_13']
      Store_procedure_create_carga_descarga = "Exec dbo.create_carga_descarga @nome_motorista = ? , @identificacao = ?,@contato = ?,@empresa = ?, @matricula = ? , @epi = ?,@owner_registo_entrada_portaria = ?, @tipo=?,@destino=?,@cliente=?,@codigo_carga=?,@tipo_veiculo=?,@matricula_reboque=?,@notas_vigilante=?"
      cursor.execute(Store_procedure_create_carga_descarga,nome,identificacao,contato,empresa,matricula,epi,username,tipo_carga,destino,cliente,codigo_carga,tipo_veiculo,matricula_reboque,notas_vigilante)
      cursor.commit()
      
      flash('Registo de entrada feito com sucesso', category='sucess')
      return redirect(url_for('status_cargas_descargas'))


#anular registo portaria
@app.route('/anular_regito_portaria/<int:id>',methods=['GET', 'POST'])
def anular_regito_portaria(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      
      motivo=request.form['var_1']
      username=session['username']
      
      Store_procedure_anular_registo_portaria = "Exec dbo.anular_registo_portaria @id = ?,@motivo = ?,@username=?"
      cursor.execute(Store_procedure_anular_registo_portaria,id_var,motivo,username)
      cursor.commit()
      flash('Registo anulado feito!', category='success')
      
      return redirect(url_for('status_cargas_descargas'))


#anular registo armazem
@app.route('/anular_regito_armazem/<int:id>',methods=['GET', 'POST'])
def anular_regito_armazem(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      
      motivo=request.form['var_1']
      username=session['username']

      Store_procedure_anular_registo_armazem = "Exec dbo.anular_registo_armazem @id = ?,@motivo = ?,@username=?"
      cursor.execute(Store_procedure_anular_registo_armazem,id_var,motivo,username)
      cursor.commit()
      flash('Registo anulado feito!', category='success')
      
      return redirect(url_for('status_armazem'))

@app.route('/registo_tempo_espera_armazem/<int:id>',methods=['GET', 'POST'])
def registo_tempo_espera_armazem(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      
      tempo=request.form['var_1']
      username=session['username']
      

      Store_procedure_registo_tempo_espera_armazem = "Exec dbo.registo_tempo_espera_armazem @id = ?,@tempo = ?,@username=?"
      cursor.execute(Store_procedure_registo_tempo_espera_armazem,id_var,tempo,username)
      cursor.commit()
      flash('Registo feito com sucesso!', category='success')
      
      return redirect(url_for('status_armazem'))

########################################################################################################################################################################
#
#
#STATUS CARTOES
#
#
@app.route('/status_chaves',methods=['GET', 'POST'])
def status_chaves():
  try:
    username=session['username']
    data_atual = date.today()
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    SP_GetRegistoChaves = "Exec dbo.[GetRegistoChaves]"
    cursor.execute(SP_GetRegistoChaves)
    SP_GetRegistoChaves = cursor.fetchall()

    SP_GetRegistoChavesDepartamentos = "Exec dbo.[GetRegistoChavesDepartamentos]"
    cursor.execute(SP_GetRegistoChavesDepartamentos)
    SP_get_departamentos = cursor.fetchall()

    SP_GetRegistoChavesMotivos = "Exec dbo.[GetRegistoChavesMotivos]"
    cursor.execute(SP_GetRegistoChavesMotivos)
    SP_get_motivos = cursor.fetchall()

    SP_GetRegistoChavesTipochaveiro = "Exec dbo.[GetRegistoChavesTipoChaveiro]"
    cursor.execute(SP_GetRegistoChavesTipochaveiro)
    SP_get_tipo_chaveiro = cursor.fetchall()

    SP_GetRegistoChavesChaveiroPrincipal = "Exec dbo.[GetRegistoChavesChaveiroPrincipal]"
    cursor.execute(SP_GetRegistoChavesChaveiroPrincipal)
    chaves_principal = cursor.fetchall()

    return render_template('/portaria/status_chaves.html',chaves_principal=chaves_principal,data_atual=data_atual,SP_GetRegistoChaves=SP_GetRegistoChaves,SP_get_departamentos=SP_get_departamentos,SP_get_motivos=SP_get_motivos,SP_get_tipo_chaveiro=SP_get_tipo_chaveiro)
  except Exception as e:
        flash('Erro de Login', category='error')
  return redirect(url_for('index'))

@app.route('/registar_entrega_chave/<int:id>',methods=['GET', 'POST'])
def registar_entrega_chave(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      
      observacao_entrega=request.form['var_3']
      username=session['username']
      Store_procedure_registo_chaves_entrega = "Exec dbo.[RegistoChavesRegistoEntrega] @id = ?,@username= ?,@obs=?"
      cursor.execute(Store_procedure_registo_chaves_entrega,id_var,username,observacao_entrega)
      cursor.commit()
      flash('Registo de entrega feito com sucesso.', category='success')
      return redirect(url_for('status_chaves'))


@app.route('/add_key_reg',methods=['GET', 'POST'])
def add_key_reg():
  try:
    if request.method == 'POST':
        username=session['username']
        var_1=request.form['var_1']
        var_2=request.form['var_2']
        var_3=request.form['var_3']
        var_5=request.form['var_5']
        var_6=request.form['var_6']
        var_10=request.form['var_10']
        var_4=request.form.getlist('var_4[]')
        var_7=request.form.getlist('var_7[]')
        var_8=request.form.getlist('var_8[]')
        var_9=request.form.getlist('var_9[]')
        var_11=request.form.getlist('var_11[]')
        for index, row in enumerate(var_4):
          cursor=conn.cursor()
          Store_procedure = "Exec dbo.[AdicionarRegistochaves]  @username = ?,@Requisitante=?,@NumeroBW=?,@Empresa=?,@TipoChaveiro=?,@Autorizacao=?,@Departamento=?,@Motivo=?,@Chave=?,@EntregaEstimada=?,@Observacoes=?,@Permanente=?"
          cursor.execute(Store_procedure,username,var_1,var_2,var_3,var_4[index],var_5,var_6,var_7[index],var_8[index],var_9[index],var_10,var_11[index])
          cursor.commit()
        flash('Valores inseridos com sucesso.', category='success')
        return redirect(url_for('status_chaves'))
    else:
      flash('erro a inserir os valores.', category='error')
      return redirect(url_for('status_chaves'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/edit_key_reg/<int:id>',methods=['GET', 'POST'])
def edit_key_reg(id):
  try:
    if request.method == 'POST':
        username=session['username']
        var_1=request.form['var_1']
        var_2=request.form['var_2']
        var_3=request.form['var_3']
        var_6=request.form['var_6']
        var_5=request.form['var_5']
        var_7=request.form['var_7']
        var_9=request.form['var_9']
        var_11=request.form['var_11']
        var_4=request.form['var_42']
        var_8=request.form['var_82']
        cursor=conn.cursor()
        Store_procedure = "Exec dbo.[EditarRegistochaves]  @id=? ,@Requisitante=?,@NumeroBW=?,@Empresa=?,@Departamento=?,@Autorizacao=?,@TipoChaveiro=?,@Chave=?,@Permanente=?,@Motivo=?,@EntregaEstimada=?"
        cursor.execute(Store_procedure,id,var_1,var_2,var_3,var_6,var_5,var_4,var_8,var_11,var_7,var_9)
        cursor.commit()
        flash('Valores editados com sucesso.', category='success')
        return redirect(url_for('status_chaves'))
    else:
      flash('erro a editar os valores.', category='error')
      return redirect(url_for('status_chaves'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))



@app.route('/get_key_from_keychain/<string:chaveiro>',methods=['GET','POST'])
def get_key_from_keychain(chaveiro):
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    sp_GetRegistoChavesChaveiro = "Exec dbo.GetRegistoChavesChaveiro @chaveiro= ?"
    cursor.execute(sp_GetRegistoChavesChaveiro,chaveiro)
    rows = cursor.fetchall()
    content = []
    for row in rows:
        id = row[0]
        posicao = row[1]
        data = {'id': id,'posicao': posicao}
        content.append(data)    
    return jsonify(content)


@app.route('/delete_key_reg/<int:id>', methods=['POST', 'GET'])
def delete_key_reg(id):
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_delete_key_reg = "Exec dbo.RegistoChaveseliminarRegisto @id = ?"
    cursor.execute(storeproc_delete_key_reg,id)
    conn.commit()
    flash('Registo eliminado com sucesso.', category='success')
    return redirect(url_for('status_chaves'))

#Historicos Chaveiro
@app.route('/history_last_7_days_chaveiro',methods=['GET', 'POST'])
def history_last_7_days_chaveiro():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    sp_RegistoChavesUltimosSeteDias = "Exec dbo.[RegistoChavesUltimosSeteDias]"
    cursor.execute(sp_RegistoChavesUltimosSeteDias)
    all_key_regs = cursor.fetchall()
    return render_template('/portaria/history_last_7_days_chaveiro.html',all_key_regs=all_key_regs)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/history_by_date_portaria_chaveiro',methods=['GET', 'POST'])
def history_by_date_portaria_chaveiro():
  try:
    username=session['username']
    data_inicial=''
    data_final=''
    data_atual = date.today()
    all_key_regs=''
    if request.method == 'POST':
      data_inicial=request.form['dataini']
      data_final=request.form['datafim']
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      storeproc = "Exec dbo.RegistoChavesPorData  @desde = ?, @ate = ?"
      cursor.execute(storeproc,data_inicial,data_final)
      all_key_regs = cursor.fetchall()
      return render_template('/portaria/history_by_date_portaria_chaveiro.html',all_key_regs=all_key_regs,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
    return render_template('/portaria/history_by_date_portaria_chaveiro.html',all_key_regs=all_key_regs,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


########################################################################################################################################################################
#CARGAS E DESCARGAS (ARMAZEM)
########################################################################################################################################################################

@app.route('/status_armazem',methods=['GET', 'POST'])
def status_armazem():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    all_cargas_descargas_status_armazem = "Exec dbo.[all_cargas_descargas_status_armazem]"
    cursor.execute(all_cargas_descargas_status_armazem)
    all_cargas_descargas_data = cursor.fetchall()

    estado_cais = "Exec dbo.[estado_cais]"
    cursor.execute(estado_cais)
    estado_cais_data = cursor.fetchall()

    standard_transports_request = "Exec dbo.[StandardTransportRequestsStatusArmazem]"
    cursor.execute(standard_transports_request)
    standard_transports_request_data = cursor.fetchall()

    
    return render_template('/armazem/status_armazem.html',standard_transports_request_data=standard_transports_request_data,all_cargas_descargas_data=all_cargas_descargas_data,estado_cais_data=estado_cais_data)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/new_status_armazem',methods=['GET', 'POST'])
def new_status_armazem():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    all_cargas_descargas_status_armazem = "Exec dbo.[all_cargas_descargas_status_armazem]"
    cursor.execute(all_cargas_descargas_status_armazem)
    all_cargas_descargas_data = cursor.fetchall()

    estado_cais = "Exec dbo.[estado_cais]"
    cursor.execute(estado_cais)
    estado_cais_data = cursor.fetchall()

    standard_transports_request = "Exec dbo.[StandardTransportRequestStatusArmazem]"
    cursor.execute(standard_transports_request)
    standard_transports_request_data = cursor.fetchall()
    
    return render_template('/armazem/new_status_armazem.html',standard_transports_request_data=standard_transports_request_data,all_cargas_descargas_data=all_cargas_descargas_data,estado_cais_data=estado_cais_data)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/registo_armazem',methods=['GET', 'POST'])
def registo_armazem():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    all_cargas_descargas_registo_armazem = "Exec dbo.[all_cargas_descargas_registo_armazem]"
    cursor.execute(all_cargas_descargas_registo_armazem)
    all_cargas_descargas_data = cursor.fetchall()
    return render_template('/armazem/registo_armazem.html',all_cargas_descargas_data=all_cargas_descargas_data)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


#historicos de cargas e descargas
@app.route('/last_7_days_armazem',methods=['GET', 'POST'])
def last_7_days_armazem():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    all_cargas_descargas_registo_armazem = "Exec dbo.[all_cargas_descargas_last_7_days]"
    cursor.execute(all_cargas_descargas_registo_armazem)
    all_cargas_descargas_data = cursor.fetchall()
    return render_template('/armazem/last_7_days_armazem.html',all_cargas_descargas_data=all_cargas_descargas_data)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/history_by_date_armazem',methods=['GET', 'POST'])
def history_by_date_armazem():
  try:
    username=session['username']
    data_inicial=''
    data_final=''
    data_atual = date.today()
    all_cargas_descargas_data=''
    if request.method == 'POST':
      data_inicial=request.form['dataini']
      data_final=request.form['datafim']
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      storeproc = "Exec dbo.all_cargas_descargas_by_date  @desde = ?, @ate = ?"
      cursor.execute(storeproc,data_inicial,data_final)
      all_cargas_descargas_data = cursor.fetchall()
      return render_template('/armazem/history_by_date_armazem.html',all_cargas_descargas_data=all_cargas_descargas_data,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
    return render_template('/armazem/history_by_date_armazem.html',all_cargas_descargas_data=all_cargas_descargas_data,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/last_7_days_portaria',methods=['GET', 'POST'])
def last_7_days_portaria():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    all_cargas_descargas_registo_armazem = "Exec dbo.[all_cargas_descargas_last_7_days]"
    cursor.execute(all_cargas_descargas_registo_armazem)
    all_cargas_descargas_data = cursor.fetchall()
    return render_template('/portaria/last_7_days_portaria.html',all_cargas_descargas_data=all_cargas_descargas_data)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/history_by_date_portaria',methods=['GET', 'POST'])
def history_by_date_portaria():
  try:
    username=session['username']
    data_inicial=''
    data_final=''
    data_atual = date.today()
    all_cargas_descargas_data=''
    if request.method == 'POST':
      data_inicial=request.form['dataini']
      data_final=request.form['datafim']
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      storeproc = "Exec dbo.all_cargas_descargas_by_date  @desde = ?, @ate = ?"
      cursor.execute(storeproc,data_inicial,data_final)
      all_cargas_descargas_data = cursor.fetchall()
      return render_template('/portaria/history_by_date_portaria.html',all_cargas_descargas_data=all_cargas_descargas_data,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
    return render_template('/portaria/history_by_date_portaria.html',all_cargas_descargas_data=all_cargas_descargas_data,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))
#----
#historicos de controlo acesso
@app.route('/history_by_date_portaria_req_visitas',methods=['GET', 'POST'])
def history_by_date_portaria_req_visitas():
  try:
    username=session['username']
    data_inicial=''
    data_final=''
    all_cargas_descargas_data=''
    if request.method == 'POST':
      data_inicial=request.form['dataini']
      data_final=request.form['datafim']
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      storeproc = "Exec dbo.all_control_acesso_by_date  @desde = ?, @ate = ?"
      cursor.execute(storeproc,data_inicial,data_final)
      all_cargas_descargas_data = cursor.fetchall()
      return render_template('/portaria/history_by_date_portaria_visitas.html',all_cargas_descargas_data=all_cargas_descargas_data,data_inicial=data_inicial,data_final=data_final)
    return render_template('/portaria/history_by_date_portaria_visitas.html',all_cargas_descargas_data=all_cargas_descargas_data,data_inicial=data_inicial,data_final=data_final)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/history_last_7_days_portaria_visitas',methods=['GET', 'POST'])
def history_last_7_days_portaria_visitas():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    all_cargas_descargas_registo_armazem = "Exec dbo.[all_control_acesso_last_7_days]"
    cursor.execute(all_cargas_descargas_registo_armazem)
    all_cargas_descargas_data = cursor.fetchall()
    return render_template('/portaria/history_last_7_days_portaria_visitas.html',all_cargas_descargas_data=all_cargas_descargas_data)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))



@app.route('/edit_transports_standard_req/<int:id>',methods=['GET', 'POST'])
def edit_transports_standard_req(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']
      ref_1=request.form['var_1']
      ref_2=request.form['var_2']
      ref_3=request.form['var_3']
      ref_4=request.form['var_4']
      ref_5=request.form['var_5']
      imputable=request.form['var_6']
      supplier_client=request.form['var_7']
      line=request.form['var_8']
      transport_type=request.form['var_9']
      observations=request.form['var_10']
      contact_name=request.form['var_11']
      contact_email=request.form['var_12']
      contact_number=request.form['var_13']
      sfe=request.form['var_14']
      sosa=request.form['var_15']
      Store_procedure = "Exec dbo.[ChangeStateStandardReq] @id = ? , @username = ?,@ref1=?,@ref2=?,@ref3=?,@ref4=?,@ref5=?,@imputable=?,@supllier_client=?,@line=?,@transport_type=?,@observations=?,@contact_name=?,@contact_email=?,@contact_number=?,@sfe=?,@sosa=?"
      cursor.execute(Store_procedure,id,username,ref_1,ref_2,ref_3,ref_4,ref_5,imputable,supplier_client,line,transport_type,observations,contact_name,contact_email,contact_number,sfe,sosa)
      cursor.commit()
      flash('Alterado com sucesso', category='success')
      return redirect(url_for('status_transport_standard'))

##Registo de estado Requisições
@app.route('/edit_warehouse_standard_req/<int:id>',methods=['GET', 'POST'])
def edit_warehouse_standard_req(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']

      transporter=request.form['var_1']
      waybill=request.form['var_2']
      state=request.form['var_3']
      date=request.form['var_4']
      time=request.form['var_5']

      Store_procedure = "Exec dbo.[ChangeStateWArehouseStandardReq] @id = ? , @username = ?,@transporter=?,@waybill=?,@state=?,@date=?,@time=?"
      cursor.execute(Store_procedure,id,username,transporter,waybill,state,date,time)
      cursor.commit()
      flash('Alterado com sucesso', category='success')
      return redirect(url_for('status_armazem'))

@app.route('/edit_warehouse_standard_reqs/<int:id>',methods=['GET', 'POST'])
def edit_warehouse_standard_reqs(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']

      transporter=request.form['var_1']
      waybill=request.form['var_2']
      state=request.form['var_3']
      date=request.form['var_4']
      time=request.form['var_5']

      Store_procedure = "Exec dbo.[ChangeStateWarehouseStandardReqs] @id = ? , @username = ?,@transporter=?,@waybill=?,@state=?,@date=?,@time=?"
      cursor.execute(Store_procedure,id,username,transporter,waybill,state,date,time)
      cursor.commit()
      flash('Alterado com sucesso', category='success')
      return redirect(url_for('status_armazem'))


@app.route('/registar_estado_armazem/<int:id>',methods=['GET', 'POST'])
def registar_estado_armazem(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      estado=request.form['var_5']
      
      username=session['username']

      Store_procedure_alterar_estado_armazem = "Exec dbo.alterar_estado_armazem @id = ?,@estado = ?,@username=?"
      cursor.execute(Store_procedure_alterar_estado_armazem,id_var,estado,username)
      cursor.commit()
      flash('Estado alterado', category='success')
      
      return redirect(url_for('status_armazem'))

@app.route('/registar_armazem_descarga/<int:id>',methods=['GET', 'POST'])
def registar_armazem_descarga(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      #transporte=request.form['var_1']
      fornecedor_1=request.form['var_2']
      guia_1=request.form['var_3']

      fornecedor_2=request.form['var_4']
      guia_2=request.form['var_5']

      fornecedor_3=request.form['var_6']
      guia_3=request.form['var_7']

      fornecedor_4=request.form['var_8']
      guia_4=request.form['var_9']

      fornecedor_5=request.form['var_10']
      guia_5=request.form['var_11']

      fornecedor_6=request.form['var_12']
      guia_6=request.form['var_13']

      fornecedor_7=request.form['var_14']
      guia_7=request.form['var_15']

      fornecedor_8=request.form['var_16']
      guia_8=request.form['var_17']

      fornecedor_9=request.form['var_18']
      guia_9=request.form['var_19']

      fornecedor_10=request.form['var_20']
      guia_10=request.form['var_21']

      fornecedor_11=request.form['var_22']
      guia_11=request.form['var_23']

      fornecedor_12=request.form['var_24']
      guia_12=request.form['var_25']

      fornecedor_13=request.form['var_26']
      guia_13=request.form['var_27']

      fornecedor_14=request.form['var_28']
      guia_14=request.form['var_29']

      fornecedor_15=request.form['var_30']
      guia_15=request.form['var_31']

      fornecedor_16=request.form['var_32']
      guia_16=request.form['var_33']

      fornecedor_17=request.form['var_34']
      guia_17=request.form['var_35']

      fornecedor_18=request.form['var_36']
      guia_18=request.form['var_37']

      fornecedor_19=request.form['var_38']
      guia_19=request.form['var_39']

      fornecedor_20=request.form['var_40']
      guia_20=request.form['var_41']

      username=session['username']

      Store_procedure_registo_armazem = "Exec dbo.registo_armazem @id = ?,@username=?,@fornecedor_1=?,@guia_1=?,@fornecedor_2=?,@guia_2=?,@fornecedor_3=?,@guia_3=?,@fornecedor_4=?,@guia_4=?,@fornecedor_5=?,@guia_5=?,@fornecedor_6=?,@guia_6=?,@fornecedor_7=?,@guia_7=?,@fornecedor_8=?,@guia_8=?,@fornecedor_9=?,@guia_9=?,@fornecedor_10=?,@guia_10=?,@fornecedor_11=?,@guia_11=?,@fornecedor_12=?,@guia_12=?,@fornecedor_13=?,@guia_13=?,@fornecedor_14=?,@guia_14=?,@fornecedor_15=?,@guia_15=?,@fornecedor_16=?,@guia_16=?,@fornecedor_17=?,@guia_17=?,@fornecedor_18=?,@guia_18=?,@fornecedor_19=?,@guia_19=?,@fornecedor_20=?,@guia_20=?"
      cursor.execute(Store_procedure_registo_armazem,id_var,username,fornecedor_1,guia_1,fornecedor_2,guia_2,fornecedor_3,guia_3,fornecedor_4,guia_4,fornecedor_5,guia_5,fornecedor_6,guia_6,fornecedor_7,guia_7,fornecedor_8,guia_8,fornecedor_9,guia_9,fornecedor_10,guia_10,fornecedor_11,guia_11,fornecedor_12,guia_12,fornecedor_13,guia_13,fornecedor_14,guia_14,fornecedor_15,guia_15,fornecedor_16,guia_16,fornecedor_17,guia_17,fornecedor_18,guia_18,fornecedor_19,guia_19,fornecedor_20,guia_20)
      cursor.commit()
      flash('Estado alterado', category='success')
      return redirect(url_for('registo_armazem'))

@app.route('/registar_armazem_descarga2/<int:id>',methods=['GET', 'POST'])
def registar_armazem_descarga2(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      transporte=request.form['var_1']
      fornecedor_1=request.form['var_2']
      guia_1=request.form['var_3']

      fornecedor_2=request.form['var_4']
      guia_2=request.form['var_5']

      fornecedor_3=request.form['var_6']
      guia_3=request.form['var_7']

      fornecedor_4=request.form['var_8']
      guia_4=request.form['var_9']

      fornecedor_5=request.form['var_10']
      guia_5=request.form['var_11']

      username=session['username']

      Store_procedure_registo_armazem = "Exec dbo.registo_armazem_2 @id = ?,@username=?,@transporte=?,@fornecedor_1=?,@guia_1=?,@fornecedor_2=?,@guia_2=?,@fornecedor_3=?,@guia_3=?,@fornecedor_4=?,@guia_4=?,@fornecedor_5=?,@guia_5=?"
      cursor.execute(Store_procedure_registo_armazem,id_var,username,transporte,fornecedor_1,guia_1,fornecedor_2,guia_2,fornecedor_3,guia_3,fornecedor_4,guia_4,fornecedor_5,guia_5)
      cursor.commit()
      flash('Estado alterado', category='success')
      return redirect(url_for('registo_armazem'))

@app.route('/registar_armazem_carga/<int:id>',methods=['GET', 'POST'])
def registar_armazem_carga(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      transporte=''
      fornecedor=''
      guia=''
      
      username=session['username']

      Store_procedure_registo_armazem_carga = "Exec dbo.registo_armazem_carga @id = ?,@username=?,@transporte=?,@fornecedor_1=?,@guia_1=?"
      cursor.execute(Store_procedure_registo_armazem_carga,id_var,username,transporte,fornecedor,guia)
      cursor.commit()
      flash('Estado alterado', category='success')
      return redirect(url_for('registo_armazem'))

@app.route('/registar_armazem_carga_after_descarga/<int:id>',methods=['GET', 'POST'])
def registar_armazem_carga_after_descarga(id):
  if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      id_var=id
      cliente=request.form['var_1']
      destino=request.form['var_2']
      codigo_carga=request.form['var_3']

      
      username=session['username']

      Store_procedure_registo_armazem_descarga_plus_carga = "Exec dbo.registo_armazem_descarga_plus_carga @id = ?,@username=?,@destino_2=?,@cliente_2=?,@codigo_carga_2=?"
      cursor.execute(Store_procedure_registo_armazem_descarga_plus_carga,id_var,username,destino,cliente,codigo_carga)
      cursor.commit()
      flash('Estado alterado', category='success')
      return redirect(url_for('registo_armazem'))

@app.route('/validar_saida_armazem/<int:id>',methods=['GET', 'POST'])
def validar_saida_armazem(id):
  
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    id_var=id
    username=session['username']

    Store_procedure_validar_saida_armazem = "Exec dbo.validar_saida_armazem @id = ?,@username=?"
    cursor.execute(Store_procedure_validar_saida_armazem,id_var,username)
    cursor.commit()
    flash('Validação concluída com sucesso!', category='success')
    return redirect(url_for('registo_armazem'))

@app.route('/validar_fim_carga/<int:id>',methods=['GET', 'POST'])
def validar_fim_carga(id):
  
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    id_var=id
    username=session['username']

    Store_procedure_validar_fim_carga = "Exec dbo.validar_fim_carga @id = ?,@username=?"
    cursor.execute(Store_procedure_validar_fim_carga,id_var,username)
    cursor.commit()
    flash('Validação concluída com sucesso!', category='success')
    return redirect(url_for('registo_armazem'))


#estado do cais
@app.route('/estado_cais',methods=['GET', 'POST'])
def estado_cais():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    SP_settings_estado_cais = "Exec dbo.[settings_estado_cais]"
    cursor.execute(SP_settings_estado_cais)
    settings_estado_cais = cursor.fetchall()
    return render_template('/armazem/estado_cais.html',settings_estado_cais=settings_estado_cais)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/alterar_cais/<int:id>', methods=['POST', 'GET'])
def alterar_cais(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_settings_alterar_estado_cais = "Exec dbo.[settings_alterar_estado_cais] @id = ?"
    cursor.execute(storeproc_settings_alterar_estado_cais,id)
    conn.commit()
    flash('Cais libertado', category='success')
    return redirect(url_for('estado_cais'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


########################################################################################################################################################################
# MRP
########################################################################################################################################################################

@app.route('/homepage_mrp',methods=['GET', 'POST'])
def homepage_mrp():
  try:
    #username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    today = date.today()
    year = today.strftime("%Y")
    return render_template('/mrp/homepage_mrp.html',year=year)
  except Exception as e:
        flash('Login Error',category='error')
  return redirect(url_for('index'))

@app.route('/status_mrp',methods=['GET', 'POST'])
def status_mrp():
  try:
    today = date.today()
    year = today.strftime("%Y")
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()

    username=session['username']
    
    if 'filter_date_mrp' in session:
      filter_date = session['filter_date_mrp']
    else:
      filter_date = None

    if 'filter_reference_mrp' in session:
      filter_reference = session['filter_reference_mrp']
    else:
      filter_reference = None

    if 'filter_mrp_mrp' in session:
      filter_mrp = session['filter_mrp_mrp']
    else:
      filter_mrp = None

    if 'filter_status_mrp' in session:
      filter_status = session['filter_status_mrp']
    else:
      filter_status = None

    if 'filter_shipto' in session:
      filter_shipto = session['filter_shipto']
    else:
      filter_shipto = None

    if 'filter_customer' in session:
      filter_customer = session['filter_customer']
    else:
      filter_customer = None

    SP_MRPGetRequests = "Exec dbo.[MRPGetRequests] @FilterDate=?,@FilterReference=?,@FilterMRP=?,@FilterStatus=?,@FilterShipTo=?,@FilterCustomer=?"
    cursor.execute(SP_MRPGetRequests,filter_date,filter_reference,filter_mrp,filter_status,filter_shipto,filter_customer)
    MRPGetRequests = cursor.fetchall()

    SP_MRPGetMotives = "Exec dbo.[MRPGetMotives]"
    cursor.execute(SP_MRPGetMotives)
    MRPGetMotives = cursor.fetchall()

    SP_MRPGetRequestsMRPfilters = "Exec dbo.[MRPGetRequestsMRPfilters] @level=?"
    cursor.execute(SP_MRPGetRequestsMRPfilters,1)
    MRPGetReferenceFilter = cursor.fetchall()
    cursor.execute(SP_MRPGetRequestsMRPfilters,2)
    MRPGetMRPFilter = cursor.fetchall()
    cursor.execute(SP_MRPGetRequestsMRPfilters,3)
    MRPGetStatusFilter = cursor.fetchall()
    
    return render_template('/mrp/status_mrp.html',today=today,year=year,MRPGetRequests=MRPGetRequests,MRPGetMotives=MRPGetMotives,MRPGetStatusFilter=MRPGetStatusFilter,MRPGetMRPFilter=MRPGetMRPFilter,MRPGetReferenceFilter=MRPGetReferenceFilter)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))

#edit Multiple shipment from mrp
@app.route('/edit_multiple_shipment_requests',methods=['GET', 'POST'])
def edit_multiple_shipment_requests():
  try:
    username=session['username']
    if request.method == 'POST':
      username=session['username']
      
      if 'filter_date_mrp' in session:
        filter_date = session['filter_date_mrp']
      else:
        filter_date = None

      if 'filter_reference_mrp' in session:
        filter_reference = session['filter_reference_mrp']
      else:
        filter_reference = None

      if 'filter_mrp_mrp' in session:
        filter_mrp = session['filter_mrp_mrp']
      else:
        filter_mrp = None

      if 'filter_status_mrp' in session:
        filter_status = session['filter_status_mrp']
      else:
        filter_status = None

      if 'filter_shipto' in session:
        filter_shipto = session['filter_shipto']
      else:
        filter_shipto = None

      if 'filter_customer' in session:
        filter_customer = session['filter_customer']
      else:
        filter_customer = None

      ShipTo = request.form['ShipTo']
      dateexp = request.form['dateexp']

      cursor=conn.cursor()
      sp_MRPRequestsMassiveEdit = "Exec dbo.[MRPRequestsMassiveEdit] @FilterDate = ?,@FilterReference=?,@FilterMRP=?, @FilterStatus=?, @ShipTo=?,@NewDateReg=?,@FilterShipto=?,@FilterCustomer=?"
      cursor.execute(sp_MRPRequestsMassiveEdit,filter_date, filter_reference, filter_mrp, filter_status, ShipTo, dateexp,filter_shipto,filter_customer)
      conn.commit()

      flash('Updated successfully', category='success')
      return redirect(url_for('status_mrp'))
    else:
      flash('Error with the fields!', category='error')
      return redirect(url_for('status_mrp'))
  except Exception as e:
      flash('Login error!', category='error')
  return redirect(url_for('index'))

@app.route('/add_shipment_requests',methods=['GET', 'POST'])
def add_shipment_requests():
  try:
    username=session['username']
    if request.method == 'POST':
      username=session['username']
      #owner_email=str(username)+str('@borgwarner.com')
      #Criacao novo internal_code
      SRQ = 'SRQ'
      today = date.today()
      format ="%y"
      year = today.strftime(format)
      ##########
      #Verifica o ultimo internal code
      ##########
      ## with multiple lines
      reference = request.form.getlist('reference[]')
      quantity = request.form.getlist('quantity[]')
      client = request.form.getlist('client[]')
      datereg = request.form.getlist('datereg[]')
      factory = request.form.getlist('factory[]')
      route = request.form.getlist('route[]')
      shipto = request.form.getlist('shipto[]')
      SOSA = request.form.getlist('SOSA[]')
      dispatch = request.form.getlist('dispatch[]')
      mrp = request.form.getlist('mrp[]')
      comments = request.form.getlist('comments[]')
      for index, row in enumerate(reference):
        conn=pyodbc.connect(string_conexao)
        cursor=conn.cursor()
        cursor.execute("SELECT [InternalCode] FROM [MRPRequests] ORDER BY id DESC")
        dados_ultimo_id = cursor.fetchone()

        last_internal_code_value=str(dados_ultimo_id[0])
        last_internal_code_value_number=last_internal_code_value[6::]
        last_internal_code_value_year=last_internal_code_value[3:5]

        if last_internal_code_value_year == year:
          #acrecentar 1 ao internal code
          new_number = int(last_internal_code_value_number) + 1
          internal_code= str(SRQ)+str(year)+str('-')+str(new_number).zfill(4)
        else:
          #Começa o ano novo
          new_number =  1
          internal_code= str(SRQ)+str(year)+str('-')+str(new_number).zfill(4)

        cursor=conn.cursor()
        sp_CreateShipmentRequests = "Exec dbo.[CreateShipmentRequests] @Internal_code = ?,@Owner=?,@Reference=?, @Quantity=?, @Client=?, @RegDate=?, @Factory=?, @Route=?, @Shipto=?, @Sosa=?, @Dispatch=?, @MRP=?, @Comments=?"
        cursor.execute(sp_CreateShipmentRequests,internal_code,username, reference[index], quantity[index], client[index],datereg[index],factory[index],route[index],shipto[index],SOSA[index],dispatch[index],mrp[index],comments[index])
        conn.commit()
      flash('Requisition Created', category='success')
      return redirect(url_for('status_mrp'))
    else:
      flash('Error with the fields!', category='error')
      return redirect(url_for('status_mrp'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/status_mrp_multiple',methods=['GET', 'POST'])
def status_mrp_multiple():
  try:
    username=session['username']
    if 'filter_reference_temp' in session:
      filter_reference = session['filter_reference_temp']
    else:
      filter_reference = None

    if 'filter_client_temp' in session:
      filter_client = session['filter_client_temp']
    else:
      filter_client = None

    if 'filter_factory_temp' in session:
      filter_factory = session['filter_factory_temp']
    else:
      filter_factory = None
    if 'filter_route_temp' in session:
      filter_route = session['filter_route_temp']
    else:
      filter_route = None
    if 'filter_mrp_temp' in session:
      filter_mrp = session['filter_mrp_temp']
    else:
      filter_mrp = None
    
    today = date.today()
    year = today.strftime("%Y")
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    SP_MRPGetRequeststemp = "Exec dbo.[MRPGetRequestsTemp] @username=?, @FilterReference=?,@FilterClient=?,@FilterFactory=?,@FilterRoute=?,@FilterMRP=?"
    cursor.execute(SP_MRPGetRequeststemp,username,filter_reference,filter_client,filter_factory,filter_route,filter_mrp)
    MRPGetRequeststemp = cursor.fetchall()
    SP_MRPGetMotives = "Exec dbo.[MRPGetMotives]"
    cursor.execute(SP_MRPGetMotives)
    MRPGetMotives = cursor.fetchall()

    SP_MRPGetRequestsTempfilters = "Exec dbo.[MRPGetRequestsTempfilters] @username=?,@level=? "
    cursor.execute(SP_MRPGetRequestsTempfilters,username,1)
    MRPGetFiltersTempReference = cursor.fetchall()
    cursor.execute(SP_MRPGetRequestsTempfilters,username,2)
    MRPGetFiltersTempClient = cursor.fetchall()
    cursor.execute(SP_MRPGetRequestsTempfilters,username,3)
    MRPGetFiltersTempFactory = cursor.fetchall()
    cursor.execute(SP_MRPGetRequestsTempfilters,username,4)
    MRPGetFiltersTempRoute = cursor.fetchall()
    cursor.execute(SP_MRPGetRequestsTempfilters,username,5)
    MRPGetFiltersTempMRP = cursor.fetchall()
    return render_template('/mrp/status_mrp_multiple.html',year=year,MRPGetRequeststemp=MRPGetRequeststemp,MRPGetMotives=MRPGetMotives,MRPGetFiltersTempReference=MRPGetFiltersTempReference,MRPGetFiltersTempClient=MRPGetFiltersTempClient,MRPGetFiltersTempFactory=MRPGetFiltersTempFactory,MRPGetFiltersTempRoute=MRPGetFiltersTempRoute,MRPGetFiltersTempMRP=MRPGetFiltersTempMRP)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))

@app.route('/edit_status_mrp_requests/<int:id>', methods=['POST', 'GET'])
def edit_status_mrp_requests(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    username=session['username']
    if request.method == 'POST':
      reference=request.form['reference']
      quantity=request.form['quantity']
      client=request.form['client']
      datereg=request.form['datereg']
      factory=request.form['factory']
      route=request.form['route']
      shipto=request.form['shipto']
      SOSA=request.form['SOSA']
      dispatch=request.form['dispatch']
      mrp=request.form['mrp']
      comments=request.form['comments']
      
      storeproc_MRPRequestEdit = "Exec dbo.[MRPRequestEdit] @id = ?,@Reference=?,@Quantity=?,@Client=?,@Factory=?,@Route=?,@RegDate=?,@Dispatch=?,@Comments=?,@Sosa=?,@MRP=?,@Shipto=?,@Username=?"
      cursor.execute(storeproc_MRPRequestEdit,id,reference,quantity,client,factory,route,datereg,dispatch,comments,SOSA,mrp,shipto,username)
      conn.commit()
      flash('Requested Edited', category='success')
      return redirect(url_for('status_mrp'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/add_multiple_shipment_requests',methods=['GET', 'POST'])
def add_multiple_shipment_requests():
  try:
    username=session['username']
    if request.method == 'POST':
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      username=session['username']
      lines=request.form['lines']
      segment_text = lines.split('\n')
      rows = []
      for line in segment_text:
          fields = line.split('\t')
          rows.append(fields)
      for row in rows:
        try:
          data_obj = datetime.strptime(row[4], '%d/%m/%Y')
          data_formatada = data_obj.strftime('%Y-%m-%d')
          if row[6] =='Sim' or row[6] =='Yes' or row[6] =='sim' or row[6] =='YES' or row[6] =='Y' or row[6] =='S' or row[6] =='y' or row[6] =='s':
            row[6] ='Yes'
          else:
            row[6] ='No'

          cursor.execute("INSERT INTO [LMS].[dbo].[MRPRequestsTemp] ([Owner], [Reference], [Client], [Factory], [Quantity],[RegDate], [Route], [Dispatch], [Comments], [Sosa], [MRP],[Shipto]) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(username,row[0],row[1], row[2], row[3],data_formatada, row[5], row[6], row[7], row[8], row[9],''))
          conn.commit()
        except Exception as e:
            # Se houver um erro ao inserir os dados, exibe uma mensagem de erro em flash
            flash('There is an error with you text! Check the pasted text!', category='error')
            conn.rollback()  # Revertendo a transação
            return redirect(url_for('status_mrp_multiple'))
      flash('Requisition Created', category='success')
      return redirect(url_for('status_mrp_multiple'))
    else:
      flash('Error with the fields!', category='error')
      return redirect(url_for('status_mrp_multiple'))
  except Exception as e:
        flash('Login error!', category='error')
  return redirect(url_for('index'))


@app.route('/delete_multiple_shipment_requests',methods=['GET', 'POST'])
def delete_multiple_shipment_requests():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    cursor.execute("DELETE FROM [MRPRequestsTemp]  WHERE [Owner] = ?",username)
    conn.commit()
    flash('All records deleted successfully', category='success')
    return redirect(url_for('status_mrp_multiple'))
  except Exception as e:
        flash('Error login!', category='error')
  return redirect(url_for('index'))


@app.route('/validate_all_data_temp',methods=['GET', 'POST'])
def validate_all_data_temp():
  try:
    username=session['username']
    SRQ = 'SRQ'
    today = date.today()
    format ="%y"
    year = today.strftime(format)
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    cursor.execute("SELECT *  FROM [MRPRequestsTemp]  WHERE [Owner] = ?",username)
    MRPGetTempData = cursor.fetchall()
    if MRPGetTempData:
      for row in MRPGetTempData:
        conn=pyodbc.connect(string_conexao)
        cursor=conn.cursor()
        cursor.execute("SELECT [InternalCode] FROM [MRPRequests] ORDER BY id DESC")
        dados_ultimo_id = cursor.fetchone()

        last_internal_code_value=str(dados_ultimo_id[0])
        last_internal_code_value_number=last_internal_code_value[6::]
        last_internal_code_value_year=last_internal_code_value[3:5]

        if last_internal_code_value_year == year:
          #acrecentar 1 ao internal code
          new_number = int(last_internal_code_value_number) + 1
          internal_code= str(SRQ)+str(year)+str('-')+str(new_number).zfill(4)
        else:
          #Começa o ano novo
          new_number =  1
          internal_code= str(SRQ)+str(year)+str('-')+str(new_number).zfill(4)

        cursor=conn.cursor()
        sp_CreateShipmentRequests = "Exec dbo.[CreateShipmentRequestsFromTemp] @Internal_code = ?,@Owner=?,@Reference=?, @Quantity=?, @Client=?, @RegDate=?, @Factory=?, @Route=?, @Shipto=?, @Sosa=?, @Dispatch=?, @MRP=?, @Comments=?,@Height=?,@Pallets=?"
        cursor.execute(sp_CreateShipmentRequests,internal_code,username, row[3], row[7], row[4],row[10],row[5],row[11],row[6],row[14],row[12],row[15],row[13],row[9],row[8])
        conn.commit()
      #End of commit delete all data inserted
      cursor.execute("DELETE FROM [MRPRequestsTemp]  WHERE [Owner] = ?",username)
      conn.commit()
      flash('All data inserted!', category='success')
      return redirect(url_for('status_mrp_multiple'))
    else:
      flash('There is no rows to validate', category='warning')
    return redirect(url_for('status_mrp_multiple'))
  except Exception as e:
        flash('Error login!', category='error')
  return redirect(url_for('index'))


@app.route('/cancel_request_mrp/<int:id>', methods=['POST', 'GET'])
def cancel_request_mrp(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    motive=request.form['motive']
    comments_refuse=request.form['comments_refuse']
    storeproc_MRPRequestsCancel = "Exec dbo.[MRPRequestsCancel] @id = ?,@motive=?,@comments_refuse=?"
    cursor.execute(storeproc_MRPRequestsCancel,id,motive,comments_refuse)
    conn.commit()
    flash('Request Canceled', category='warning')
    return redirect(url_for('status_mrp'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

############################
#Add Filters MultipleTemp
@app.route('/status_mrp_multiple_temp_filters', methods=['GET', 'POST'])
def status_mrp_multiple_temp_filters():
  if 'filter_reference' in request.form:
    session['filter_reference_temp']=request.form['filter_reference']
  if 'filter_client' in request.form:
    session['filter_client_temp']=request.form['filter_client']
  if 'filter_factory' in request.form:
    session['filter_factory_temp']=request.form['filter_factory']
  if 'filter_route' in request.form:
    session['filter_route_temp']=request.form['filter_route']
  if 'filter_mrp' in request.form:
    session['filter_mrp_temp']=request.form['filter_mrp']
  flash('Filters applied', category='warning')
  return redirect(url_for('status_mrp_multiple'))

#Remove Filters MultipleTemp
@app.route('/status_mrp_multiple_temp_remove_filters', methods=['GET', 'POST'])
def status_mrp_multiple_temp_remove_filters():
  session.pop('filter_reference_temp', '')
  session.pop('filter_client_temp', '')
  session.pop('filter_factory_temp', '')
  session.pop('filter_route_temp', '')
  session.pop('filter_mrp_temp', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('status_mrp_multiple'))

############################
#Add Filters First Page
@app.route('/status_mrp_temp_filters', methods=['GET', 'POST'])
def status_mrp_temp_filters():
  if 'filter_date' in request.form:
    session['filter_date_mrp']=request.form['filter_date']
  if 'filter_reference' in request.form:
    session['filter_reference_mrp']=request.form['filter_reference']
  if 'filter_mrp' in request.form:
    session['filter_mrp_mrp']=request.form['filter_mrp']
  if 'filter_status' in request.form:
    session['filter_status_mrp']=request.form['filter_status']
  if 'filter_shipto' in request.form:
    session['filter_shipto']=request.form['filter_shipto']
  if 'filter_customer' in request.form:
    session['filter_customer']=request.form['filter_customer']
  flash('Filters applied', category='warning')
  return redirect(url_for('status_mrp'))

#Remove Filters First Page
@app.route('/status_mrp_multiple_remove_filters', methods=['GET', 'POST'])
def status_mrp_multiple_remove_filters():
  session.pop('filter_date_mrp', '')
  session.pop('filter_reference_mrp', '')
  session.pop('filter_mrp_mrp', '')
  session.pop('filter_status_mrp', '')
  session.pop('filter_shipto', '')
  session.pop('filter_customer', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('status_mrp'))

#StatusMRPMultipleEdit
@app.route('/edit_status_mrp_multiple_page/<int:id>', methods=['POST', 'GET'])
def edit_status_mrp_multiple_page(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    reference=request.form['reference']
    quantity=request.form['quantity']
    client=request.form['client']
    datereg=request.form['datereg']
    factory=request.form['factory']
    route=request.form['route']
    shipto=request.form['shipto']
    SOSA=request.form['SOSA']
    dispatch=request.form['dispatch']
    mrp=request.form['mrp']
    comments=request.form['comments']
    storeproc_MRPRequestsMultipleEdit = "Exec dbo.[MRPRequestsMultipleEdit] @id = ?,@Reference=?,@Client=?,@Factory=?,@Shipto=?,@Quantity=?,@RegDate=?,@Route=?,@Dispatch=?,@Comments=?,@Sosa=?,@MRP=?"
    cursor.execute(storeproc_MRPRequestsMultipleEdit,id,reference,client,factory,shipto,quantity,datereg,route,dispatch,comments,SOSA,mrp)
    conn.commit()
    flash('Request Changed successfully', category='success')
    return redirect(url_for('status_mrp_multiple'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/delete_status_mrp_multiple_page/<int:id>', methods=['POST', 'GET'])
def delete_status_mrp_multiple_page(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    storeproc_MRPRequestsMultipleDelete = "Exec dbo.[MRPRequestsMultipleDelete] @id = ?"
    cursor.execute(storeproc_MRPRequestsMultipleDelete,id)
    conn.commit()
    flash('Request Delete successfully', category='success')
    return redirect(url_for('status_mrp_multiple'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

############################
##Historicos MRP
@app.route('/history_last_7_days_mrp',methods=['GET', 'POST'])
def history_last_7_days_mrp():
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    sp_MRPHistoryLast7days = "Exec dbo.[MRPHistoryLast7days]"
    cursor.execute(sp_MRPHistoryLast7days)
    history_last_7days = cursor.fetchall()
    return render_template('/mrp/history_last_7_days_mrp.html',history_last_7days=history_last_7days)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/history_by_date_mrp',methods=['GET', 'POST'])
def history_by_date_mrp():
  try:
    username=session['username']
    data_inicial=''
    data_final=''
    data_atual = date.today()
    all_regs=''
    if request.method == 'POST':
      data_inicial=request.form['dataini']
      data_final=request.form['datafim']
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      storeproc = "Exec dbo.MRPHistorybyDate  @desde = ?, @ate = ?"
      cursor.execute(storeproc,data_inicial,data_final)
      all_regs = cursor.fetchall()
      return render_template('/mrp/history_by_date_mrp.html',all_regs=all_regs,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
    return render_template('/mrp/history_by_date_mrp.html',all_regs=all_regs,data_inicial=data_inicial,data_final=data_final,data_atual=data_atual)
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

############################
## Notification Feed MRP
@app.route('/notifications_feed_mrp',methods=['GET', 'POST'])
def notifications_feed_mrp():
  try:
    today = date.today()
    year = today.strftime("%Y")
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    username=session['username']
    if 'filter_notificatons_date_mrp' in session:
      filter_date = session['filter_notificatons_date_mrp']
    else:
      filter_date = None
    if 'filter_notifications_login_mrp' in session:
      filter_login = session['filter_notifications_login_mrp']
    else:
      filter_login = None
    if 'filter_notifications_type_mrp' in session:
      filter_type = session['filter_notifications_type_mrp']
    else:
      filter_type = None
    if 'filter_notifications_internal_code_mrp' in session:
      filter_internal_code = session['filter_notifications_internal_code_mrp']
    else:
      filter_internal_code = None
    SP_MRPGetRequests = "Exec dbo.[MRPGetNotifications] @FilterDate=?,@FilterLogin=?,@Filtertype=?,@FilterInternalCode=?"
    cursor.execute(SP_MRPGetRequests,filter_date,filter_login,filter_type,filter_internal_code)
    MRPGetRequests = cursor.fetchall()

    SP_MRPGetRequestsNotificationsFilters = "Exec dbo.[MRPGetRequestsNotificationsFilters] @level=?"
    cursor.execute(SP_MRPGetRequestsNotificationsFilters,1)
    MRPGetNotificationsTypeFilter = cursor.fetchall()
    return render_template('/mrp/notifications_feed_mrp.html',year=year,MRPGetRequests=MRPGetRequests,MRPGetNotificationsTypeFilter=MRPGetNotificationsTypeFilter)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))


#Add Filters Notifications
@app.route('/notifications_mrp_temp_filters', methods=['GET', 'POST'])
def notifications_mrp_temp_filters():
  if 'filter_notificatons_date_mrp' in request.form:
    session['filter_notificatons_date_mrp']=request.form['filter_notificatons_date_mrp']
  if 'filter_notifications_login_mrp' in request.form:
    session['filter_notifications_login_mrp']=request.form['filter_notifications_login_mrp']
  if 'filter_notifications_type_mrp' in request.form:
    session['filter_notifications_type_mrp']=request.form['filter_notifications_type_mrp']
  if 'filter_notifications_internal_code_mrp' in request.form:
    session['filter_notifications_internal_code_mrp']=request.form['filter_notifications_internal_code_mrp']
  flash('Filters applied', category='warning')
  return redirect(url_for('notifications_feed_mrp'))

#Remove Filters Notifications
@app.route('/notifications_mrp_remove_filters', methods=['GET', 'POST'])
def notifications_mrp_remove_filters():
  session.pop('filter_notificatons_date_mrp', '')
  session.pop('filter_notifications_login_mrp', '')
  session.pop('filter_notifications_type_mrp', '')
  session.pop('filter_notifications_internal_code_mrp', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('notifications_feed_mrp'))

##########
#EXPEDITION TRANSPORTS
@app.route('/expedition_requests_transports')
def expedition_requests_transports():
  try:

    if 'filter_expedition_date' in session:
      filter_expedition_date = session['filter_expedition_date']
    else:
      filter_expedition_date = None

    if 'filter_expedition_id_transport' in session:
      filter_expedition_id_transport = session['filter_expedition_id_transport']
    else:
      filter_expedition_id_transport = None

    if 'filter_expedition_client' in session:
      filter_expedition_client = session['filter_expedition_client']
    else:
      filter_expedition_client = None

    if 'filter_expedition_reservation' in session:
      filter_expedition_reservation = session['filter_expedition_reservation']
    else:
      filter_expedition_reservation = None

    if 'filter_expedition_shipment' in session:
      filter_expedition_shipment = session['filter_expedition_shipment']
    else:
      filter_expedition_shipment = None

    if 'filter_expedition_mrp' in session:
      filter_expedition_mrp = session['filter_expedition_mrp']
    else:
      filter_expedition_mrp = None

    if 'filter_expedition_factory' in session:
      filter_expedition_factory = session['filter_expedition_factory']
    else:
      filter_expedition_factory = None

    if 'filter_expedition_shipto' in session:
      filter_expedition_shipto = session['filter_expedition_shipto']
    else:
      filter_expedition_shipto = None

    username=session['username']
    cursor=conn.cursor()
    #cursor.execute("SELECT * from [MRPRequests] order by id desc")
    
    #MRPGetRequests = cursor.fetchall()
    SP_MRPGetRecurringTransportsID = "Exec dbo.[MRPGetExpeditionRequests] @FilterDate=?,@FilterIdTransport=?,@FilterClient=?,@FilterReservation=?,@FilterShipment=?,@FilterFactory=?,@FilterShipTo=?,@FilterMRP=?"
    cursor.execute(SP_MRPGetRecurringTransportsID,filter_expedition_date,filter_expedition_id_transport,filter_expedition_client,filter_expedition_reservation,filter_expedition_shipment,filter_expedition_factory,filter_expedition_shipto,filter_expedition_mrp)
    MRPGetRequests = cursor.fetchall()

    cursor.execute("SELECT * from [TransportsReservationDescription] order by id desc")
    transports_reservation = cursor.fetchall()

    cursor.execute("SELECT * from [MRPTransportsID] where status = 0 order by id desc")
    transports_id = cursor.fetchall()

    SP_MRPGetMotives = "Exec dbo.[MRPGetMotives]"
    cursor.execute(SP_MRPGetMotives)
    MRPGetMotives = cursor.fetchall()
    return render_template('/transports/expedition_requests_transports.html',transports_id=transports_id,transports_reservation=transports_reservation,MRPGetMotives=MRPGetMotives,MRPGetRequests=MRPGetRequests)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))
#Transport cancel Request
@app.route('/cancel_request_transport/<int:id>', methods=['POST', 'GET'])
def cancel_request_transport(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    motive=request.form['motive']
    username=session['username']
    comments_refuse=request.form['comments_refuse']
    storeproc_TransportsExpeditionRequestCancel = "Exec dbo.[TransportsExpeditionRequestCancel] @id = ?,@motive=?,@comments_refuse=?,@Owner=?"
    cursor.execute(storeproc_TransportsExpeditionRequestCancel,id,motive,comments_refuse,username)
    conn.commit()
    flash('Request Canceled', category='warning')
    return redirect(url_for('expedition_requests_transports'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))
#Transport edit Request
@app.route('/edit_expedition_transports_requests/<int:id>', methods=['POST', 'GET'])
def edit_expedition_transports_requests(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    username=session['username']
    if request.method == 'POST':
      client=request.form['client']
      quantity=request.form['quantity']
      factory=request.form['factory']
      datereg=request.form['datereg']
      route=request.form['route']
      idtransport=request.form['idtransport']
      shipment=request.form['shipment']
      Reservation=request.form['Reservation']
      username=session['username']
      urgent=request.form['urgent']
      storeproc_MRPRequestTransportEdit = "Exec dbo.[MRPRequestTransportEdit] @id = ?,@Quantity=?,@Client=?,@Factory=?,@RegDate=?,@Route=?,@idtransport=?,@Shipment=?,@Reservation=?, @username =?, @Urgent =?"
      cursor.execute(storeproc_MRPRequestTransportEdit,id,quantity,client,factory,datereg,route,idtransport,shipment,Reservation,username,urgent)
      conn.commit()
      flash('Requested Edited', category='success')
      return redirect(url_for('expedition_requests_transports'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))
#EXPEDITION TRANSPORTS FILTERS
@app.route('/notifications_expedition_requests_filters', methods=['GET', 'POST'])
def notifications_expedition_requests_filters():
  if 'filter_expedition_date' in request.form:
    session['filter_expedition_date']=request.form['filter_expedition_date']

  if 'filter_expedition_id_transport' in request.form:
    session['filter_expedition_id_transport']=request.form['filter_expedition_id_transport']

  if 'filter_expedition_client' in request.form:
    session['filter_expedition_client']=request.form['filter_expedition_client']

  if 'filter_expedition_reservation' in request.form:
    session['filter_expedition_reservation']=request.form['filter_expedition_reservation']

  if 'filter_expedition_shipment' in request.form:
    session['filter_expedition_shipment']=request.form['filter_expedition_shipment']

  if 'filter_expedition_mrp' in request.form:
    session['filter_expedition_mrp']=request.form['filter_expedition_mrp']

  if 'filter_expedition_factory' in request.form:
    session['filter_expedition_factory']=request.form['filter_expedition_factory']

  if 'filter_expedition_shipto' in request.form:
    session['filter_expedition_shipto']=request.form['filter_expedition_shipto']


  flash('Filters applied', category='warning')
  return redirect(url_for('expedition_requests_transports'))

#Remove EXPEDITION TRANSPORTS FILTERS
@app.route('/expedition_transport_remove_filters', methods=['GET', 'POST'])
def expedition_transport_remove_filters():
  session.pop('filter_expedition_date', '')
  session.pop('filter_expedition_id_transport', '')
  session.pop('filter_expedition_client', '')
  session.pop('filter_expedition_reservation', '')
  session.pop('filter_expedition_shipment', '')
  session.pop('filter_expedition_mrp', '')
  session.pop('filter_expedition_factory', '')
  session.pop('filter_expedition_shipto', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('expedition_requests_transports'))



#edit Multiple shipment from mrp
@app.route('/edit_multiple_expedition_requests_transports',methods=['GET', 'POST'])
def edit_multiple_expedition_requests_transports():
  try:
    username=session['username']
    if request.method == 'POST':
      username=session['username']
      
      if 'filter_expedition_date' in session:
        filter_date = session['filter_expedition_date']
      else:
        filter_date = None

      if 'filter_expedition_id_transport' in session:
        filter_id_transport = session['filter_expedition_id_transport']
      else:
        filter_id_transport = None

      if 'filter_expedition_client' in session:
        filter_client = session['filter_expedition_client']
      else:
        filter_client = None

      if 'filter_expedition_reservation' in session:
        filter_expedition_reservation = session['filter_expedition_reservation']
      else:
        filter_expedition_reservation = None

      if 'filter_expedition_shipment' in session:
        filter_expedition_shipment = session['filter_expedition_shipment']
      else:
        filter_expedition_shipment = None

      if 'filter_expedition_mrp' in session:
        filter_expedition_mrp = session['filter_expedition_mrp']
      else:
        filter_expedition_mrp = None

      if 'filter_expedition_factory' in session:
        filter_expedition_factory = session['filter_expedition_factory']
      else:
        filter_expedition_factory = None

      if 'filter_expedition_shipto' in session:
        filter_expedition_shipto = session['filter_expedition_shipto']
      else:
        filter_expedition_shipto = None

      idtransport = request.form['idtransport']
      reservation = request.form['reservation']
      route = request.form['route']
      dateexp = request.form['dateexp']
      """
      print (filter_date)
      print (filter_id_transport)
      print (filter_client)
      print (filter_expedition_reservation)
      print (filter_expedition_shipment)
      print (filter_expedition_mrp)
      print (filter_expedition_factory)
      print (filter_expedition_shipto)
      print (idtransport)
      print (reservation)
      print (route)
      print (dateexp)
      """
      cursor=conn.cursor()
      sp_ExpeditionRequestsMassiveEdit = "Exec dbo.[ExpeditionRequestsMassiveEdit] @FilterDate = ?,@FilterIdTransport=?,@FilterClient=?, @FilterExpeditionReservation=?, @FilterExpeditionShipment=?,@FilterExpeditionMRP=?,@FilterExpeditionFactory=?,@FilterExpeditionShipto=?,@IdTransport=?,@Reservation=?,@Route=?,@NewDateReg=?"
      cursor.execute(sp_ExpeditionRequestsMassiveEdit,filter_date, filter_id_transport, filter_client, filter_expedition_reservation, filter_expedition_shipment, filter_expedition_mrp,filter_expedition_factory,filter_expedition_shipto,idtransport,reservation,route,dateexp)
      conn.commit()

      flash('Updated successfully', category='success')
      return redirect(url_for('expedition_requests_transports'))
    else:
      flash('Error with the fields!', category='error')
      return redirect(url_for('expedition_requests_transports'))
  except Exception as e:
      flash('Login error!', category='error')
  return redirect(url_for('index'))



## Notification Feed
@app.route('/expeditions_notifications_transports',methods=['GET', 'POST'])
def expeditions_notifications_transports():
  try:
    today = date.today()
    year = today.strftime("%Y")
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    username=session['username']
    if 'filter_notificatons_date_expedition_transport' in session:
      filter_date = session['filter_notificatons_date_expedition_transport']
    else:
      filter_date = None
    if 'filter_notifications_login_expedition_transport' in session:
      filter_login = session['filter_notifications_login_expedition_transport']
    else:
      filter_login = None
    if 'filter_notifications_type_expedition_transport' in session:
      filter_type = session['filter_notifications_type_expedition_transport']
    else:
      filter_type = None
    if 'filter_notifications_internal_code_expedition_transport' in session:
      filter_internal_code = session['filter_notifications_internal_code_expedition_transport']
    else:
      filter_internal_code = None
    SP_TransportsGetNotifications = "Exec dbo.[TransportsGetNotifications] @FilterDate=?,@FilterLogin=?,@Filtertype=?,@FilterInternalCode=?"
    cursor.execute(SP_TransportsGetNotifications,filter_date,filter_login,filter_type,filter_internal_code)
    MRPGetRequests = cursor.fetchall()

    SP_MRPGetRequestsNotificationsFilters = "Exec dbo.[MRPGetRequestsNotificationsFilters] @level=?"
    cursor.execute(SP_MRPGetRequestsNotificationsFilters,1)
    MRPGetNotificationsTypeFilter = cursor.fetchall()
    return render_template('/transports/expeditions_notifications_transports.html',year=year,MRPGetRequests=MRPGetRequests,MRPGetNotificationsTypeFilter=MRPGetNotificationsTypeFilter)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))

#Add Filters Notifications expedition
@app.route('/notifications_expeditions_temp_filters', methods=['GET', 'POST'])
def notifications_expeditions_temp_filters():
  if 'filter_notificatons_date_expedition_transport' in request.form:
    session['filter_notificatons_date_expedition_transport']=request.form['filter_notificatons_date_expedition_transport']
  if 'filter_notifications_login_expedition_transport' in request.form:
    session['filter_notifications_login_expedition_transport']=request.form['filter_notifications_login_expedition_transport']
  if 'filter_notifications_type_expedition_transport' in request.form:
    session['filter_notifications_type_expedition_transport']=request.form['filter_notifications_type_expedition_transport']
  if 'filter_notifications_internal_code_expedition_transport' in request.form:
    session['filter_notifications_internal_code_expedition_transport']=request.form['filter_notifications_internal_code_expedition_transport']
  flash('Filters applied', category='warning')
  return redirect(url_for('expeditions_notifications_transports'))

#Remove EXPEDITION TRANSPORTS FILTERS
@app.route('/notifications_expeditions_temp_filters_remove', methods=['GET', 'POST'])
def notifications_expeditions_temp_filters_remove():
  session.pop('filter_notificatons_date_expedition_transport', '')
  session.pop('filter_notifications_login_expedition_transport', '')
  session.pop('filter_notifications_type_expedition_transport', '')
  session.pop('filter_notifications_internal_code_expedition_transport', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('expeditions_notifications_transports'))



#ID Transport Page sporadic
@app.route('/create_id_transports')
def create_id_transports():
  try:
    username=session['username']
    if 'filter_type_id_sporadic' in session:
      filter_type_id_sporadic = session['filter_type_id_sporadic']
    else:
      filter_type_id_sporadic = None

    if 'filter_date_sporadic' in session:
      filter_date_sporadic = session['filter_date_sporadic']
    else:
      filter_date_sporadic = None

    if 'filter_week_sporadic' in session:
      filter_week_sporadic = session['filter_week_sporadic']
    else:
      filter_week_sporadic = None
    cursor=conn.cursor()
    SP_MRPGetRequeststemp = "Exec dbo.[MRPGetSporadicTransportsID] @FilterType=?,@FilterDate=?,@FilterWeek=?"
    cursor.execute(SP_MRPGetRequeststemp,filter_type_id_sporadic,filter_date_sporadic,filter_week_sporadic)
    MRPGetTransportsID = cursor.fetchall()
    SP_MRPGetMotives = "Exec dbo.[MRPGetMotives]"
    cursor.execute(SP_MRPGetMotives)
    MRPGetMotives = cursor.fetchall()
    return render_template('/transports/create_id_transports.html',MRPGetMotives=MRPGetMotives,MRPGetTransportsID=MRPGetTransportsID)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))
#Fitlers  Page sporadic
@app.route('/sporadic_id_transport_filters', methods=['GET', 'POST'])
def sporadic_id_transport_filters():
  if 'filter_type_id_sporadic' in request.form:
    session['filter_type_id_sporadic']=request.form['filter_type_id_sporadic']
  if 'filter_date_sporadic' in request.form:
    session['filter_date_sporadic']=request.form['filter_date_sporadic']
  if 'filter_week_sporadic' in request.form:
    session['filter_week_sporadic']=request.form['filter_week_sporadic']
  flash('Filters applied', category='warning')
  return redirect(url_for('create_id_transports'))

#Remove Filters Transport Page sporadic
@app.route('/sporadic_id_transport_remove_filters', methods=['GET', 'POST'])
def sporadic_id_transport_remove_filters():
  session.pop('filter_type_id_sporadic', '')
  session.pop('filter_date_sporadic', '')
  session.pop('filter_week_sporadic', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('create_id_transports'))

@app.route('/delete_transports_sporadic/<int:id>',methods=['GET', 'POST'])
def delete_transports_sporadic(id):
  try:
    username=session['username']
    cursor=conn.cursor()
    storeproc_TransportIDTransportEdit = "Exec dbo.[TransportIDTransportDelete] @id = ?,@username=?"
    cursor.execute(storeproc_TransportIDTransportEdit,id,username)
    conn.commit()
    flash('Id Deleted', category='success')
    return redirect(url_for('create_id_transports'))
  except Exception as e:
        flash('Error login!', category='error')
  return redirect(url_for('index'))

@app.route('/edit_transports_sporadic/<int:id>',methods=['GET', 'POST'])
def edit_transports_sporadic(id):
  try:
    username=session['username']
    if request.method == 'POST':
      cursor=conn.cursor()
      beginhour=request.form['beginhour']
      endhour=request.form['endhour']
      comments=request.form['comments']
      beginhour_time = datetime.strptime(beginhour, '%H:%M')
      endhour_time = datetime.strptime(endhour, '%H:%M')
      difference = endhour_time - beginhour_time
      duration = difference.total_seconds() / 60
      if duration >= 0:
        print ('Pode editar')
        cursor.execute("UPDATE [MRPTransportsID] set BeginHour= ?, Endhour=?,Duration=?,Comments=? where id=?",beginhour,endhour,duration,comments,id)
        conn.commit()
        flash('Id edited successfully', category='success')
        return redirect(url_for('create_id_transports'))
      else:
        flash('Error in Hours', category='error')
        return redirect(url_for('create_id_transports'))
      #cursor.commit()
      #adicionar em notificações ?
      
  except Exception as e:
        flash('Error login!', category='error')
  return redirect(url_for('index'))

@app.route('/add_id_transports_sporadic',methods=['GET', 'POST'])
def add_id_transports_sporadic():
  try:
    username=session['username']
    if request.method == 'POST':
      username=session['username']
      date_var=request.form['date_var']
      beginhour=request.form['beginhour']
      endhour=request.form['endhour']
      comments=request.form['comments']
      TR = 'TR'
      data = pd.to_datetime(date_var)
      ano = data.year
      semana = data.isocalendar().week
      ultimos_dois_digitos_ano = str(data.year)[-2:]
      InternalCode= str(TR)+str(semana)+str(ultimos_dois_digitos_ano)+str('0001')
      begin_time = datetime.strptime(beginhour, '%H:%M')
      end_time = datetime.strptime(endhour, '%H:%M')
      time_difference = end_time - begin_time
      duration = time_difference.total_seconds() / 60
      cursor=conn.cursor()
      cursor.execute("SELECT TOP (1) * FROM [LMS].[dbo].[MRPTransportsID]  WHERE DATEPART(YEAR,[Date]) = ? AND DATEPART(WEEK,[Date]) = ? and [Type]='Sporadic' ORDER BY id DESC",ano,semana)
      GetIdTransport = cursor.fetchall()
      if GetIdTransport:
        new_number = GetIdTransport[0][3][6:]
        new_numberfor_id=(int(new_number)+1)
        InternalCode= str(TR)+str(semana)+str(ultimos_dois_digitos_ano)+str(new_numberfor_id).zfill(4)
        storeproc_TransportCreateSporadicID = "Exec dbo.[TransportCreateSporadicID] @Username = ?,@InternalCode=?,@Date_var=?,@Beginhour=?,@Endhour=?,@Duration=?,@Comments=?"
        cursor.execute(storeproc_TransportCreateSporadicID,username,InternalCode,date_var,beginhour,endhour,duration,comments)
        conn.commit()
        flash('Transport Request Created!', category='success')
        return redirect(url_for('create_id_transports'))
      else:
        InternalCode= str(TR)+str(semana)+str(ultimos_dois_digitos_ano)+str('0001')
        storeproc_TransportCreateSporadicID = "Exec dbo.[TransportCreateSporadicID] @Username = ?,@InternalCode=?,@Date_var=?,@Beginhour=?,@Endhour=?,@Duration=?,@Comments=?"
        cursor.execute(storeproc_TransportCreateSporadicID,username,InternalCode,date_var,beginhour,endhour,duration,comments)
        conn.commit()
        flash('Transport Request Created!', category='success')
        return redirect(url_for('create_id_transports'))
      flash('Erro to create new Transport Plan', category='error')
      return redirect(url_for('create_id_transports'))
    else:
      flash('Error with the fields!', category='error')
      return redirect(url_for('create_id_transports'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

#Load Plan
@app.route('/load_plan')
def load_plan():
  try:
    username=session['username']

    if 'filter_type_id_recurring' in session:
      filter_type_id_recurring = session['filter_type_id_recurring']
    else:
      filter_type_id_recurring = None

    if 'filter_date_recurring' in session:
      filter_date_recurring = session['filter_date_recurring']
    else:
      filter_date_recurring = None

    if 'filter_week_recurring' in session:
      filter_week_recurring = session['filter_week_recurring']
    else:
      filter_week_recurring = None

    cursor=conn.cursor()
    SP_MRPGetRequeststemp = "Exec dbo.[MRPGetRecurringTransportsID] @FilterType=?,@FilterDate=?,@FilterWeek=?"
    cursor.execute(SP_MRPGetRequeststemp,filter_type_id_recurring,filter_date_recurring,filter_week_recurring)
    MRPGetTransportsID = cursor.fetchall() 

    SP_MRPGetMotives = "Exec dbo.[MRPGetMotives]"
    cursor.execute(SP_MRPGetMotives)
    MRPGetMotives = cursor.fetchall()
    return render_template('/transports/load_plan.html',MRPGetMotives=MRPGetMotives,MRPGetTransportsID=MRPGetTransportsID)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))

#Fitlers  Load Plan
@app.route('/recurring_id_transport_filters', methods=['GET', 'POST'])
def recurring_id_transport_filters():
  if 'filter_type_id_recurring' in request.form:
    session['filter_type_id_recurring']=request.form['filter_type_id_recurring']
  if 'filter_date_recurring' in request.form:
    session['filter_date_recurring']=request.form['filter_date_recurring']
  if 'filter_week_recurring' in request.form:
    session['filter_week_recurring']=request.form['filter_week_recurring']
  flash('Filters applied', category='warning')
  return redirect(url_for('load_plan'))
#Remove Filters Transport Load Plan
@app.route('/recurring_id_transport_remove_filters', methods=['GET', 'POST'])
def recurring_id_transport_remove_filters():
  session.pop('filter_type_id_recurring', '')
  session.pop('filter_date_recurring', '')
  session.pop('filter_week_recurring', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('load_plan'))

@app.route('/add_recurring_transport_id',methods=['GET', 'POST'])
def add_recurring_transport_id():
  try:
    username=session['username']
    if request.method == 'POST':
      username=session['username']
      begin_date_var=request.form['begin_date_var']
      end_date_var=request.form['end_date_var']
      beginhour=request.form['beginhour']
      endhour=request.form['endhour']
      monday=request.form['monday']
      tuesday=request.form['tuesday']
      wednesday=request.form['wednesday']
      thursday=request.form['thursday']
      friday=request.form['friday']
      saturday=request.form['saturday']
      sunday=request.form['sunday']
      client=request.form['client']
      comments=request.form['comments']

      # Converte strings de data para objetos datetime
      begin_date = datetime.strptime(begin_date_var, '%Y-%m-%d')
      end_date = datetime.strptime(end_date_var, '%Y-%m-%d')
      days_of_week = {
          'monday': 0,
          'tuesday': 1,
          'wednesday': 2,
          'thursday': 3,
          'friday': 4,
          'saturday': 5,
          'sunday': 6
      }

      # Lista dos dias selecionados
      selected_days = []
      if monday == 'Yes': selected_days.append(days_of_week['monday'])
      if tuesday == 'Yes': selected_days.append(days_of_week['tuesday'])
      if wednesday == 'Yes': selected_days.append(days_of_week['wednesday'])
      if thursday == 'Yes': selected_days.append(days_of_week['thursday'])
      if friday == 'Yes': selected_days.append(days_of_week['friday'])
      if saturday == 'Yes': selected_days.append(days_of_week['saturday'])
      if sunday == 'Yes': selected_days.append(days_of_week['sunday'])
      
      if selected_days == []:
        flash('You need to select atleast one day', category='warning')
        return redirect(url_for('load_plan'))      
      current_date = begin_date
      while current_date <= end_date:
          if current_date.weekday() in selected_days:
              # Cria a hora de início e fim do evento
              begin_datetime = datetime.combine(current_date, datetime.strptime(beginhour, '%H:%M').time())
              end_datetime = datetime.combine(current_date, datetime.strptime(endhour, '%H:%M').time())
              year, week_number, _ = current_date.isocalendar()

              cursor=conn.cursor()
              cursor.execute("SELECT TOP (1) * FROM [LMS].[dbo].[MRPTransportsID]  WHERE DATEPART(YEAR,[Date]) = ? AND DATEPART(WEEK,[Date]) = ? and Client=? and type =? ORDER BY [IdTransport] DESC",year,week_number,client,'Recurring')
              GetIdTransport = cursor.fetchall()
              if GetIdTransport:

                begin_time = datetime.strptime(beginhour, '%H:%M')
                end_time = datetime.strptime(endhour, '%H:%M')
                time_difference = end_time - begin_time
                duration = time_difference.total_seconds() / 60
                clientCode = client[:3].upper()
                year_last = str(year)[-2:]
                new_number = GetIdTransport[0][3][9:]
                new_numberfor_id=(int(new_number)+1)
                InternalCode= str('PC')+str(clientCode)+str(week_number)+str(year_last)+str(new_numberfor_id).zfill(4)
                storeproc_TransportCreateRecurringID = "Exec dbo.[TransportCreateRecurringID] @Username = ?,@InternalCode=?,@Date_var=?,@Beginhour=?,@Endhour=?,@Duration=?,@Comments=?,@Client=?"
                cursor.execute(storeproc_TransportCreateRecurringID,username,InternalCode,current_date,beginhour,endhour,duration,comments,client)
                conn.commit()
              else:
                begin_time = datetime.strptime(beginhour, '%H:%M')
                end_time = datetime.strptime(endhour, '%H:%M')
                time_difference = end_time - begin_time
                duration = time_difference.total_seconds() / 60
                clientCode = client[:3].upper()
                year_last = str(year)[-2:]
                InternalCode=str('PC')+str(clientCode)+str(week_number)+str(year_last)+str('0001')
                storeproc_TransportCreateRecurringID = "Exec dbo.[TransportCreateRecurringID] @Username = ?,@InternalCode=?,@Date_var=?,@Beginhour=?,@Endhour=?,@Duration=?,@Comments=?,@Client=?"
                cursor.execute(storeproc_TransportCreateRecurringID,username,InternalCode,current_date,beginhour,endhour,duration,comments,client)
                conn.commit()
                print (InternalCode)
          # Incrementa o dia
          current_date += timedelta(days=1)
      flash('Recurring Transport created successfully', category='success')
      return redirect(url_for('load_plan'))
    else:
      flash('Error with the fields!', category='error')
      return redirect(url_for('load_plan'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/delete_transports_recurring/<int:id>',methods=['GET', 'POST'])
def delete_transports_recurring(id):
  try:
    username=session['username']
    cursor=conn.cursor()
    storeproc_TransportIDTransportEdit = "Exec dbo.[TransportIDTransportDelete] @id = ?,@username=?"
    cursor.execute(storeproc_TransportIDTransportEdit,id,username)
    conn.commit()
    flash('Id Deleted', category='success')
    return redirect(url_for('load_plan'))
  except Exception as e:
        flash('Error login!', category='error')
  return redirect(url_for('index'))

#################################################
#Precarga 
@app.route('/homepage_armazem_new',methods=['GET','POST'])
def homepage_armazem_new():
   try:
      
      return render_template('armazem/homepage_armazem_new.html')
   except Exception as e:
      return render_template('armazem/homepage_armazem_new.html')

@app.route('/expedition_request_warehouse',methods=['GET','POST'])
def expedition_request_warehouse():
   try:
      cursor=conn.cursor()

      if 'filter_warehouse_date' in session:
        filter_warehouse_date = session['filter_warehouse_date']
      else:
        filter_warehouse_date = None

      if 'filter_warehouse_part_number' in session:
        filter_warehouse_part_number = session['filter_warehouse_part_number']
      else:
        filter_warehouse_part_number = None

      if 'filter_warehouse_status' in session:
        filter_warehouse_status = session['filter_warehouse_status']
      else:
        filter_warehouse_status = None

      if 'filter_warehouse_shipto' in session:
        filter_warehouse_shipto = session['filter_warehouse_shipto']
      else:
        filter_warehouse_shipto = None

      if 'filter_warehouse_costumer' in session:
        filter_warehouse_costumer = session['filter_warehouse_costumer']
      else:
        filter_warehouse_costumer = None

      if 'filter_warehouse_order' in session:
        filter_warehouse_order = session['filter_warehouse_order']
      else:
        filter_warehouse_order = None
      SP_MRPGetMotives = "Exec dbo.[MRPGetMotives]"
      cursor.execute(SP_MRPGetMotives)
      MRPGetMotives = cursor.fetchall()

      

      SP_MRPGetRequests= "Exec dbo.[MRPGetExpeditionRequestsWarehouse] @FilterDate=?,@FilterPartNumber=?,@FilterStatus=?,@FilterShipTo=?,@FilterCostumer=?,@FilterOrder=?"
      cursor.execute(SP_MRPGetRequests,filter_warehouse_date,filter_warehouse_part_number,filter_warehouse_status,filter_warehouse_shipto,filter_warehouse_costumer,filter_warehouse_order)
      GetIdTransport = cursor.fetchall() 

      #cursor.execute("SELECT TOP (1000) * FROM [LMS].[dbo].[MRPRequests] ORDER BY [id] DESC")
      #GetIdTransport = cursor.fetchall()
      return render_template('armazem/expedition_request_warehouse.html',GetIdTransport=GetIdTransport,MRPGetMotives=MRPGetMotives)
   except Exception as e:
      return render_template('armazem/expedition_request_warehouse.html')

#FilterExpedition_requests
@app.route('/expedition_request_warehouse_filters', methods=['GET', 'POST'])
def expedition_request_warehouse_filters():
  if 'filter_warehouse_date' in request.form:
    session['filter_warehouse_date']=request.form['filter_warehouse_date']
  if 'filter_warehouse_part_number' in request.form:
    session['filter_warehouse_part_number']=request.form['filter_warehouse_part_number']
  if 'filter_warehouse_status' in request.form:
    session['filter_warehouse_status']=request.form['filter_warehouse_status']
  if 'filter_warehouse_shipto' in request.form:
    session['filter_warehouse_shipto']=request.form['filter_warehouse_shipto']
  if 'filter_warehouse_costumer' in request.form:
    session['filter_warehouse_costumer']=request.form['filter_warehouse_costumer']

  if 'filter_warehouse_order' in request.form:
    session['filter_warehouse_order']=request.form['filter_warehouse_order']
  flash('Filtros Aplicados', category='warning')
  return redirect(url_for('expedition_request_warehouse'))


#Remove Filters Transport Load Plan
@app.route('/expedition_request_warehouse_remove_filters', methods=['GET', 'POST'])
def expedition_request_warehouse_remove_filters():
  session.pop('filter_warehouse_date', '')
  session.pop('filter_warehouse_part_number', '')
  session.pop('filter_warehouse_status', '')
  session.pop('filter_warehouse_shipto', '')
  session.pop('filter_warehouse_costumer', '')
  session.pop('filter_warehouse_order', '')
  flash('Filtros Removidos', category='warning')
  return redirect(url_for('expedition_request_warehouse'))


@app.route('/expedition_request_warehouse_table',methods=['GET'])
def expedition_request_warehouse_table():
    cursor=conn.cursor()
    cursor.execute("SELECT TOP (1000) * FROM [LMS].[dbo].[MRPRequests] ORDER BY [id] DESC")
    data = cursor.fetchall()
    data = [list(row) for row in data]
    return jsonify(data)


@app.route('/expedition_request_warehouse_edit/<int:id>',methods=['GET', 'POST'])
def expedition_request_warehouse_edit(id):
  try:
    username=session['username']
    if request.method == 'POST':
      cursor=conn.cursor()
      quantidade=request.form['qtd']
      rota=request.form['rota']
      guia=request.form['guia']
      estadoarmazem=request.form['estadoarmazem']
      mypack=request.form['mypack']
      
      picking=request.form['picking']
      expedido=request.form['expedido']

      cursor.execute("UPDATE [MRPRequests] set Quantity= ?, Route=?,Invoice=?,WarehouseStatus=?,Timetable=?,Picking=?,Dispatched=?,MyPack=? where id=?",quantidade,rota,guia,estadoarmazem,'',picking,expedido,mypack,id)
      conn.commit()
      flash('Id edited successfully', category='success')
      return redirect(url_for('expedition_request_warehouse'))      
  except Exception as e:
        flash('Error login!', category='error')
  return redirect(url_for('index'))

@app.route('/cancel_request_transport_warehouse/<int:id>', methods=['POST', 'GET'])
def cancel_request_transport_warehouse(id):
  try:
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    motive=request.form['motive']
    username=session['username']
    comments_refuse=request.form['comments_refuse']
    storeproc_TransportsExpeditionRequestCancel = "Exec dbo.[TransportsExpeditionRequestCancel] @id = ?,@motive=?,@comments_refuse=?,@Owner=?"
    cursor.execute(storeproc_TransportsExpeditionRequestCancel,id,motive,comments_refuse,username)
    conn.commit()
    flash('Request Canceled', category='warning')
    return redirect(url_for('expedition_request_warehouse'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/change_state_picking_warehouse_yes/<int:id>', methods=['POST', 'GET'])
def change_state_picking_warehouse_yes(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    estado= 'Sim'
    estado_geral= '6'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Picking]=?, [PickingStatusChange]=?,[PickingStatusOwner]=?, [Status]=?  WHERE id = ?',estado,formatted_date,username,estado_geral,id)
    conn.commit()
    #flash('Estado alterado com sucesso',category='success')
    success = True
    return jsonify({'success': success})
    #return redirect(url_for('expedition_request_warehouse'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/change_state_picking_warehouse_no/<int:id>', methods=['POST', 'GET'])
def change_state_picking_warehouse_no(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    estado= 'Nao'
    estado_geral= '5'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Picking]=?, [PickingStatusChange]=?,[PickingStatusOwner]=?,[Status]=?  WHERE id = ?',estado,formatted_date,username,estado_geral,id)
    conn.commit()
    #flash('Estado alterado com sucesso',category='success')
    success = True
    return jsonify({'success': success})
    #return redirect(url_for('expedition_request_warehouse'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/change_state_warehousestate_no/<int:id>', methods=['POST', 'GET'])
def change_state_warehousestate_no(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    estado= 'Nao'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Dispatched]=?, [DispatchedStatusDate]=?,[DispatchedStatusOwner]=?  WHERE id = ?',estado,formatted_date,username,id)
    conn.commit()
    #flash('Estado alterado com sucesso',category='success')
    success = True
    return jsonify({'success': success})
    #return redirect(url_for('expedition_request_warehouse'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/change_state_warehousestate_yes/<int:id>', methods=['POST', 'GET'])
def change_state_warehousestate_yes(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    estado= 'Sim'
    estado_11= '11'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Dispatched]=?, [DispatchedStatusDate]=?,[DispatchedStatusOwner]=? , [status]=? WHERE id = ?',estado,formatted_date,username,estado_11,id)
    conn.commit()
    #flash('Estado alterado com sucesso',category='success')
    success = True
    return jsonify({'success': success})
    #return redirect(url_for('expedition_request_warehouse'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/fgw',methods=['GET'])
def fgw():
   try:
      cursor=conn.cursor()
      cursor.execute("SELECT TOP (1000) * FROM [LMS].[dbo].[MRPRequests]where Picking ='sim'and status ='6'  ORDER BY [id] DESC")
      GetIdTransportpicking = cursor.fetchall()

      cursor.execute("SELECT TOP (1000) req.*,gama.[Link]FROM [LMS].[dbo].[MRPRequests] req LEFT JOIN [LMS].[dbo].[MRPGamas] gama ON req.[ShipTo] = gama.[ShipTo] WHERE req.[Picking] = 'sim' AND req.[status] = '7' ORDER BY req.[id] DESC;")
      GetIdTransportPreparation = cursor.fetchall()

      cursor.execute("SELECT TOP (1000) * FROM [LMS].[dbo].[MRPRequests]where Picking ='sim' and status ='8' ORDER BY [id] DESC")
      GetIdTransportFinish = cursor.fetchall()

      return render_template('armazem/fgw.html',GetIdTransportpicking=GetIdTransportpicking,GetIdTransportPreparation=GetIdTransportPreparation,GetIdTransportFinish=GetIdTransportFinish)
   except Exception as e:
      return render_template('armazem/fgw.html')
  
#Change State Picking to Prepare
@app.route('/change_state_picking_to_prepare/<int:id>', methods=['POST', 'GET'])
def change_state_picking_to_prepare(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    estado= '7'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Status]=?, [PickingToPrepare]=?,[PickingToPrepareOwner]=?  WHERE id = ?',estado,formatted_date,username,id)
    conn.commit()
    flash('Estado alterado com sucesso',category='success')
    return redirect(url_for('fgw'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))
#Change State Prepare to Picking
@app.route('/change_state_prepare_to_picking/<int:id>', methods=['POST', 'GET'])
def change_state_prepare_to_picking(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    estado= '6'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Status]=?, [PickingToPrepare]=?,[PickingToPrepareOwner]=?  WHERE id = ?',estado,formatted_date,username,id)
    conn.commit()
    flash('Estado alterado com sucesso',category='success')
    return redirect(url_for('fgw'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

#Change State Prepare to Finish
@app.route('/change_state_prepare_to_finish/<int:id>', methods=['POST', 'GET'])
def change_state_prepare_to_finish(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    quantity=request.form['quantity']
    estado= '8'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Status]=?, [PrepareToFinish]=?,[PrepareToFinishOwner]=?, [QuantityPalletsFGW]=?  WHERE id = ?',estado,formatted_date,username,quantity,id)
    conn.commit()
    flash('Estado alterado com sucesso',category='success')
    return redirect(url_for('fgw'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

  #Change State Finish to Prepare
@app.route('/change_state_finish_to_prepare/<int:id>', methods=['POST', 'GET'])
def change_state_finish_to_prepare(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    estado= '7'
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M")
    cursor.execute('UPDATE [MRPRequests] set [Status]=?, [PrepareToFinish]=?,[PrepareToFinishOwner]=?  WHERE id = ?',estado,formatted_date,username,id)
    conn.commit()
    flash('Estado alterado com sucesso',category='success')
    return redirect(url_for('fgw'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/expedition_notifications',methods=['GET', 'POST'])
def expedition_notifications():
  try:
    today = date.today()
    year = today.strftime("%Y")
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    username=session['username']

    if 'filter_date_expedition' in session:
      filter_date = session['filter_date_expedition']
    else:
      filter_date = None

    if 'filter_internalcode_expedition' in session:
      filter_internal_code = session['filter_internalcode_expedition']
    else:
      filter_internal_code = None

    if 'filter_login_expedition' in session:
      filter_login = session['filter_login_expedition']
    else:
      filter_login = None

    if 'filter_type_expedition' in session:
      filter_type = session['filter_type_expedition']
    else:
      filter_type = None


    SP_MRPGetRequests = "Exec dbo.[MRPGetNotifications] @FilterDate=?,@FilterLogin=?,@Filtertype=?,@FilterInternalCode=?"
    cursor.execute(SP_MRPGetRequests,filter_date,filter_login,filter_type,filter_internal_code)
    MRPGetRequests = cursor.fetchall()

    SP_MRPGetRequestsNotificationsFilters = "Exec dbo.[MRPGetRequestsNotificationsFilters] @level=?"
    cursor.execute(SP_MRPGetRequestsNotificationsFilters,1)
    MRPGetNotificationsTypeFilter = cursor.fetchall()

    return render_template('/armazem/expedition_notifications.html',year=year,MRPGetRequests=MRPGetRequests,MRPGetNotificationsTypeFilter=MRPGetNotificationsTypeFilter)
  except Exception as e:
        flash('You need to login', category='error')
  return redirect(url_for('index'))



#Fitlers  Load Plan
@app.route('/expedition_notifications_filters', methods=['GET', 'POST'])
def expedition_notifications_filters():
  if 'filter_date_expedition' in request.form:
    session['filter_date_expedition']=request.form['filter_date_expedition']

  if 'filter_internalcode_expedition' in request.form:
    session['filter_internalcode_expedition']=request.form['filter_internalcode_expedition']

  if 'filter_login_expedition' in request.form:
    session['filter_login_expedition']=request.form['filter_login_expedition']

  if 'filter_type_expedition' in request.form:
    session['filter_type_expedition']=request.form['filter_type_expedition']

  flash('Added Filters ', category='warning')
  return redirect(url_for('expedition_notifications'))
#Remove Filters Transport Load Plan
@app.route('/expedition_notifications_remove_filters', methods=['GET', 'POST'])
def expedition_notifications_remove_filters():
  session.pop('filter_date_expedition', '')
  session.pop('filter_internalcode_expedition', '')
  session.pop('filter_login_expedition', '')
  session.pop('filter_type_expedition', '')
  flash('Filters removed', category='warning')
  return redirect(url_for('expedition_notifications'))


@app.route('/pre_load_fgw',methods=['GET'])
def pre_load_fgw():
   try:
      username=session['username']
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      sp_PreLoadFGWTable = "Exec dbo.[PreLoadFGWTable]"
      cursor.execute(sp_PreLoadFGWTable)
      GetIdTransportFinish = cursor.fetchall()
      

      sp_PreLoadFGWQueues = "Exec dbo.[PreLoadFGWQueues]"
      cursor.execute(sp_PreLoadFGWQueues)
      GetQueues = cursor.fetchall()      
      return render_template('armazem/pre_load_fgw.html',GetIdTransportFinish=GetIdTransportFinish,GetQueues=GetQueues)
   except Exception as e:
      return render_template('armazem/pre_load_fgw.html')


@app.route('/update_sosa_status', methods=['POST'])
def update_sosa_status():
    data = request.get_json()
    row_id = data['row_id']
    
    # Conectar ao banco de dados e atualizar o estado
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    cursor.execute('UPDATE MRPRequests SET SosaCopyState = ? WHERE id = ?', ('1', row_id))
    conn.commit()
    conn.close()
    return redirect(url_for('expedition_request_warehouse'))
    #return jsonify({'success': True})

#Change State Prepare to Finish
@app.route('/transfer_to_pre_load/<int:id>', methods=['POST', 'GET'])
def transfer_to_pre_load(id):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    if request.method == 'POST':
      palletquantity=request.form['palletquantity']
      fila=request.form['fila']
      sp_PreLoadFGWTransfer = "Exec dbo.[PreLoadFGWTransfer] @Id = ?, @PalletQuantity=?, @Queue=?, @username=?"
      cursor.execute(sp_PreLoadFGWTransfer,id,palletquantity,fila,username)
      conn.commit()
      flash('Estado alterado com sucesso',category='success')
    return redirect(url_for('pre_load_fgw'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/get_info_transfer_to_pre_load', methods=['GET'])
def get_info_transfer_to_pre_load():
    id = request.args.get('id')
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    cursor.execute("SELECT [InternalCode] FROM [MRPRequests]  where id = ?",(id))
    internal_code = cursor.fetchone()
    #cursor.execute("SELECT [CreationDate],[InternalCode],[Owner],[Reference],[Client],[Factory],[Reservation],[Invoice],[TotalPalletsQuantity],[PalletsQuantity],[Queue] FROM [MRPRequestsFollowUp]  where InternalCode = ?",(internal_code)) 
    cursor.execute("SELECT Queue,MAX(Reference) as Reference,MAX(Client) as Client,MAX(Factory) as Factory,MAX(Reservation) as Reservation,MAX(Invoice) as Invoice,avg(TotalPalletsQuantity) as TotalPalletsQuantitySum,SUM(PalletsQuantity) as PalletsQuantitySum FROM MRPRequestsFollowUp WHERE InternalCode = ? GROUP BY Queue",(internal_code))
    data = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    # Convertendo os resultados para uma lista de dicionários
    result_list = []
    for row in data:
        result_dict = dict(zip(column_names, row))
        result_list.append(result_dict)  
    return jsonify(result_list)

#teste para abrir noutra pagina
@app.route('/pre_load_fgw_info_by_intenal_code/<id>', methods=['POST', 'GET'])
def pre_load_fgw_info_by_intenal_code(id):
    return render_template("pre_load_fgw.html")




@app.route('/load',methods=['GET'])
def load():
   try:
      username=session['username']
      conn=pyodbc.connect(string_conexao)
      cursor=conn.cursor()
      sp_LoadFGWTable = "Exec dbo.[LoadFGWTable]"
      cursor.execute(sp_LoadFGWTable)
      GetAllLoadFGW = cursor.fetchall()

      return render_template('armazem/load.html',GetAllLoadFGW=GetAllLoadFGW)
   except Exception as e:
      return render_template('armazem/load.html')


@app.route('/begin_load/<string:internalcode>', methods=['POST', 'GET'])
def begin_load(internalcode):
  try:
    print(internalcode)
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    now = datetime.now()
    sp_WarehouseLoadBegin = "Exec dbo.[WarehouseLoadBegin] @InternalCode = ?"
    cursor.execute(sp_WarehouseLoadBegin,internalcode)
    conn.commit()
    return redirect(url_for('load'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))

@app.route('/end_load/<string:internalcode>', methods=['POST', 'GET'])
def end_load(internalcode):
  try:
    username=session['username']
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    now = datetime.now()
    sp_WarehouseLoadEnd = "Exec dbo.[WarehouseLoadEnd] @InternalCode = ?"
    cursor.execute(sp_WarehouseLoadEnd,internalcode)
    conn.commit()
    return redirect(url_for('load'))
  except Exception as e:
        flash('Erro login!', category='error')
  return redirect(url_for('index'))


@app.route('/get_info_to_guias_filas', methods=['GET'])
def get_info_to_guias_filas():
    internalcode = request.args.get('id')
    conn=pyodbc.connect(string_conexao)
    cursor=conn.cursor()
    cursor.execute("SELECT [InternalCode] FROM [MRPRequests]  where TransportID = ?",(internalcode))
    internal_code = cursor.fetchone()
    cursor.execute("SELECT Queue,MAX(Reference) as Reference,MAX(Client) as Client,MAX(Factory) as Factory,MAX(Reservation) as Reservation,MAX(Invoice) as Invoice,avg(TotalPalletsQuantity) as TotalPalletsQuantitySum,SUM(PalletsQuantity) as PalletsQuantitySum FROM MRPRequestsFollowUp WHERE InternalCode = ? GROUP BY Queue",(internal_code))
    data = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    # Convertendo os resultados para uma lista de dicionários
    result_list = []
    for row in data:
        result_dict = dict(zip(column_names, row))
        result_list.append(result_dict)  
    return jsonify(result_list)

@app.route('/viewPDF',methods=['GET'])
def viewPDF():
   try:
      return render_template('armazem/viewPDF.html')
   except Exception as e:
      return render_template('armazem/viewPDF.html')
if __name__ == "__main__":
    app.run(debug=True)

