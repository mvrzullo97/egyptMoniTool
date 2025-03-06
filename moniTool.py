import dbManager, excelManager
import sys, os, re, time, json
from paramiko import AutoAddPolicy, Channel, SSHClient
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPDigestAuth
import pytz
import warnings



class DualLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout  
        self.log = open(filename, "a")  

    def write(self, message):
        self.terminal.write(message)  
        self.log.write(message) 

    def flush(self):
        pass 

def checkPingMachine(nome_macchina, ip, bridge_ip, bridge_user, bridge_pwd, ssh_client_vmtech: SSHClient) -> str :  
    
    cmd =f"ping -c 4 {ip}"
    stdin, stdout, stderr = ssh_client_vmtech.exec_command(cmd)
    res = stdout.read().decode().strip()

    match nome_macchina:
        case "controller_pista" :
            nome_macchina = "Controller di Pista"
        case "axis_external" :
            nome_macchina = "Axis External"
        case "axis_internal" :
            nome_macchina = "Axis Internal"

    if ("4 packets transmitted") in res and ("0 received") not in res :
        if "TTL expired in transit" in res or "TTL expired during transit" in res :
            print(f"{nome_macchina} (ip: {ip}) non raggiungibile!\n")
            return "F"
        print(f"{nome_macchina} (ip: {ip}) raggiunto!")
        return "T"
    elif ("Destination Host Unreachable") in res :
        print(f"{nome_macchina} (ip: {ip}) non raggiungibile!\n")
        return "F"
    else :
        print(f"{nome_macchina} (ip: {ip}) non raggiungibile!\n")
        return "F"

def createTunnelSSH(ssh_client_vmtech: SSHClient, ip_dest, port=None) :
    try:
        transport = ssh_client_vmtech.get_transport()
        dst_addr = (ip_dest, 22)
        lcl_addr = ('127.0.0.1', 0)
        tunnel_ssh: Channel = transport.open_channel("direct-tcpip", dst_addr, lcl_addr)

    except Exception as e:
        print(f"Errore nella creazione del tunnel SSH: {e}")
    
    finally :  
        if tunnel_ssh.active :
            return tunnel_ssh

def checkPingPeriferiche(dict_periferiche, ssh_client: SSHClient, tipo_pista) -> str :
    
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

def checkVecchiaiaFiles(ssh_client: SSHClient, cmd) -> bool :
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    min_ts_str = stdout.read().decode().strip()
    if min_ts_str != "" or None :
        current_year = datetime.now().year
        min_ts_date = datetime.strptime(min_ts_str, "%b %d %H:%M")

        if min_ts_date.replace(year=current_year) > datetime.now():
            min_ts_date = min_ts_date.replace(year=current_year - 1)
        else:
            min_ts_date = min_ts_date.replace(year=current_year)

        egypt_tz = pytz.timezone("Africa/Cairo")
        min_ts_date = egypt_tz.localize(min_ts_date)
        regex_ts_date = min_ts_date + timedelta(minutes=10)
        egypt_time = datetime.now(egypt_tz)

        if regex_ts_date >= egypt_time:
            return True
        else:
            return False
    else:
        print(f"Il comando bash lanciato: {cmd} non ha prodotto alcun risultato!" )
        return False
    
def getInfoBySSHSession(ssh_client_vmtech: SSHClient, controller_pista, dict_pacchetti_controller, dict_periferiche, user, pwd, tipo_pista) : 
    
    tunnel_ssh = createTunnelSSH(ssh_client_vmtech, controller_pista)
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    
    lista_stato_periferiche=''
    stato_transiti_foto = ""
    try:       
        ssh_client.connect(hostname=controller_pista, 
                           username=user, 
                           password=pwd, 
                           sock=tunnel_ssh, 
                           allow_agent=True, look_for_keys=True)
        
        print(f"------> Avvio connessione in ssh ({controller_pista}) <------\n")
        
        print("Acquisizione acme spool ...")
        cmd_transiti = "ls -ltr /acme/spool/transits/ | grep ^- | head -1 | awk '{print $6, $7, $8}'"
        cmd_foto = "ls -ltr /acme/spool/photos | grep ^- | head -1 | awk '{print $6, $7, $8}'"
        
        stato_foto = checkVecchiaiaFiles(ssh_client, cmd_foto)
        stato_transito = checkVecchiaiaFiles(ssh_client, cmd_transiti)

        if stato_transito and stato_foto :
            stato_transiti_foto = "OK"
            print(f"---> Esito: {stato_transiti_foto}\n")
        elif not stato_transito and not stato_foto :
            stato_transiti_foto = "KO"
            print(f"---> Esito: {stato_transiti_foto}\n")
        elif not stato_transito :
            stato_transiti_foto = "Transits KO"
            print(f"---> Esito: {stato_transiti_foto}\n")
        elif not stato_foto :
            stato_transiti_foto = "Photos KO"
            print(f"---> Esito: {stato_transiti_foto}\n")

        print("Recupero versioni controller di Pista e pacchetti relativi...")
        vrs_ctr, lista_vrs_pacchetti = getVersioneControllerAndPacchetti(dict_pacchetti_controller, ssh_client)
        print("Versioni controller e pacchetti recuperate con successo!\n")
        
        print("Verifico raggiungibilità delle periferiche di Pista...")
        lista_stato_periferiche = checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista)
        print("Verifica raggiungibilità periferiche terminata!\n")

        print("Recupero versioni Software delle periferiche di Pista...")
        dict_versioni_periferiche = getVersioniPeriferiche(ssh_client, dict_periferiche, lista_stato_periferiche, controller_pista)
        print("Versioni Software recuperate con successo!\n")

    finally :    
        print(f"------> Chiudo connessione in ssh ({controller_pista}) <------\n") 
        ssh_client.close()
        tunnel_ssh.close()
        return vrs_ctr, lista_vrs_pacchetti, lista_stato_periferiche, dict_versioni_periferiche, stato_transiti_foto

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
            vrs_pac = vrs_pac.replace("\n", ", ")+" ---> (WARNING)"
        versioni_pacchetti.append(vrs_pac)

        print(f"---> Versione pacchetto {key} recuperata: {vrs_pac}") 

    return vrs_ctr, versioni_pacchetti

def getVersioniPeriferiche(ssh_client_pista: SSHClient, dict_periferiche, lista_stato_periferiche, controller_pista) -> dict : 
    
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
        
        if ('user' or 'pwd') in dict_periferiche[key] :
            user = dict_periferiche[key]["user"]
            pwd = dict_periferiche[key]["pwd"]

        match key:
            case "barriera_ottica" :
                
                if stato_periferica == "F" :
                    print(f"---Versione Barriera Ottica : {unreachable_vrs}")
                    dict_versioni_periferiche["v_barriera_ottica"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---Versione Barriera Ottica : {not_expected_vrs}")
                    dict_versioni_periferiche["v_barriera_ottica"] = not_expected_vrs
                
                else :
                    stringa_versione = "Mif version is: "
                    barriera_cmd = "/var/mif/mif -v"
                                        
                    cmd = f"sshpass -p {pwd} ssh {user}@{ip_periferica} '{barriera_cmd}' "
                    stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                    file_content = stdout.read().decode()
                    versione_barriera = file_content.split(f"{stringa_versione}")[1].split("\n")[0]
                    
                    if versione_barriera == None or file_content == "":
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
                    stringa_versione = "KAT ACQ"     
                    antenna_cmd = "grep 'KAT ACQ' /flash/log/KatAcqFFM.log"
                    
                    cmd = f"sshpass -p {pwd} ssh {user}@{ip_periferica} '{antenna_cmd}' "
                    stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                    file_content = stdout.read().decode()
                    lines = file_content.split("\n")

                    last_line = None
                    for line in lines:
                        if stringa_versione in line:
                            last_line = line
                            
                    if last_line == None or last_line == "":
                        print(f"---> Errore riscontrato durante il recupero della versione dell'Antenna, lo traccio nel file Excel...") 
                        dict_versioni_periferiche["v_antenna"] = "Errore"
                    else :
                        m = re.search(rf"--\s*({stringa_versione} \d+\.\d+)\s*--", last_line)
                        versione_antenna = m.group(1)
                        
                        print(f"---> Versione Antenna recuperata: {versione_antenna}") 
                        dict_versioni_periferiche["v_antenna"] = versione_antenna

            case "anpr_zona_1" :
                versione_anp_zona_1 = ""
                url_anpr_zona_1 = f"http://{user}:{pwd}@{controller_pista}:32180/cgi-bin/CGI_DeviceInfo.cgi"

                if stato_periferica == "F" :
                    print(f"---> Versione Telecamera Anpr Zona 1 : {unreachable_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_1"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione Telecamera Anpr Zona 1 : {not_expected_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_1"] = not_expected_vrs
                
                else :
                    response = requests.get(url_anpr_zona_1, verify=False)
                    match = re.search(r"Firmware version\s*=\s*([^\n]*\s2024)", response.text)
                    if match:
                        versione_anp_zona_1 = match.group(1)
                        print(f"---> Versione Telecamera Anpr Zona 1 recuperata: {versione_anp_zona_1}") 
                    else:
                        versione_anp_zona_1 = "Errore"
                        print(f"---> Errore riscontrato durante il recupero della Versione Telecamera Anpr Zona 1, lo traccio nel file Excel...")
                
                    dict_versioni_periferiche["v_anpr_zona_1"] = versione_anp_zona_1

                   
            
            case "anpr_zona_2" :
                versione_anp_zona_2 = ""
                url_anpr_zona_2 = f"http://{user}:{pwd}@{controller_pista}:32280/cgi-bin/CGI_DeviceInfo.cgi"
        
                if stato_periferica == "F" :
                    print(f"---> Versione Telecamera Anpr Zona 2 : {unreachable_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_2"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione Telecamera Anpr Zona 2 : {not_expected_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_2"] = not_expected_vrs
                
                else :
                    response = requests.get(url_anpr_zona_2, verify=False)
                    match = re.search(r"Firmware version\s*=\s*([^\n]*\s2024)", response.text)
                    if match:
                        versione_anp_zona_2 = match.group(1)
                        print(f"---> Versione Telecamera Anpr Zona 2 recuperata: {versione_anp_zona_2}") 
                    else:
                        versione_anp_zona_1 = "Errore"
                        print(f"---> Errore riscontrato durante il recupero della Versione Telecamera Anpr Zona 2, lo traccio nel file Excel...")
                
                    dict_versioni_periferiche["v_anpr_zona_2"] = versione_anp_zona_2
                    
            
            case "anpr_zona_3" :
                versione_anp_zona_3 = ""
                url_anpr_zona_3 = f"http://{user}:{pwd}@{controller_pista}:32280/cgi-bin/CGI_DeviceInfo.cgi"

                if stato_periferica == "F" :
                    print(f"---> Versione Telecamera Anpr Zona 3 : {unreachable_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_3"] = unreachable_vrs
                
                elif stato_periferica == "N" :
                    print(f"---> Versione Telecamera Anpr Zona 3 : {not_expected_vrs}")
                    dict_versioni_periferiche["v_anpr_zona_3"] = not_expected_vrs
                
                else :
                    response = requests.get(url_anpr_zona_3, verify=False)
                    match = re.search(r"Firmware version\s*=\s*([^\n]*\s2024)", response.text)
                    if match:
                        versione_anp_zona_3 = match.group(1)
                        print(f"---> Versione Telecamera Anpr Zona 3 recuperata: {versione_anp_zona_3}") 
                    else:
                        versione_anp_zona_1 = "Errore"
                        print(f"---> Errore riscontrato durante il recupero della Versione Telecamera Anpr Zona 3, lo traccio nel file Excel...")
                
                    dict_versioni_periferiche["v_anpr_zona_3"] = versione_anp_zona_3
            
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
                    dac_cmd = "/FN0/S30DacDRIVER/dac -v"
                    bio_cmd = "cat /FN0/version.txt"
                    stringhe_versioni_bio = ["BIO_EGYPT v", "BIO v", "SAM_ATECH v"]
                    versione_BIO = ""
                                        
                    cmd = f"sshpass -p {pwd} ssh {user}@{ip_periferica} '{dac_cmd}' "
                    stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                    file_content = stdout.read().decode()
                    versione_DAC = file_content.strip()
                    
                    if versione_DAC == None or versione_DAC == "":
                        print(f"---> Errore riscontrato durante il recupero della versione del DAC Driver, lo traccio nel file Excel...") 
                        versione_DAC = "Errore"
                    else :
                        print(f"---> Versione DAC recuperata: {versione_DAC}")

                    dict_versioni_periferiche["v_bio"][0] = versione_DAC

                    cmd = f"sshpass -p {pwd} ssh {user}@{ip_periferica} '{bio_cmd}' "
                    stdin, stdout, stderr = ssh_client_pista.exec_command(cmd)
                    file_content = stdout.read().decode()
                    
                    if file_content == None or file_content == "" :
                        print(f"---> Errore riscontrato durante il recupero della versione della BIO Board, lo traccio nel file Excel...") 
                        versione_BIO = "Errore"
                        
                    else :
                        for k in stringhe_versioni_bio:
                            match = re.search(rf"{k}\d+\.\d+", file_content)
                            versione_BIO += match.group() + ", "              
                        versione_BIO = versione_BIO.rstrip(', ')
                        print(f"---> Versione BIO recuperata: {versione_BIO}")
                     
                    dict_versioni_periferiche["v_bio"][1] = versione_BIO
    
    return dict_versioni_periferiche

def getVersioniAxis(ip_axis, user, pwd, type) -> str: 
    url = f"http://{ip_axis}/axis-cgi/firmwaremanagement.cgi"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json"
        }
    data = {
        "apiVersion": "1.2",
        "method": "status",
        "params": {}
    }
    
    response = requests.post(url, json=data, headers=headers, auth=HTTPDigestAuth(user, pwd), verify=False)
    match = re.search(r'"activeFirmwareVersion":\s*"([^"]+)"', response.text)
    if match:
        versione_telecamera = match.group(1)
        print(f"---> Versione Telecamera Axis {type} recuperata: {versione_telecamera}\n")
    else:
        versione_telecamera = "Errore"
        print(f"---> Errore durante il recupero della Versione Telecamera Axis {type}, lo traccio nel file Excel...")
    return versione_telecamera

warnings.filterwarnings("ignore", category=DeprecationWarning)
json_filename = "config_tool.json"

try:
    print(f"\nFile di configurazione {json_filename} trovato, estraggo i parametri...")

    with open(json_filename, 'r') as f:
        config = json.load(f)
    try :
        
        bridge_name = config['bridge']['hostname']
        bridge_ip = config['bridge']['ip']
        bridge_user = config['bridge']['user']
        bridge_pwd = config['bridge']['pwd']
        
        db_name = config['database']['dbname']
        db_ip = config['database']['ip']
        db_port = config['database']['port']
        db_user = config['database']['user']
        db_pwd = config['database']['pwd']

        rete = config['pista']['rete']
        stazione = config['pista']['stazione']
        folder_name_Excel_out = config['pista']['folder_output']
        log = config['pista']['logging']
        
        user_controller = config['info_controller']['user']
        pwd_controller = config['info_controller']['pwd']

        ip_barriera_ottica = config['info_periferiche']['barriera_ottica']['ip']
        user_barriera_ottica = config['info_periferiche']['barriera_ottica']['user']
        pwd_barriera_ottica = config['info_periferiche']['barriera_ottica']['pwd']

        ip_antenna = config['info_periferiche']['antenna']['ip']
        user_antenna = config['info_periferiche']['antenna']['user']
        pwd_antenna = config['info_periferiche']['antenna']['pwd']

        ip_anpr_zona_1 = config['info_periferiche']['anpr_zona_1']['ip']
        user_anpr_zona_1 = config['info_periferiche']['anpr_zona_1']['user']
        pwd_anpr_zona_1 = config['info_periferiche']['anpr_zona_1']['pwd']

        ip_anpr_zona_2 = config['info_periferiche']['anpr_zona_2']['ip']
        user_anpr_zona_2 = config['info_periferiche']['anpr_zona_2']['user']
        pwd_anpr_zona_2 = config['info_periferiche']['anpr_zona_2']['pwd']

        ip_anpr_zona_3 = config['info_periferiche']['anpr_zona_3']['ip']
        user_anpr_zona_3 = config['info_periferiche']['anpr_zona_3']['user']
        pwd_anpr_zona_3 = config['info_periferiche']['anpr_zona_3']['pwd']

        ip_bio = config['info_periferiche']['bio']['ip']
        user_bio = config['info_periferiche']['bio']['user']
        pwd_bio = config['info_periferiche']['bio']['pwd']
        
        ip_stampante = config['info_periferiche']['stampante']['ip']
        ip_fare_display = config['info_periferiche']['fare_display']['ip']
        ip_WIM = config['info_periferiche']['WIM']['ip']

        user_axis = config['info_axis']['user']
        pwd_axis = config['info_axis']['pwd']
    
    except KeyError as e:
        print(f"Errore: La chiave '{e.args[0]}' non è presente nel file di configurazione!\n")
        sys.exit(1)
except FileNotFoundError:
        print(f"Errore: Il file {json_filename} non esiste!\n")
        sys.exit(1)
except json.JSONDecodeError:
        
        print(f"Errore: Il file {json_filename} non è un JSON valido!\n")
        sys.exit(1)

if log : sys.stdout = DualLogger("tmp.log")

if os.path.exists(folder_name_Excel_out) and os.path.isdir(folder_name_Excel_out) :
    print(f"Cartella {folder_name_Excel_out} esistente al path: '{os.path.abspath(folder_name_Excel_out)}'...")
else :
    print(f"Cartella {folder_name_Excel_out} non trovata, la creo...")
    os.makedirs(folder_name_Excel_out, exist_ok=True)

inizio_esecuzione = datetime.now().replace(microsecond=0)

ssh_client_vmtech = SSHClient()
ssh_client_vmtech.set_missing_host_key_policy(AutoAddPolicy())
ssh_client_vmtech.connect(hostname=bridge_ip, username=bridge_user, password=bridge_pwd, allow_agent=True, look_for_keys=True)

print(f"\n---------------------------------> Avvio connessione in ssh sul bridge: {bridge_name} ({bridge_ip}) <---------------------------------")

try :
    tunnel_ssh = createTunnelSSH(ssh_client_vmtech, db_ip, db_port)
    db_connection = dbManager.connessione_db_gsegy06(db_name, db_user, db_pwd, db_ip, db_port, tunnel_ssh)
    if db_connection : piste = dbManager.select_data_from_tjmd06_lne(db_connection, stazione, rete)
finally:
    tunnel_ssh.close()

dict_barriera_ottica = {"ip" : ip_barriera_ottica, "stato" : '', "versione" : '', "user" : user_barriera_ottica, "pwd" : pwd_barriera_ottica}
dict_antenna = {"ip" : ip_antenna, "stato" : '', "versione" : '', "user" : user_antenna, "pwd" : pwd_antenna}
dict_anpr_zona_1 = {"ip" : ip_anpr_zona_1, "stato" : '', "versione" : '', "user" : user_anpr_zona_1, "pwd" : pwd_anpr_zona_1}
dict_anpr_zona_2 = {"ip" : ip_anpr_zona_2, "stato" : '', "versione" : '', "user" : user_anpr_zona_2, "pwd" : pwd_anpr_zona_2}
dict_anpr_zona_3 = {"ip" : ip_anpr_zona_3, "stato" : '', "versione" : '', "user" : user_anpr_zona_3, "pwd" : pwd_anpr_zona_3}
dict_bio = {"ip" : ip_bio, "stato" : '', "versioneBIO" : '', "versioneDAC" : '', "user" : user_bio, "pwd" : pwd_bio}
dict_stampante = {"ip" : ip_stampante, "stato" : ''}
dict_fare_display = {"ip" : ip_fare_display, "stato" : ''}
dict_WIM = {"ip" : ip_WIM, "stato" : ''}

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

dict_controller = {"ip" : '', "stato" : '', "versione" : '', "versione_pacchetti" : dict_pacchetti_controller, "stato_transiti_foto" : ""}
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
    dict_barriera_ottica = {"ip" : ip_barriera_ottica, "stato" : '', "versione" : '', "user" : user_barriera_ottica, "pwd" : pwd_barriera_ottica}
    dict_antenna = {"ip" : ip_antenna, "stato" : '', "versione" : '', "user" : user_antenna, "pwd" : pwd_antenna}
    dict_anpr_zona_1 = {"ip" : ip_anpr_zona_1, "stato" : '', "versione" : '', "user" : user_anpr_zona_1, "pwd" : pwd_anpr_zona_1}
    dict_anpr_zona_2 = {"ip" : ip_anpr_zona_2, "stato" : '', "versione" : '', "user" : user_anpr_zona_2, "pwd" : pwd_anpr_zona_2}
    dict_anpr_zona_3 = {"ip" : ip_anpr_zona_3, "stato" : '', "versione" : '', "user" : user_anpr_zona_3, "pwd" : pwd_anpr_zona_3}
    dict_bio = {"ip" : ip_bio, "stato" : '', "versioneBIO" : '', "versioneDAC" : '', "user" : user_bio, "pwd" : pwd_bio}
    dict_stampante = {"ip" : ip_stampante, "stato" : ''}
    dict_fare_display = {"ip" : ip_fare_display, "stato" : ''}
    dict_WIM = {"ip" : ip_WIM, "stato" : ''}
    dict_periferiche = {"barriera_ottica" : dict_barriera_ottica, "antenna" : dict_antenna, "anpr_zona_1" : dict_anpr_zona_1, "anpr_zona_2" : dict_anpr_zona_2, "anpr_zona_3" : dict_anpr_zona_3, "bio" : dict_bio, "stampante" : dict_stampante, "fare_display" : dict_fare_display, "WIM" : dict_WIM}
    dict_controller = {"ip" : '', "stato" : '', "versione" : '', "versione_pacchetti" : dict_pacchetti_controller, "stato_transiti_foto" : ""}
    dict_axis_external = {"ip" : '', "stato" : '', "versione" : ''}
    dict_axis_internal = {"ip" : '', "stato" : '', "versione" : ''}
    dict_pista = {"codice_pista" : '', "tipo_pista" : '', "controller_pista" : [dict_controller,  dict_periferiche], "axis_external" : dict_axis_external, "axis_internal" : dict_axis_internal}

    codice_pista = int(piste[j][0])
    tipo_pista = piste[j][1]
    unreachable_vrs = "Unreachable"
    not_expected_vrs = "Not Expected"
    
    print(f"\n------------------------------ Analisi Pista_{codice_pista} ({j+1} di {len(piste)}) ------------------------------\n")

    for i, key in enumerate(dict_pista) :

        info_pista = piste[j][i]
        
        if key in ("axis_external", "axis_internal") :
            
            type_axis = "External" if key == "axis_external" else "Internal"
            dict_pista[key]["ip"] = info_pista
            stato_axis = checkPingMachine(key, info_pista, bridge_ip, bridge_user, bridge_pwd, ssh_client_vmtech)
            dict_pista[key]["stato"] = stato_axis
            
            if stato_axis == "F" :
                dict_pista[key]["versione"] = unreachable_vrs
            elif stato_axis == "N" :
                dict_pista[key]["versione"] = not_expected_vrs
            else :
                dict_pista[key]["versione"] = getVersioniAxis(info_pista, user_axis, pwd_axis, type_axis)
            
        elif key == "controller_pista" :
            
            controller_pista = info_pista
            dict_pista[key][0]["ip"] = info_pista
            dict_pista[key][0]["stato"] = checkPingMachine(key, info_pista, bridge_ip, bridge_user, bridge_pwd, ssh_client_vmtech)
            
            if dict_pista[key][0]["stato"] == "F" :
                
                print("Controller di Pista non raggiungibile, considero 'Unreachable' periferiche versioni relative...\n")
                dict_pista[key][0]["stato_transiti_foto"] = "Unreachable"
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
                versione_controller, lista_versione_pacchetti, lista_stato_periferiche, dict_versione_periferiche, stato_transiti_foto = getInfoBySSHSession (
                    ssh_client_vmtech,
                    controller_pista, 
                    dict_pacchetti_controller, 
                    dict_periferiche, 
                    user_controller, 
                    pwd_controller, 
                    tipo_pista )
                
                dict_pista[key][0]["stato_transiti_foto"] = stato_transiti_foto
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

print(f"\n---------------------------------> Chiudo connessione in ssh sul bridge: {bridge_name} ({bridge_ip}) <---------------------------------\n")
ssh_client_vmtech.close()

fine_esecuzione = datetime.now().replace(microsecond=0)
print(f"Fine esecuzione: {fine_esecuzione}\n")
diff = fine_esecuzione - inizio_esecuzione
ore = diff.seconds // 3600
minuti = (diff.seconds % 3600) // 60
secondi = diff.seconds % 60
tempo_tot = f"{ore} ore, {minuti} minuti, {secondi} secondi"
print(f"Tempo di esecuzione totale: {tempo_tot}")

ts_fine_esec = fine_esecuzione.strftime("%Y.%m.%d.%H.%M")
nome_file_Excel=f"{ts_fine_esec} Egitto-Monitoraggio Rete {rete} Stazione {stazione}.xlsx"

colonne_Excel_ping = ('Codice Pista', 'Tipo Pista', 'Controller', 'Barriera Ottica', 'Antenna RFID', 
                 'Telecamera ANPR Zona 1', 'Telecamera ANPR Zona 2', 'Telecamera ANPR Zona 3',
                  'BIO Board', 'Stampante', 'Fare Display', 'WIM', 'Telecamere CCTV Esterna ', 'Telecamere CCTV Interna ')

colonne_Excel_versioni = ('Codice Pista', 'Controller', 
                          'movyonEgypt', 'movyonEgyptConf', 'arcd_application_base', 'arcdLibs', 'arcd', 'arcd_application_core',
                          'Barriera Ottica', 'Antenna RFID', 
                          'Telecamera ANPR Zona 1', 'Telecamera ANPR Zona 2', 'Telecamera ANPR Zona 3',
                          'Bio Board', 'DAC Driver', 'Telecamera CCTV esterna', 'Telecamera CCTV interna')

dict_info_Excel = {"IP Database" : db_ip,
                   "Nome Database" : db_name,
                   "Rete" : rete,
                   "Stazione" : stazione,
                   "lista_ip_periferiche" : "",
                   "Inizio Esecuzione" : inizio_esecuzione,
                   "Fine Esecuzione" : fine_esecuzione,
                   "Tempo Totale (hh:mm:ss)" : diff }

path_file_Excel = os.path.join(os.path.abspath(folder_name_Excel_out), nome_file_Excel)

excelManager.insertInfoRunAndLegende(path_file_Excel, dict_info_Excel, dict_periferiche)
excelManager.insertPingResultsIntoExcel(path_file_Excel, dict_all_piste, colonne_Excel_ping)
excelManager.insertVersionResultsIntoExcel(path_file_Excel, dict_all_piste, colonne_Excel_versioni)
excelManager.insertStatoTransitiFotoIntoExcel(path_file_Excel, dict_all_piste)

print(f"\nFile '{nome_file_Excel}' generato con successo!")
print(f"File salvato in: '{path_file_Excel}'\n")

if log :
    sys.stdout = sys.__stdout__ 
    nome_log = f"Monitoraggio_Egitto_{ts_fine_esec}.log"
    os.rename("tmp.log", nome_log)
