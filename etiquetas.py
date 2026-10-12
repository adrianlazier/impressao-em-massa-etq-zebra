import json
import os
import socket
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

# ---------------- Configuração ----------------
IP_PADRAO = "192.168.0.1"
PORTA_PADRAO = 9100
LOTE = 50  # etiquetas enviadas por vez

TEMPLATE_ZPL = """^XA
^PW720
^LL320
^FO60,110^A0N,105,95^FD{codigo}^FS
^FO550,85^BXN,9,200^FD{codigo}^FS
^PQ1
^XZ
"""


def pasta_app():
    """Pasta onde fica o .exe (ou o .py), para salvar a configuração."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


ARQUIVO_CONFIG = os.path.join(pasta_app(), "config_etiquetas.json")


def carregar_config():
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg.get("ip", IP_PADRAO), int(cfg.get("porta", PORTA_PADRAO))
    except Exception:
        return IP_PADRAO, PORTA_PADRAO


def salvar_config(ip, porta):
    try:
        with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
            json.dump({"ip": ip, "porta": porta}, f)
    except Exception:
        pass  # sem permissão de escrita: ignora


def limpar_codigo(codigo):
    # ^ e ~ são caracteres de controle do ZPL e quebrariam a etiqueta
    return codigo.replace("^", "").replace("~", "").strip()


# ---------------- Interface ----------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Impressão de Etiquetas")
        self.geometry("520x560")
        self.minsize(460, 480)

        ip, porta = carregar_config()
        self.var_ip = tk.StringVar(value=ip)
        self.var_porta = tk.StringVar(value=str(porta))
        self.var_status = tk.StringVar(value="Pronto.")
        self.imprimindo = False

        self._montar()

    def _montar(self):
        pad = {"padx": 10, "pady": 5}

        # Impressora
        frame_imp = ttk.LabelFrame(self, text="Impressora")
        frame_imp.pack(fill="x", **pad)
        ttk.Label(frame_imp, text="IP:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame_imp, textvariable=self.var_ip, width=18).grid(row=0, column=1)
        ttk.Label(frame_imp, text="Porta:").grid(row=0, column=2, padx=5)
        ttk.Entry(frame_imp, textvariable=self.var_porta, width=7).grid(row=0, column=3)
        ttk.Button(frame_imp, text="Testar conexão", command=self.testar).grid(
            row=0, column=4, padx=10
        )

        # Lista
        frame_lista = ttk.LabelFrame(
            self, text="Códigos (um por linha) — cole aqui ou abra um .txt"
        )
        frame_lista.pack(fill="both", expand=True, **pad)
        self.txt = scrolledtext.ScrolledText(frame_lista, height=15, font=("Consolas", 11))
        self.txt.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt.bind("<<Modified>>", self._contar)

        barra = ttk.Frame(frame_lista)
        barra.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Button(barra, text="Abrir arquivo .txt", command=self.abrir_arquivo).pack(side="left")
        ttk.Button(barra, text="Limpar", command=self.limpar).pack(side="left", padx=5)
        self.lbl_qtd = ttk.Label(barra, text="0 etiquetas")
        self.lbl_qtd.pack(side="right")

        # Ação
        self.btn_imprimir = ttk.Button(self, text="IMPRIMIR", command=self.imprimir)
        self.btn_imprimir.pack(fill="x", padx=10, pady=5, ipady=8)

        self.barra_prog = ttk.Progressbar(self, mode="determinate")
        self.barra_prog.pack(fill="x", padx=10)
        ttk.Label(self, textvariable=self.var_status).pack(anchor="w", padx=10, pady=5)

    # ---------- utilidades ----------
    def codigos(self):
        linhas = self.txt.get("1.0", "end").splitlines()
        return [limpar_codigo(l) for l in linhas if limpar_codigo(l)]

    def _contar(self, _=None):
        if self.txt.edit_modified():
            self.lbl_qtd.config(text=f"{len(self.codigos())} etiquetas")
            self.txt.edit_modified(False)

    def abrir_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Escolha a lista de códigos",
            filetypes=[("Arquivos de texto", "*.txt"), ("Todos", "*.*")],
        )
        if not caminho:
            return
        for enc in ("utf-8-sig", "latin-1"):
            try:
                with open(caminho, "r", encoding=enc) as f:
                    conteudo = f.read()
                break
            except UnicodeDecodeError:
                continue
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", conteudo)

    def limpar(self):
        self.txt.delete("1.0", "end")

    def _dados_impressora(self):
        ip = self.var_ip.get().strip()
        try:
            porta = int(self.var_porta.get())
        except ValueError:
            messagebox.showerror("Erro", "A porta precisa ser um número (normalmente 9100).")
            return None
        if not ip:
            messagebox.showerror("Erro", "Informe o IP da impressora.")
            return None
        return ip, porta

    # ---------- ações ----------
    def testar(self):
        dados = self._dados_impressora()
        if not dados:
            return
        ip, porta = dados
        try:
            with socket.create_connection((ip, porta), timeout=5):
                pass
            salvar_config(ip, porta)
            messagebox.showinfo("Conexão", f"Impressora {ip} respondeu. ✓")
        except Exception as e:
            messagebox.showerror("Conexão", f"Não foi possível conectar em {ip}:{porta}\n\n{e}")

    def imprimir(self):
        if self.imprimindo:
            return
        dados = self._dados_impressora()
        if not dados:
            return
        codigos = self.codigos()
        if not codigos:
            messagebox.showwarning("Atenção", "Nenhum código informado.")
            return
        if not messagebox.askyesno(
            "Confirmar", f"Imprimir {len(codigos)} etiquetas na impressora {dados[0]}?"
        ):
            return

        salvar_config(*dados)
        self.imprimindo = True
        self.btn_imprimir.state(["disabled"])
        self.barra_prog.config(maximum=len(codigos), value=0)
        threading.Thread(target=self._enviar, args=(dados, codigos), daemon=True).start()

    def _enviar(self, dados, codigos):
        ip, porta = dados
        enviados = 0
        try:
            with socket.create_connection((ip, porta), timeout=10) as s:
                for i in range(0, len(codigos), LOTE):
                    lote = codigos[i : i + LOTE]
                    buffer = "".join(TEMPLATE_ZPL.format(codigo=c) for c in lote)
                    s.sendall(buffer.encode("latin-1", errors="replace"))
                    enviados += len(lote)
                    self.after(0, self._progresso, enviados, len(codigos))
            self.after(0, self._fim, True, f"✓ {enviados} etiquetas enviadas com sucesso!")
        except Exception as e:
            self.after(
                0, self._fim, False, f"Erro após enviar {enviados} etiquetas:\n\n{e}"
            )

    def _progresso(self, atual, total):
        self.barra_prog.config(value=atual)
        self.var_status.set(f"Enviando... {atual}/{total}")

    def _fim(self, ok, msg):
        self.imprimindo = False
        self.btn_imprimir.state(["!disabled"])
        self.var_status.set(msg.splitlines()[0])
        (messagebox.showinfo if ok else messagebox.showerror)("Resultado", msg)


if __name__ == "__main__":
    App().mainloop()