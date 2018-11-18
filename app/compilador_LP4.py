import psycopg2
import time
from threading import Thread
import subprocess
from difflib import SequenceMatcher
from threading import Lock
import random

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

banco   = input("Informe o nome do banco de dados: ")
usuario = input("Informe o nome do usuário para logar no database: ")
senha   = input("Informe sua senha para logar no database: ")
fila_submissoes = []
database = Database(banco, usuario, senha)
DIRETORIO = "/home/vinicius/Documentos/Python/compilador-multilinguagens/arquivos/"
bloqueio = Lock()

def BuscarSubmissoes():
    global fila_submissoes, database, bloqueio

    while True:
        bloqueio.acquire()

        fila_submissoes = database.query("SELECT ID, STATUS, LINGUAGEM_ID, PROBLEMA_ID FROM SUBMISSAO WHERE STATUS = 'Processando' ORDER BY ID")
        if len(fila_submissoes) > 0:
            print(fila_submissoes)
            for i in fila_submissoes:
                AtualizarStatus(i[0], "Compilando")
                # 1: ID, 2: linguagem, 3: problema
                Script(i[0], i[2], i[3])

        bloqueio.release()

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
            AtualizarCompilacao("Correta", "Solução compilada e executada com sucesso!", arquivo)
        else:
            print("Resposta %s incorreta: file%s" % (resposta, arquivo))
            AtualizarCompilacao("Incorreta", "Solução incorreta: %s" % resposta + "%", arquivo)

    else:
        print("Erro ao compilar: file%s" % arquivo)
        compilacao_frmt = compilacao.decode()
        AtualizarCompilacao("Erro de compilação", compilacao_frmt.replace("'", "´").
                            replace("/home/vinicius/Documentos/Python/compilador-multilinguagens/arquivos/", ""), arquivo)

def CalcularPercentualDeErro(arquivo, saida):
    compilacao     = open(arquivo).read()
    saida_esperada = open(saida).read()
    percent        = SequenceMatcher(None, compilacao, saida_esperada)
    resposta       = percent.ratio() * 100
    erro           = "%.2f" % (100.0 - resposta)
    return erro

def Bot():
    j = 0
    while j < 500:

        j = j + 1

        bloqueio.acquire()

        print(" ---------------  CRIANDO UM ARQUIVO NOVO --------------- ")

        sql = "SELECT MAX(ID) FROM SUBMISSAO"
        retorno = database.query(sql)

        print(retorno)

        max_id = retorno[0][0]

        if not max_id:
            max_id = 0

        id = max_id + 1

        print("ID ATUAL: %s" % id)

        codigos_corretos_cpp = \
            [{1001: """
#include <iostream>
using namespace std;
int main() {
  int a, b;
  cin >> a >> b;
  cout << "X = " << a + b << endl;
  return 0;
}    
        """},
             {1002: """
#include <iostream>
#include <iomanip>
#include <cmath>
using namespace std;
int main () {
  cout << fixed << setprecision(4);
  double pi=3.14159, raio, area;
  cin >> raio;
  area = (pi * (pow(raio,2)));
  cout << "A=" << area << endl;
  return 0;
}    
        """},
             {1003: """
#include <iostream>
using namespace std;
int main() {
  int a, b;
  cin >> a >> b;
  cout << "SOMA = " << a + b << endl;
  return 0;
}    
        """}]

        codigos_errados_cpp = \
            [{1001: """
#include <iostream>
using namespace std;
int main() {
  int a, b;
  cin >> a >> b;
  cout << "X=" << a + b << endl;
  return 0;
}    
        """},
             {1002: """
#include <iostream>
#include <iomanip>
#include <cmath>
using namespace std;
int main () {
  cout << fixed << setprecision(4);
  double pi=3.14159, raio, area;
  cin >> raio;
  area = (pi * (pow(raio,2)));
  cout << "AREA=" << area << endl;
  return 0;
}    
        """},
             {1003: """
#include <iostream>
using namespace std;
int main() {
  int a, b;
  cin >> a >> b;
  cout << "SOMA = " << a + b << endl
  return 0;
}    
        """}]

        codigos_corretos_python = \
            [
                {1001: """
x = int(input())
y = int(input())
soma = x + y
print("X = %s" % soma)        
"""},
        {1002: """
pi = 3.14159
raio = float(input())
area = pi * (raio * raio)
print("A=%.4f" % area)        
        """},
                {1003: """
x = int(input())
y = int(input())
soma = x + y
print("SOMA = %s" % soma)          
        """}]

        codigos_errados_python = \
            [
                {1001: """
x = int(input())
y = int(input())
soma = x + y
print("Y = %s" % soma)        
        """},
                {1002: """
pi = 3.14159
raio = float(input())
area = pi * (raio * raio)
print("AREA=%.4f" % area)        
        """},
                {1003: """
x = int(input())
y = int(input())
soma = x + y
    print("SOMA = %s" % soma)          
        """}]

        codigos_corretos_java = \
            [
                {1001: """
import java.util.Scanner;
public class file%s { 
   public static void main(String []args) {
     Scanner sc = new Scanner(System.in);
     int x, y, soma;
     x = sc.nextInt();
     y = sc.nextInt();
     soma = x + y;
     System.out.println("X = " + soma);
   }
}    
            """ % id},
                {1002: """
import java.util.Scanner;
import java.util.Locale;
import java.text.DecimalFormat;
public class file%s {
   public static void main(String []args) {
     Scanner sc = new Scanner(System.in);
     sc.useLocale(Locale.ENGLISH);
     double raio, pi=3.14159, area;
     raio = sc.nextDouble();
     area = pi * (raio * raio);
     DecimalFormat formato = new DecimalFormat("#.####");
     String valor = String.valueOf(formato.format(area));
     valor = valor.replace(",",".");
     System.out.println("A=" + valor);
   }
}    
            """ % id},
                {1003: """
import java.util.Scanner;
public class file%s { 
   public static void main(String []args) {
     Scanner sc = new Scanner(System.in);
     int x, y, soma;
     x = sc.nextInt();
     y = sc.nextInt();
     soma = x + y;
     System.out.println("SOMA = " + soma);
   }
}    
            """ % id}
            ]

        codigos_errados_java = \
            [
                {1001: """
import java.util.Scanner;
public class file%s { 
   public static void main(String []args) {
     Scanner sc = new Scanner(System.in);
     int x, y, soma;
     x = sc.nextInt();
     y = sc.nextInt();
     soma = x + y;
     System.out.println("X = " + soma)
   }
}    
            """ % id},
                {1002: """
import java.util.Scanner;
import java.util.Locale;
import java.text.DecimalFormat;
public class file%s {
   public static void main(String []args) {
     Scanner sc = new Scanner(System.in);
     sc.useLocale(Locale.ENGLISH);
     double raio, pi=3.14159, area;
     raio = sc.nextDouble();
     area = pi * (raio * raio);
     DecimalFormat formato = new DecimalFormat("#.####");
     String valor = String.valueOf(formato.format(area));             
     System.out.println("A=" + valor);
   }
}    
            """ % id},
                {1003: """
import java.util.Scanner;
public class file%s { 
   public static void main(String []args) {
     Scanner sc = new Scanner(System.in);
     int x, y, soma;
     x = sc.nextInt();
     y = sc.nextInt();
     soma = x + y;
     System.out.println("soma=" + soma);
   }
}    
            """ % id}
            ]

        registro = random.randrange(0, 3)  # 0 -> 1001, 1 -> 1002, 2 -> 1003
        linguagem = random.randrange(1, 4)
        correto_errado = random.randrange(1, 3)

        print("LINGUAGEM: %s" % linguagem)
        print("CORRETO OU ERRADO: %s" % correto_errado)

        if registro == 0:
            problema = 1001
        elif registro == 1:
            problema = 1002
        elif registro == 2:
            problema = 1003

        print("PROBLEMA: %s" % problema)

        if linguagem == 1:  # C++
            if correto_errado == 1:
                codigo = codigos_corretos_cpp[registro][problema]
            elif correto_errado == 2:
                codigo = codigos_errados_cpp[registro][problema]

            ext = ".cpp"

        elif linguagem == 2:  # Python
            if correto_errado == 1:
                codigo = codigos_corretos_python[registro][problema]
            elif correto_errado == 2:
                codigo = codigos_errados_python[registro][problema]

            ext = ".py"

        elif linguagem == 3:  # Java
            if correto_errado == 1:
                codigo = codigos_corretos_java[registro][problema]
            elif correto_errado == 2:
                codigo = codigos_errados_java[registro][problema]

            ext = ".java"

        #print(codigo)

        comando_criar = "touch %sfile%s%s && echo '%s' > %sfile%s%s" % (DIRETORIO, id, ext, codigo, DIRETORIO, id, ext)
        #print(comando_criar)

        subprocess.check_output(comando_criar, shell=True)

        sql = "INSERT INTO SUBMISSAO (ID, STATUS, RESPOSTA, LINGUAGEM_ID, PROBLEMA_ID) VALUES (%s, 'Processando', '', %s, %s)" \
              % (id, linguagem, problema)
        #print(sql)
        database.execute(sql)

        bloqueio.release()

def Main():

    buscar_submissoes = Thread(target=BuscarSubmissoes)
    buscar_submissoes.start()

    bot = Thread(target=Bot)
    bot.start()

Main()