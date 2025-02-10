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


# C_TLL_PLZ configurabile

def select_data_from_tjmd06_lne (connessione):
    
    try:
        conn = connessione_db_gsegy06()
        print("Connessione al DB avvenuta con successo!\n")
        cursor = conn.cursor()
        q = '''SELECT C_LNE, C_LNE_TYP, N_IP_CON_CRO, N_IP_CTV, N_IP_TLL_BTH 
            FROM JMDA.TJMD06_LNE WHERE C_TLL_PLZ = 1 ORDER BY C_LNE ASC'''
        cursor.execute(q)
        res = cursor.fetchmany(size=2)
        if res :
            print(f"Ho trovato {len(res)} records nella tabella TJMD06_LNE, inizio l'estrazione")
            return res
        else :     
            print("Dati estratti dalla tabella TJMD06_LNE")
    except psycopg2.Error as err:
        print(f"Errore durante l'esecuzione della Query: {err}")
    



