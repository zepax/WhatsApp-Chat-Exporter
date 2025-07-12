#!/bin/bash

# Test para chats exportados
# Ejecuta el exporter con archivos .txt exportados de WhatsApp

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$TEST_DIR")"
OUTPUT_DIR="$TEST_DIR/output/exported_chat_$(date +%Y%m%d_%H%M%S)"

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

echo "📄 Ejecutando prueba para chats exportados..."

# Buscar archivos .txt exportados
EXPORTED_DIR="$TEST_DIR/exported"
CHAT_FILE=""

# Buscar primer archivo .txt
for file in "$EXPORTED_DIR"/*.txt; do
    if [ -f "$file" ]; then
        CHAT_FILE="$file"
        break
    fi
done

if [ -z "$CHAT_FILE" ]; then
    print_error "No se encontró archivo .txt exportado en: $EXPORTED_DIR"
    print_warning "Coloca un archivo de chat exportado (.txt) en exported/"
    exit 1
fi

# Verificar contenido del archivo
if [ ! -s "$CHAT_FILE" ]; then
    print_error "El archivo $CHAT_FILE está vacío"
    exit 1
fi

# Mostrar información del archivo
CHAT_NAME=$(basename "$CHAT_FILE" .txt)
FILE_SIZE=$(wc -l < "$CHAT_FILE")

print_status "Archivo encontrado:"
print_status "  - Archivo: $CHAT_FILE"
print_status "  - Nombre: $CHAT_NAME"
print_status "  - Líneas: $FILE_SIZE"

# Mostrar preview del contenido
print_status "Preview del contenido:"
head -n 5 "$CHAT_FILE" | while read -r line; do
    echo "  $line"
done

# Verificar archivos de media asociados
MEDIA_COUNT=0
MEDIA_DIR=$(dirname "$CHAT_FILE")
for ext in jpg jpeg png gif webp mp4 avi mov 3gp ogg mp3 wav aac pdf doc docx xls xlsx ppt pptx; do
    MEDIA_COUNT=$((MEDIA_COUNT + $(find "$MEDIA_DIR" -name "*.$ext" -type f 2>/dev/null | wc -l)))
done

if [ $MEDIA_COUNT -gt 0 ]; then
    print_status "Media encontrada: $MEDIA_COUNT archivos"
else
    print_warning "No se encontraron archivos de media asociados"
fi

# Crear directorio de salida
mkdir -p "$OUTPUT_DIR"

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR"

print_status "Ejecutando WhatsApp Chat Exporter..."
print_status "Salida: $OUTPUT_DIR"

# Determinar flags adicionales
ADDITIONAL_FLAGS=""
if [ "$1" = "--assume-first-as-me" ]; then
    ADDITIONAL_FLAGS="--assume-first-as-me"
    print_status "Modo: Asumir primer mensaje como propio"
elif [ "$1" = "--prompt-user" ]; then
    ADDITIONAL_FLAGS="--prompt-user"
    print_status "Modo: Preguntar interactivamente quién soy"
fi

# Ejecutar el exporter
COMMAND="poetry run python -m Whatsapp_Chat_Exporter \\
    --exported \"$CHAT_FILE\" \\
    --output \"$OUTPUT_DIR\" \\
    --json \"$OUTPUT_DIR/result.json\" \\
    --summary \"$OUTPUT_DIR/summary.json\" \\
    $ADDITIONAL_FLAGS \\
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
    
    # Verificar media copiada
    if [ -d "$OUTPUT_DIR/media" ]; then
        COPIED_MEDIA=$(find "$OUTPUT_DIR/media" -type f | wc -l)
        print_status "Media copiada: $COPIED_MEDIA archivos"
    fi
    
    echo ""
    print_success "Revisa los resultados en: $OUTPUT_DIR"
    
else
    print_error "La exportación falló. Revisa el log en: $OUTPUT_DIR/execution.log"
    print_warning "Posibles problemas:"
    print_warning "  - Formato de archivo incorrecto"
    print_warning "  - Archivos de media no encontrados"
    print_warning "  - Problemas con la detección de participantes"
    exit 1
fi