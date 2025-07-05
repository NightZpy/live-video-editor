# WSL2 Setup Guide for AMD GPU + ROCm

## Prerequisites
1. Windows 11 or Windows 10 version 2004+ (Build 19041+)
2. AMD GPU: RX 5000 series or newer, Vega, NAVI, RDNA
3. WSL2 enabled

## Step 1: Enable WSL2 (if not already enabled)
```powershell
# Run in PowerShell as Administrator
wsl --install
# OR if WSL is already installed:
wsl --set-default-version 2
```

## Step 2: Install Ubuntu 22.04 LTS (recommended for ROCm)
```powershell
wsl --install -d Ubuntu-22.04
```

## Step 3: Update Ubuntu and install dependencies
```bash
# Inside WSL2 Ubuntu
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Install ROCm dependencies
sudo apt install -y libnuma-dev
```

## Step 4: Install ROCm for Ubuntu
```bash
# Add ROCm repository
wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/5.7 ubuntu main' | sudo tee /etc/apt/sources.list.d/rocm.list

# Install ROCm
sudo apt update
sudo apt install -y rocm-dev rocm-libs rocm-utils

# Add user to render group
sudo usermod -a -G render $USER
sudo usermod -a -G video $USER

# Reboot WSL
exit
# Then in Windows: wsl --shutdown
# Then: wsl
```

## Step 5: Install Python dependencies
```bash
# Create project directory
mkdir -p ~/live-video-editor
cd ~/live-video-editor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PyTorch with ROCm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7

# Clone/copy your project files (see next section)
```

## Step 6: Access Windows files from WSL2
Your Windows project files are accessible at `/mnt/d/Proyectos/live-video-editor/`

```bash
# Option A: Work directly with Windows files
cd /mnt/d/Proyectos/live-video-editor/
source venv/bin/activate  # If you have a venv there

# Option B: Copy project to WSL2 (recommended for performance)
cp -r /mnt/d/Proyectos/live-video-editor/* ~/live-video-editor/
cd ~/live-video-editor
```

## Step 7: Install project dependencies
```bash
# Install dependencies (without the problematic Windows video player)
pip install customtkinter>=5.2.2
pip install ffmpeg-python==0.2.0
pip install opencv-python>=4.9.0
pip install Pillow>=10.0.1
pip install openai>=1.35.0
pip install python-dotenv==1.0.0

# Install Whisper
pip install git+https://github.com/openai/whisper.git

# Test GPU detection
python3 -c "import torch; print('ROCm available:', torch.cuda.is_available()); print('GPU devices:', torch.cuda.device_count())"
```

## Step 8: Run the application
```bash
# For GUI applications, you need X11 forwarding
export DISPLAY=:0
python3 main.py
```

## GUI Options for WSL2

### Option A: WSLg (Windows 11 22H2+)
- GUI apps work automatically
- No additional setup needed

### Option B: X11 forwarding (Windows 10/11)
- Install VcXsrv or X410
- Configure X11 forwarding

### Option C: Web interface
- Modify the app to run as web interface
- Access via browser at localhost

## Performance Notes
- File I/O is faster when files are in WSL2 filesystem (~/live-video-editor)
- GPU performance is near-native
- Memory sharing between Windows/WSL2 is efficient

## 🚪 Cómo acceder a WSL Ubuntu desde Windows

### Método 1: Menú de Inicio (Más fácil)
1. **Presiona la tecla Windows**
2. **Escribe "Ubuntu"** 
3. **Click en "Ubuntu 22.04 LTS"** (o la versión que tengas instalada)
4. Se abrirá una terminal de Ubuntu directamente

### Método 2: Terminal de Windows
```cmd
# Abrir WSL directamente
wsl

# O especificar la distribución
wsl -d Ubuntu-22.04
```

### Método 3: PowerShell/CMD
```powershell
# En PowerShell o CMD
wsl
# O específicamente Ubuntu
ubuntu
```

### Método 4: Windows Terminal (Recomendado)
1. **Instala Windows Terminal** desde Microsoft Store (si no lo tienes)
2. **Abre Windows Terminal**
3. **Click en la flecha hacia abajo** ▼ junto al ícono +
4. **Selecciona "Ubuntu 22.04"** de la lista

### Método 5: VS Code integrado
```bash
# En VS Code, abre la paleta de comandos (Ctrl+Shift+P)
# Escribe: "WSL: Connect to WSL"
# Selecciona tu distribución Ubuntu
```

### Método 6: Explorador de archivos
1. **Abre el Explorador de archivos**
2. **En la barra lateral izquierda**, busca **"Linux"**
3. **Expande Ubuntu** 
4. **Click derecho en cualquier carpeta** → "Abrir en Terminal"

## 🔧 Comandos útiles de WSL desde Windows

### Gestión de WSL
```cmd
# Ver distribuciones instaladas
wsl --list --verbose

# Iniciar una distribución específica
wsl -d Ubuntu-22.04

# Parar WSL completamente
wsl --shutdown

# Reiniciar una distribución
wsl --terminate Ubuntu-22.04
wsl -d Ubuntu-22.04

# Establecer distribución por defecto
wsl --set-default Ubuntu-22.04
```

### Acceso a archivos
```bash
# Desde WSL, acceder a archivos de Windows:
cd /mnt/c/Users/tu-usuario/
cd /mnt/d/Proyectos/live-video-editor/

# Desde Windows, acceder a archivos de WSL:
# En el explorador: \\wsl$\Ubuntu-22.04\home\tu-usuario\
```

## 🎯 Para nuestro proyecto específico

### Primera vez (instalación):
```cmd
# 1. Abrir PowerShell como Administrador
# Método: Click derecho en el botón de Windows → "Windows PowerShell (Admin)"

# 2. Ejecutar setup
cd d:\Proyectos\live-video-editor
.\setup-wsl2.ps1
```

### Después de la instalación:
```bash
# 1. Abrir Ubuntu desde el menú de inicio
# 2. Ejecutar nuestro script
chmod +x ~/setup-wsl2.sh
~/setup-wsl2.sh
```

### Para usar la aplicación diariamente:
```bash
# Opción A: Desde el menú de inicio → Ubuntu
cd ~/live-video-editor
./start_app.sh

# Opción B: Desde Windows Terminal
# Seleccionar pestaña Ubuntu → ejecutar comandos arriba
```

## 🖥️ Integración con VS Code

Si usas VS Code, puedes trabajar directamente con archivos WSL:

1. **Instala la extensión "WSL"** en VS Code
2. **Abre VS Code**
3. **Ctrl+Shift+P** → "WSL: Connect to WSL"
4. **Selecciona Ubuntu**
5. **VS Code se reiniciará** conectado a WSL
6. **Abre la carpeta** `~/live-video-editor`

## 💡 Consejos

### Para acceso rápido:
- **Pin Ubuntu** al menú de inicio o barra de tareas
- **Usa Windows Terminal** con pestañas para múltiples sesiones
- **Crea un acceso directo** en el escritorio

### Para desarrollo:
- **Trabaja con archivos** directamente en WSL (`~/live-video-editor`)
- **Usa VS Code** con extensión WSL para editar código
- **Mantén el proyecto** en el sistema de archivos Linux para mejor rendimiento
