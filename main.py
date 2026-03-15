import customtkinter
import os
import time
import math
import csv
import json
from datetime import datetime, timedelta
import tkinter
from tkinter import messagebox, simpledialog

# Tenta importar o matplotlib para os gráficos
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# Tenta importar pystray e PIL para o ícone da bandeja do sistema
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None


class CronometroEstudo:
    def __init__(self):
        # Configuração inicial de aparência e tema
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("dark-blue")

        # Janela principal (auto-dimensionável)
        self.root = customtkinter.CTk()
        self.root.title("Cronômetro & Estatísticas de Estudo")
        self.root.geometry("500x600")
        self.root.minsize(500, 600)
        try:
            self.root.iconbitmap("app_icon.ico")  # Certifique-se de ter um arquivo chamado app_icon.ico
        except Exception as e:
            print("Ícone não encontrado:", e)

        # Variáveis de controle do tempo e modos
        self.daily_target = 60 * 60  # Tempo alvo diário em segundos (padrão: 60 min)
        self.pomodoro_mode = False
        self.in_break = False
        self.session_time = 0         # Para modo contínuo
        self.focus_time = 0           # Tempo de foco na sessão Pomodoro (atual segmento)
        self.break_time = 0           # Tempo de pausa na sessão Pomodoro
        self.total_focus = 0          # Acumula todos os períodos de foco na sessão Pomodoro
        self.running = False          # Sessão ativa ou não
        self.last_update = time.time()
        self.current_mode = "Contínuo"  # ou "Pomodoro"

        # Lista de matérias (disponível para o usuário)
        self.subjects = ["Geral", "Matemática", "Português", "Inglês", "História", "Ciências"]
        self.current_subject = "Geral"

        # Arquivo CSV para histórico de sessões (cria com cabeçalho, se não existir)
        self.history_file = "historico.csv"
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["data", "categoria", "duracao", "modo"])

        # Cria uma interface com abas para separar funcionalidades
        self.tabview = customtkinter.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabview.add("Estudo")
        self.tabview.add("Relatórios")
        self.tabview.add("Configurações")
        self.tab_estudo = self.tabview.tab("Estudo")
        self.tab_relatorios = self.tabview.tab("Relatórios")
        self.tab_config = self.tabview.tab("Configurações")

        # ----------------------------
        # Aba "Estudo"
        # ----------------------------
        # Label do cronômetro (mostra tempo da sessão ou de foco/pausa no Pomodoro)
        self.timer_label = customtkinter.CTkLabel(
            master=self.tab_estudo, text="Sessão: 00:00:00", font=("Arial", 24)
        )
        self.timer_label.pack(pady=10)

        # Barra de progresso (representa o avanço até atingir o tempo alvo)
        self.progress_bar = customtkinter.CTkProgressBar(master=self.tab_estudo)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, fill="x", padx=20)

        # Menu para selecionar a matéria
        self.subject_menu = customtkinter.CTkOptionMenu(
            master=self.tab_estudo, values=self.subjects, command=self.set_subject
        )
        self.subject_menu.set("Geral")
        self.subject_menu.pack(pady=10)

        # Botão para iniciar/pausar a sessão
        self.toggle_button = customtkinter.CTkButton(
            master=self.tab_estudo, text="Iniciar", command=self.toggle_pause
        )
        self.toggle_button.pack(pady=10)

        # Botão para registrar horas manualmente (caso o usuário estude offline)
        self.manual_button = customtkinter.CTkButton(
            master=self.tab_estudo, text="Registrar Manualmente", command=self.registrar_manual
        )
        self.manual_button.pack(pady=10)

        # Exibe o tempo investido em cada matéria
        self.subject_stats_label = customtkinter.CTkLabel(
            master=self.tab_estudo, text="Tempo Investido por Matéria:\n", font=("Arial", 12)
        )
        self.subject_stats_label.pack(pady=10)
        self.atualizar_estatisticas_materias()

        # ----------------------------
        # Aba "Relatórios"
        # ----------------------------
        self.graph_button = customtkinter.CTkButton(
            master=self.tab_relatorios, text="Gerar Gráfico", command=self.gerar_grafico
        )
        self.graph_button.pack(pady=10)

        self.history_button = customtkinter.CTkButton(
            master=self.tab_relatorios, text="Histórico Completo", command=self.mostrar_historico
        )
        self.history_button.pack(pady=10)

        self.stats_label = customtkinter.CTkLabel(
            master=self.tab_relatorios, text="Estatísticas: ", font=("Arial", 16)
        )
        self.stats_label.pack(pady=10)

        # ----------------------------
        # Aba "Configurações"
        # ----------------------------
        # Tempo alvo diário (minutos)
        self.label_target = customtkinter.CTkLabel(
            master=self.tab_config, text="Tempo Alvo Diário (min):", font=("Arial", 14)
        )
        self.label_target.pack(pady=5)
        self.entry_target = customtkinter.CTkEntry(master=self.tab_config, width=60)
        self.entry_target.insert(0, str(self.daily_target // 60))
        self.entry_target.pack(pady=5)
        self.btn_set_target = customtkinter.CTkButton(
            master=self.tab_config, text="Definir Tempo Alvo", command=self.definir_tempo_alvo
        )
        self.btn_set_target.pack(pady=5)

        # Ciclos Pomodoro
        self.label_pomodoro = customtkinter.CTkLabel(
            master=self.tab_config, text="Ciclos Pomodoro:", font=("Arial", 14)
        )
        self.label_pomodoro.pack(pady=5)
        self.entry_pomodoro_cycles = customtkinter.CTkEntry(master=self.tab_config, width=60)
        self.entry_pomodoro_cycles.insert(0, "4")
        self.entry_pomodoro_cycles.pack(pady=5)

        # Seleção de tema
        self.label_tema = customtkinter.CTkLabel(
            master=self.tab_config, text="Tema:", font=("Arial", 14)
        )
        self.label_tema.pack(pady=5)
        self.temas = ["dark-blue", "green", "purple", "light"]
        self.option_tema = customtkinter.CTkOptionMenu(
            master=self.tab_config, values=self.temas, command=self.alterar_tema
        )
        self.option_tema.set("dark-blue")
        self.option_tema.pack(pady=5)

        # Toggle para ativar/desativar Modo Pomodoro
        self.toggle_pomodoro = customtkinter.CTkButton(
            master=self.tab_config, text="Ativar Modo Pomodoro", command=self.toggle_pomodoro_mode
        )
        self.toggle_pomodoro.pack(pady=5)

        # Botão para exportar os dados para JSON
        self.export_button = customtkinter.CTkButton(
            master=self.tab_config, text="Exportar Dados (JSON)", command=self.exportar_dados
        )
        self.export_button.pack(pady=5)

        # Botão para simular backup na nuvem
        self.backup_button = customtkinter.CTkButton(
            master=self.tab_config, text="Backup na Nuvem", command=self.backup_nuvem
        )
        self.backup_button.pack(pady=5)

        # Adicionar nova matéria
        self.label_adicionar_materia = customtkinter.CTkLabel(
            master=self.tab_config, text="Adicionar Matéria:", font=("Arial", 14)
        )
        self.label_adicionar_materia.pack(pady=5)
        self.entry_adicionar_materia = customtkinter.CTkEntry(master=self.tab_config, width=140)
        self.entry_adicionar_materia.pack(pady=5)
        self.btn_adicionar_materia = customtkinter.CTkButton(
            master=self.tab_config, text="Adicionar", command=self.adicionar_materia
        )
        self.btn_adicionar_materia.pack(pady=5)

        # Botão para minimizar para a bandeja do sistema (se pystray estiver disponível)
        if pystray is not None:
            self.btn_tray = customtkinter.CTkButton(
                master=self.tab_config, text="Minimizar para Tray", command=self.minimizar_para_tray
            )
            self.btn_tray.pack(pady=5)

        # Atualiza o cronômetro a cada segundo
        self.atualizar_cronometro()

        # Ao fechar a janela, registra a sessão atual e encerra adequadamente
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    # Atualiza o assunto selecionado
    def set_subject(self, value):
        self.current_subject = value

    # Alterna entre iniciar e pausar a sessão
    def toggle_pause(self):
        if not self.running:
            # Inicia a sessão
            self.running = True
            self.last_update = time.time()
            self.toggle_button.configure(text="Pausar")
        else:
            # Pausa a sessão e registra o tempo acumulado
            if self.pomodoro_mode:
                duration = self.total_focus
                mode = "Pomodoro"
                self.total_focus = 0
                self.focus_time = 0
                self.break_time = 0
                self.in_break = False
            else:
                duration = self.session_time
                mode = "Contínuo"
                self.session_time = 0
            if duration > 0:
                self.registrar_sessao(duration, mode)
            self.running = False
            self.toggle_button.configure(text="Iniciar")

    # Atualiza o cronômetro a cada segundo; adapta o modo Pomodoro conforme o tempo alvo e ciclos definidos
    def atualizar_cronometro(self):
        if self.running:
            current_time = time.time()
            elapsed = int(current_time - self.last_update)
            if elapsed >= 1:
                self.last_update = current_time
                if self.pomodoro_mode:
                    try:
                        cycles = int(self.entry_pomodoro_cycles.get())
                    except:
                        cycles = 4
                    if cycles < 1:
                        cycles = 1
                    # Cálculo baseado em 90% do tempo para foco e 10% para pausas
                    focus_interval = int(self.daily_target * 0.9 / cycles)
                    break_interval = int(self.daily_target * 0.1 / (cycles - 1)) if cycles > 1 else 0

                    if not self.in_break:
                        self.focus_time += elapsed
                        self.total_focus += elapsed
                        if self.focus_time >= focus_interval:
                            messagebox.showinfo("Pomodoro", f"Fim do foco! Iniciando pausa de {break_interval//60} minutos.")
                            self.in_break = True
                            self.break_time = 0
                    else:
                        self.break_time += elapsed
                        if self.break_time >= break_interval:
                            messagebox.showinfo("Pomodoro", "Pausa encerrada. Retomando foco.")
                            self.in_break = False
                            self.focus_time = 0
                else:
                    self.session_time += elapsed

                if self.pomodoro_mode:
                    if self.in_break:
                        tempo_display = str(timedelta(seconds=self.break_time))
                        mode_text = "Pausa"
                    else:
                        tempo_display = str(timedelta(seconds=self.focus_time))
                        mode_text = "Foco"
                    self.timer_label.configure(text=f"{mode_text}: {tempo_display}")
                    progress = self.total_focus / self.daily_target
                else:
                    self.timer_label.configure(text="Sessão: " + str(timedelta(seconds=self.session_time)))
                    progress = self.session_time / self.daily_target

                progress = min(progress, 1)
                self.progress_bar.set(progress)
        self.root.after(1000, self.atualizar_cronometro)

    # Registra a sessão atual no histórico (arquivo CSV)
    def registrar_sessao(self, duration, mode):
        with open(self.history_file, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([now, self.current_subject, duration, mode])

    # Permite ao usuário registrar horas manualmente (caso o cronômetro não esteja ligado)
    def registrar_manual(self):
        try:
            minutos = float(simpledialog.askstring("Registro Manual", "Digite minutos estudados:"))
            duration = int(minutos * 60)
            self.registrar_sessao(duration, "Manual")
            messagebox.showinfo("Registro Manual", f"{minutos} minutos registrados manualmente.")
        except Exception as e:
            messagebox.showerror("Erro", "Entrada inválida.")

    # Define o tempo alvo diário a partir do valor inserido (minutos)
    def definir_tempo_alvo(self):
        try:
            minutos = float(self.entry_target.get())
            self.daily_target = int(minutos * 60)
            messagebox.showinfo("Tempo Alvo", f"Tempo alvo diário definido para {minutos} minutos.")
        except Exception as e:
            messagebox.showerror("Erro", "Por favor, insira um número válido.")

    # Altera o tema da interface
    def alterar_tema(self, tema):
        customtkinter.set_default_color_theme(tema)
        messagebox.showinfo("Tema", f"Tema alterado para {tema}.")

    # Alterna o modo Pomodoro
    def toggle_pomodoro_mode(self):
        self.pomodoro_mode = not self.pomodoro_mode
        if self.pomodoro_mode:
            self.toggle_pomodoro.configure(text="Desativar Modo Pomodoro")
            self.current_mode = "Pomodoro"
            self.focus_time = 0
            self.break_time = 0
            self.total_focus = 0
            self.in_break = False
            messagebox.showinfo("Pomodoro", "Modo Pomodoro ativado.\nO tempo de foco e pausa será calculado com base no tempo alvo diário e nos ciclos definidos.")
        else:
            self.toggle_pomodoro.configure(text="Ativar Modo Pomodoro")
            self.current_mode = "Contínuo"
            messagebox.showinfo("Pomodoro", "Modo Pomodoro desativado.")

    # Exporta os dados do histórico para um arquivo JSON
    def exportar_dados(self):
        if not os.path.exists(self.history_file):
            messagebox.showerror("Erro", "Arquivo de histórico não encontrado.")
            return
        data = []
        with open(self.history_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        with open("historico.json", "w") as jsonfile:
            json.dump(data, jsonfile, indent=4)
        messagebox.showinfo("Exportar Dados", "Dados exportados para historico.json com sucesso.")

    # Simula o backup dos dados na nuvem (apenas simulação)
    def backup_nuvem(self):
        messagebox.showinfo("Backup", "Backup realizado com sucesso na nuvem (simulação).")

    # Gera um gráfico das horas de estudo diárias usando matplotlib
    def gerar_grafico(self):
        if plt is None:
            messagebox.showerror("Erro", "Matplotlib não está instalado.")
            return

        data_agg = {}
        with open(self.history_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                date_str = row["data"].split(" ")[0]
                try:
                    duracao = int(row["duracao"])
                except:
                    continue
                data_agg[date_str] = data_agg.get(date_str, 0) + duracao / 3600  # em horas

        if data_agg:
            dates = sorted(data_agg.keys())[-7:]
            hours = [data_agg[d] for d in dates]
        else:
            dates = []
            hours = []

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.bar(dates, hours, color='skyblue')
        ax.set_title("Horas de Estudo Diárias")
        ax.set_ylabel("Horas")
        if hours:
            ax.set_ylim(0, max(hours + [self.daily_target / 3600, 1]))
        else:
            ax.set_ylim(0, self.daily_target / 3600 if self.daily_target > 0 else 1)

        total = self.calcular_total_estudado() / 3600
        avg = sum(hours) / len(hours) if hours else 0
        if total < 10:
            level = "Iniciante"
        elif total < 50:
            level = "Avançado"
        else:
            level = "Mestre do estudo"
        self.stats_label.configure(
            text=f"Total Estudado: {total:.2f}h | Média: {avg:.2f}h/dia | Nível: {level}"
        )

        top = customtkinter.CTkToplevel(self.root)
        top.title("Gráfico de Estudo Diário")
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack()

    # Mostra o histórico completo em uma nova janela
    def mostrar_historico(self):
        top = customtkinter.CTkToplevel(self.root)
        top.title("Histórico Completo")
        txt = tkinter.Text(top, width=80, height=20)
        txt.pack()
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as csvfile:
                content = csvfile.read()
                txt.insert("end", content)
        else:
            txt.insert("end", "Nenhum registro encontrado.")

    # Calcula o total de tempo estudado (em segundos) a partir do histórico
    def calcular_total_estudado(self):
        total = 0
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        total += int(row["duracao"])
                    except:
                        pass
        return total

    # Atualiza as estatísticas de tempo investido por matéria e as exibe na UI
    def atualizar_estatisticas_materias(self):
        subject_totals = {}
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        duracao = int(row["duracao"])
                    except:
                        duracao = 0
                    subject = row["categoria"]
                    subject_totals[subject] = subject_totals.get(subject, 0) + duracao
        text = "Tempo Investido por Matéria:\n"
        for subj, secs in subject_totals.items():
            text += f"{subj}: {str(timedelta(seconds=secs))}\n"
        self.subject_stats_label.configure(text=text)
        self.root.after(5000, self.atualizar_estatisticas_materias)

    # Adiciona uma nova matéria à lista de matérias
    def adicionar_materia(self):
        nova_materia = self.entry_adicionar_materia.get().strip()
        if nova_materia and nova_materia not in self.subjects:
            self.subjects.append(nova_materia)
            self.subject_menu.configure(values=self.subjects)
            messagebox.showinfo("Matéria", f"Matéria '{nova_materia}' adicionada.")
        else:
            messagebox.showerror("Erro", "Matéria inválida ou já existente.")

    # Minimiza para a bandeja do sistema usando pystray
    def minimizar_para_tray(self):
        self.root.withdraw()  # Esconde a janela principal
        if pystray is not None:
            image = self.criar_imagem_tray()
            menu = pystray.Menu(
                pystray.MenuItem("Abrir", self.mostrar_janela),
                pystray.MenuItem("Sair", self.sair_tray)
            )
            self.tray_icon = pystray.Icon("app", image, "Cronômetro de Estudo", menu)
            # Executa o ícone da bandeja em um thread separado
            self.tray_icon.run()

    # Cria uma imagem para o ícone da bandeja (usando PIL)
    def criar_imagem_tray(self):
        image = Image.new('RGB', (64, 64), color="black")
        dc = ImageDraw.Draw(image)
        dc.ellipse((0, 0, 64, 64), fill="blue")
        return image

    # Callback para mostrar a janela principal ao clicar no tray
    def mostrar_janela(self, icon, item):
        self.root.after(0, self.mostrar_janela_callback)

    def mostrar_janela_callback(self):
        self.root.deiconify()
        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            self.tray_icon.stop()
            self.tray_icon = None

    # Sai do aplicativo a partir do ícone da bandeja
    def sair_tray(self, icon, item):
        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            self.tray_icon.stop()
        self.root.destroy()

    # Ao fechar a janela, registra a sessão atual (se houver) e encerra o aplicativo
    def on_close(self):
        if self.running:
            if self.pomodoro_mode:
                duration = self.total_focus
            else:
                duration = self.session_time
            if duration > 0:
                mode = "Pomodoro" if self.pomodoro_mode else "Contínuo"
                self.registrar_sessao(duration, mode)
        self.root.destroy()


if __name__ == "__main__":
    CronometroEstudo()