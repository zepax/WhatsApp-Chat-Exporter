# Guía de Pruebas - WhatsApp Chat Exporter

## Configuración Inicial

### 1. Configurar el Entorno

```bash
# Desde el directorio test_environment
./setup_test_env.sh
```

Este script:
- Verifica que Poetry esté instalado
- Instala todas las dependencias
- Configura la estructura de directorios
- Verifica que el módulo se importe correctamente

### 2. Colocar Archivos de Prueba

#### Para Android:
```bash
# Bases de datos
cp msgstore.db android/databases/
cp wa.db android/databases/

# Media (mantener estructura original)
cp -r WhatsApp/ android/

# Para backups cifrados
cp key android/keys/
# o
cp crypt15_key.hex android/keys/
cp msgstore.db.crypt15 android/databases/
```

#### Para iOS:
```bash
# Backup completo de iTunes/Finder
cp -r /path/to/backup/ ios/backup/
```

#### Para Chats Exportados:
```bash
# Archivos .txt y media asociada
cp "WhatsApp Chat - Contact.txt" exported/
cp IMG-*.jpg exported/
cp VID-*.mp4 exported/
```

## Ejecutar Pruebas

### Pruebas Individuales

```bash
# Android básico
./scripts/test_android_basic.sh

# Android con backup cifrado
./scripts/test_android_encrypted.sh

# iOS básico
./scripts/test_ios_basic.sh

# iOS Business
./scripts/test_ios_basic.sh --business

# Chat exportado
./scripts/test_exported_chat.sh
./scripts/test_exported_chat.sh --assume-first-as-me
./scripts/test_exported_chat.sh --prompt-user
```

### Prueba Completa

```bash
# Ejecuta todas las pruebas disponibles
./scripts/test_all_formats.sh
```

## Interpretar Resultados

### Estructura de Salida

```
output/
├── android_basic_20231201_143022/
│   ├── result.json              # Datos exportados
│   ├── summary.json            # Resumen de estadísticas
│   ├── *.html                  # Archivos HTML generados
│   ├── execution.log           # Log de ejecución
│   └── WhatsApp/               # Media copiada
├── ios_basic_20231201_143155/
└── test_report.json            # Reporte consolidado
```

### Verificar Éxito

✅ **Prueba exitosa:**
- Código de salida 0
- Archivos HTML generados
- JSON válido
- Media copiada correctamente
- No errores críticos en el log

❌ **Prueba fallida:**
- Código de salida != 0
- Archivos de salida faltantes
- Errores en el log
- Dependencias faltantes

## Casos de Prueba Comunes

### 1. Prueba Básica (Android)
```bash
./scripts/test_android_basic.sh
```
**Verifica:**
- Lectura de bases de datos SQLite
- Generación de HTML/JSON
- Copia de archivos media
- Procesamiento de contactos

### 2. Descifrado (Android)
```bash
./scripts/test_android_encrypted.sh
```
**Verifica:**
- Descifrado de backups
- Detección automática de tipo de cifrado
- Manejo de claves
- Generación de bases de datos desencriptadas

### 3. Backup iOS
```bash
./scripts/test_ios_basic.sh
```
**Verifica:**
- Procesamiento de backups iTunes/Finder
- Extracción de media
- Lectura de manifiestos
- Identificadores de archivos

### 4. Chats Exportados
```bash
./scripts/test_exported_chat.sh
```
**Verifica:**
- Parsing de formato de texto
- Detección de participantes
- Resolución de rutas de media
- Copia de archivos asociados

## Solución de Problemas

### Dependencias Faltantes

```bash
# Instalar dependencias opcionales
poetry install --extras "android_backup vcards crypt15"

# Verificar dependencias específicas
python -c "import pycryptodome; print('OK')"
python -c "import javaobj; print('OK')"
python -c "import iphone_backup_decrypt; print('OK')"
```

### Problemas de Permisos

```bash
# Dar permisos a scripts
chmod +x scripts/*.sh
chmod +x setup_test_env.sh
```

### Archivos de Prueba Corruptos

```bash
# Verificar integridad de bases de datos
sqlite3 android/databases/msgstore.db ".tables"
sqlite3 android/databases/wa.db ".tables"

# Verificar backups iOS
file ios/backup/Manifest.db
```

### Memoria Insuficiente

```bash
# Usar modo streaming para datasets grandes
poetry run python -m Whatsapp_Chat_Exporter \
    --android \
    --db android/databases/msgstore.db \
    --output output/streaming \
    --stream-json \
    --skip-media
```

## Métricas de Rendimiento

Los scripts generan métricas automáticamente:

```json
{
    "execution_time": 45.2,
    "memory_peak": "256MB",
    "output_size": "15MB",
    "chat_count": 25,
    "message_count": 5430,
    "media_files": 120
}
```

## Configuraciones Avanzadas

### Variables de Entorno

```bash
# Configurar chunk size para iOS
export DECRYPT_CHUNK_SIZE=2097152

# Configurar workers para brute force
export MAX_BRUTEFORCE_WORKERS=4

# Habilitar modo debug
export DEBUG=1
```

### Filtros de Prueba

```bash
# Filtrar por fecha
./scripts/test_android_basic.sh --date "> 2023-01-01"

# Filtrar por contacto
./scripts/test_android_basic.sh --include 1234567890

# Excluir chats vacíos
./scripts/test_android_basic.sh --dont-filter-empty
```

## Automatización CI/CD

Los scripts están diseñados para integrarse en pipelines:

```bash
# Ejecutar en modo silencioso
./scripts/test_all_formats.sh --quiet

# Generar reporte JUnit
./scripts/test_all_formats.sh --junit-output results.xml

# Verificar código de salida
if [ $? -eq 0 ]; then
    echo "Todas las pruebas pasaron"
else
    echo "Algunas pruebas fallaron"
    exit 1
fi
```