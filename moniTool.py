import dbManager
import sys, os, time, math, re, time
from paramiko import AutoAddPolicy, ProxyCommand, SSHClient, Channel
from datetime import datetime
import openpyxl
from openpyxl.styles import Alignment, PatternFill, Border, Side, Font


'''------------------------------------- PROVE -------------------------------------'''

'''def isOutputGenerated(channel, timeout=10):
    start_time = time.time()
    output=''
    while time.time() - start_time < timeout:
        if channel.recv_ready():
            output += channel.recv(4096).decode()
        else:
            break
        time.sleep(0.5)
    
    output_lines = output.split("\n")
    if len(output_lines) > 1:
        output = "\n".join(output_lines[1:])
    return True, output

def connectSSHx2():
    # Configurazione della connessione pista -> perfierica
    ip_pista = "10.1.65.4"
    user_pista = "root"
    pwd_pista = "Movyon.2022!"

    ip_perfierica = "172.16.0.30"
    user_perfierica = "root"
    pwd_perfierica = "UHF-RFID-Dev"

    ssh_client_pista = SSHClient()
    ssh_client_pista.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client_pista.connect(ip_pista, username=user_pista, password=pwd_pista)

    
    channel = ssh_client_pista.invoke_shell()
    channel.recv(1024)  
    print("Invoco la shell interattiva...")
    channel.send(f"ssh {user_perfierica}@{ip_perfierica}\n")
    time.sleep(20)
    if isOutputGenerated(channel)[0]: # Prendo solo il valore di ritorno booleano
        channel.send(pwd_perfierica + "\n")
        print("Inserisco la password....")
        time.sleep(20)
        if isOutputGenerated(channel)[0]:
            print("Recupero le informazioni utili di barriera")
            channel.send("grep 'KAT ACQ' /flash/log/KatAcqFFM.log\n")
            time.sleep(10)
            esito, v_antenna = isOutputGenerated(channel)
            match = re.search(r"--\s*(KAT ACQ \d+\.\d+)\s*--", v_antenna)
            v_antenna = match.group(1)
            print("verisone finale antenna" + v_antenna)
    else:       
        print("Nessun output generato!")

    channel.close()
    ssh_client_pista.close()

    return v_antenna

barr = connectSSHx2()
#print(barr)


    


sys.exit(1)'''






def checkPingMachine(ip) -> str :  
    res = os.popen(f"ping {ip}").read()
    if ("Trasmessi = 4") in res and ("Ricevuti = 0") not in res :
        if ("TTL scaduto durante il passaggio.") in res:
            print(f"Macchina (ip: {ip}) non raggiungibile!")
            return "F"
        print(f"Macchina (ip: {ip}) raggiunta!")
        return "T"
    else :
        print(f"Macchina (ip: {ip}) non raggiungibile!")
        return "F"

def checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista) -> str :
    
    lista_stato_periferiche='' 
    
    for key in dict_periferiche :
        
        if key == "anpr_zona_2" and tipo_pista != 'I' :
            print(f"Periferica anpr_zona_2 non presa in considerazione per pista di tipo {tipo_pista}")
            lista_stato_periferiche+="N"
        elif key == "anpr_zona_3" and tipo_pista in ('H','I') :
             print(f"Periferica anpr_zona_3 non presa in considerazione per pista di tipo {tipo_pista}")
             lista_stato_periferiche+="N"
        elif key == "WIM" and tipo_pista != 'K' :
             print(f"Periferica WIM non presa in considerazione per pista di tipo {tipo_pista}")
             lista_stato_periferiche+="N"
        else :          
            ip_periferica = dict_periferiche[key]["ip"]
            stdin, stdout, stderr = ssh_client.exec_command(f'ping -c 4 {ip_periferica}')
            res = stdout.read().decode()

            if ("4 packets transmitted,") in res and ("0 received,") not in res :    
                if("Time to live exceeded") in res :
                    print(f"Periferica {key} (ip: {ip_periferica}) non raggiungibile causa TTL scaduta!")
                    lista_stato_periferiche+="F"
                else :
                    print(f"Periferica {key} (ip: {ip_periferica}) raggiunta!")
                    lista_stato_periferiche+="T"    
            else :
                print(f"Periferica {key} (ip: {ip_periferica}) non raggiungibile, non verifico la sua versione")
                lista_stato_periferiche+="F"
        
    return lista_stato_periferiche

    print("CIAO")

def getInfoBySSHSession(controller_pista, dict_pacchetti_controller, dict_periferiche, user, pwd, tipo_pista) : 
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    
    lista_stato_periferiche='TTFFFTFFF' # da settare a '' dopo 
    
    try:       
        ssh_client.connect(hostname=controller_pista, username=user, password=pwd, allow_agent=True, look_for_keys=True)
        print(f"Avvio connessione in ssh ({controller_pista})")
        #vrs_ctr, lista_vrs_pacchetti = getVersioneControllerAndPacchetti(controller_pista, dict_pacchetti_controller, user, pwd, ssh_client) 
        #lista_stato_periferiche = checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista)
        

        #TO DO, va cancellato poi
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
            
        getVersioniPeriferiche(ssh_client, dict_periferiche, lista_stato_periferiche)


        # to do recuperare altre versioni -> soluzione funzione che si prende in input lista, dict, sshclient, con switch per capire dove atterrare e restituisce una lisra di versioni

    finally : 
        print(f"Chiudo connessione in ssh ({controller_pista})")
        
        ssh_client.close()
        sys.exit(1) # TO DO TOGLIERE
        #return vrs_ctr, lista_vrs_pacchetti, lista_stato_periferiche

def getVersioneControllerAndPacchetti (controller_pista, dict_pacchetti_controller, user, pwd, ssh_client) -> str :
    
    versioni_pacchetti=[]
    print(f"Sono sulla macchina di Pista ({controller_pista}) per recuperare le versioni...")
    stdin, stdout, stderr = ssh_client.exec_command('cat /etc/ansible/facts.d/customfacts.fact')
    vrs_ctr = stdout.read().decode().strip()
    vrs_ctr = re.search(r"=\s*(.*)", vrs_ctr)

    for key in dict_pacchetti_controller :
        stdin, stdout, stderr = ssh_client.exec_command(f'rpm -qa | grep {key}')
        vrs_pac = stdout.read().decode().strip()
        versioni_pacchetti.append(vrs_pac) 

    print("Versioni controller e pacchetti recuperate con successo!")

    return vrs_ctr, versioni_pacchetti

def isOutputGenerated(channel, timeout=10):
    start_time = time.time()
    output=''
    while time.time() - start_time < timeout:
        if channel.recv_ready():
            output += channel.recv(4096).decode()
        else:
            break
        time.sleep(0.5)
    
    output_lines = output.split("\n")
    if len(output_lines) > 1:
        output = "\n".join(output_lines[1:])
    return True, output

def getVersioniPeriferiche(ssh_client_pista: SSHClient, dict_periferiche, lista_stato_periferiche) -> str : 
    
    for i, key in enumerate(dict_periferiche) :
        stato_periferica = lista_stato_periferiche[i]
        ip_periferica = dict_periferiche[key]["ip"]

        '''if stato_periferica != "T":
            print(f"Periferica {key} ({ip_periferica}) non raggiungibile, non verifico la versione relativa")'''
        match key:
            case "barriera_ottica" if stato_periferica == "T":
                user_barriera = "root"
                pwd_barriera = "controlcard"  
                channel_barriera = ssh_client_pista.invoke_shell()
                channel_barriera.recv(1024)
                
                print("Recupero la versione della Barriera Ottica tramite Shell interattiva...")

                channel_barriera.send(f"ssh {user_barriera}@{ip_periferica}\n")
                time.sleep(20)
                if isOutputGenerated(channel_barriera)[0]:
                    channel_barriera.send(pwd_barriera + "\n")
                    time.sleep(20)
                    if isOutputGenerated(channel_barriera)[0]:
                        channel_barriera.send("/var/mif/mif -v\n")
                        time.sleep(10)
                        esito, versione_barriera = isOutputGenerated(channel_barriera)                        
                v = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', versione_barriera)
                match = re.search(rf"Mif version is: \d+\.\d+", v)
                v = match.group()
                versione_barriera = v.split(": ")[1]
                
                print(f"Versione Barriera Ottica recueperata: {versione_barriera}")
                channel_barriera.close()

            case "antenna" if stato_periferica == "T":
                
                user_antenna = "root"
                pwd_antenna = "UHF-RFID-Dev"  
                channel_antenna = ssh_client_pista.invoke_shell()
                channel_antenna.recv(1024)                
                
                print("Recupero la versione dell'Antenna tramite Shell interattiva...")
                
                channel_antenna.send(f"ssh {user_antenna}@{ip_periferica}\n")
                time.sleep(20)
                if isOutputGenerated(channel_antenna)[0]:
                    channel_antenna.send(pwd_antenna + "\n")
                    time.sleep(20)
                    if isOutputGenerated(channel_antenna)[0]:
                        channel_antenna.send("grep 'KAT ACQ' /flash/log/KatAcqFFM.log\n")
                        time.sleep(15)
                        esito, versione_antenna = isOutputGenerated(channel_antenna)
                        m = re.search(r"--\s*(KAT ACQ \d+\.\d+)\s*--", versione_antenna)
                        versione_antenna = m.group(1)
                
                print(f"Versione Antenna recuperata: {versione_antenna}") 
                channel_antenna.close()

            case "anpr_zona_1" if stato_periferica == "T":
                print("Sono sulla anprz1")
                print("front end NO SSH")
            case "anpr_zona_2" if stato_periferica == "T":
                print("Sono sulla anprz2")
                print("front end NO SSH")
            case "anpr_zona_3" if stato_periferica == "T":
                print("Sono sulla anprz3")
                print("front end NO SSH")
            
            case "bio" if stato_periferica == "T":                
                user_bio = "root"
                pwd_bio = "itsegypt"  
                channel_bio = ssh_client_pista.invoke_shell()
                channel_bio.recv(1024)

                print("Recupero la versione di BIO Board e DAC Driver tramite Shell interattiva...")
                
                channel_bio.send(f"ssh {user_bio}@{ip_periferica}\n")
                time.sleep(5)
                if isOutputGenerated(channel_bio)[0] :
                    channel_bio.send(pwd_bio + "\n")
                    time.sleep(5)
                    if isOutputGenerated(channel_bio)[0] :
                        channel_bio.send("/FN0/S30DacDRIVER/dac -v\n")
                        time.sleep(10)
                        esito, versione_DAC = isOutputGenerated(channel_bio)
                        if esito :       
                            channel_bio.send("vi /FN0/version.txt \n")
                            time.sleep(10)
                            esito, file_txt_BIO = isOutputGenerated(channel_bio)
                            if isOutputGenerated(channel_bio) :
                                file_txt_BIO = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', file_txt_BIO)
                                keys = ["FRW BIO for update_BIO_EGYPT v", "BIO v", "SAM_ATECH v"]
                                versione_BIO = ''
                                for k in keys:
                                    match = re.search(rf"{k}\d+\.\d+", file_txt_BIO)
                                    versione_BIO += match.group() + ", "

                versione_DAC = versione_DAC.split("\r")[0]
                versione_BIO = versione_BIO.rstrip(",")
                print(f"Versione DAC recuperata: {versione_DAC}") 
                print(f"Versione BIO recuperata: {versione_BIO}")
                channel_bio.close()
    
def insertInfoIntoExcel(nome_file, dict_all_piste, colonne_Excel) :
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report_Piste_Egitto"    
    
    bold_colonne = Font(bold=True)

    bordi = Border(left=Side(border_style="thin", color="000000"), right=Side(border_style="thin", color="000000"), top=Side(border_style="thin", color="000000"), bottom=Side(border_style="thin", color="000000"))

    colore_rosso = PatternFill(start_color="FF6666", end_color="FF6666", fill_type="solid")
    colore_verde = PatternFill(start_color="66CC66", end_color="66CC66", fill_type="solid")
    colore_giallo = PatternFill(start_color="FFEE99", end_color="FFEE99", fill_type="solid")
    colore_neutro = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    for i_col, nome_colonna in enumerate(colonne_Excel, start=1) :
        colonna = ws.cell(row=1, column=i_col, value=nome_colonna)
        col_letter = ws.cell(row=1, column=i_col).column_letter  
        if nome_colonna == "WIM":
            nome_fittizio = "NotExpected"
            ws.column_dimensions[col_letter].width = max(len(nome_fittizio) + 2, 10)
        else:
            ws.column_dimensions[col_letter].width = max(len(nome_colonna) + 2, 10)

        colonna.alignment = Alignment(horizontal="center", vertical="center")
        colonna.border = bordi
        colonna.font = bold_colonne
    
    for i, key in enumerate(dict_all_piste) :
        exc_codice_pista = str(dict_all_piste[key]["codice_pista"])
        exc_tipo_pista = str(dict_all_piste[key]["tipo_pista"])
        exc_controller_pista = str(dict_all_piste[key]["controller_pista"][0]["stato"])
        exc_barriera_ottica = str(dict_all_piste[key]["controller_pista"][1]["barriera_ottica"]["stato"])
        exc_antenna = str(dict_all_piste[key]["controller_pista"][1]["antenna"]["stato"])
        exc_anpr_zona_1 = str(dict_all_piste[key]["controller_pista"][1]["anpr_zona_1"]["stato"])
        exc_anpr_zona_2 = str(dict_all_piste[key]["controller_pista"][1]["anpr_zona_2"]["stato"])
        exc_anpr_zona_3 = str(dict_all_piste[key]["controller_pista"][1]["anpr_zona_3"]["stato"])
        exc_bio = str(dict_all_piste[key]["controller_pista"][1]["bio"]["stato"])
        exc_stampante = str(dict_all_piste[key]["controller_pista"][1]["stampante"]["stato"])
        exc_fare_display = str(dict_all_piste[key]["controller_pista"][1]["fare_display"]["stato"])
        exc_WIM = str(dict_all_piste[key]["controller_pista"][1]["WIM"]["stato"])
        exc_external = str(dict_all_piste[key]["axis_external"]['stato'])
        exc_internal = str(dict_all_piste[key]["axis_internal"]['stato'])

        dati_pista = (exc_codice_pista, exc_tipo_pista, exc_controller_pista, 
                        exc_barriera_ottica, exc_antenna, exc_anpr_zona_1, exc_anpr_zona_2, exc_anpr_zona_3,exc_bio, exc_stampante, exc_fare_display, exc_WIM, 
                        exc_external, exc_internal)

        for col_i, element in enumerate(dati_pista, start=1):  
            colore = colore_neutro
            match element :
                case "T":
                    element = "Yes"
                    colore = colore_verde
                case "F":
                    element = "No"
                    colore = colore_rosso
                case "N":
                    element = "Not Expected"
                    colore = colore_giallo

            row = ws.cell(row=i+2, column=col_i, value=element)
            row.alignment = Alignment(horizontal="center", vertical="center")
            row.fill = colore
            row.border = bordi
    wb.save(nome_file)
    print(f"File '{nome_file}' generato con successo!")
    print("File salvato in:", os.path.abspath(nome_file))


    print("Inizio il recupero delle versioni delle periferiche raggiungibili")
    # to do switch case
    





    
    '''ssh_client_perfierica = SSHClient()
    ssh_client_perfierica.set_missing_host_key_policy(AutoAddPolicy())
    try:
        ssh_client_perfierica.connect(hostname="172.16.0.10", username="root", password="controlcard", sock=channel)
        print(f"Connessione a 172.16.0.10 riuscita!")
        stdin, stdout, stderr = ssh_client_perfierica.exec_command('/var/mif/mif -v')
        a = stdout.read().decode().strip()
        print(a)
    finally:
        ssh_client_perfierica.close()'''
    '''for x, key_periferiche in enumerate(dict_periferiche) :
        
        
        
        print(f"{key_periferiche} e stato{lista_stato_periferiche[x]}")   
'''



user="root"
pwd="Movyon.2022!"
controller_pista = '10.1.65.4'
inizio_esecuzione = datetime.now().replace(microsecond=0)
#piste = dbManager.select_data_from_tjmd06_lne(dbManager.connessione_db_gsegy06())

piste = (('1', 'K', '10.1.65.4', '10.1.123.132', '10.1.64.164'), ('2', 'I ', '10.1.65.8', '10.1.64.133', '10.1.123.165'))


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
    print(f"\n------------------------ Inizio l'analisi della Pista_{codice_pista} ({j+1} di {len(piste)})------------------------\n")

    for i, key in enumerate(dict_pista) :

        info_pista = piste[j][i] 
        if key in ("axis_external", "axis_internal") :

            dict_pista[key]["ip"] = info_pista
            dict_pista[key]["stato"] = checkPingMachine(info_pista) 

        elif key == "controller_pista" :
            
            controller_pista = info_pista
            dict_pista[key][0]["ip"] = info_pista
            dict_pista[key][0]["stato"] = checkPingMachine(info_pista)
            
            versione_controller, lista_versione_pacchetti, lista_stato_periferiche = getInfoBySSHSession(controller_pista, 
                                                                                                       dict_pacchetti_controller, 
                                                                                                       dict_periferiche, 
                                                                                                       user, pwd, tipo_pista)
            
            dict_pista[key][0]["versione"] = versione_controller

            #TO DO vedere il caso di '\n' per un pacchetto
            for i, key_pacchetto in enumerate(dict_pacchetti_controller) :
                dict_pista[key][0]["versione_pacchetti"][key_pacchetto] = lista_versione_pacchetti[i]

            if dict_pista[key][0]["stato"] == "F" :
                print("Controller Pista non raggiungibile, considero non raggiungibili le periferiche relative")
                lista_stato_periferiche = 'FFFFFFFFF'

            for x, key in enumerate(dict_periferiche) :
                ip_periferica = dict_periferiche[key]["ip"]
                dict_periferiche[key]["stato"] = lista_stato_periferiche[x]

        elif key == "codice_pista" :
            dict_pista[key] = int(info_pista)

        else :  
            dict_pista[key] = info_pista
    
    dict_all_piste["Pista_"+ str(codice_pista)] = dict_pista.copy()



print(dict_all_piste)



nome_file_Excel="report_piste_Egitto.xlsx"
colonne_Excel = ('Codice Pista', 'Tipo Pista', 'Controller', 'Barriera Ottica', 'Antenna RFID', 
                 'Telecamera ANPR Zona 1', 'Telecamera ANPR Zona 2', 'Telecamera ANPR Zona 3',
                  'BIO Board', 'Stampante', 'Fare Display', 'WIM', 'Telecamere CCTV Esterna ', 'Telecamere CCTV Interna ')


#insertInfoIntoExcel(nome_file_Excel, dict_all_piste, colonne_Excel)

fine_esecuzione = datetime.now().replace(microsecond=0)
print(f"Fine esecuzione: {fine_esecuzione}")
delta = fine_esecuzione - inizio_esecuzione
delta_min = delta.total_seconds()/60
delta_min = math.trunc(delta_min * 100)/100

print(f"Tempo di esecuzione totale: {delta_min} minuti")




'''DOPO PROVO 
esito, channel_bio = invokeShellAndInsertUserAndPassword(ssh_client_pista, ip_periferica, user_bio, pwd_bio) 
                
                print("Recupero versione di BIO Board e DAC Driver")
                if isOutputGenerated(channel_bio)[0] :
                        print("Recupero le informazioni utili di DAC e BIO...")
                        channel_bio.send("/FN0/S30DacDRIVER/dac -v\n")
                        time.sleep(10)
                        esito, versione_DAC = isOutputGenerated(channel_bio)
                        if esito :
                            
                            channel_bio.send("vi /FN0/version.txt \n")
                            time.sleep(10)
                            esito, file_txt_BIO = isOutputGenerated(channel_bio)
                            if isOutputGenerated(channel_bio) :
                                file_txt_BIO = re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', file_txt_BIO)
                                keys = ["FRW BIO for update_BIO_EGYPT v", "BIO v", "SAM_ATECH v"]
                                versione_BIO = ''
                                for k in keys:
                                    match = re.search(rf"{k}\d+\.\d+", file_txt_BIO)
                                    versione_BIO += match.group() + ", "
                                    versione_BIO = versione_BIO.rstrip(",")
                #versione_DAC, versione_BIO = getVersioniDacAndBio(channel_bio, esito)
                channel_bio.close()
                print("Chiudo Shell interattiva")
                print(f"Versione DAC recuperata: {versione_DAC}") 
                print(f"Versione BIO recuperata: {versione_BIO}")'''