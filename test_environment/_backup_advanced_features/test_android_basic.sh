#!/bin/bash

# Test básico para Android
# Ejecuta el exporter con archivos de base de datos Android desencriptados

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$TEST_DIR")"
OUTPUT_DIR="$TEST_DIR/output/android_basic_$(date +%Y%m%d_%H%M%S)"

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

echo "🤖 Ejecutando prueba básica para Android..."

# Verificar archivos necesarios
MSGSTORE_DB="$TEST_DIR/android/databases/msgstore.db"
WA_DB="$TEST_DIR/android/databases/wa.db"
MEDIA_DIR="$TEST_DIR/android/WhatsApp"

if [ ! -f "$MSGSTORE_DB" ]; then
    print_error "No se encontró msgstore.db en: $MSGSTORE_DB"
    print_warning "Coloca el archivo msgstore.db en android/databases/"
    exit 1
fi

if [ ! -f "$WA_DB" ]; then
    print_warning "No se encontró wa.db en: $WA_DB"
    print_warning "Coloca el archivo wa.db en android/databases/ para mejor experiencia"
fi

if [ ! -d "$MEDIA_DIR" ]; then
    print_warning "No se encontró directorio de media en: $MEDIA_DIR"
    print_warning "Coloca archivos de media en android/WhatsApp/ para incluirlos en la exportación"
fi

# Crear directorio de salida
mkdir -p "$OUTPUT_DIR"

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR"

print_status "Ejecutando WhatsApp Chat Exporter..."
print_status "Archivos de entrada:"
print_status "  - msgstore.db: $MSGSTORE_DB"
print_status "  - wa.db: $WA_DB"
print_status "  - media: $MEDIA_DIR"
print_status "Salida: $OUTPUT_DIR"

# Ejecutar el exporter
COMMAND="poetry run python -m Whatsapp_Chat_Exporter \\
    --android \\
    --db \"$MSGSTORE_DB\" \\
    --wa \"$WA_DB\" \\
    --media \"$MEDIA_DIR\" \\
    --output \"$OUTPUT_DIR\" \\
    --json \"$OUTPUT_DIR/result.json\" \\
    --summary \"$OUTPUT_DIR/summary.json\" \\
    --verbose"

echo ""
print_status "Comando ejecutado:"
echo "$COMMAND"
echo ""

# Ejecutar
eval $COMMAND 2>&1 | tee "$OUTPUT_DIR/execution.log"

# Verificar resultados
if [ $? -eq 0 ]; then
    print_success "Exportación completada exitosamente!"
    
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
    ls -la "$OUTPUT_DIR" | grep -E "\\.(html|json|txt)$" | while read -r line; do
        echo "  - $line"
    done
    
    echo ""
    print_success "Revisa los resultados en: $OUTPUT_DIR"
    
else
    print_error "La exportación falló. Revisa el log en: $OUTPUT_DIR/execution.log"
    exit 1
fi