import re

def getVersioneAnprFromText(text) :
    match = re.search(r'Firmware version\s*=\s*(VEGA BASIC [\d\.]+(?:\.[A-Za-z0-9_]+)?(?: [A-Za-z]+ \d+))', text)
    if match:
        return match.group(1)  # Restituisce solo la versione trovata
    else:
        return "Error"
