import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import serial
import serial.tools.list_ports
import time
import json
from threading import Thread, Lock

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class RobotArmController(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Control de Brazo Robótico - ESP32-C3")
        self.geometry("960x540")
        self.resizable(False, False)
        self.configure(fg_color="#0F0F0F") # Marco exterior oscuro

        self.ser = None
        self.ser_lock = Lock()
        self.recorded_sequence = []
        self.is_playing = False

        self.last_sent_angles = {}
        self.last_send_time = {}

        self.servos = [
            {"id": 0, "name": "SERVO 1", "pin": "GPIO 2"},
            {"id": 1, "name": "SERVO 2", "pin": "GPIO 3"},
            {"id": 2, "name": "SERVO 3", "pin": "GPIO 4"},
            {"id": 3, "name": "SERVO 4", "pin": "GPIO 5"},
        ]

        self.sliders = []
        self.angle_labels = []

        self._build_ui()

    def _build_ui(self):
        # Panel Principal Blanco
        self.main_panel = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=22)
        self.main_panel.pack(fill="both", expand=True, padx=12, pady=12)

        # --- CABECERA ---
        # Botón PUERTO (Arriba Izquierda)
        self.btn_puerto = ctk.CTkButton(
            self.main_panel,
            text="PUERTO",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#202020",
            hover_color="#333333",
            text_color="#FFFFFF",
            corner_radius=20,
            width=110,
            height=38,
            command=self.open_port_window
        )
        self.btn_puerto.place(x=35, y=25)

        # Título Central
        lbl_title1 = ctk.CTkLabel(
            self.main_panel,
            text="CONTROL DE BRAZO ROBÓTICO",
            font=ctk.CTkFont(family="Arial", size=22, weight="bold"),
            text_color="#1A1A1A"
        )
        lbl_title1.place(relx=0.5, y=26, anchor="n")

        lbl_sub = ctk.CTkLabel(
            self.main_panel,
            text="ESP32-C3 SUPERMINI - SERVO CONTROLLER",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color="#666666"
        )
        lbl_sub.place(relx=0.5, y=65, anchor="n")

        # Botones Minimizar y Cerrar (Arriba Derecha)
        self.btn_min = ctk.CTkButton(
            self.main_panel,
            text="Minimizar",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#202020",
            hover_color="#333333",
            text_color="#FFFFFF",
            corner_radius=18,
            width=85,
            height=34,
            command=self.iconify
        )
        self.btn_min.place(x=745, y=25)

        self.btn_close = ctk.CTkButton(
            self.main_panel,
            text="Cerrar",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#202020",
            hover_color="#333333",
            text_color="#FFFFFF",
            corner_radius=18,
            width=75,
            height=34,
            command=self.destroy
        )
        self.btn_close.place(x=840, y=25)

        # --- BOTONES DE ACCIÓN IZQUIERDOS (GUARDAR, REPRODUCIR, DETENER) ---
        left_btns = [
            ("GUARDAR", self.save_current_pose, 165),
            ("REPRODUCIR", self.play_sequence, 235),
            ("DETENER", self.stop_sequence, 305),
        ]

        for text, cmd, y_pos in left_btns:
            btn = ctk.CTkButton(
                self.main_panel,
                text=text,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#202020",
                hover_color="#383838",
                text_color="#FFFFFF",
                corner_radius=20,
                width=125,
                height=42,
                command=cmd
            )
            btn.place(x=45, y=y_pos)

        # --- BOTONES DE ACCIÓN DERECHOS (EXPORTAR, IMPORTAR, REINICIAR) ---
        right_btns = [
            ("EXPORTAR", self.export_sequence, 165),
            ("IMPORTAR", self.import_sequence, 235),
            ("REINICIAR", self.reset_all_home, 305),
        ]

        for text, cmd, y_pos in right_btns:
            btn = ctk.CTkButton(
                self.main_panel,
                text=text,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#202020",
                hover_color="#383838",
                text_color="#FFFFFF",
                corner_radius=20,
                width=125,
                height=42,
                command=cmd
            )
            btn.place(x=770, y=y_pos)

        # --- 4 SLIDERS DE CONTROL DE SERVOS ---
        slider_y_positions = [155, 215, 275, 335]

        for i, (servo, y_pos) in enumerate(zip(self.servos, slider_y_positions)):
            lbl_name = ctk.CTkLabel(
                self.main_panel,
                text=f"{servo['name']} [{servo['pin']}]",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#202020"
            )
            lbl_name.place(x=225, y=y_pos + 6)

            slider_frame = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=18, width=320, height=36)
            slider_frame.place(x=350, y=y_pos)
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
                width=290,
                height=18,
                command=lambda val, s_id=servo['id']: self.on_slider_change(s_id, val)
            )
            slider.set(90)
            slider.place(relx=0.5, rely=0.5, anchor="center")
            self.sliders.append(slider)

            val_frame = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=18, width=54, height=36)
            val_frame.place(x=685, y=y_pos)
            val_frame.pack_propagate(False)

            val_lbl = ctk.CTkLabel(
                val_frame,
                text="090",
                font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                text_color="#FFFFFF"
            )
            val_lbl.place(relx=0.5, rely=0.5, anchor="center")
            self.angle_labels.append(val_lbl)

        # --- TARJETA INFORMATIVA E INFERIOR (ESTADO) ---
        self.info_card = ctk.CTkFrame(self.main_panel, fg_color="#202020", corner_radius=18, width=440, height=72)
        self.info_card.place(relx=0.5, y=405, anchor="n")
        self.info_card.pack_propagate(False)

        info_line1 = ctk.CTkLabel(
            self.info_card,
            text="Sistema de Control de Brazo Robótico | ESP32-C3 SuperMini",
            font=ctk.CTkFont(size=10),
            text_color="#DDDDDD"
        )
        info_line1.pack(pady=(6, 0))

        info_line2 = ctk.CTkLabel(
            self.info_card,
            text="by FabricCreator | Version 1.0 | 2026",
            font=ctk.CTkFont(size=10),
            text_color="#AAAAAA"
        )
        info_line2.pack(pady=0)

        self.lbl_status = ctk.CTkLabel(
            self.info_card,
            text="¡Bienvenido! Por favor, seleccione un puerto COM para comenzar",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#00E5FF"
        )
        self.lbl_status.pack(pady=(1, 6))

    # --- POPUP PUERTO COM ---
    def open_port_window(self):
        port_win = ctk.CTkToplevel(self)
        port_win.title("Seleccionar Puerto COM")
        port_win.geometry("340x200")
        port_win.resizable(False, False)
        port_win.grab_set()

        ctk.CTkLabel(port_win, text="Puerto USB / COM", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))

        ports = self.get_ports()
        combo = ctk.CTkOptionMenu(port_win, values=ports, width=200, fg_color="#202020")
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

                    # Abrir con timeouts estrictos para prevenir bloqueos de la GUI en Windows
                    self.ser = serial.Serial(
                        selected, 
                        115200, 
                        timeout=0.1, 
                        write_timeout=0.2
                    )
                    self.ser.dtr = False
                    self.ser.rts = False

                time.sleep(1.0)
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

        ctk.CTkButton(btn_frame, text="Conectar", fg_color="#2b8a3e", width=95, command=connect_action).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Desconectar", fg_color="#c93b2b", width=95, command=disconnect_action).pack(side="left", padx=5)

    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["No detectado"]

    def _send_cmd_async(self, servo_id, angle):
        """ Envía el comando serial en un hilo secundario con límite de frecuencia (debounce) """
        if not self.ser or not self.ser.is_open:
            return

        now = time.time()
        if self.last_sent_angles.get(servo_id) == angle:
            return
        if now - self.last_send_time.get(servo_id, 0) < 0.035: # Máximo ~28 msgs/seg por servo
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
                pass # Prevenir que cualquier falla en la conexión mate la app

        Thread(target=_worker, daemon=True).start()

    def on_slider_change(self, servo_id, value):
        angle = int(value)
        # Actualización instantánea de la UI
        self.angle_labels[servo_id].configure(text=f"{angle:03d}")
        # Envío asíncrono no bloqueante
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
                    self.angle_labels[s_id].configure(text=f"{angle:03d}")
                    self._send_cmd_async(s_id, angle)
                time.sleep(0.8)

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
