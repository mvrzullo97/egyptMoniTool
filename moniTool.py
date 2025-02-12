import dbManager
import sys, os, time, math 
from paramiko import AutoAddPolicy, SSHClient
from datetime import datetime
import openpyxl
from openpyxl.styles import Alignment, PatternFill, Border, Side, Font


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
    
    stati_periferiche='' 
    
    for key in dict_periferiche :
        
        if key == "anpr_zona_2" and tipo_pista != 'I' :
            print(f"Periferica anpr_zona_2 non presa in considerazione per pista di tipo {tipo_pista}")
            stati_periferiche+="N"
        elif key == "anpr_zona_3" and tipo_pista in ('H','I') :
             print(f"Periferica anpr_zona_3 non presa in considerazione per pista di tipo {tipo_pista}")
             stati_periferiche+="N"
        elif key == "WIM" and tipo_pista != 'K' :
             print(f"Periferica WIM non presa in considerazione per pista di tipo {tipo_pista}")
             stati_periferiche+="N"
        else :          
            ip_periferica = dict_periferiche[key]["ip"]
            stdin, stdout, stderr = ssh_client.exec_command(f'ping -c 4 {ip_periferica}')
            res = stdout.read().decode()

 #           if ("4 packets transmitted, 4 received, 0% packet loss,") in res :
            if ("4 packets transmitted,") in res and ("0 received,") not in res :    
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
    
def startSessionInSSH(controller_pista, dict_periferiche, user, pwd, tipo_pista) : 
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    stati_periferiche='' 
    try:
        print(f"Avvio connessione in ssh ({controller_pista})")
        ssh_client.connect(hostname=controller_pista, username=user, password=pwd)
        


        stati_periferiche = checkPingPeriferiche(dict_periferiche, ssh_client, tipo_pista)
        
    finally : 
        print(f"Chiudo connessione in ssh ({controller_pista})")
        ssh_client.close()
        return stati_periferiche

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



piste = dbManager.select_data_from_tjmd06_lne(dbManager.connessione_db_gsegy06())

'''ris atteso: prima lista TFT seconda lista FFT'''
#piste_VERO = (('1', 'K ', '10.1.65.4', '10.1.64.132', '10.1.64.164'), ('2', 'J ', '10.1.65.8', '10.1.64.133', '10.1.64.165'))


# ris atteso = TFT - TTF
#piste = (('1', 'K', '10.2.65.4', '10.1.123.132', '10.1.64.164'), ('2', 'I ', '10.1.65.8', '10.1.64.133', '10.1.123.165'))

#piste = (('1', 'K', '10.1.65.4', '10.1.123.132', '10.1.64.164'))



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
              "controller_pista" : [dict_controller,  dict_periferiche], 
              "axis_external" : dict_axis_external,
              "axis_internal" : dict_axis_internal}

dict_all_piste = {}

user="root"
pwd="Movyon.2022!"
controller_pista = '10.1.65.4'
inizio_esecuzione = datetime.now().replace(microsecond=0)
print(f"\nInizio esecuzione: {inizio_esecuzione}")

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
            
            if dict_pista[key][0]["stato"] == "T" :
                stati_periferiche = startSessionInSSH(controller_pista, dict_periferiche, user, pwd, tipo_pista)
            
            else:
                print("Macchina controller_ pista non raggiungibile, salto la verifica delle periferiche")
                stati_periferiche = 'FFFFFFFFF'

            for x, key in enumerate(dict_periferiche) :
                ip_periferica = dict_periferiche[key]["ip"]
                dict_periferiche[key]["stato"] = stati_periferiche[x]

        elif key == "codice_pista" :
            dict_pista[key] = int(info_pista)

        else :  
            dict_pista[key] = info_pista
    
    dict_all_piste["Pista_"+ str(codice_pista)] = dict_pista.copy()


nome_file_Excel="report_piste_Egitto.xlsx"

colonne_Excel = ('Codice Pista', 'Tipo Pista', 'Controller', 'Barriera Ottica', 'Antenna RFID', 
                 'Telecamera ANPR Zona 1', 'Telecamera ANPR Zona 2', 'Telecamera ANPR Zona 3',
                  'BIO Board', 'Stampante', 'Fare Display', 'WIM', 'Telecamere CCTV Esterna ', 'Telecamere CCTV Interna ')


insertInfoIntoExcel(nome_file_Excel, dict_all_piste, colonne_Excel)

fine_esecuzione = datetime.now().replace(microsecond=0)
print(f"Fine esecuzione: {fine_esecuzione}")
delta = fine_esecuzione - inizio_esecuzione
delta_min = delta.total_seconds()/60
delta_min = math.trunc(delta_min * 100)/100

print(f"Tempo di esecuzione totale: {delta_min} minuti")