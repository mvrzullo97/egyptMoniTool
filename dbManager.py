import psycopg2, sys

def connessione_db_gsegy06 (db_name, user, pwd, ip, port) : 
    try:
        db_connection = psycopg2.connect(
            dbname = db_name,
            user = user,
            password = pwd,
            host = ip,
            port = port
        )
        print(f"\nConnessione al Database '{db_name}' avvenuta con successo...")
        return db_connection
    
    except Exception as err:
        print(f"Errore: {err}")
        sys.exit(1)

def select_data_from_tjmd06_lne (db_connection, stazione, rete):
    try:
        cursor = db_connection.cursor()
        q = f'''SELECT C_LNE, TRIM(C_LNE_TYP), N_IP_CON_CRO, N_IP_CTV, N_IP_TLL_BTH 
            FROM JMDA.TJMD06_LNE WHERE C_NET = {rete} AND C_TLL_PLZ = {stazione} ORDER BY C_LNE ASC'''
        cursor.execute(q)
        res = cursor.fetchmany(size=1)
        #res = cursor.fetchall()
        if res :
            print(f"---> Ho trovato {len(res)} record nella tabella TJMD06_LNE aventi rete {rete} e stazione {stazione}, li estraggo...")
            return res
    except psycopg2.Error as err:
        print(f"Errore durante l'esecuzione della Query: {err}")
        sys.exit(1)
    finally:
        cursor.close()
        db_connection.close()


