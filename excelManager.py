import openpyxl
from openpyxl import load_workbook
from openpyxl.styles import Alignment, PatternFill, Border, Side, Font

def insertPingResultsIntoExcel(nome_file, dict_all_piste, colonne_Excel_ping) :
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Raggiungibilità Piste Egitto"    
    
    bold_colonne = Font(bold=True)

    bordi = Border(left=Side(border_style="thin", color="000000"), right=Side(border_style="thin", color="000000"), top=Side(border_style="thin", color="000000"), bottom=Side(border_style="thin", color="000000"))

    colore_rosso = PatternFill(start_color="FF6666", end_color="FF6666", fill_type="solid")
    colore_verde = PatternFill(start_color="66CC66", end_color="66CC66", fill_type="solid")
    colore_giallo = PatternFill(start_color="FFEE99", end_color="FFEE99", fill_type="solid")
    colore_neutro = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    for i_col, nome_colonna in enumerate(colonne_Excel_ping, start=1) :
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
    
    for i in range(1, ws.max_row + 1):
        ws.row_dimensions[i].height = 19

    wb.save(nome_file)
    
def insertVersionResultsIntoExcel(nome_file_Excel, dict_all_piste, colonne_Excel_versioni) :
    wb = load_workbook(nome_file_Excel)
    ws2 = wb.create_sheet("Verifica Versioni Software")


    bold_colonne = Font(bold=True)
    bordi = Border(left=Side(border_style="thin", color="000000"), right=Side(border_style="thin", color="000000"), top=Side(border_style="thin", color="000000"), bottom=Side(border_style="thin", color="000000"))

    colore_rosso = PatternFill(start_color="FF6666", end_color="FF6666", fill_type="solid")
    colore_giallo = PatternFill(start_color="FFEE99", end_color="FFEE99", fill_type="solid")
    colore_verde = PatternFill(start_color="66CC66", end_color="90EE90", fill_type="solid")
    colore_arancione = PatternFill(start_color="e87c1b", end_color="e87c1b", fill_type="solid")
    colore_celeste = PatternFill(start_color="1bb9e8", end_color="1bb9e8", fill_type="solid")

    for i_col, nome_colonna in enumerate(colonne_Excel_versioni, start=1) :
        colonna = ws2.cell(row=1, column=i_col, value=nome_colonna)
        col_letter = ws2.cell(row=1, column=i_col).column_letter  
        colonna.alignment = Alignment(horizontal="center", vertical="center")
        colonna.border = bordi
        colonna.font = bold_colonne
    
    for i, key in enumerate(dict_all_piste) :
        
        exc_codice_pista = str(dict_all_piste[key]["codice_pista"])
        vrs_controller_pista = str(dict_all_piste[key]["controller_pista"][0]["versione"])
        
        vrs_pacc_movyonEgypt = str(dict_all_piste[key]["controller_pista"][0]["versione_pacchetti"]["movyonEgypt-"])
        vrs_pacc_movyonEgyptConf = str(dict_all_piste[key]["controller_pista"][0]["versione_pacchetti"]["movyonEgyptConf"])
        vrs_pacc_arcd_application_base = str(dict_all_piste[key]["controller_pista"][0]["versione_pacchetti"]["arcd_application_base"])
        vrs_pacc_arcdLibs = str(dict_all_piste[key]["controller_pista"][0]["versione_pacchetti"]["arcdLibs"])
        vrs_pacc_arcd = str(dict_all_piste[key]["controller_pista"][0]["versione_pacchetti"]["arcd-"])
        vrs_pacc_arcd_application_core = str(dict_all_piste[key]["controller_pista"][0]["versione_pacchetti"]["arcd_application_core-"])
        
        vrs_barriera_ottica = str(dict_all_piste[key]["controller_pista"][1]["barriera_ottica"]["versione"])
        vrs_antenna = str(dict_all_piste[key]["controller_pista"][1]["antenna"]["versione"])
        vrs_anpr_zona_1 = str(dict_all_piste[key]["controller_pista"][1]["anpr_zona_1"]["versione"])
        vrs_anpr_zona_2 = str(dict_all_piste[key]["controller_pista"][1]["anpr_zona_2"]["versione"])
        vrs_anpr_zona_3 = str(dict_all_piste[key]["controller_pista"][1]["anpr_zona_3"]["versione"])
        vrs_bio = str(dict_all_piste[key]["controller_pista"][1]["bio"]["versioneBIO"])
        vrs_dac = str(dict_all_piste[key]["controller_pista"][1]["bio"]["versioneDAC"])
          
        vrs_external = str(dict_all_piste[key]["axis_external"]['versione'])
        vrs_internal = str(dict_all_piste[key]["axis_internal"]['versione'])
    
        versioni_software_pista = (exc_codice_pista, vrs_controller_pista, 
                                vrs_pacc_movyonEgypt, vrs_pacc_movyonEgyptConf, vrs_pacc_arcd_application_base, vrs_pacc_arcdLibs, vrs_pacc_arcd, vrs_pacc_arcd_application_core,
                                vrs_barriera_ottica, vrs_antenna, vrs_anpr_zona_1, vrs_anpr_zona_2, vrs_anpr_zona_3, vrs_bio, vrs_dac, vrs_external, vrs_internal)
    
        for col_i, element in enumerate(versioni_software_pista, start=1):  
                colore = colore_verde
                match element :
                    case "Not Expected":
                        colore = colore_giallo
                    case "Unreachable":
                        colore = colore_rosso
                    case "Errore":
                        colore = colore_arancione
                    case "Non disponibile":
                        colore = colore_celeste
                
                if " -> (WARNING)" in element :
                    colore = colore_arancione
                    #element.replace(" -> (WARNING)", "")
                row = ws2.cell(row=i+2, column=col_i, value=element)
                row.alignment = Alignment(horizontal="center", vertical="center")
            
                if col_i != 1:
                    row.fill = colore
                row.border = bordi
    
        for col in ws2.columns:
            max_length = 0
            col_letter = col[0].column_letter 
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))  
            ws2.column_dimensions[col_letter].width = max_length + 2 
  
        for i in range(1, ws2.max_row + 1):
            ws2.row_dimensions[i].height = 19

    wb.save(nome_file_Excel)