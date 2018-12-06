import psycopg2
import time
from threading import Thread
import subprocess
from difflib import SequenceMatcher

class Database():
    def __init__(self, banco, usuario, senha):
        try:
            self.connection = psycopg2.connect(
                "dbname='%s' user='%s' host='localhost' password='%s' port='5432'" % (banco, usuario, senha))
            self.connection.autocommit = True
            self.cursor = self.connection.cursor()
            print("Conexao com o banco de dados efetuada com sucesso")
        except:
            print("Erro ao conectar no database!")

    def query(self, sql):
        self.cursor.execute(sql)
        registros = self.cursor.fetchall()
        return registros

    def execute(self, sql):
        self.cursor.execute(sql)

fila_submissoes = []
banco     = input("Informe o nome do banco de dados: ")
usuario   = input("Informe o nome do usuario para logar no database: ")
senha     = input("Informe sua senha para logar no database: ")
database  = Database(banco, usuario, senha)
DIRETORIO = "/home/vinicius/Documentos/Python/compilador-multilinguagens/arquivos/"

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

    entrada_1001 = '%sentradas/1001.in' % DIRETORIO
    entrada_1002 = '%sentradas/1002.in' % DIRETORIO
    entrada_1003 = '%sentradas/1003.in' % DIRETORIO
    saida_1001   = '%ssaidas/1001.out' % DIRETORIO
    saida_1002   = '%ssaidas/1002.out' % DIRETORIO
    saida_1003   = '%ssaidas/1003.out' % DIRETORIO

    if problema == 1001:
        entrada = entrada_1001
        saida = saida_1001
    elif problema == 1002:
        entrada = entrada_1002
        saida = saida_1002
    elif problema == 1003:
        entrada = entrada_1003
        saida = saida_1003

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

        executar = "python3 %s__pycache__/file%s.cpython-35.pyc < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)
        #executar = "python %sfile%s.pyc < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

    elif linguagem == 3:

        MudarClasseArquivosEmJava("file%s" % arquivo)

        compilar = "javac %sfile%s.java 2> " \
                   "%serros/erros_file%s.txt && echo 'Compilado com sucesso' || " \
                   "cat %serros/erros_file%s.txt" % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

        executar = "cd %s && java file%s < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

    compilacao = subprocess.check_output(compilar, shell=True)

    if compilacao.decode('utf-8').strip() == 'Compilado com sucesso':
        print("Compilado com sucesso: file%s" % arquivo)

        #Try adicionado: Resolveu a questao do arquivo com erros de execução no PYTHON
        executou = True
        try:
            subprocess.check_output(executar, shell=True)
        except Exception as e:
            print("Erro na execução: %s" % e)
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
                            replace("/home/vinicius/Documentos/Python/compilador-multilinguagens/arquivos/", ""), arquivo)

def CalcularPercentualDeErro(arquivo, saida):
    compilacao     = open(arquivo).read()
    saida_esperada = open(saida).read()
    percent        = SequenceMatcher(None, compilacao, saida_esperada)
    resposta       = percent.ratio() * 100
    erro           = "%.2f" % (100.0 - resposta)
    return erro

def MudarClasseArquivosEmJava(arquivo):

    print("Conteúdo do arquivo: %s" % arquivo)

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
