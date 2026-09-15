import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import serial
import serial.tools.list_ports
import time
import json
import os
from threading import Thread, Lock

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

def get_asset_path(filename):
    """ Busca un archivo de imagen en múltiples ubicaciones relativas posibles """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    candidates = [
        os.path.join(base_dir, "assets", filename),
        os.path.join(base_dir, "..", "assets", filename),
        os.path.join(cwd, "assets", filename),
        os.path.join(cwd, filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None

class RobotArmController(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Control - ESP32-C3")
        # Resolución 1280x720 HD
        self.geometry("1280x720")
        self.resizable(False, False)
        self.configure(fg_color="#0A0A0A") # Marco exterior negro profundo

        self.ser = None
        self.ser_lock = Lock()
        self.recorded_sequence = []
        self.is_playing = False

        self.current_speed = 75
        self.last_sent_angles = {}
        self.last_send_time = {}

        self.servos = [
            {"id": 0},
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ]

        self.sliders = []
        self.angle_labels = []

        self._build_ui()

    def _build_ui(self):
        # Panel Principal Blanco con Marco Oscuro Exterior Elegante y Esquinas Redondeadas
        self.main_panel = ctk.CTkFrame(
            self, 
            fg_color="#FFFFFF", 
            corner_radius=30
        )
        self.main_panel.pack(fill="both", expand=True, padx=12, pady=12)

        # --- IMAGEN DE FONDO (assets/Fondo.png) ---
        bg_path = get_asset_path("Fondo.png") or get_asset_path("fondo.png")

        if bg_path:
            pil_bg = Image.open(bg_path)
            # Tamaño interior exacto para 1280x720 con padding de 12px (1256x696)
            self.bg_ctk_img = ctk.CTkImage(light_image=pil_bg, dark_image=pil_bg, size=(1256, 696))
            self.bg_label = ctk.CTkLabel(self.main_panel, image=self.bg_ctk_img, text="", corner_radius=26)
            self.bg_label.place(x=0, y=0)

        # --- CABECERA SUPERIOR ---
        # Botón PUERTO (Arriba Izquierda)
        self.btn_puerto = ctk.CTkButton(
            self.main_panel,
            text="PUERTO",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#202020",
            hover_color="#333333",
            text_color="#FFFFFF",
            corner_radius=20,
            width=125,
            height=40,
            command=self.open_port_window
        )
        self.btn_puerto.place(x=35, y=25)

        # Botones Minimizar y Cerrar (Arriba Derecha)
        self.btn_min = ctk.CTkButton(
            self.main_panel,
            text="Minimizar",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#202020",
            hover_color="#333333",
            text_color="#FFFFFF",
            corner_radius=18,
            width=100,
            height=38,
            command=self.iconify
        )
        self.btn_min.place(x=990, y=25)

        self.btn_close = ctk.CTkButton(
            self.main_panel,
            text="Cerrar",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#202020",
            hover_color="#333333",
            text_color="#FFFFFF",
            corner_radius=18,
            width=85,
            height=38,
            command=self.destroy
        )
        self.btn_close.place(x=1105, y=25)

        # --- BOTONES DE ACCIÓN IZQUIERDOS (GUARDAR, REPRODUCIR, DETENER) ---
        left_btns = [
            ("GUARDAR", self.save_current_pose, 200),
            ("REPRODUCIR", self.play_sequence, 285),
            ("DETENER", self.stop_sequence, 370),
        ]

        for text, cmd, y_pos in left_btns:
            btn = ctk.CTkButton(
                self.main_panel,
                text=text,
                font=ctk.CTkFont(size=15, weight="bold"),
                fg_color="#202020",
                hover_color="#383838",
                text_color="#FFFFFF",
                corner_radius=22,
                width=150,
                height=48,
                command=cmd
            )
            btn.place(x=35, y=y_pos)

        # --- BOTONES DE ACCIÓN DERECHOS (EXPORTAR, IMPORTAR, REINICIAR) ---
        right_btns = [
            ("EXPORTAR", self.export_sequence, 200),
            ("IMPORTAR", self.import_sequence, 285),
            ("REINICIAR", self.reset_all_home, 370),
        ]

        for text, cmd, y_pos in right_btns:
            btn = ctk.CTkButton(
                self.main_panel,
                text=text,
                font=ctk.CTkFont(size=15, weight="bold"),
                fg_color="#202020",
                hover_color="#383838",
                text_color="#FFFFFF",
                corner_radius=22,
                width=150,
                height=48,
                command=cmd
            )
            btn.place(x=1040, y=y_pos)

        # --- 4 SLIDERS DE CONTROL DE SERVOS ---
        slider_y_positions = [200, 270, 340, 410]

        for i, (servo, y_pos) in enumerate(zip(self.servos, slider_y_positions)):
            slider_frame = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=22, width=400, height=44)
            slider_frame.place(x=535, y=y_pos)
            slider_frame.pack_propagate(False)

            slider = ctk.CTkSlider(
                slider_frame,
                from_=0,
                to=180,
                number_of_steps=180,
                fg_color="#202020",
                progress_color="#202020",
                button_color="#FFFFFF",
                button_hover_color="#F0F0F0",
                width=360,
                height=20,
                button_length=20,
                command=lambda val, s_id=servo['id']: self.on_slider_change(s_id, val)
            )
            slider.set(90)
            slider.place(relx=0.5, rely=0.5, anchor="center")
            self.sliders.append(slider)

            val_frame = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=22, width=65, height=44)
            val_frame.place(x=945, y=y_pos)
            val_frame.pack_propagate(False)

            val_lbl = ctk.CTkLabel(
                val_frame,
                text="90°",
                font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
                text_color="#FFFFFF"
            )
            val_lbl.place(relx=0.5, rely=0.5, anchor="center")
            self.angle_labels.append(val_lbl)

        # --- SLIDER DE VELOCIDAD (Sin texto 'VELOCIDAD') ---
        speed_y_pos = 480

        speed_frame = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=22, width=400, height=44)
        speed_frame.place(x=535, y=speed_y_pos)
        speed_frame.pack_propagate(False)

        self.speed_slider = ctk.CTkSlider(
            speed_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            fg_color="#202020",
            progress_color="#00E5FF",
            button_color="#FFFFFF",
            button_hover_color="#F0F0F0",
            width=360,
            height=20,
            button_length=20,
            command=self.on_speed_change
        )
        self.speed_slider.set(75)
        self.speed_slider.place(relx=0.5, rely=0.5, anchor="center")

        speed_val_frame = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=22, width=65, height=44)
        speed_val_frame.place(x=945, y=speed_y_pos)
        speed_val_frame.pack_propagate(False)

        self.lbl_speed_val = ctk.CTkLabel(
            speed_val_frame,
            text="75%",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#00E5FF"
        )
        self.lbl_speed_val.place(relx=0.5, rely=0.5, anchor="center")

        # --- TARJETA INFORMATIVA E INFERIOR (ESTADO) ---
        self.info_card = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=20, width=540, height=68)
        self.info_card.place(relx=0.5, y=560, anchor="n")
        self.info_card.pack_propagate(False)

        info_line1 = ctk.CTkLabel(
            self.info_card,
            text="Sistema de Control | ESP32-C3 SuperMini",
            font=ctk.CTkFont(size=11),
            text_color="#DDDDDD"
        )
        info_line1.pack(pady=(6, 0))

        self.lbl_status = ctk.CTkLabel(
            self.info_card,
            text="¡Bienvenido! Por favor, seleccione un puerto COM para comenzar",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00E5FF"
        )
        self.lbl_status.pack(pady=(2, 6))

    # --- POPUP PUERTO COM ---
    def open_port_window(self):
        port_win = ctk.CTkToplevel(self)
        port_win.title("Seleccionar Puerto COM")
        port_win.geometry("360x200")
        port_win.resizable(False, False)
        port_win.grab_set()

        ctk.CTkLabel(port_win, text="Puerto USB / COM", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(16, 5))

        ports = self.get_ports()
        combo = ctk.CTkOptionMenu(port_win, values=ports, width=220, fg_color="#202020")
        combo.pack(pady=10)
        if ports and ports[0] != "No detectado":
            combo.set(ports[0])

        btn_frame = ctk.CTkFrame(port_win, fg_color="transparent")
        btn_frame.pack(pady=10)

        def connect_action():
            selected = combo.get()
            if selected == "No detectado":
                messagebox.showwarning("Puerto no encontrado", "Conecte el ESP32-C3.")
                return

            try:
                with self.ser_lock:
                    if self.ser and self.ser.is_open:
                        self.ser.close()

                    self.ser = serial.Serial(
                        selected, 
                        115200, 
                        timeout=0.1, 
                        write_timeout=0.2
                    )
                    self.ser.dtr = False
                    self.ser.rts = False

                time.sleep(1.0)
                self._send_speed_async(self.current_speed)

                self.btn_puerto.configure(fg_color="#2b8a3e")
                self.lbl_status.configure(text=f"Estado: Conectado en {selected} @ 115200 baudios", text_color="#2b8a3e")
                port_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo conectar a {selected}:\n{e}")

        def disconnect_action():
            with self.ser_lock:
                if self.ser and self.ser.is_open:
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                    self.ser = None
            self.btn_puerto.configure(fg_color="#202020")
            self.lbl_status.configure(text="Estado: Desconectado", text_color="#00E5FF")
            port_win.destroy()

        ctk.CTkButton(btn_frame, text="Conectar", fg_color="#2b8a3e", width=100, command=connect_action).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Desconectar", fg_color="#c93b2b", width=100, command=disconnect_action).pack(side="left", padx=5)

    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["No detectado"]

    def _send_cmd_async(self, servo_id, angle):
        if not self.ser or not self.ser.is_open:
            return

        now = time.time()
        if self.last_sent_angles.get(servo_id) == angle:
            return
        if now - self.last_send_time.get(servo_id, 0) < 0.035:
            return

        self.last_send_time[servo_id] = now
        self.last_sent_angles[servo_id] = angle

        def _worker():
            try:
                with self.ser_lock:
                    if self.ser and self.ser.is_open:
                        cmd = f"{servo_id}:{angle}\n"
                        self.ser.write(cmd.encode("utf-8"))
            except Exception:
                pass

        Thread(target=_worker, daemon=True).start()

    def _send_speed_async(self, speed):
        if not self.ser or not self.ser.is_open:
            return

        def _worker():
            try:
                with self.ser_lock:
                    if self.ser and self.ser.is_open:
                        cmd = f"S:{speed}\n"
                        self.ser.write(cmd.encode("utf-8"))
            except Exception:
                pass

        Thread(target=_worker, daemon=True).start()

    def on_speed_change(self, value):
        self.current_speed = int(value)
        self.lbl_speed_val.configure(text=f"{self.current_speed}%")
        self._send_speed_async(self.current_speed)

    def on_slider_change(self, servo_id, value):
        angle = int(value)
        self.angle_labels[servo_id].configure(text=f"{angle}°")
        self._send_cmd_async(servo_id, angle)

    def save_current_pose(self):
        current_angles = [int(slider.get()) for slider in self.sliders]
        self.recorded_sequence.append(current_angles)
        self.lbl_status.configure(text=f"Posición guardada #{len(self.recorded_sequence)}: {current_angles}", text_color="#2b8a3e")

    def play_sequence(self):
        if not self.recorded_sequence:
            messagebox.showinfo("Secuencia Vacía", "No hay posiciones guardadas.")
            return

        if self.is_playing:
            return

        self.is_playing = True

        def loop_play():
            for idx, angles in enumerate(self.recorded_sequence):
                if not self.is_playing:
                    break
                
                self.lbl_status.configure(text=f"Paso {idx+1}/{len(self.recorded_sequence)}: {angles}", text_color="#00E5FF")
                for s_id, angle in enumerate(angles):
                    self.sliders[s_id].set(angle)
                    self.angle_labels[s_id].configure(text=f"{angle}°")
                    self._send_cmd_async(s_id, angle)
                
                pause_time = max(0.2, 1.6 - (self.current_speed * 0.013))
                time.sleep(pause_time)

            self.is_playing = False
            self.lbl_status.configure(text="Reproducción completada.", text_color="#2b8a3e")

        Thread(target=loop_play, daemon=True).start()

    def stop_sequence(self):
        self.is_playing = False
        self.lbl_status.configure(text="Secuencia detenida.", text_color="#d9534f")

    def reset_all_home(self):
        for i, slider in enumerate(self.sliders):
            slider.set(90)
            self.on_slider_change(i, 90)
        self.lbl_status.configure(text="Todos los servomotores reiniciados a 90°", text_color="#00E5FF")

    def export_sequence(self):
        if not self.recorded_sequence:
            messagebox.showinfo("Exportar", "No hay datos para exportar.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Archivos JSON", "*.json")])
        if filepath:
            with open(filepath, "w") as f:
                json.dump(self.recorded_sequence, f, indent=4)
            messagebox.showinfo("Exportar", "Secuencia guardada exitosamente.")

    def import_sequence(self):
        filepath = filedialog.askopenfilename(filetypes=[("Archivos JSON", "*.json")])
        if filepath:
            try:
                with open(filepath, "r") as f:
                    self.recorded_sequence = json.load(f)
                messagebox.showinfo("Importar", f"Cargadas {len(self.recorded_sequence)} posiciones.")
                self.lbl_status.configure(text=f"Secuencia importada ({len(self.recorded_sequence)} pasos).", text_color="#2b8a3e")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

if __name__ == "__main__":
    app = RobotArmController()
    app.mainloop()
