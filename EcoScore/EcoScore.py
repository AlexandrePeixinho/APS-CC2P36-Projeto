
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

ARQUIVO_USUARIOS = "usuarios.csv"
ARQUIVO_HISTORICO = "historico.csv" 
ARQUIVO_ULTIMO_RESET = "ultimo_reset.txt" 

META_POR_CATEGORIA = {
    "reciclagem": 100,
    "agua_luz": 100,
    "habitos": 100,
    "gases": 100
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

if not os.path.exists(ARQUIVO_USUARIOS):
    df0 = pd.DataFrame(columns=[
        "usuario", "senha",
        "reciclagem", "agua_luz", "habitos", "gases", "total"
    ])
    df0.to_csv(ARQUIVO_USUARIOS, index=False)

if not os.path.exists(ARQUIVO_HISTORICO):
    hist0 = pd.DataFrame(columns=[
        "usuario", "data_iso",
        "reciclagem", "agua_luz", "habitos", "gases", "total"
    ])
    hist0.to_csv(ARQUIVO_HISTORICO, index=False)
    
if not os.path.exists(ARQUIVO_ULTIMO_RESET):
    with open(ARQUIVO_ULTIMO_RESET, "w", encoding="utf-8") as f:
        f.write((datetime.now(timezone.utc) - timedelta(days=8)).date().isoformat())

def carregar_df_usuarios():
    df = pd.read_csv(ARQUIVO_USUARIOS)
    for c in ["reciclagem", "agua_luz", "habitos", "gases", "total"]:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df

def salvar_df_usuarios(df):
    df.to_csv(ARQUIVO_USUARIOS, index=False)

def recalcular_total(df):
    df["total"] = (df["reciclagem"].fillna(0).astype(int) +
                   df["agua_luz"].fillna(0).astype(int) +
                   df["habitos"].fillna(0).astype(int) +
                   df["gases"].fillna(0).astype(int))
    return df

def salvar_snapshot_historico():

    df = carregar_df_usuarios()
    if df.empty:
        return

    df_snapshot = df.copy()
    df_snapshot["data_iso"] = datetime.now(timezone.utc).date().isoformat()

    cols = ["usuario", "data_iso", "reciclagem", "agua_luz", "habitos", "gases", "total"]
    df_snapshot = df_snapshot[cols]
    df_hist = pd.read_csv(ARQUIVO_HISTORICO)
    df_hist = pd.concat([df_hist, df_snapshot], ignore_index=True)
    df_hist.to_csv(ARQUIVO_HISTORICO, index=False)
    df2 = df.copy()
    for c in ["reciclagem", "agua_luz", "habitos", "gases", "total"]:
        df2[c] = 0
    salvar_df_usuarios(df2)

def precisa_reset_semana():
    try:
        with open(ARQUIVO_ULTIMO_RESET, "r", encoding="utf-8") as f:
            s = f.read().strip()
            if not s:
                return True
            last = datetime.fromisoformat(s).date()
            return (datetime.now(timezone.utc).date() - last).days >= 7
    except Exception:
        return True

def registrar_reset_realizado():
    with open(ARQUIVO_ULTIMO_RESET, "w", encoding="utf-8") as f:
        f.write(datetime.now(timezone.utc).date().isoformat())

def adicionar_pontos_usuario(usuario, categoria, pontos):
    df = carregar_df_usuarios()
    if usuario not in df["usuario"].values:
        return False
    df.loc[df["usuario"] == usuario, categoria] += pontos
    df = recalcular_total(df)
    salvar_df_usuarios(df)
    return True

class ProjetoEcoScore(ctk.CTk):
 
    def __init__(self):
        super().__init__()

        self.title("Projeto EcoScore")
 
        self.geometry("1200x760")
        self.minsize(1000, 620)

        self.bg_gray = "#2E2E2E"
        self.card_green = "#2F7A3E"
        self.accent_green = "#4CAF50"
        self.light_green = "#A5D6A7"

        self.usuario_logado = None
        self.current_category_chart = None

        self.configure(bg=self.bg_gray)

        if precisa_reset_semana():

            salvar_snapshot_historico()
            registrar_reset_realizado()

        self._build_sidebar()
        self._build_header()
        self._build_main_area()

        self.show_frame("login")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.bg_gray)
        self.sidebar.pack(side="left", fill="y")

        self.logo_frame = ctk.CTkFrame(self.sidebar, height=100, corner_radius=12, fg_color=self.card_green)
        self.logo_frame.pack(padx=14, pady=18, fill="x")
        self.logo_title = ctk.CTkLabel(self.logo_frame, text="EcoScore", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_title.place(relx=0.04, rely=0.22)
        self.logo_sub = ctk.CTkLabel(self.logo_frame, text="Projeto APS", font=ctk.CTkFont(size=11))
        self.logo_sub.place(relx=0.04, rely=0.62)

        pad = {"padx": 12, "pady": 8, "fill": "x"}
        self.btn_tabela = ctk.CTkButton(self.sidebar, text="Tabela", command=lambda: self.show_frame("tabela"))
        self.btn_tabela.pack(**pad)
        self.btn_actions = ctk.CTkButton(self.sidebar, text="Registrar Ações", command=lambda: self.show_frame("actions"))
        self.btn_actions.pack(**pad)
        self.btn_ranking = ctk.CTkButton(self.sidebar, text="Rankings", command=lambda: self.show_frame("ranking"))
        self.btn_ranking.pack(**pad)
        self.btn_perf = ctk.CTkButton(self.sidebar, text="Desempenho", command=lambda: self.show_frame("performance"))
        self.btn_perf.pack(**pad)

        self.footer_label = ctk.CTkLabel(self.sidebar, text="Projeto APS • UNIP", font=ctk.CTkFont(size=11))
        self.footer_label.pack(side="bottom", pady=10)

    def _build_header(self):
        self.header = ctk.CTkFrame(self, height=64, fg_color=self.bg_gray, corner_radius=0)
        self.header.pack(side="top", fill="x")
 
        self.user_info = ctk.CTkLabel(self.header, text="Não logado", width=220)
        self.user_info.place(relx=0.86, rely=0.5, anchor="e")
    
        self.logout_btn = ctk.CTkButton(self.header, text="Sair", width=80, command=self._logout)
        self.logout_btn.place(relx=0.98, rely=0.5, anchor="e")

    def _build_main_area(self):

        self.main_area = ctk.CTkFrame(self, fg_color=self.bg_gray, corner_radius=0)
        self.main_area.pack(side="right", fill="both", expand=True)
        self.frames = {}

        page_classes = [
            ("login", FrameLogin),
            ("tabela", Frametabela),
            ("actions", FrameActions),
            ("ranking", FrameRanking),
            ("performance", FramePerformance)
        ]
        for name, cls in page_classes:
            frame = cls(parent=self.main_area, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

    def show_frame(self, name):

        frame = self.frames.get(name)
        if frame:
            self._update_usuario_info()
            frame.update_data()
            frame.tkraise()

    def login_success(self, usuario):

        self.usuario_logado = usuario
        self._update_usuario_info()
        self.show_frame("tabela")

    def _update_usuario_info(self):

        if self.usuario_logado:
            self.user_info.configure(text=f"Usuário: {self.usuario_logado}")
        else:
            self.user_info.configure(text="Não logado")

    def _logout(self):
    
        self.usuario_logado = None
        self._update_usuario_info()
        self.show_frame("login")

class FrameLogin(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=self.controller.bg_gray)

        left = ctk.CTkFrame(self, width=520, fg_color=self.controller.card_green, corner_radius=12)
        left.pack(side="left", fill="both", expand=False, padx=(36, 20), pady=36)
        right = ctk.CTkFrame(self, fg_color=self.controller.bg_gray)
        right.pack(side="right", fill="both", expand=True, padx=(20, 36), pady=36)

        left_title = ctk.CTkLabel(left, text="EcoScore", anchor="w", justify="left",
                                  font=ctk.CTkFont(size=46, weight="bold"), text_color="white")
        left_title.place(relx=0.06, rely=0.12)
        left_sub = ctk.CTkLabel(left,
                                text=("Bem-vindo ao EcoScore \n\n"
                                      "Monitore seus hábitos sustentáveis,\n"
                                      "ganhe pontos e suba no ranking ecológico!\n"
                                      "Faça a diferença pelo planeta de forma divertida.\n\n\n\n\n"
                                      "Registre suas Tarefas diariamente!"),
                                anchor="w", justify="left",
                                font=ctk.CTkFont(size=20), text_color="white")
        left_sub.place(relx=0.06, rely=0.34)

        form = ctk.CTkFrame(right, fg_color=self.controller.bg_gray)
        form.place(relx=0.5, rely=0.45, anchor="center")

        lbl_user = ctk.CTkLabel(form, text="Usuário", anchor="w")
        lbl_user.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.input_user = ctk.CTkEntry(form, width=360, placeholder_text="Digite seu usuário")
        self.input_user.grid(row=1, column=0, pady=(0, 12))

        lbl_pass = ctk.CTkLabel(form, text="Senha", anchor="w")
        lbl_pass.grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.input_pass = ctk.CTkEntry(form, width=360, placeholder_text="Senha", show="*")
        self.input_pass.grid(row=3, column=0, pady=(0, 12))

        self.btn_login = ctk.CTkButton(form, text="Entrar", width=220, command=self.tentar_login,
                                      fg_color=self.controller.accent_green)
        self.btn_login.grid(row=4, column=0, pady=(8, 12))

        self.info_txt = ctk.CTkLabel(form, text="Ainda não possui uma conta?")
        self.info_txt.grid(row=5, column=0, pady=(6, 6))
        self.btn_create = ctk.CTkButton(form, text="Criar Conta", width=180, command=self.tela_cadastro,
                                        fg_color=self.controller.light_green)
        self.btn_create.grid(row=6, column=0, pady=(2, 4))

    def tentar_login(self):
   
        usuario = self.input_user.get().strip()
        senha = self.input_pass.get().strip()
        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha usuário e senha.")
            return
        df = carregar_df_usuarios()
        row = df[df["usuario"] == usuario]
        if row.empty:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return
        if row.iloc[0]["senha"] != senha:
            messagebox.showerror("Erro", "Senha incorreta.")
            return
        self.input_user.delete(0, "end")
        self.input_pass.delete(0, "end")
        self.controller.login_success(usuario)

    def tela_cadastro(self):

        popup = ctk.CTkToplevel(self)
        popup.title("Criar Conta")
        popup.geometry("420x320")
        popup.transient(self)
        popup.grab_set()

        lbl = ctk.CTkLabel(popup, text="Crie sua conta", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(pady=12)
        in_user = ctk.CTkEntry(popup, placeholder_text="Usuário", width=340)
        in_user.pack(pady=8)
        in_pass = ctk.CTkEntry(popup, placeholder_text="Senha", show="*", width=340)
        in_pass.pack(pady=8)

        def confirmar():
            u = in_user.get().strip()
            s = in_pass.get().strip()
            if not u or not s:
                messagebox.showwarning("Aviso", "Preencha os campos.")
                return
            df = carregar_df_usuarios()
            if u in df["usuario"].values:
                messagebox.showerror("Erro", "Usuário já existe.")
                return
            novo = {"usuario": u, "senha": s, "reciclagem": 0, "agua_luz": 0, "habitos": 0, "gases": 0, "total": 0}
            df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
            salvar_df_usuarios(df)
            messagebox.showinfo("Sucesso", "Conta criada! Faça login.")
            popup.destroy()

        ctk.CTkButton(popup, text="Confirmar", command=confirmar, fg_color=self.controller.accent_green).pack(pady=14)

    def update_data(self):
        pass

class Frametabela(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=self.controller.bg_gray)
        cards_frame = ctk.CTkFrame(self, fg_color=self.controller.bg_gray)
        cards_frame.pack(fill="x", padx=20, pady=(18, 10))

        self.cards = {}
        categorias = [("Reciclagem", "reciclagem"), ("Água & Luz", "agua_luz"),
                      ("Hábitos Saudáveis", "habitos"), ("Emissão de Gases Poluentes", "gases")]
        for i, (label, key) in enumerate(categorias):
            card = ctk.CTkFrame(cards_frame, width=260, height=120, corner_radius=12, fg_color="#244f33")
            card.pack(side="left", padx=12, pady=4, expand=False)
            lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=14, weight="bold"))
            lbl.place(relx=0.04, rely=0.12)
            val = ctk.CTkLabel(card, text="0 pts", font=ctk.CTkFont(size=20))
            val.place(relx=0.04, rely=0.45)
            btn = ctk.CTkButton(card, text="Ver gráfico", width=110, command=lambda k=key: self._on_click_category(k),
                                fg_color=self.controller.accent_green)
            btn.place(relx=0.65, rely=0.56)
            self.cards[key] = {"frame": card, "label": lbl, "value": val, "button": btn}

        total_frame = ctk.CTkFrame(self, height=110, corner_radius=12, fg_color="#1f5a3a")
        total_frame.pack(fill="x", padx=20, pady=(8, 8))
        self.total_label = ctk.CTkLabel(total_frame, text="Pontuação Total", font=ctk.CTkFont(size=18, weight="bold"))
        self.total_label.place(relx=0.02, rely=0.12)
        self.total_value = ctk.CTkLabel(total_frame, text="0 pts", font=ctk.CTkFont(size=28, weight="bold"))
        self.total_value.place(relx=0.02, rely=0.45)
        chart_frame = ctk.CTkFrame(self, fg_color=self.controller.bg_gray)
        chart_frame.pack(fill="both", expand=True, padx=20, pady=(4, 20))
        self.fig, self.ax = plt.subplots(figsize=(9, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.current_chart_category = None

    def _on_click_category(self, cat_key):
        if self.current_chart_category == cat_key:
            self.current_chart_category = None
        else:
            self.current_chart_category = cat_key
        self.update_data()

    def update_data(self):
    
        df = carregar_df_usuarios()
        df = recalcular_total(df)
        usuario = self.controller.usuario_logado
        for key, d in self.cards.items():
            if usuario and usuario in df["usuario"].values:
                val = int(df.loc[df["usuario"] == usuario, key].iloc[0])
            else:
                val = 0
            d["value"].configure(text=f"{val} pts")

        if usuario and usuario in df["usuario"].values:
            tot = int(df.loc[df["usuario"] == usuario, "total"].iloc[0])
        else:
            tot = 0
        self.total_value.configure(text=f"{tot} pts")

        self.ax.clear()
        if self.current_chart_category is None:
            df_sorted = df.sort_values("total", ascending=False).head(10)
            users = df_sorted["usuario"].tolist()
            vals = df_sorted["total"].tolist()
            bars = self.ax.bar(users, vals, color=self.controller.light_green)
            self.ax.set_title("Top 10 - Pontos Totais")
            self.ax.set_ylabel("Pontos")
            if usuario in df["usuario"].values:
                for i, u in enumerate(users):
                    if u == usuario:
                        bars[i].set_color(self.controller.accent_green)
        else:
            cat = self.current_chart_category
            df_sorted = df.sort_values(cat, ascending=False).head(10)
            users = df_sorted["usuario"].tolist()
            vals = df_sorted[cat].tolist()
            bars = self.ax.bar(users, vals, color="#86c997")
            self.ax.set_title(f"Top 10 - {cat.capitalize()} (pontos atuais)")
            self.ax.set_ylabel("Pontos")
            if usuario in df["usuario"].values:
                for i, u in enumerate(users):
                    if u == usuario:
                        bars[i].set_color(self.controller.accent_green)
            if usuario and usuario in df["usuario"].values:
                user_pts = int(df.loc[df["usuario"] == usuario, cat].iloc[0])
                self.ax.text(0.99, 0.95, f"Seu {cat}: {user_pts} pts", transform=self.ax.transAxes, ha="right", va="top",
                             bbox=dict(facecolor="#1f5a3a", alpha=0.9, boxstyle="round,pad=0.5"), color="white")

        self.fig.tight_layout()
        self.canvas.draw_idle()

class FrameActions(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=self.controller.bg_gray)
        left = ctk.CTkFrame(self, fg_color=self.controller.bg_gray)
        left.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)
        right = ctk.CTkFrame(self, width=360, fg_color="#263e2d")
        right.pack(side="right", fill="y", padx=(10, 20), pady=20)

        ctk.CTkLabel(left, text="Registrar Ações Sustentáveis", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(6, 10))

        tasks = {
            "Separar o lixo corretamente": ("reciclagem", 15),
            "Evitar o uso de plástico descartável": ("reciclagem", 30),
            "Levar lixo a um ponto de reciclagem": ("reciclagem", 55),
            "Optar por produtos com embalagens recicláveis": ("reciclagem", 30),
            "Organizar um mutirão de coleta no bairro": ("reciclagem", 80),
            "Reutilizar lixo orgânico de forma inteligente": ("reciclagem", 40),
            "Diminuir tempo de banho para menos de 10 minutos": ("agua_luz", 35),
            "Desligar as luzes ao sair do cômodo": ("agua_luz", 15),
            "Fechar torneira ao escovar os dentes": ("agua_luz", 20),
            "Usar balde no lugar da mangueira": ("agua_luz", 40),
            "Aproveitar a luz natural": ("agua_luz", 50),
            "Reaproveitar água da máquina de lavar": ("agua_luz", 90),
            "Beber mais água e evitar refrigerante": ("habitos", 20),
            "Diminuir tempo nas redes sociais": ("habitos", 40),
            "Praticar atividade física": ("habitos", 35),
            "Ler um livro": ("habitos", 55),
            "Fazer trabalho voluntário ambiental": ("habitos", 100),
            "Caminhar em vez de usar carro": ("gases", 20),
            "Escolher alimentos locais/orgânicos": ("gases", 30),
            "Optar por transporte público ou bicicleta": ("gases", 20),
            "Evitar o uso de ar-condicionado": ("gases", 20),
            "Plantar uma árvore": ("gases", 80),
            "Fazer carona solidária": ("gases", 80),
        }
        self.check_vars = {}
        for text, (cat, pts) in tasks.items():
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(left, text=f"{text} (+{pts})", variable=var)
            cb.pack(anchor="w", pady=4)
            self.check_vars[text] = (var, cat, pts)

        ctk.CTkButton(left, text="Confirmar", command=self.confirmar, fg_color=self.controller.accent_green).pack(pady=12)
        ctk.CTkLabel(right, text="Seu Progresso", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(8, 6))
        self.summary = ctk.CTkTextbox(right, width=320, height=320, fg_color="#263e2d")
        self.summary.pack(pady=6, padx=8)
        self.summary.bind("<Key>", lambda e: "break")
        self.summary.bind("<Button-1>", lambda e: "break")

    def confirmar(self):

        usuario = self.controller.usuario_logado
        if not usuario:
            messagebox.showwarning("Aviso", "Faça login para registrar ações.")
            return
        df = carregar_df_usuarios()
        total_added = 0
        for text, (var, cat, pts) in self.check_vars.items():
            if var.get():
                df.loc[df["usuario"] == usuario, cat] += pts
                total_added += pts
        if total_added > 0:
            df = recalcular_total(df)
            salvar_df_usuarios(df)
            messagebox.showinfo("Sucesso", f"{total_added} pontos adicionados!")

            for text, (var, cat, pts) in self.check_vars.items():
                var.set(False)
            self.update_data()
        else:
            messagebox.showwarning("Aviso", "Nenhuma ação selecionada.")

    def update_data(self):

        usuario = self.controller.usuario_logado
        df = carregar_df_usuarios()
        if usuario and usuario in df["usuario"].values:
            row = df[df["usuario"] == usuario].iloc[0]
            txt = (f"Usuário: {usuario}\n\n"
                   f"Reciclagem: {row['reciclagem']} pts\n"
                   f"Água & Luz: {row['agua_luz']} pts\n"
                   f"Hábitos: {row['habitos']} pts\n"
                   f"Emissão de Gases Poluentes: {row['gases']} pts\n\n"
                   f"Total: {row['total']} pts\n")
        else:
            txt = "Faça login para ver seu progresso."
        self.summary.delete("0.0", "end")
        self.summary.insert("0.0", txt)

class FrameRanking(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=self.controller.bg_gray)

        ctk.CTkLabel(self, text="Usuário - Rankings", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 6))

        header = ctk.CTkFrame(self, fg_color=self.controller.bg_gray)
        header.pack(fill="x", padx=20)
        cols = ["Posição", "Usuário", "Reciclagem", "Água & Luz", "Hábitos Saudáveis", "Emissão de Gases Poluentes", "Total"]
        widths = [60, 240, 100, 100, 100, 100, 100]
        for i, (cname, w) in enumerate(zip(cols, widths)):
            lbl = ctk.CTkLabel(header, text=cname, width=w, anchor="w", font=ctk.CTkFont(size=11, weight="bold"))
            lbl.grid(row=0, column=i, padx=6)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=20, pady=12)

    def update_data(self):

        for w in self.scroll.winfo_children():
            w.destroy()
        df = carregar_df_usuarios()
        df = recalcular_total(df)
        df_sorted = df.sort_values("total", ascending=False).reset_index(drop=True)
        for i, row in df_sorted.iterrows():
            r = ctk.CTkFrame(self.scroll, fg_color="#263e2d")
            r.pack(fill="x", pady=6, padx=6)
            ctk.CTkLabel(r, text=f"{i+1}", width=60).grid(row=0, column=0, padx=6, pady=8)
            ctk.CTkLabel(r, text=row["usuario"], width=240).grid(row=0, column=1, padx=6)
            ctk.CTkLabel(r, text=f"{int(row['reciclagem'])}", width=100).grid(row=0, column=2, padx=6)
            ctk.CTkLabel(r, text=f"{int(row['agua_luz'])}", width=100).grid(row=0, column=3, padx=6)
            ctk.CTkLabel(r, text=f"{int(row['habitos'])}", width=100).grid(row=0, column=4, padx=6)
            ctk.CTkLabel(r, text=f"{int(row['gases'])}", width=100).grid(row=0, column=5, padx=6)
            ctk.CTkLabel(r, text=f"{int(row['total'])}", width=100).grid(row=0, column=6, padx=6)

class FramePerformance(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=self.controller.bg_gray)

        ctk.CTkLabel(self, text="Desempenho", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 8))
        chart_frame = ctk.CTkFrame(self)
        chart_frame.pack(fill="both", expand=True, padx=20, pady=(4, 8))
        self.fig, self.ax = plt.subplots(figsize=(8, 3.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        small_chart_frame = ctk.CTkFrame(self)
        small_chart_frame.pack(fill="x", padx=20, pady=(4, 6))
        self.fig2, self.ax2 = plt.subplots(figsize=(8, 2))
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=small_chart_frame)
        self.canvas2.get_tk_widget().pack(fill="both", expand=True)
        bottom = ctk.CTkFrame(self, fg_color="#263e2d")
        bottom.pack(fill="x", padx=20, pady=(6, 18))
        ctk.CTkLabel(bottom, text="Dicas para melhorar:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(8, 6), padx=12)
        self.tips_box = ctk.CTkTextbox(bottom, width=920, height=160, fg_color="#263e2d")
        self.tips_box.pack(padx=12, pady=(0, 12))
        self.tips_box.bind("<Key>", lambda e: "break")
        self.tips_box.bind("<Button-1>", lambda e: "break")

    def update_data(self):

        usuario = self.controller.usuario_logado
        df = carregar_df_usuarios()
        df = recalcular_total(df)

        if not usuario or usuario not in df["usuario"].values:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "Faça login para ver seu desempenho", ha="center", va="center", fontsize=14, color="white")
            self.canvas.draw_idle()

            self.ax2.clear()
            self.ax2.text(0.5, 0.5, "Gráfico de comparação semanal indisponível (login necessário)", ha="center", va="center", fontsize=10, color="white")
            self.canvas2.draw_idle()

            self.tips_box.delete("0.0", "end")
            self.tips_box.insert("0.0", "Faça login para ver dicas personalizadas.")
            return

        row = df[df["usuario"] == usuario].iloc[0]
        cats = ["reciclagem", "agua_luz", "habitos", "gases"]
        labels = ["Reciclagem", "Água & Luz", "Hábitos Saudáveis", "Emissão de Gases Poluentes"]
        values = [int(row[c]) for c in cats]

        self.ax.clear()
        bars = self.ax.bar(labels, values, color=[self.controller.light_green, "#7fc6d1", "#fae415", "#f0a657"])
        self.ax.set_title(f"Pontuação atual por categoria — {usuario}")
        self.ax.set_ylabel("Pontos")
        for rect, val in zip(bars, values):
            height = rect.get_height()
            self.ax.text(rect.get_x() + rect.get_width() / 2.0, height + max(3, height * 0.03), f"{val}", ha="center", va="bottom", color="white", fontsize=10, fontweight="bold")
        self.fig.tight_layout()
        self.canvas.draw_idle()
        hist = pd.read_csv(ARQUIVO_HISTORICO)
        hist_user = hist[hist["usuario"] == usuario].copy()

        if hist_user.empty:
            self.ax2.clear()
            self.ax2.text(0.5, 0.5, "Sem histórico semanal (nenhum reset anterior).", ha="center", va="center", fontsize=10, color="white")
            self.canvas2.draw_idle()
        else:
            try:
                hist_user["data_iso"] = pd.to_datetime(hist_user["data_iso"]).dt.date
                hist_user = hist_user.sort_values("data_iso")
                ultima = hist_user.iloc[-1]
                anterior = None
                if len(hist_user) >= 2:
                    anterior = hist_user.iloc[-2]
                melhor_total = hist_user["total"].max()
                melhor_row = hist_user[hist_user["total"] == melhor_total].iloc[0]

                atual_total = int(row["total"])
                labels_line = []
                values_line = []
                if anterior is not None:
                    labels_line.append("Semana\nAnterior")
                    values_line.append(int(anterior["total"]))
                labels_line.append("Melhor\nSemana")
                values_line.append(int(melhor_row["total"]))
                labels_line.append("Semana\nAtual")
                values_line.append(atual_total)

                self.ax2.clear()
                x = range(len(values_line))
                self.ax2.plot(x, values_line, marker='o', linestyle='-', color=self.controller.light_green)
                self.ax2.set_xticks(x)
                self.ax2.set_xticklabels(labels_line)
                self.ax2.set_title("Comparação: Semana Anterior / Melhor / Atual (totais)")
                for xi, yi in zip(x, values_line):
                    self.ax2.text(xi, yi + max(1, yi * 0.03), str(yi), ha="center", color="white")
                self.fig2.tight_layout()
                self.canvas2.draw_idle()
            except Exception:
                self.ax2.clear()
                self.ax2.text(0.5, 0.5, "Erro ao processar histórico.", ha="center", va="center", fontsize=10, color="white")
                self.canvas2.draw_idle()

        dicas = []
        for cat, label, val in zip(cats, labels, values):
            meta = META_POR_CATEGORIA.get(cat, 100)
            if val < meta:
                if cat == "reciclagem":
                    dicas.append(f" {label} — Separe lixo de papel, plástico e metal e leve a pontos de coleta.\n\n")
                elif cat == "agua_luz":
                    dicas.append(f" {label} — Reduza o tempo de banho e feche a torneira enquanto não estiver usando.\n\n")
                elif cat == "habitos":
                    dicas.append(f" {label} — Se exercite e faça refeições saudáveis.\n\n")
                elif cat == "gases":
                    dicas.append(f" {label} — Prefira transporte público, bicicleta ou caronas.\n\n")

        self.tips_box.delete("0.0", "end")
        if len(dicas) == 0:
            self.tips_box.insert("0.0", " Parabéns! Você atingiu todas as metas, continue assim!\n\n")
        else:
            for d in dicas:
                self.tips_box.insert("end", d)

ProjetoEcoScore()
ProjetoEcoScore().mainloop()