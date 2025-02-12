
import dbManager
import sys, os, time, math 
from paramiko import AutoAddPolicy, SSHClient
from datetime import datetime
import openpyxl




# usare titoli della mail


def checkPingMachine(ip) -> str :  
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

def checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista) -> str :
    
    stati_periferiche='' 
    
    for key in dict_periferiche :
        
        if key == "anpr_zona_2" and tipo_pista != 'I' :
            stati_periferiche+="N"
            print("SONO NEL PRIMO IF: key == anpr_zona_2 and tipo_pista != 'I'")
        elif key == "anpr_zona_3" and tipo_pista in ('H','I') :
             stati_periferiche+="N"
             print("SONO NEL SECONDO IF: key == anpr_zona_3 and tipo_pista in ('H','I')")
        elif key == "WIM" and tipo_pista != 'K':
             stati_periferiche+="N"
             print("SONO NEL TERZO IF: key == WIM and tipo_pista != K:")
        else :          
            ip_periferica = dict_periferiche[key]["ip"]
            stdin, stdout, stderr = ssh_client.exec_command(f'ping -c 4 {ip_periferica}')
            res = stdout.read().decode()

            if ("4 packets transmitted, 4 received, 0% packet loss,") in res :
                if("Time to live exceeded") in res :
                    print(f"Periferica {key} (ip: {ip_periferica}) non raggiungibile causa TTL scaduta!")
                    stati_periferiche+="F"
                else :
                    print(f"Periferica {key} (ip: {ip_periferica}) raggiunta!")
                    stati_periferiche+="T"    
            else :
                print(f"Periferica {key} (ip: {ip_periferica}) non raggiungibile!")
                stati_periferiche+="F"
        
    return stati_periferiche
    
def startSessionInSSH(ip_controller, dict_periferiche, user, pwd, tipo_pista) : 
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    stati_periferiche='' 
    try:
        print(f"Avvio connessione in ssh ({ip_controller})")
        ssh_client.connect(hostname=ip_controller, username=user, password=pwd)
        
        stati_periferiche = checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista)
        
    finally : 
        print(f"Chiudo connessione in ssh ({ip_controller})")
        ssh_client.close()
        return stati_periferiche


#piste = dbManager.select_data_from_tjmd06_lne(dbManager.connessione_db_gsegy06())

'''ris atteso: prima lista TFT seconda lista FFT'''
#piste_VERO = (('1', 'K ', '10.1.65.4', '10.1.64.132', '10.1.64.164'), ('2', 'J ', '10.1.65.8', '10.1.64.133', '10.1.64.165'))


# ris atteso = TFT - TTF
piste = (('1', 'K', '10.1.65.4', '10.1.123.132', '10.1.64.164'), ('2', 'I ', '10.1.65.8', '10.1.64.133', '10.1.123.165'))

dict_barriera_ottica = {"ip" : '172.16.0.10', "stato" : ''}
dict_antenna = {"ip" : '172.16.0.30', "stato" : ''}
dict_anpr_zona_1 = {"ip" : '172.16.0.21', "stato" : ''}
dict_anpr_zona_2 = {"ip" : '172.16.0.22', "stato" : ''}
dict_anpr_zona_3 = {"ip" : '172.16.0.22', "stato" : ''}
dict_bio = {"ip" : '172.16.0.2', "stato" : ''}
dict_stampante = {"ip" : '172.16.0.40', "stato" : ''}
dict_fare_display = {"ip" : '172.16.0.60', "stato" : ''}
dict_WIM = {"ip" : '172.16.0.70', "stato" : ''}

dict_periferiche = {"barriera_ottica" : dict_barriera_ottica,
                   "antenna" : dict_antenna,
                   "anpr_zona_1" : dict_anpr_zona_1,
                    "anpr_zona_2" : dict_anpr_zona_2,
                    "anpr_zona_3" : dict_anpr_zona_3,
                    "bio" : dict_bio,
                    "stampante" : dict_stampante,
                    "fare_display" : dict_fare_display,
                    "WIM" : dict_WIM}

dict_controller = {"ip" : '', "stato" : ''}
dict_axis_external = {"ip" : '', "stato" : ''}
dict_axis_internal = {"ip" : '', "stato" : ''}


dict_pista = {"codice_pista" : '',
              "tipo_pista" : '',
              "ip_controller" : [dict_controller,  dict_periferiche], 
              "dict_axis_external" : dict_axis_external,
              "dict_axis_internal" : dict_axis_internal}

dict_all_piste = {}

user="root"
pwd="Movyon.2022!"
ip_controller = '10.1.65.4'
inizio_esecuzione = datetime.now().replace(microsecond=0)
print(f"\nInizio esecuzione: {inizio_esecuzione}\n")

for j in range(0, len(piste)) : 

    dict_barriera_ottica = {"ip" : '172.16.0.10', "stato" : ''}
    dict_antenna = {"ip" : '172.16.0.30', "stato" : ''}
    dict_anpr_zona_1 = {"ip" : '172.16.0.21', "stato" : ''}
    dict_anpr_zona_2 = {"ip" : '172.16.0.22', "stato" : ''}
    dict_anpr_zona_3 = {"ip" : '172.16.0.22', "stato" : ''}
    dict_bio = {"ip" : '172.16.0.2', "stato" : ''}
    dict_stampante = {"ip" : '172.16.0.40', "stato" : ''}
    dict_fare_display = {"ip" : '172.16.0.60', "stato" : ''}
    dict_WIM = {"ip" : '172.16.0.70', "stato" : ''}
    dict_periferiche = {"barriera_ottica" : dict_barriera_ottica, "antenna" : dict_antenna, "anpr_zona_1" : dict_anpr_zona_1, "anpr_zona_2" : dict_anpr_zona_2, "anpr_zona_3" : dict_anpr_zona_3, "bio" : dict_bio, "stampante" : dict_stampante, "fare_display" : dict_fare_display, "WIM" : dict_WIM}
    dict_controller = {"ip" : '', "stato" : ''}
    dict_axis_external = {"ip" : '', "stato" : ''}
    dict_axis_internal = {"ip" : '', "stato" : ''}
    dict_pista = {"codice_pista" : '', "tipo_pista" : '', "ip_controller" : [dict_controller,  dict_periferiche], "dict_axis_external" : dict_axis_external, "dict_axis_internal" : dict_axis_internal}

    codice_pista = int(piste[j][0])
    tipo_pista = piste[j][1]
    print(f"Inizio l'analisi della Pista_{codice_pista}...\n")

    for i, key in enumerate(dict_pista) :

        info_pista = piste[j][i] 
        if key in ("dict_axis_external", "dict_axis_internal") :

            dict_pista[key]["ip"] = info_pista
            dict_pista[key]["stato"] = checkPingMachine(info_pista) 

        elif key == "ip_controller" :
            ip_controller = info_pista
            dict_pista[key][0]["ip"] = info_pista
            dict_pista[key][0]["stato"] = checkPingMachine(info_pista)
            
            stati_periferiche = startSessionInSSH(ip_controller, dict_periferiche, user, pwd, tipo_pista)

            for x, key in enumerate(dict_periferiche) :
                ip_periferica = dict_periferiche[key]["ip"]
                dict_periferiche[key]["stato"] = stati_periferiche[x]

        elif key == "codice_pista" :
            dict_pista[key] = int(info_pista)

        else :  
            dict_pista[key] = info_pista
    
    dict_all_piste["Pista_"+ str(codice_pista)] = dict_pista.copy()


print("Stampo il dizionario finale...\n")
print(dict_all_piste)



fine_esecuzione = datetime.now().replace(microsecond=0)
print(f"\nFine esecuzione: {fine_esecuzione}\n")
delta = fine_esecuzione - inizio_esecuzione
delta_min = delta.total_seconds()/60
delta_min = math.trunc(delta_min * 100)/100

print(f"Tempo di esecuzione totale: {delta_min} minuti")

# TO DO
# capire le casistiche di NOTEXPECTED
# generare file excel 


#generazione colonne Excel 
colonne_excel = list(dict_all_piste[next(iter(dict_all_piste))].keys())
for i, key in enumerate(dict_all_piste['Pista_1']):
    if key == "ip_controller" : 
        a = list(dict_periferiche.keys())  
        colonne_excel = colonne_excel[:i+1] + a + colonne_excel[i+1:]

print(colonne_excel)

