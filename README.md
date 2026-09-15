# 🤖 Brazo Robótico v1 - ESP32-C3 SuperMini

Sistema completo de control para brazo robótico de 4 grados de libertad (4 servomotores) utilizando una placa **ESP32-C3 SuperMini** y una interfaz gráfica de usuario (GUI) moderna desarrollada en **Python** con `CustomTkinter`.

---

## 📁 Estructura del Repositorio

```text
Brazo Robotico v1/
├── firmware/
│   └── esp32_c3_arm/
│       └── esp32_c3_arm.ino    # Código Arduino C++ para el ESP32-C3 SuperMini
├── gui.py                      # Interfaz gráfica de control en Python
├── requirements.txt            # Dependencias de Python
└── README.md                   # Documentación del proyecto
```

---

## ⚡ Esquema de Conexiones Hardware

> [!WARNING]
> **Alimentación Externa:** Los servomotores exigen picos de corriente que el puerto USB del ESP32-C3 SuperMini **no** puede suministrar. Conecta los servos a una fuente externa de **5V (2A - 3A)**.
> **Masa Común:** Asegúrate de unir la masa (**GND**) de la fuente externa con el pin **GND** del ESP32-C3.

### Conexiones de Pines GPIO (ESP32-C3 SuperMini)

| Servomotor | Función | Pin GPIO | Señal PWM | Fuente Externa |
| :--- | :--- | :--- | :--- | :--- |
| **Servo 1** | Base | `GPIO 2` | Cable Naranja/Amarillo | 5V / GND |
| **Servo 2** | Hombro | `GPIO 3` | Cable Naranja/Amarillo | 5V / GND |
| **Servo 3** | Codo | `GPIO 4` | Cable Naranja/Amarillo | 5V / GND |
| **Servo 4** | Pinza | `GPIO 5` | Cable Naranja/Amarillo | 5V / GND |

---

## 🛠️ Configuración e Instalación

### 1. Programar el ESP32-C3 SuperMini (Arduino IDE)

1. Abre **Arduino IDE** (v2.0+ recomendada).
2. Agrega la URL del gestor de tarjetas ESP32 en *Archivo > Preferencias > URLs Adicionales de Gestor de Tarjetas*:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Ve a *Herramientas > Placa > Gestor de Tarjetas* y busca **esp32** de Espressif (instala la versión más reciente).
4. Ve a *Herramientas > Gestor de Librerías* y busca e instala **`ESP32Servo`** por Kevin Harrington.
5. Selecciona la placa: **ESP32C3 Dev Module** (o ESP32-C3 SuperMini si está disponible).
6. Abre el archivo [`firmware/esp32_c3_arm/esp32_c3_arm.ino`](firmware/esp32_c3_arm/esp32_c3_arm.ino) y presiona **Subir** (Upload).

---

### 2. Ejecutar la Interfaz de Control (Python GUI)

#### Requisitos Previos
- Python 3.10+ o [uv](https://github.com/astral-sh/uv).

#### Pasos de Ejecución
1. Clona o abre la carpeta del proyecto en tu terminal.
2. Crea el entorno virtual e instala las dependencias:
   ```powershell
   uv venv
   uv pip install -r requirements.txt
   ```
   *(O usando pip estándar: `python -m venv .venv` y luego `.\.venv\Scripts\pip install -r requirements.txt`)*

3. Ejecuta la interfaz gráfica:
   ```powershell
   .\.venv\Scripts\python.exe gui.py
   ```

---

## 🎮 Funcionalidades de la GUI

- **Detección Automática de Puertos USB/COM:** Encuentra y actualiza los puertos serie disponibles al instante.
- **Control Deslizante Independiente (0° - 180°):** Ajuste preciso en tiempo real para cada uno de los 4 articulaciones.
- **Botón Home (Posición Inicial):** Restablece todos los servomotores a $90^\circ$ con un solo clic.
- **Protocolo Serie Ligero (115200 Baudios):** Tramas en formato `<SERVO_ID>:<ANGULO>\n`.
- **Diseño Moderno:** Tema visual en modo oscuro estilizado.
