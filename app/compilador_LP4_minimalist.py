import psycopg2
import subprocess
from difflib import SequenceMatcher

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

DIRETORIO = "/home/vinicius/Documentos/Python/compilador-multilinguagens/arquivos/"


def CalcularPercentualDeErro(arquivo, saida):
    compilacao     = open(arquivo).read()
    saida_esperada = open(saida).read()
    percent        = SequenceMatcher(None, compilacao, saida_esperada)
    resposta       = percent.ratio() * 100
    erro           = "%.2f" % (100.0 - resposta)
    return erro

def Main():
    banco   = input("Informe o nome do banco de dados: ")
    usuario = input("Informe o nome do usuário para logar no database: ")
    senha   = input("Informe sua senha para logar no database: ")
    database = Database(banco, usuario, senha)

    while True:
        fila_submissoes = []

        fila_submissoes = database.query(
            "SELECT ID, STATUS, LINGUAGEM_ID, PROBLEMA_ID FROM SUBMISSAO WHERE STATUS = 'Processando' ORDER BY ID"
        )

#        if len(fila_submissoes) == 0:
#            print("Nenhuma submissão encontrada, o compilador vai dormir por 10 segundos!")
#            time.sleep(10)

        for i in fila_submissoes:
            arquivo   = i[0]
            linguagem = i[2]
            problema  = i[3]

            # Linguagens
            # 1 - C++
            # 2 - Python
            # 3 - Java

            entrada_1001 = '%sentradas/1001.in' % DIRETORIO
            entrada_1002 = '%sentradas/1002.in' % DIRETORIO
            entrada_1003 = '%sentradas/1003.in' % DIRETORIO
            saida_1001   = '%ssaidas/1001.out'  % DIRETORIO
            saida_1002   = '%ssaidas/1002.out'  % DIRETORIO
            saida_1003   = '%ssaidas/1003.out'  % DIRETORIO

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
                               "%serros/erros_file%s.txt && echo 'Compilado com sucesso!' || cat %serros/erros_file%s.txt" \
                           % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

                executar = "cd %scompilacoes/ && ./file%s < %s " \
                           "> %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

            elif linguagem == 2:
                compilar = "python -m py_compile %sfile%s.py 2> " \
                           "%serros/erros_file%s.txt && echo 'Compilado com sucesso!' || " \
                           "cat %serros/erros_file%s.txt" % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

                executar = "python3 %s__pycache__/file%s.cpython-35.pyc < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

            elif linguagem == 3:
                compilar = "javac %sfile%s.java 2> " \
                           "%serros/erros_file%s.txt && echo 'Compilado com sucesso!' || " \
                           "cat %serros/erros_file%s.txt" % (DIRETORIO, arquivo, DIRETORIO, arquivo, DIRETORIO, arquivo)

                executar = "cd %s && java file%s < %s > %scompilacoes/file%s.txt" % (DIRETORIO, arquivo, entrada, DIRETORIO, arquivo)

            compilacao = subprocess.check_output(compilar, shell=True)

            if compilacao.decode().strip() == 'Compilado com sucesso!':
                print("Compilado com sucesso: file%s" % arquivo)

                subprocess.check_output(executar, shell=True)

                resposta = CalcularPercentualDeErro("%scompilacoes/file%s.txt" % (DIRETORIO, arquivo), saida)
                if float(resposta) <= 0:
                    print("Resposta correta: file%s" % arquivo)
                    sql = "UPDATE SUBMISSAO SET STATUS = 'Correta', RESPOSTA = 'Solução compilada e executada com sucesso!' " \
                          "WHERE ID = %s" % arquivo
                    database.execute(sql)
                else:
                    print("Resposta %s incorreta: file%s" % (resposta, arquivo))
                    sql = "UPDATE SUBMISSAO SET STATUS = 'Incorreta',  RESPOSTA = 'Solução incorreta: %s' WHERE ID = %s" % (resposta + "%", arquivo)
                    database.execute(sql)

            else:
                print("Erro ao compilar: file%s" % arquivo)
                compilacao_frmt = compilacao.decode()
                sql = "UPDATE SUBMISSAO SET STATUS = 'Erro de compilação', RESPOSTA = '%s' WHERE ID = %s" \
                      % (compilacao_frmt.replace("'", "´").
                                    replace("/home/vinicius/Documentos/Python/compilador-multilinguagens/arquivos/", ""), arquivo)
                database.execute(sql)

Main()