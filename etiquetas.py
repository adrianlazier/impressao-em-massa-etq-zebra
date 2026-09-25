import socket
import os

IP_IMPRESSORA = "10.47.36.158"
PORTA = 9100
ARQUIVO_LISTA = os.path.abspath("etiquetas.txt")

TEMPLATE_ZPL = """^XA
^PW720
^LL320
^FO60,110^A0N,105,95^FD{codigo}^FS
^FO550,85^BXN,9,200^FD{codigo}^FS
^PQ1
^XZ
"""

def imprimir():
    with open(ARQUIVO_LISTA, "r", encoding="utf-8") as f:
        codigos = [linha.strip() for linha in f if linha.strip()]

    if not codigos:
        print("Nenhum código encontrado no arquivo.")
        return

    buffer_zpl = "".join([TEMPLATE_ZPL.format(codigo=c) for c in codigos])

    print(f"Enviando {len(codigos)} etiquetas para {IP_IMPRESSORA}...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        s.connect((IP_IMPRESSORA, PORTA))
        s.sendall(buffer_zpl.encode("latin-1"))
    
    print("✓ Concluído com sucesso!")

if __name__ == "__main__":
    imprimir()