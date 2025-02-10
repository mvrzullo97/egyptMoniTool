
import dbManager
import sys, os

# to do list
#   1) creare dbManager per connessione al DB - OK
#   2) estrarre dati da query su TJMD06_LNE ed inserirli in un dict
#   3) pingare gli IP estratti ed inserire esito in dict


# ping barriera ottica -> atterro su controller e pingo (vedi mail)
# 'not expected' in base alla tipoogia pista 
# 

def checkDirectPingMachine(ip) -> str:  
    res = os.popen(f"ping {ip} ").read()
    if ("Richiesta scaduta." or "Ricevuti = 0") in res :
        print(f"Macchina con ip {ip} non raggiungibile!")
        return "F"
    else :
        print(f"Macchina con ip {ip} raggiunta!")
        return "F"


#piste = dbManager.select_data_from_tjmd06_lne(dbManager.connessione_db_gsegy06())


piste = (('1', 'K ', '10.151.48.238', '10.151.48.238', '10.151.44.238') , ('2', 'J ', '10.151.46.20', '10.151.48.238', '10.151.44.238'))

#piste = (('1', 'K ', '10.1.65.4', '10.1.64.132', '10.1.64.164'), ('2', 'J ', '10.1.65.8', '10.1.64.133', '10.1.64.165'))

dict_all_piste = {}

dict_controller = {"barriera_ottica" : ['172.16.0.10', ''],
                   "antenna" : ['172.16.0.30', ''],
                   "anpr_zona_1" : ['172.16.0.21', ''],
                    "anpr_zona_2" : ['172.16.0.22', ''],
                    "anpr_zona_3" : ['172.16.0.22', ''],
                    "bio" : ['172.16.0.2', ''],
                    "stampante" : ['172.16.0.40', '']}

dict_pista = {"codice_pista" : '',
              "tipo_pista" : '',
              "ip_controller" : ['','', dict_controller],  # ricordarsi di fare il copy
              "ip_ctv" : ['',''],
              "ip_tll_bth" : ['','']}



#sys.exit(1)

# Si, No, NotExpected, NonVerificabile
# record_pista: c_lne	c_lne_typ	n_ip_con_cro	n_ip_ctv	n_ip_tll_bth
# record_pista: CODICE_LANE	TIPO_PISTA	CONTROLLER	AXIS_EXT	AXIS_INT
# se ping controller ok ma non ssh allora tutte le perifieriche 'Nonverifficabie'

for j in range(0, len(piste)) :
    for i in range(0, (len(dict_pista)-1)) :
        ping_resp=''    
        if i in (3,4) : # ping macchina 
            res = checkDirectPingMachine(piste[j][i])
            print(res)
            index = list(dict_pista)[i]
            dict_pista[index][1] = res
        dict_pista[list(dict_pista)[i]] = piste[j][i]
        dict_all_piste["Pista-"+piste[j][0]] = dict_pista.copy()



print(dict_all_piste)















