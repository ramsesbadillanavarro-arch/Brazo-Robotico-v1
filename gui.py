import customtkinter as ctk
import serial
import serial.tools.list_ports
import time
from threading import Thread

# Configuración del tema visual
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ModernServoController(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Ventana Principal
        self.title("⚡ Control de Servomotor ESP32-C3")
        self.geometry("550x580")
        self.resizable(False, False)

        self.ser = None

        # --- TÍTULO Y CABECERA ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1A1C23")
        self.header_frame.pack(padx=20, pady=(20, 10), fill="x")

        self.lbl_title = ctk.CTkLabel(
            self.header_frame, 
            text="ESP32-C3 SERVO CONTROL", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00E5FF"
        )
        self.lbl_title.pack(padx=20, pady=(15, 2))

        self.lbl_subtitle = ctk.CTkLabel(
            self.header_frame, 
            text="Interfaz de Control Serial USB / UART", 
            font=ctk.CTkFont(size=12),
            text_color="#8F96A0"
        )
        self.lbl_subtitle.pack(padx=20, pady=(0, 15))

        # --- PANEL DE CONEXIÓN USB ---
        self.conn_frame = ctk.CTkFrame(self, corner_radius=15)
        self.conn_frame.pack(padx=20, pady=10, fill="x")

        self.lbl_port = ctk.CTkLabel(self.conn_frame, text="Puerto USB:", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_port.pack(side="left", padx=(20, 10), pady=15)

        self.combo_ports = ctk.CTkOptionMenu(
            self.conn_frame, 
            values=self.get_ports(),
            width=160,
            dynamic_resizing=False,
            button_color="#2B2D42"
        )
        self.combo_ports.pack(side="left", padx=5, pady=15)

        self.btn_refresh = ctk.CTkButton(
            self.conn_frame, 
            text="🔄", 
            width=40, 
            command=self.refresh_ports,
            fg_color="#2B2D42",
            hover_color="#3D405B"
        )
        self.btn_refresh.pack(side="left", padx=5, pady=15)

        self.btn_connect = ctk.CTkButton(
            self.conn_frame, 
            text="Conectar", 
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.toggle_connection,
            fg_color="#00B4D8",
            hover_color="#0096C7",
            width=110
        )
        self.btn_connect.pack(side="right", padx=20, pady=15)

        # --- TARJETAS DE CONTROL DE SERVOS ---
        self.servos_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.servos_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.sliders = []
        self.labels_val = []

        # Crear 2 canales de servos estilizados
        self.create_servo_card(id_servo=0, gpio_pin="GPIO 2")
        self.create_servo_card(id_servo=1, gpio_pin="GPIO 3")

        # --- BARRA DE ESTADO INFERIOR ---
        self.status_frame = ctk.CTkFrame(self, height=35, corner_radius=0, fg_color="#111217")
        self.status_frame.pack(fill="x", side="bottom")

        self.lbl_status = ctk.CTkLabel(
            self.status_frame, 
            text="🔴 Estado: Desconectado", 
            font=ctk.CTkFont(size=12),
            text_color="#E63946"
        )
        self.lbl_status.pack(side="left", padx=20, pady=5)

    def get_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["No detectado"]

    def refresh_ports(self):
        ports = self.get_ports()
        self.combo_ports.configure(values=ports)
        if ports:
            self.combo_ports.set(ports[0])

    def create_servo_card(self, id_servo, gpio_pin):
        card = ctk.CTkFrame(self.servos_frame, corner_radius=15, fg_color="#1E2029")
        card.pack(fill="x", pady=8, ipady=5)

        # Encabezado de la tarjeta
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(12, 5))

        title = ctk.CTkLabel(
            header, 
            text=f"SERVO {id_servo + 1}", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8F9FA"
        )
        title.pack(side="left")

        badge = ctk.CTkLabel(
            header, 
            text=f"[{gpio_pin}]", 
            font=ctk.CTkFont(size=11),
            text_color="#00E5FF"
        )
        badge.pack(side="left", padx=8)

        lbl_val = ctk.CTkLabel(
            header, 
            text="90°", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00E5FF"
        )
        lbl_val.pack(side="right")
        self.labels_val.append(lbl_val)

        # Slider estilizado
        slider = ctk.CTkSlider(
            card, 
            from_=0, 
            to=180, 
            number_of_steps=180, 
            button_color="#00E5FF",
            button_hover_color="#80E5FF",
            progress_color="#0077B6",
            command=lambda val, s_id=id_servo: self.on_slider_move(s_id, val)
        )
        slider.set(90)
        slider.pack(fill="x", padx=15, pady=(5, 12))
        self.sliders.append(slider)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.btn_connect.configure(text="Conectar", fg_color="#00B4D8", hover_color="#0096C7")
            self.lbl_status.configure(text="🔴 Estado: Desconectado", text_color="#E63946")
            return

        selected_port = self.combo_ports.get()
        if selected_port == "No detectado":
            return

        try:
            # 115200 Baudios
            self.ser = serial.Serial(selected_port, 115200, timeout=0.1)
            time.sleep(1.5) # Esperar a que el C3 complete el reset tras abrir el puerto
            
            self.btn_connect.configure(text="Desconectar", fg_color="#E63946", hover_color="#D62828")
            self.lbl_status.configure(text=f"🟢 Conectado en {selected_port} @ 115200 baudios", text_color="#2EC4B6")
        except Exception as e:
            self.lbl_status.configure(text=f"⚠️ Error: No se pudo abrir {selected_port}", text_color="#FFB703")

    def on_slider_move(self, servo_id, value):
        angle = int(value)
        self.labels_val[servo_id].configure(text=f"{angle}°")
        
        # Envío del comando serial
        if self.ser and self.ser.is_open:
            command = f"{servo_id}:{angle}\n"
            self.ser.write(command.encode('utf-8'))

if __name__ == "__main__":
    app = ModernServoController()
    app.mainloop()