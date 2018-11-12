import psycopg2

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

def Main():
    banco   = input("Informe o nome do banco de dados: ")
    usuario = input("Informe o nome do usuário para logar no database: ")
    senha   = input("Informe sua senha para logar no database: ")
    database = Database(banco, usuario, senha)

    while True:
        fila_submissoes = database.query(
            "SELECT ID, STATUS, LINGUAGEM_ID, PROBLEMA_ID FROM SUBMISSAO WHERE STATUS = 'Processando' ORDER BY ID"
        )

        for i in fila_submissoes:

            pass


Main()