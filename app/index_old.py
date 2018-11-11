import psycopg2
import time
from threading import Thread
import subprocess

class Database():
    def __init__(self, banco, usuario, senha):
        try:
            self.connection = psycopg2.connect(
                "dbname='%s' user='%s' host='localhost' password='%s' port='5432'" % (banco, usuario, senha))
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            print("Conexão com o banco de dados efetuada com sucesso!")
        except:
            print("Erro ao conectar no database!")

    def query(self, sql):
        self.cursor.execute(sql)
        registros = self.cursor.fetchall()
        return registros

    def execute(self, sql):
        self.cursor.execute(sql)

fila_submissoes = []
database = Database()

def BuscarSubmissoes():
    global fila_submissoes, database

    while True:
        time.sleep(3)

        fila_submissoes = database.query("SELECT ID, STATUS, LINGUAGEM_ID FROM SUBMISSAO WHERE STATUS = 'PROCESSANDO' ORDER BY ID")

        if len(fila_submissoes) > 0:
            print(fila_submissoes)
            AtualizarStatusCompilando()

def AtualizarStatusCompilando():
    global fila_submissoes, database

    for i in fila_submissoes:
        sql = "UPDATE SUBMISSAO SET STATUS = 'COMPILANDO' WHERE ID = %s" %i[0]
        database.execute(sql)

def AtualizarStatus(id, status):
    sql = "UPDATE SUBMISSAO SET STATUS = '%s' WHERE ID = %s" % (status, id)
    database.execute(sql)

def AtualizarResposta(id, resposta):
    sql = "UPDATE SUBMISSAO SET RESPOSTA = '%s' WHERE ID = %s" % (resposta, id)
    database.execute(sql)

def Compilando():
    # O nome do arquivo será o ID do registro
    while True:
        time.sleep(3)
        for i in fila_submissoes:
            # print("ID: " + str(i[0]) + " | Linguagem: " + str(i[2]))
            Script(i[0], i[2])

def Script(arquivo, linguagem):

    # Linguagens
    # 1 - C++
    # 2 - Kotlin
    # 3 - Java
    # 4 - Python
    # 5 - Ruby

    if linguagem == 1:
        compilar = "g++ ../arquivos/file%s.cpp -o ../arquivos/compilacoes/file%s 2> " \
                       "../arquivos/erros/erros_file%s.txt && echo 'Compilado com sucesso!' || cat ../arquivos/erros/erros_file%s.txt" % (
                       arquivo, arquivo, arquivo, arquivo)

        executar = "./../arquivos/compilacoes/file%s" % arquivo

    elif linguagem == 2:
        compilar = "kotlinc ../arquivos/%s.kt -include-runtime -d ../arquivos/compilacoes/%s.jar 2> " \
                   "../arquivos/erros/erros_%s.txt && echo 'Compilado com sucesso!' || cat ../arquivos/erros/erros_%s.txt" % (
                       arquivo, arquivo, arquivo, arquivo)
    elif linguagem == 3:
        compilar = "javac ../arquivos/file%s.java 2> " \
                   "../arquivos/erros/erros_file%s.txt && echo 'Compilado com sucesso!' || " \
                   "cat ../arquivos/erros/erros_file%s.txt" % (arquivo, arquivo, arquivo)

        executar = "cd ../arquivos/ && java file%s" % arquivo

    elif linguagem == 4:
        compilar = "python -m py_compile ../arquivos/file%s.py 2> " \
                   "../arquivos/erros/erros_file%s.txt && echo 'Compilado com sucesso!' || " \
                   "cat ../arquivos/erros/erros_file%s.txt" % (arquivo, arquivo, arquivo)

        executar = "python3 ../arquivos/__pycache__/file%s.cpython-35.pyc" % arquivo

    elif linguagem == 5:
        pass

    compilacao = subprocess.check_output(compilar, shell=True)

    if compilacao.decode().strip() == 'Compilado com sucesso!':
        print("Compilado com sucesso: file%s" % arquivo)

        # Falta capturar os erros quando der falha de execução
        # o shell=True que mostra o erro no console
        sucesso = True
        try:
            execucao = subprocess.check_output(executar, shell=True)
        except Exception as e:
            sucesso = False
            print(e)

        if sucesso:
            print("Executado com sucesso: file%s" % arquivo)
            AtualizarResposta(arquivo, execucao.decode())
            AtualizarStatus(arquivo, "CORRETA")
        else:
            print("Falha ao executar: file%s" % arquivo)
            AtualizarResposta(arquivo, 'Erro na execução!')
            AtualizarStatus(arquivo, "FALHA NA EXECUÇÃO")
    else:
        print("Erro ao compilar: file%s" % arquivo)
        compilacao_frmt = compilacao.decode()
        AtualizarResposta(arquivo, compilacao_frmt.replace("'", "´"))
        AtualizarStatus(arquivo, "INCORRETA")

def Main():
    buscar_submissoes = Thread(target=BuscarSubmissoes)
    buscar_submissoes.start()

    compilando = Thread(target=Compilando)
    compilando.start()

Main()