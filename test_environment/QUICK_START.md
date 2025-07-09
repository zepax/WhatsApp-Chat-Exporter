# Quick Start - Entorno de Pruebas

## 🚀 Inicio Rápido

### 1. Configurar el Entorno (Solo la primera vez)

```bash
cd test_environment
./setup_test_env.sh
```

### 2. Verificar Configuración

```bash
./check_setup.sh
```

### 3. Colocar Archivos de Prueba

**Android:**
```bash
# Coloca estos archivos:
android/databases/msgstore.db          # Base de datos de mensajes
android/databases/wa.db                # Base de datos de contactos
android/WhatsApp/Media/                # Archivos de media
android/keys/key                       # Clave para backups cifrados
```

**iOS:**
```bash
# Coloca el backup completo:
ios/backup/Manifest.db                 # Archivo principal del backup
ios/backup/Info.plist                  # Información del dispositivo
ios/backup/[archivos con hash]         # Contenido del backup
```

**Chats Exportados:**
```bash
# Coloca archivos .txt y media:
exported/chat_example.txt              # Chat exportado
exported/IMG-20231201-WA0001.jpg       # Archivos de media
```

### 4. Ejecutar Pruebas

```bash
# Todas las pruebas disponibles
./scripts/test_all_formats.sh

# Pruebas individuales
./scripts/test_android_basic.sh
./scripts/test_android_encrypted.sh
./scripts/test_ios_basic.sh
./scripts/test_exported_chat.sh
```

### 5. Revisar Resultados

Los resultados se guardan en `output/` con timestamp único:
```
output/
├── android_basic_20231201_143022/
│   ├── result.json
│   ├── summary.json
│   ├── *.html
│   └── execution.log
└── test_report.json
```

## 📋 Comandos Útiles

```bash
# Verificar configuración
./check_setup.sh

# Ejecutar prueba específica
./scripts/test_android_basic.sh

# Ver ayuda del exporter
cd .. && poetry run python -m Whatsapp_Chat_Exporter --help

# Verificar dependencias
poetry run python -c "import Whatsapp_Chat_Exporter; print('OK')"
```

## 🔧 Solución de Problemas

**Error: "Poetry no encontrado"**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Error: "Módulo no encontrado"**
```bash
cd .. && poetry install --all-extras
```

**Error: "Permisos denegados"**
```bash
chmod +x scripts/*.sh
```

## 📚 Documentación Completa

- `README.md` - Información general
- `TESTING_GUIDE.md` - Guía detallada
- `android/README.md` - Archivos Android
- `ios/README.md` - Archivos iOS
- `exported/README.md` - Archivos exportados