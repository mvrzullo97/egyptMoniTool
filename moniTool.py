import dbManager, excelManager
import sys, os, time, math, re, time
from paramiko import AutoAddPolicy, ProxyCommand, SSHClient, Channel
from datetime import datetime



'''------------------------------------- PROVE -------------------------------------'''



#sys.exit(1)

class DualLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout  
        self.log = open(filename, "a")  

    def write(self, message):
        self.terminal.write(message)  
        self.log.write(message) 

    def flush(self):
        pass 

sys.stdout = DualLogger("report_egitto.log")

def checkPingMachine(ip, nome_macchina) -> str :  
    res = os.popen(f"ping {ip}").read()
    if ("Trasmessi = 4") in res and ("Ricevuti = 0") not in res :
        if ("TTL scaduto durante il passaggio.") in res:
            print(f"{nome_macchina} (ip: {ip}) non raggiungibile!\n")
            return "F"
        print(f"{nome_macchina} (ip: {ip}) raggiunto!\n")
        return "T"
    elif ("Destination Host Unreachable") in res :
        print(f"{nome_macchina} (ip: {ip}) non raggiungibile!\n")
        return "F"
    else :
        print(f"{nome_macchina} (ip: {ip}) non raggiungibile!\n")
        return "F"

def checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista) -> str :
    
    lista_stato_periferiche='' 
    
    for key in dict_periferiche :
        
        if key == "anpr_zona_2" and tipo_pista != 'I' :
            print(f"---> Periferica anpr_zona_2 non presa in considerazione per pista di tipo {tipo_pista}")
            lista_stato_periferiche+="N"
        elif key == "anpr_zona_3" and tipo_pista in ('H','I') :
             print(f"---> Periferica anpr_zona_3 non presa in considerazione per pista di tipo {tipo_pista}")
             lista_stato_periferiche+="N"
        elif key == "WIM" and tipo_pista != 'K' :
             print(f"---> Periferica WIM non presa in considerazione per pista di tipo {tipo_pista}")
             lista_stato_periferiche+="N"
        else :          
            ip_periferica = dict_periferiche[key]["ip"]
            stdin, stdout, stderr = ssh_client.exec_command(f'ping -c 4 {ip_periferica}')
            res = stdout.read().decode()

            if ("4 packets transmitted,") in res and ("0 received,") not in res :    
                if("Time to live exceeded") in res :
                    print(f"---> Periferica {key} (ip: {ip_periferica}) non raggiungibile causa TTL scaduta!")
                    lista_stato_periferiche+="F"
                else :
                    print(f"---> Periferica {key} (ip: {ip_periferica}) raggiunta!")
                    lista_stato_periferiche+="T"    
            else :
                print(f"---> Periferica {key} (ip: {ip_periferica}) non raggiungibile")
                lista_stato_periferiche+="F"
        
    return lista_stato_periferiche

    print("CIAO")

def getInfoBySSHSession(controller_pista, dict_pacchetti_controller, dict_periferiche, user, pwd, tipo_pista) : 
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    
    lista_stato_periferiche=''
    
    try:       
        ssh_client.connect(hostname=controller_pista, username=user, password=pwd, allow_agent=True, look_for_keys=True)
        print(f"---> Avvio connessione in ssh ({controller_pista})\n")
        
        print("Recupero versioni controller di Pista e pacchetti relativi...")
        vrs_ctr, lista_vrs_pacchetti = getVersioneControllerAndPacchetti(dict_pacchetti_controller, ssh_client)
        print("Versioni controller e pacchetti recuperate con successo!\n")
        
        print("Verifico raggiungibilità delle periferiche di Pista...")
        lista_stato_periferiche = checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista)
        print("Verifica raggiungibilità periferiche terminata!\n")

        print("Recupero versioni SW delle periferiche di Pista...")
        dict_versioni_periferiche = getVersioniPeriferiche(ssh_client, dict_periferiche, lista_stato_periferiche)
        print("Versioni SW recuperate con successo!\n")

    finally : 
        
        print(f"---> Chiudo connessione in ssh ({controller_pista})\n")
        
        ssh_client.close()
        #sys.exit(1) # TO DO TOGLIERE
        return vrs_ctr, lista_vrs_pacchetti, lista_stato_periferiche, dict_versioni_periferiche

def getVersioneControllerAndPacchetti (dict_pacchetti_controller, ssh_client: SSHClient) -> str :
    
    versioni_pacchetti=[]
    stdin, stdout, stderr = ssh_client.exec_command('cat /etc/ansible/facts.d/customfacts.fact')
    vrs_ctr = stdout.read().decode().strip()
    vrs_ctr = re.search(r"=\s*(.*)", vrs_ctr)
    vrs_ctr = vrs_ctr.group(1)

    for key in dict_pacchetti_controller :
        stdin, stdout, stderr = ssh_client.exec_command(f'rpm -qa | grep {key}')
        vrs_pac = stdout.read().decode().strip()
        if len(vrs_pac.splitlines()) > 1 :
            vrs_pac = vrs_pac.replace("\n", ", ")+" -> (WARNING)"
        versioni_pacchetti.append(vrs_pac)

        print(f"---> Versione pacchetto {key} recuperata: {vrs_pac}") 

    return vrs_ctr, versioni_pacchetti

def getVersioniPeriferiche(ssh_client_pista: SSHClient, dict_periferiche, lista_stato_periferiche) -> dict : 
    
    dict_versioni_periferiche = {"v_barriera_ottica" : '', 
                                "v_antenna" : '', 
                                "v_anpr_zona_1" : '', 
                                "v_anpr_zona_2" : '', 
                                "v_anpr_zona_3" : '', 
                                "v_bio": ['', '']}
    
    unreachable_vrs = "Unreachable"
    not_expected_vrs = "Not Expected"

    for i, key in enumerate(dict_periferiche) :
        stato_periferica = lista_stato_periferiche[i]
        ip_periferica = dict_periferiche[key]["ip"]

        match key:
            case "barriera_ottica" :
                
                if stato_periferica == "F" :
                    print(f"---Versione Barriera Ottica : {unreachable_vrs}")
                    dict_versioni_periferiche["v_barriera_ottica"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---Versione Barriera Ottica : {not_expected_vrs}")
                    dict_versioni_periferiche["v_barriera_ottica"] = not_expected_vrs
                
                else :
                    user_barriera = "root"
                    pwd_barriera = "controlcard"
                    stringa_versione = "Mif version is: "
                    barriera_cmd = "/var/mif/mif -v"
                                        
                    cmd = f"sshpass -p {pwd_barriera} ssh {user_barriera}@{ip_periferica} '{barriera_cmd}' "
                    stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                    file_content = stdout.read().decode()
                    versione_barriera = file_content.split(f"{stringa_versione}")[1].split("\n")[0]
                    
                    if versione_barriera == None :
                        print(f"---> Errore riscontrato durante il recupero della versione della Barriera Ottica, lo traccio nel file Excel...") 
                        dict_versioni_periferiche["v_barriera_ottica"] = "Errore"
                    else :
                        print(f"---> Versione Barriera Ottica recuperata: {versione_barriera}")
                        dict_versioni_periferiche["v_barriera_ottica"] = versione_barriera
                
            case "antenna" :
                
                if stato_periferica == "F" :
                    print(f"---> Versione Antenna : {unreachable_vrs}")
                    dict_versioni_periferiche["v_antenna"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione Antenna : {not_expected_vrs}")
                    dict_versioni_periferiche["v_antenna"] = not_expected_vrs

                else :
                    user_antenna = "root"
                    pwd_antenna = "UHF-RFID-Dev"
                    stringa_versione = "KAT ACQ"     
                    antenna_cmd = "grep 'KAT ACQ' /flash/log/KatAcqFFM.log"
                    
                    cmd = f"sshpass -p {pwd_antenna} ssh {user_antenna}@{ip_periferica} '{antenna_cmd}' "
                    stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                    file_content = stdout.read().decode()
                    lines = file_content.split("\n")

                    last_line = None
                    for line in lines:
                        if stringa_versione in line:
                            last_line = line
                            
                    if last_line == None :
                        print(f"---> Errore riscontrato durante il recupero della versione dell'Antenna, lo traccio nel file Excel...") 
                        dict_versioni_periferiche["v_antenna"] = "Errore"
                    else :
                        m = re.search(rf"--\s*({stringa_versione} \d+\.\d+)\s*--", last_line)
                        versione_antenna = m.group(1)
                        
                        print(f"---> Versione Antenna recuperata: {versione_antenna}") 
                        dict_versioni_periferiche["v_antenna"] = versione_antenna

            case "anpr_zona_1" :
                
                user_anpr_zona_1 = ""
                pwd_anpr_zona_1 = ""
                versione_anp_zona_1 = ""
 
                if stato_periferica == "F" :
                    print(f"---> Versione anpr_zona_1 : {unreachable_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_1"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione anpr_zona_1 : {not_expected_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_1"] = not_expected_vrs
                
                else :
                    print("---> Versione anpr_zona_1: momentaneamente non disponibile")
                    dict_versioni_periferiche["v_anpr_zona_1"] = "Non disponibile"
            
            case "anpr_zona_2" :
                
                user_anpr_zona_2 = ""
                pwd_anpr_zona_2 = ""
                versione_anp_zona_2 = ""
 
                if stato_periferica == "F" :
                    print(f"---> Versione anpr_zona_2 : {unreachable_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_2"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione anpr_zona_2 : {not_expected_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_2"] = not_expected_vrs
                
                else :
                    print("---> Versione anpr_zona_2: momentaneamente non disponibile")
                    dict_versioni_periferiche["v_anpr_zona_2"] = "Non disponibile"
            
            case "anpr_zona_3" :
                
                user_anpr_zona_3 = ""
                pwd_anpr_zona_3 = ""
                versione_anp_zona_3 = ""
 
                if stato_periferica == "F" :
                    print(f"---> Versione anpr_zona_3 : {unreachable_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_3"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione anpr_zona_3 : {not_expected_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_3"] = not_expected_vrs
                
                else :
                    print("---> Versione anpr_zona_3: momentaneamente non disponibile")
                    dict_versioni_periferiche["v_anpr_zona_3"] = "Non disponibile"
            
            case "bio" :                
                
                if stato_periferica == "F" :
                    print(f"---> Versione DAC : {unreachable_vrs}") 
                    print(f"---> Versione BIO : {unreachable_vrs}")
                    dict_versioni_periferiche["v_bio"][0] = unreachable_vrs
                    dict_versioni_periferiche["v_bio"][1] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione BIO Board e DAC Driver : {not_expected_vrs}")
                    dict_versioni_periferiche["v_bio"][0] = not_expected_vrs
                    dict_versioni_periferiche["v_bio"][1] = not_expected_vrs
                
                else :
                    user_bio = "root"
                    pwd_bio = "itsegypt"  
                    dac_cmd = "/FN0/S30DacDRIVER/dac -v"
                    bio_cmd = "cat /FN0/version.txt"
                    versione_BIO = ''
                    stringhe_versioni_bio = ["BIO_EGYPT v", "BIO v", "SAM_ATECH v"]
                                        
                    cmd = f"sshpass -p {pwd_bio} ssh {user_bio}@{ip_periferica} '{dac_cmd}' "
                    stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                    file_content = stdout.read().decode()
                    versione_DAC = file_content.strip()
                    if versione_DAC == None :
                        print(f"---> Errore riscontrato durante il recupero della versione del DAC Driver, lo traccio nel file Excel...") 
                        dict_versioni_periferiche["v_bio"][0] = "Errore"
                    else :
                        cmd = f"sshpass -p {pwd_bio} ssh {user_bio}@{ip_periferica} '{bio_cmd}' "
                        stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                        file_content = stdout.read().decode()
                    
                    if file_content == None :
                        print(f"---> Errore riscontrato durante il recupero della versione della BIO Board, lo traccio nel file Excel...") 
                        dict_versioni_periferiche["v_bio"][1] = "Errore"
                    else :
                        
                        for k in stringhe_versioni_bio:
                            match = re.search(rf"{k}\d+\.\d+", file_content)
                            versione_BIO += match.group() + ", "              
                        versione_BIO = versione_BIO.rstrip(', ')

                        print(f"---> Versione DAC recuperata: {versione_DAC}") 
                        print(f"---> Versione BIO recuperata: {versione_BIO}")
                        dict_versioni_periferiche["v_bio"][0] = versione_DAC
                        dict_versioni_periferiche["v_bio"][1] = versione_BIO
    
    return dict_versioni_periferiche

def getVersioniAxis(ip_axis, user, pwd) -> str:
        
        print("---> Versione Axis External: momentaneamente non disponibile\n")
        return "Non disponibile"

user="root"
pwd="Movyon.2022!"
inizio_esecuzione = datetime.now().replace(microsecond=0)

piste = dbManager.select_data_from_tjmd06_lne(dbManager.connessione_db_gsegy06())
#piste = (('1', 'K', '10.1.45.4', '10.1.123.132', '10.1.64.164'), ('2', 'I ', '10.1.65.8', '10.1.64.133', '10.1.123.165'))
#piste = (('8', 'I', '10.1.65.32', '10.1.64.139', '10.1.64.171'), ('2', 'I ', '10.2.62.8', '10.1.64.133', '10.1.123.165'))


dict_barriera_ottica = {"ip" : '172.16.0.10', "stato" : '', "versione" : ''}
dict_antenna = {"ip" : '172.16.0.30', "stato" : '', "versione" : ''}
dict_anpr_zona_1 = {"ip" : '172.16.0.21', "stato" : '', "versione" : ''}
dict_anpr_zona_2 = {"ip" : '172.16.0.22', "stato" : '', "versione" : ''}
dict_anpr_zona_3 = {"ip" : '172.16.0.22', "stato" : '', "versione" : ''}
dict_bio = {"ip" : '172.16.0.2', "stato" : '', "versioneBIO" : '', "versioneDAC" : ''}
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

dict_pacchetti_controller = {"movyonEgypt-" :'',
                             "movyonEgyptConf" :'',
                             "arcd_application_base" :'',
                             "arcdLibs" :'',
                             "arcd-" :'',
                             "arcd_application_core-" :''}

dict_controller = {"ip" : '', "stato" : '', "versione" :'', "versione_pacchetti" :dict_pacchetti_controller}
dict_axis_external = {"ip" : '', "stato" : '', "versione" : ''}
dict_axis_internal = {"ip" : '', "stato" : '', "versione" : ''}


dict_pista = {"codice_pista" : '',
              "tipo_pista" : '',
              "controller_pista" : [dict_controller,  dict_periferiche], 
              "axis_external" : dict_axis_external,
              "axis_internal" : dict_axis_internal}

dict_all_piste = {}

print(f"\nInizio esecuzione: {inizio_esecuzione}")

for j in range(0, len(piste)) : 

    dict_pacchetti_controller = {"movyonEgypt-" :'', "movyonEgyptConf" :'', "arcd_application_base" :'', "arcdLibs" :'', "arcd-" :'', "arcd_application_core-" :''}
    dict_barriera_ottica = {"ip" : '172.16.0.10', "stato" : '', "versione" : ''}
    dict_antenna = {"ip" : '172.16.0.30', "stato" : '', "versione" : ''}
    dict_anpr_zona_1 = {"ip" : '172.16.0.21', "stato" : '', "versione" : ''}
    dict_anpr_zona_2 = {"ip" : '172.16.0.22', "stato" : '', "versione" : ''}
    dict_anpr_zona_3 = {"ip" : '172.16.0.22', "stato" : '', "versione" : ''}
    dict_bio = {"ip" : '172.16.0.2', "stato" : '', "versioneBIO" : '', "versioneDAC" : ''}
    dict_stampante = {"ip" : '172.16.0.40', "stato" : ''}
    dict_fare_display = {"ip" : '172.16.0.60', "stato" : ''}
    dict_WIM = {"ip" : '172.16.0.70', "stato" : ''}
    dict_periferiche = {"barriera_ottica" : dict_barriera_ottica, "antenna" : dict_antenna, "anpr_zona_1" : dict_anpr_zona_1, "anpr_zona_2" : dict_anpr_zona_2, "anpr_zona_3" : dict_anpr_zona_3, "bio" : dict_bio, "stampante" : dict_stampante, "fare_display" : dict_fare_display, "WIM" : dict_WIM}
    dict_controller = {"ip" : '', "stato" : '', "versione" : '', "versione_pacchetti" :dict_pacchetti_controller}
    dict_axis_external = {"ip" : '', "stato" : '', "versione" : ''}
    dict_axis_internal = {"ip" : '', "stato" : '', "versione" : ''}
    dict_pista = {"codice_pista" : '', "tipo_pista" : '', "controller_pista" : [dict_controller,  dict_periferiche], "axis_external" : dict_axis_external, "axis_internal" : dict_axis_internal}

    codice_pista = int(piste[j][0])
    tipo_pista = piste[j][1]
    unreachable_vrs = "Unreachable"
    not_expected_vrs = "Not Expected"
    
    print(f"\n------------------------------ Inizio l'analisi della Pista_{codice_pista} ({j+1} di {len(piste)}) ------------------------------\n")

    for i, key in enumerate(dict_pista) :

        info_pista = piste[j][i]
        

        if key in ("axis_external", "axis_internal") :

            dict_pista[key]["ip"] = info_pista
            stato_axis = checkPingMachine(info_pista, key)
            dict_pista[key]["stato"] = stato_axis
            
            if stato_axis == "F" :
                dict_pista[key]["versione"] = unreachable_vrs
            elif stato_axis == "N" :
                dict_pista[key]["versione"] = not_expected_vrs
            else :
                dict_pista[key]["versione"] = getVersioniAxis(info_pista, user, pwd)
            
        elif key == "controller_pista" :
            
            controller_pista = info_pista
            dict_pista[key][0]["ip"] = info_pista
            dict_pista[key][0]["stato"] = checkPingMachine(info_pista, key)
            
            if dict_pista[key][0]["stato"] == "F" :
                
                print("Controller di Pista non raggiungibile, considero 'Unreachable' periferiche e versioni relative...\n")
                
                lista_stato_periferiche = 'FFFFFFFFF'
                dict_pista[key][0]["versione"] = unreachable_vrs

                for i, key_pacchetto in enumerate(dict_pacchetti_controller) :
                    dict_pista[key][0]["versione_pacchetti"][key_pacchetto] = unreachable_vrs

                for x, key in enumerate(dict_periferiche) :
                    dict_periferiche[key]["stato"] = lista_stato_periferiche[x]
                    if key == "bio" :
                        dict_periferiche[key]["versioneBIO"] = unreachable_vrs
                        dict_periferiche[key]["versioneDAC"] = unreachable_vrs
                    else :
                        dict_periferiche[key]["versione"] = unreachable_vrs
                                
            else :
                versione_controller, lista_versione_pacchetti, lista_stato_periferiche, dict_versione_periferiche = getInfoBySSHSession(controller_pista, 
                                                                                                        dict_pacchetti_controller, 
                                                                                                        dict_periferiche, 
                                                                                                        user, pwd, tipo_pista)
                dict_pista[key][0]["versione"] = versione_controller.strip()

                for i, key_pacchetto in enumerate(dict_pacchetti_controller) :
                    dict_pista[key][0]["versione_pacchetti"][key_pacchetto] = lista_versione_pacchetti[i].strip()

                for x, key in enumerate(dict_periferiche) :
                    ip_periferica = dict_periferiche[key]["ip"]
                    dict_periferiche[key]["stato"] = lista_stato_periferiche[x]

                for key in dict_periferiche :
                    if f"v_{key}" in dict_versione_periferiche :
                        if key == "bio" :
                            dict_pista["controller_pista"][1][key]["versioneDAC"] = dict_versione_periferiche["v_bio"][0]
                            dict_pista["controller_pista"][1][key]["versioneBIO"] = dict_versione_periferiche["v_bio"][1]
                        else :     
                            dict_pista["controller_pista"][1][key]["versione"] = dict_versione_periferiche[f"v_{key}"]
        
        elif key == "codice_pista" :
            dict_pista[key] = int(info_pista)

        else :  
            dict_pista[key] = info_pista
    
    dict_all_piste["Pista_"+ str(codice_pista)] = dict_pista.copy()



#print(dict_all_piste)

nome_file_Excel="report_piste_Egitto.xlsx"

colonne_Excel_ping = ('Codice Pista', 'Tipo Pista', 'Controller', 'Barriera Ottica', 'Antenna RFID', 
                 'Telecamera ANPR Zona 1', 'Telecamera ANPR Zona 2', 'Telecamera ANPR Zona 3',
                  'BIO Board', 'Stampante', 'Fare Display', 'WIM', 'Telecamere CCTV Esterna ', 'Telecamere CCTV Interna ')

colonne_Excel_versioni = ('Codice Pista', 'Controller', 
                          'movyonEgypt', 'movyonEgyptConf', 'arcd_application_base', 'arcdLibs', 'arcd', 'arcd_application_core',
                          'Barriera Ottica', 'Antenna RFID', 
                          'Telecamera ANPR Zona 1', 'Telecamera ANPR Zona 2', 'Telecamera ANPR Zona 3',
                          'Bio Board', 'DAC Driver', 'Telecamera CCTV esterna', 'Telecamera CCTV interna')



excelManager.insertPingResultsIntoExcel(nome_file_Excel, dict_all_piste, colonne_Excel_ping)

excelManager.insertVersionResultsIntoExcel(nome_file_Excel, dict_all_piste, colonne_Excel_versioni)

print(f"\nFile '{nome_file_Excel}' generato con successo!")
print("File salvato in:", os.path.abspath(nome_file_Excel) +"\n")


fine_esecuzione = datetime.now().replace(microsecond=0)
print(f"Fine esecuzione: {fine_esecuzione}\n")
delta = fine_esecuzione - inizio_esecuzione
delta_min = delta.total_seconds()/60
delta_min = math.trunc(delta_min * 100)/100

print(f"Tempo di esecuzione totale: {delta_min} minuti\n")


