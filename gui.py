import customtkinter as ctk
import serial
import serial.tools.list_ports
import time

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RobotArmController(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Control Brazo Robotico - ESP32-C3")
        self.geometry("520x640")
        self.resizable(False, False)

        self.ser = None

        self.servos = [
            {"id": 0, "name": "Base", "pin": "GPIO 2"},
            {"id": 1, "name": "Hombro", "pin": "GPIO 3"},
            {"id": 2, "name": "Codo", "pin": "GPIO 4"},
            {"id": 3, "name": "Pinza", "pin": "GPIO 5"},
        ]

        self.sliders = []
        self.labels = []

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(header, text="Control de Servomotores", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(header, text="ESP32-C3 SuperMini - Protocolo Serie UART", font=ctk.CTkFont(size=12), text_color="gray")
        subtitle.pack(anchor="w")

        # Conexión Serial
        conn_frame = ctk.CTkFrame(self)
        conn_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(conn_frame, text="Puerto:").pack(side="left", padx=(15, 5), pady=10)

        self.combo_ports = ctk.CTkOptionMenu(conn_frame, values=self.get_ports(), width=140)
        self.combo_ports.pack(side="left", padx=5, pady=10)

        btn_refresh = ctk.CTkButton(conn_frame, text="Refrescar", width=80, fg_color="#333333", hover_color="#444444", command=self.refresh_ports)
        btn_refresh.pack(side="left", padx=5, pady=10)

        self.btn_connect = ctk.CTkButton(conn_frame, text="Conectar", width=100, command=self.toggle_connection)
        self.btn_connect.pack(side="right", padx=15, pady=10)

        # Acciones rápidas
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=5)

        btn_home = ctk.CTkButton(action_frame, text="Posición Inicial (90°)", fg_color="#5c3d99", hover_color="#4a317c", command=self.set_home_position)
        btn_home.pack(fill="x")

        # Contenedor de Servos
        servos_container = ctk.CTkFrame(self)
        servos_container.pack(fill="both", expand=True, padx=20, pady=10)

        for servo in self.servos:
            card = ctk.CTkFrame(servos_container, fg_color="#2b2b2b")
            card.pack(fill="x", padx=12, pady=6)

            card_header = ctk.CTkFrame(card, fg_color="transparent")
            card_header.pack(fill="x", padx=10, pady=(8, 2))

            name_lbl = ctk.CTkLabel(card_header, text=f"{servo['name']} [{servo['pin']}]", font=ctk.CTkFont(size=13, weight="bold"))
            name_lbl.pack(side="left")

            val_lbl = ctk.CTkLabel(card_header, text="90°", font=ctk.CTkFont(size=14, weight="bold"), text_color="#1f538d")
            val_lbl.pack(side="right")
            self.labels.append(val_lbl)

            slider = ctk.CTkSlider(
                card, 
                from_=0, 
                to=180, 
                number_of_steps=180, 
                command=lambda val, s_id=servo['id']: self.on_slider_change(s_id, val)
            )
            slider.set(90)
            slider.pack(fill="x", padx=10, pady=(2, 8))
            self.sliders.append(slider)

        # Status Bar
        self.status_lbl = ctk.CTkLabel(self, text="Estado: Desconectado", font=ctk.CTkFont(size=11), text_color="gray")
        self.status_lbl.pack(side="bottom", pady=5)

    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["No detectado"]

    def refresh_ports(self):
        ports = self.get_ports()
        self.combo_ports.configure(values=ports)
        if ports and ports[0] != "No detectado":
            self.combo_ports.set(ports[0])

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            self.btn_connect.configure(text="Conectar", fg_color="#1f6aa5")
            self.status_lbl.configure(text="Estado: Desconectado", text_color="gray")
            return

        port = self.combo_ports.get()
        if port == "No detectado":
            self.status_lbl.configure(text="Error: No se detecto ningún puerto USB", text_color="#d9534f")
            return

        try:
            self.ser = serial.Serial(port, 115200, timeout=0.1)
            time.sleep(1.5)
            self.btn_connect.configure(text="Desconectar", fg_color="#c93b2b")
            self.status_lbl.configure(text=f"Estado: Conectado en {port} @ 115200 baudios", text_color="#2b8a3e")
        except Exception as e:
            self.status_lbl.configure(text=f"Error al abrir puerto {port}", text_color="#d9534f")

    def on_slider_change(self, servo_id, value):
        angle = int(value)
        self.labels[servo_id].configure(text=f"{angle}°")

        if self.ser and self.ser.is_open:
            cmd = f"{servo_id}:{angle}\n"
            try:
                self.ser.write(cmd.encode("utf-8"))
            except Exception:
                self.status_lbl.configure(text="Error de comunicación serial", text_color="#d9534f")

    def set_home_position(self):
        for i, slider in enumerate(self.sliders):
            slider.set(90)
            self.on_slider_change(i, 90)

if __name__ == "__main__":
    app = RobotArmController()
    app.mainloop()