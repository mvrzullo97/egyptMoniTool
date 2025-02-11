
import dbManager
import sys, os
from paramiko import AutoAddPolicy, SSHClient
# to do list
#   1) creare dbManager per connessione al DB - OK
#   2) estrarre dati da query su TJMD06_LNE ed inserirli in un dict
#   3) pingare gli IP estratti ed inserire esito in dict


# ping barriera ottica -> atterro su controller e pingo (vedi mail)
# 'not expected' in base alla tipoogia pista 
# 




def checkDirectPingMachine(ip) -> str :  
    res = os.popen(f"ping {ip}").read()
    if ("Richiesta scaduta." or "Ricevuti = 0") in res :
        print(f"Macchina (ip: {ip}) non raggiungibile!")
        return "F"
    else :
        print(f"Macchina (ip: {ip}) raggiunta!")
        return "T"

def checkPingMachineInSSH(ip_controller, ip_perfierica, user, pwd) : 
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        print("Avvio connessione in ssh")
        ssh_client.connect(hostname=ip_controller, username=user, password=pwd)
        stdin, stdout, stderr = ssh_client.exec_command(f'ping -c 4 {ip_perfierica}')
        res = stdout.read().decode()
        print(res)
        if  ("0 received," or "100% packet loss,") in res :
            print(f"Periferica (ip: {ip_perfierica}) non raggiungibile!")
            return "F"
        else :
            print(f"Periferica (ip: {ip_perfierica}) raggiunta!")
            return "T"
    finally:
        print("Chiudo connessione in ssh")
        ssh_client.close()


#piste = dbManager.select_data_from_tjmd06_lne(dbManager.connessione_db_gsegy06())

'''ris atteso: prima lista TTF seconda lista FFT'''
piste = (('1', 'K ', '10.151.48.1', '10.151.48.2', '10.151.44.3') , ('2', 'J ', '10.151.48.4', '10.151.48.5', '10.151.44.238'))

#piste = (('1', 'K ', '10.1.65.4', '10.1.64.132', '10.1.64.164'), ('2', 'J ', '10.1.65.8', '10.1.64.133', '10.1.64.165'))

dict_barriera_ottica = {"ip" : '172.16.0.10', "stato" : ''}
dict_antenna = {"ip" : '172.16.0.30', "stato" : ''}
dict_anpr_zona_1 = {"ip" : '172.16.0.21', "stato" : ''}
dict_anpr_zona_2 = {"ip" : '172.16.0.22', "stato" : ''}
dict_anpr_zona_3 = {"ip" : '172.16.0.22', "stato" : ''}
dict_bio = {"ip" : '172.16.0.2', "stato" : ''}
dict_stampante = {"ip" : '172.16.0.40', "stato" : ''}

dict_periferiche = {"barriera_ottica" : dict_barriera_ottica,
                   "antenna" : dict_antenna,
                   "anpr_zona_1" : dict_anpr_zona_1,
                    "anpr_zona_2" : dict_anpr_zona_2,
                    "anpr_zona_3" : dict_anpr_zona_3,
                    "bio" : dict_bio,
                    "stampante" : dict_stampante}

dict_controller = {"ip" : '', "stato" : ''}
dict_ipv = {"ip" : '', "stato" : ''}
dict_ip_tll_bth = {"ip" : '', "stato" : ''}


dict_pista = {"codice_pista" : '',
              "tipo_pista" : '',
              "ip_controller" : [dict_controller,  dict_periferiche], 
              "ip_ctv" : dict_ipv,
              "ip_tll_bth" : dict_ip_tll_bth}

dict_all_piste = {}


for j in range(0, len(piste)) : 

    dict_barriera_ottica = {"ip" : '172.16.0.10', "stato" : ''}
    dict_antenna = {"ip" : '172.16.0.30', "stato" : ''}
    dict_anpr_zona_1 = {"ip" : '172.16.0.21', "stato" : ''}
    dict_anpr_zona_2 = {"ip" : '172.16.0.22', "stato" : ''}
    dict_anpr_zona_3 = {"ip" : '172.16.0.22', "stato" : ''}
    dict_bio = {"ip" : '172.16.0.2', "stato" : ''}
    dict_stampante = {"ip" : '172.16.0.40', "stato" : ''}
    dict_periferiche = {"barriera_ottica" : dict_barriera_ottica, "antenna" : dict_antenna, "anpr_zona_1" : dict_anpr_zona_1, "anpr_zona_2" : dict_anpr_zona_2, "anpr_zona_3" : dict_anpr_zona_3, "bio" : dict_bio, "stampante" : dict_stampante}
    dict_controller = {"ip" : '', "stato" : ''}
    dict_ipv = {"ip" : '', "stato" : ''}
    dict_ip_tll_bth = {"ip" : '', "stato" : ''}
    dict_pista = {"codice_pista" : '', "tipo_pista" : '', "ip_controller" : [dict_controller,  dict_periferiche], "ip_ctv" : dict_ipv, "ip_tll_bth" : dict_ip_tll_bth}

    for i, key in enumerate(dict_pista) :

        info_pista = piste[j][i]
        codice_pista = piste[j][0]

        if key in ("ip_ctv", "ip_tll_bth"):

            dict_pista[key]["ip"] = info_pista
            dict_pista[key]["stato"] = checkDirectPingMachine(info_pista) # to do chiamare func

        elif key == "ip_controller" :

            dict_pista[key][0]["ip"] = info_pista
            dict_pista[key][0]["stato"] = checkDirectPingMachine(info_pista) # to do chiamare func
            
            for key in dict_periferiche :
                dict_periferiche[key]["stato"] = "NOT YET" # to do chiamamre func

        else :  
            dict_pista[key] = info_pista
    
    dict_all_piste["Pista_"+ codice_pista] = dict_pista.copy()

print(dict_all_piste)



sys.exit(1) 









#sys.exit(1)

# Si, No, NotExpected, NonVerificabile
# record_pista: c_lne	c_lne_typ	n_ip_con_cro	n_ip_ctv	n_ip_tll_bth
# record_pista: CODICE_LANE	TIPO_PISTA	CONTROLLER	AXIS_EXT	AXIS_INT
# se ping controller ok ma non ssh allora tutte le perifieriche 'Nonverificabile'

for j in range(0, len(piste)) : 
    
    dict_barriera_ottica = {"ip" : '', "stato" : ''}
    dict_antenna = {"ip" : '', "stato" : ''}
    dict_anpr_zona_1 = {"ip" : '', "stato" : ''}
    dict_anpr_zona_2 = {"ip" : '', "stato" : ''}
    dict_anpr_zona_3 = {"ip" : '', "stato" : ''}
    dict_bio = {"ip" : '', "stato" : ''}
    dict_stampante = {"ip" : '', "stato" : ''}

    dict_controller = {"barriera_ottica" : dict_barriera_ottica, "antenna" : dict_antenna, "anpr_zona_1" : dict_anpr_zona_1,
                    "anpr_zona_2" : dict_anpr_zona_2, "anpr_zona_3" : dict_anpr_zona_3, "bio" : dict_bio, "stampante" : dict_stampante}
    
    dict_pista = {"codice_pista" : '', "tipo_pista" : '', "ip_controller" : ['','', dict_controller], "ip_ctv" : dict_ipv, "ip_tll_bth" : dict_ip_tll_bth}   

    for i, key in enumerate(dict_pista) : 
        
        info_pista = piste[j][i]
        codice_pista = piste[j][0]

        if key in ("ip_ctv", "ip_tll_bth", "ip_controller") :
            
            dict_pista[key][0] = info_pista #ip
            status = checkDirectPingMachine(info_pista)
            dict_pista[key][1] = status
            
            if key == "ip_controller" : 
                print("status")

        else :  
            dict_pista[key] = info_pista

    dict_all_piste["Pista-"+ codice_pista] = dict_pista.copy()


print(dict_all_piste)












