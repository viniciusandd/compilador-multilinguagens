import psycopg2
import time
from threading import Thread
import subprocess
from difflib import SequenceMatcher

class Database():
    def __init__(self, ip, banco, usuario, senha):
        try:
            self.connection = psycopg2.connect(
                "dbname='%s' user='%s' host='%s' password='%s' port='5432'" % (banco, usuario, ip, senha))
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            print("Conexao com o banco de dados efetuada com sucesso")
        except Exception as e:
            print("Erro ao conectar no database: %s" % e)

    def query(self, sql):
        self.cursor.execute(sql)
        registros = self.cursor.fetchall()
        return registros

    def execute(self, sql):
        self.cursor.execute(sql)

fila_submissoes = []
ip        = input()
banco     = input()
usuario   = input()
senha     = input()
database  = Database(ip, banco, usuario, senha)
DIRETORIO = "/home/vinicius/Documentos/Python/compilador/arquivos/"

def BuscarSubmissoes():
    global fila_submissoes, database, bloqueio

    while True:
        time.sleep(5)

        fila_submissoes = database.query("SELECT ID, STATUS, LINGUAGEM_ID, PROBLEMA_ID FROM SUBMISSAO WHERE STATUS = 'Processando' ORDER BY ID")

        if len(fila_submissoes) > 0:
            print(fila_submissoes)
            for i in fila_submissoes:
                AtualizarStatus(i[0], "Compilando")
              # 1: ID, 2: linguagem, 3: problema
                Script(i[0], i[2], i[3])

def AtualizarStatus(id, status):
    sql = "UPDATE SUBMISSAO SET STATUS = '%s' WHERE ID = %s" % (status, id)
    database.execute(sql)

def AtualizarCompilacao(status, resposta, id):
    sql = "UPDATE SUBMISSAO SET STATUS = '%s', RESPOSTA = '%s' WHERE ID = %s" % (status, resposta, id)
    database.execute(sql)

def Script(arquivo, linguagem, problema):

    # Linguagens
    # 1 - C++
    # 2 - Python
    # 3 - Java

    entrada_1 = '%sentradas/1.in' % DIRETORIO
    entrada_2 = '%sentradas/2.in' % DIRETORIO
    entrada_3 = '%sentradas/3.in' % DIRETORIO
    saida_1   = '%ssaidas/1.out' % DIRETORIO
    saida_2   = '%ssaidas/2.out' % DIRETORIO
    saida_3   = '%ssaidas/3.out' % DIRETORIO

    if problema == 1:
        entrada = entrada_1
        saida = saida_1
    elif problema == 2:
        entrada = entrada_2
        saida = saida_2
    elif problema == 3:
        entrada = entrada_3
        saida = saida_3

    if linguagem == 1:
        compilar = "g++ %sfile%s.cpp -o %scompilacoes/file%s 2> " \
                       "%serros/erros_file%s.txt && echo 'Compilado com sucesso' || cat %serros/erros_file%s.txt" \
                   % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

        executar = "cd %scompilacoes/ && ./file%s < %s " \
                   "> %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

    elif linguagem == 2:
        compilar = "python -m py_compile %sfile%s.py 2> " \
                   "%serros/erros_file%s.txt && echo 'Compilado com sucesso' || " \
                   "cat %serros/erros_file%s.txt" % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

        #executar = "python3 %s__pycache__/file%s.cpython-35.pyc < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)
        executar = "python %sfile%s.pyc < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

    elif linguagem == 3:
	MudarClasseArquivosJava("file%s" % arquivo)

        compilar = "javac %sfile%s.java 2> " \
                   "%serros/erros_file%s.txt && echo 'Compilado com sucesso' || " \
                   "cat %serros/erros_file%s.txt" % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

        executar = "cd %s && java file%s < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

    compilacao = subprocess.check_output(compilar, shell=True)

    if compilacao.decode('utf-8').strip() == 'Compilado com sucesso':
        print("Compilado com sucesso: file%s" % arquivo)

	executou = True
        try:
		subprocess.check_output(executar, shell=True)
	except Exception as e:
	        print("Erro na execucao: %s" % e)
		executou = False

	if executou:
		resposta = CalcularPercentualDeErro("%scompilacoes/file%s.txt" % (DIRETORIO, arquivo), saida)
		if float(resposta) <= 0:
		    print("Resposta correta: file%s" % arquivo)
		    AtualizarCompilacao("Correta", "Solucao compilada e executada com sucesso", arquivo)
		else:
		    print("Resposta %s incorreta: file%s" % (resposta, arquivo))
		    AtualizarCompilacao("Incorreta", "Solucao incorreta: %s" % resposta + "%", arquivo)	
	else:
		print("Resposta 100% incorreta!")
		AtualizarCompilacao("Incorreta", "Solucao incorreta: 100.0%", arquivo)			



    else:
        print("Erro ao compilar: file%s" % arquivo)
        compilacao_frmt = compilacao.decode('utf-8')
        AtualizarCompilacao("Erro de compilacao", compilacao_frmt.replace("'", "|").
                            replace("/home/vinicius/Documentos/Python/compilador/arquivos/", ""), arquivo)

def CalcularPercentualDeErro(arquivo, saida):
    compilacao     = open(arquivo).read()
    saida_esperada = open(saida).read()
    percent        = SequenceMatcher(None, compilacao, saida_esperada)
    resposta       = percent.ratio() * 100
    erro           = "%.2f" % (100.0 - resposta)
    return erro

def MudarClasseArquivosJava(arquivo):
	f = open("%s%s.java" % (DIRETORIO, arquivo), 'r')
	retorno = f.read()
	f.close()

	f = open("%s%s.java" % (DIRETORIO, arquivo), 'w') 
	f.write(retorno.replace("public class Main", "public class %s" % arquivo))
	f.close()

def Main():

    buscar_submissoes = Thread(target=BuscarSubmissoes)
    buscar_submissoes.start()

Main()
