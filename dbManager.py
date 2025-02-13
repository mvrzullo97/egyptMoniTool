import psycopg2

def connessione_db_gsegy06 () : 
    try:
        connessione = psycopg2.connect(
            dbname = "gsegy06",
            user = "jread",
            password = "jread",
            host = "10.1.12.4",
            port = "5432"
        )
        return connessione
    
    except Exception as err:
        print(f"Errore: {err}")


# C_TLL_PLZ configurabile in futuro
def select_data_from_tjmd06_lne (connessione):
    
    try:
        conn = connessione_db_gsegy06()
        print("\nConnessione al DB avvenuta con successo!")
        cursor = conn.cursor()
        q = '''SELECT C_LNE, TRIM(C_LNE_TYP), N_IP_CON_CRO, N_IP_CTV, N_IP_TLL_BTH 
            FROM JMDA.TJMD06_LNE WHERE C_TLL_PLZ = 1 ORDER BY C_LNE ASC'''
        cursor.execute(q)
        #res = cursor.fetchmany(size=2)
        res = cursor.fetchall()
        if res :
            print(f"Ho trovato {len(res)} record nella tabella TJMD06_LNE, li estraggo...")
            return res
    except psycopg2.Error as err:
        print(f"Errore durante l'esecuzione della Query: {err}")
    



