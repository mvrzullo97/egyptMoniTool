
import dbManager
import sys, os, subprocess
from paramiko import AutoAddPolicy, SSHClient


def checkDirectPingMachine(ip) -> str :  
    res = os.popen(f"ping {ip}").read()
    if ("Trasmessi = 4") and ("Ricevuti = 4") and ("Persi = 0") in res :
        if ("TTL scaduto durante il passaggio.") in res:
            print(f"Macchina (ip: {ip}) non raggiungibile!")
            return "F"
        print(f"Macchina (ip: {ip}) raggiunta!")
        return "T"
    else :
        print(f"Macchina (ip: {ip}) non raggiungibile!")
        return "T"

def checkPingPerifericheInSSH(ip_controller, dict_periferiche, user, pwd) : 
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    str=''
    try:
        print(f"\nAvvio connessione in ssh ({ip_controller})\n")
        ssh_client.connect(hostname=ip_controller, username=user, password=pwd)
        
        for key in dict_periferiche :

            ip_periferica = dict_periferiche[key]["ip"]
            stdin, stdout, stderr = ssh_client.exec_command(f'ping -c 4 {ip_periferica}')
            res = stdout.read().decode()
#            print(res)
            if ("4 packets transmitted, 4 received, 0% packet loss,") in res :
                if("Time to live exceeded") in res :
                    print(f"Periferica {key} (ip: {ip_periferica}) non raggiungibile causa TTL scaduta!")
                    #dict_periferiche[key]["stato"] = "F"ù
                    str+="F"
                else :
                    print(f"Periferica {key} (ip: {ip_periferica}) raggiunta!")
                    str+="T"    
            else :
                print(f"Periferica {key} (ip: {ip_periferica}) non raggiungibile!")
                str+="F"
                    #dict_periferiche[key]["stato"] = "T"
    finally : 
        print(f"\nChiudo connessione in ssh ({ip_controller})\n")
        ssh_client.close()
        return str


#piste = dbManager.select_data_from_tjmd06_lne(dbManager.connessione_db_gsegy06())

'''ris atteso: prima lista TFT seconda lista FFT'''
#piste_VERO = (('1', 'K ', '10.1.65.4', '10.1.64.132', '10.1.64.164'), ('2', 'J ', '10.1.65.8', '10.1.64.133', '10.1.64.165'))


# ris atteso = TFT - TTF
piste = (('1', 'K ', '10.1.65.4', '10.1.123.132', '10.1.64.164'), ('2', 'J ', '10.1.65.8', '10.1.64.133', '10.1.123.165'))

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



user="root"
pwd="Movyon.2022!"
ip_controller = '10.1.65.4'

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

    codice_pista = piste[j][0]
    print(f"Inizio l'analisi della Pista_{codice_pista}...\n")

    for i, key in enumerate(dict_pista) :

        info_pista = piste[j][i]
        
        if key in ("ip_ctv", "ip_tll_bth"):

            dict_pista[key]["ip"] = info_pista
            dict_pista[key]["stato"] = checkDirectPingMachine(info_pista) 

        elif key == "ip_controller" :
            ip_controller = info_pista
            dict_pista[key][0]["ip"] = info_pista
            dict_pista[key][0]["stato"] = checkDirectPingMachine(info_pista)
            
            stati_periferiche = checkPingPerifericheInSSH(ip_controller, dict_periferiche, user, pwd)

            for x, key in enumerate(dict_periferiche) :
                ip_periferica = dict_periferiche[key]["ip"]
                dict_periferiche[key]["stato"] = stati_periferiche[x]

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












