import pyodbc

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-MGR8475\\SQLEXPRESS;"
    "DATABASE=imoveis;"
    "Trusted_Connection=yes;"
)

def salvar_imovel(imovel: dict):
    conn = pyodbc.connect(CONN_STR)
    cursor = conn.cursor()

    try:
        # 1. Verifica se o imóvel já existe no banco
        cursor.execute("SELECT id FROM fato_imoveis WHERE id = ?", imovel['id'])
        existe = cursor.fetchone()

        if existe:
            # 2. Se o imóvel JÁ EXISTE: Faz apenas a atualização do dia (UPDATE)
            sql_update = """
                UPDATE fato_imoveis 
                SET preco_atual = ?, 
                    preco_m2 = ?, 
                    area_m2 = ?, 
                    condominio = ?, 
                    iptu = ?, 
                    url_foto = ?, 
                    data_ultima_coleta = ?
                WHERE id = ?
            """
            cursor.execute(sql_update, 
                imovel['preco_atual'], imovel['preco_m2'], imovel['area_m2'], 
                imovel['condominio'], imovel['iptu'], imovel['url_foto'], imovel['data_coleta'],
                imovel['id']
            )
            
        else:
            # 3. Se o imóvel é NOVO: Salva a história completa (INSERT)
            sql_insert = """
                INSERT INTO fato_imoveis (
                    id, titulo, url, url_foto, tipo_negocio, tipo_imovel, 
                    bairro, cidade, estado, area_m2, quartos, banheiros, garagens, 
                    preco_original, preco_atual, preco_m2, condominio, iptu, 
                    data_primeira_coleta, data_ultima_coleta
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_insert,
                imovel['id'], imovel['titulo'], imovel['url'], imovel['url_foto'],
                imovel['tipo_negocio'], imovel['tipo_imovel'],
                imovel['bairro'], imovel['cidade'], imovel['estado'],
                imovel['area_m2'], imovel['quartos'], imovel['banheiros'], imovel['garagens'],
                imovel['preco_atual'], imovel['preco_atual'], imovel['preco_m2'], 
                imovel['condominio'], imovel['iptu'], 
                imovel['data_coleta'], imovel['data_coleta'] 
            )
        
        # Confirma a gravação no banco
        conn.commit()

    except pyodbc.Error as e:
        # Se der erro, desfaz a transação para não quebrar o banco
        conn.rollback()
        # Repassa o erro para o main.py imprimir o "✗ Erro" em vermelho
        raise e
        
    finally:
        # Fecha a conexão para não sobrecarregar o SQL Server
        conn.close()