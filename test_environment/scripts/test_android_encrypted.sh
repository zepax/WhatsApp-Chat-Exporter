#!/bin/bash

# Test para Android con backup cifrado
# Ejecuta el exporter con archivos crypt12/14/15

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$TEST_DIR")"
OUTPUT_DIR="$TEST_DIR/output/android_encrypted_$(date +%Y%m%d_%H%M%S)"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

echo "🔒 Ejecutando prueba para Android con backup cifrado..."

# Buscar archivos de backup cifrado
BACKUP_FILE=""
KEY_FILE=""

# Buscar backup cifrado
for ext in crypt12 crypt14 crypt15; do
    for file in "$TEST_DIR/android/databases/"*.$ext; do
        if [ -f "$file" ]; then
            BACKUP_FILE="$file"
            CRYPT_TYPE="$ext"
            break 2
        fi
    done
done

if [ -z "$BACKUP_FILE" ]; then
    print_error "No se encontró archivo de backup cifrado (.crypt12, .crypt14, .crypt15)"
    print_warning "Coloca un archivo de backup cifrado en android/databases/"
    exit 1
fi

# Buscar archivo de clave
if [ -f "$TEST_DIR/android/keys/key" ]; then
    KEY_FILE="$TEST_DIR/android/keys/key"
elif [ -f "$TEST_DIR/android/keys/crypt15_key.hex" ]; then
    KEY_FILE="$TEST_DIR/android/keys/crypt15_key.hex"
else
    print_error "No se encontró archivo de clave en android/keys/"
    print_warning "Coloca el archivo 'key' o 'crypt15_key.hex' en android/keys/"
    exit 1
fi

# Otros archivos
WA_DB="$TEST_DIR/android/databases/wa.db"
MEDIA_DIR="$TEST_DIR/android/WhatsApp"

print_status "Archivos encontrados:"
print_status "  - Backup cifrado: $BACKUP_FILE ($CRYPT_TYPE)"
print_status "  - Clave: $KEY_FILE"

if [ ! -f "$WA_DB" ]; then
    print_warning "No se encontró wa.db en: $WA_DB"
fi

if [ ! -d "$MEDIA_DIR" ]; then
    print_warning "No se encontró directorio de media en: $MEDIA_DIR"
fi

# Crear directorio de salida
mkdir -p "$OUTPUT_DIR"

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR"

print_status "Ejecutando WhatsApp Chat Exporter con descifrado..."
print_status "Salida: $OUTPUT_DIR"

# Ejecutar el exporter
COMMAND="poetry run python -m Whatsapp_Chat_Exporter \\
    --android \\
    --backup \"$BACKUP_FILE\" \\
    --key \"$KEY_FILE\" \\
    --wa \"$WA_DB\" \\
    --media \"$MEDIA_DIR\" \\
    --output \"$OUTPUT_DIR\" \\
    --json \"$OUTPUT_DIR/result.json\" \\
    --summary \"$OUTPUT_DIR/summary.json\" \\
    --showkey \\
    --verbose"

echo ""
print_status "Comando ejecutado:"
echo "$COMMAND"
echo ""

# Ejecutar
eval $COMMAND 2>&1 | tee "$OUTPUT_DIR/execution.log"

# Verificar resultados
if [ $? -eq 0 ]; then
    print_success "Descifrado y exportación completados exitosamente!"
    
    # Mostrar estadísticas
    if [ -f "$OUTPUT_DIR/summary.json" ]; then
        print_status "Estadísticas:"
        python3 -c "
import json
try:
    with open('$OUTPUT_DIR/summary.json', 'r') as f:
        data = json.load(f)
    print(f'  - Total de chats: {data.get(\"total_chats\", 0)}')
    for jid, chat in data.get('chats', {}).items():
        print(f'  - {chat.get(\"name\", jid)}: {chat.get(\"message_count\", 0)} mensajes')
except Exception as e:
    print(f'  Error leyendo estadísticas: {e}')
"
    fi
    
    # Mostrar archivos generados
    print_status "Archivos generados:"
    ls -la "$OUTPUT_DIR" | grep -E "\\.(html|json|txt|db)$" | while read -r line; do
        echo "  - $line"
    done
    
    echo ""
    print_success "Revisa los resultados en: $OUTPUT_DIR"
    
else
    print_error "La exportación falló. Revisa el log en: $OUTPUT_DIR/execution.log"
    print_warning "Posibles problemas:"
    print_warning "  - Clave incorrecta para el backup"
    print_warning "  - Archivo de backup corrupto"
    print_warning "  - Dependencias faltantes (pycryptodome, javaobj-py3)"
    exit 1
fi