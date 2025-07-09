#!/bin/bash

# Test básico para iOS
# Ejecuta el exporter con backup de iTunes/Finder

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$TEST_DIR")"
OUTPUT_DIR="$TEST_DIR/output/ios_basic_$(date +%Y%m%d_%H%M%S)"

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

echo "📱 Ejecutando prueba básica para iOS..."

# Verificar archivos necesarios
BACKUP_DIR="$TEST_DIR/ios/backup"

if [ ! -d "$BACKUP_DIR" ]; then
    print_error "No se encontró directorio de backup en: $BACKUP_DIR"
    print_warning "Coloca el backup completo de iTunes/Finder en ios/backup/"
    exit 1
fi

# Verificar archivos críticos del backup
if [ ! -f "$BACKUP_DIR/Manifest.db" ]; then
    print_error "No se encontró Manifest.db en el backup"
    print_warning "Asegúrate de que el backup esté completo"
    exit 1
fi

if [ ! -f "$BACKUP_DIR/Info.plist" ]; then
    print_warning "No se encontró Info.plist en el backup"
fi

# Verificar si es un backup cifrado
ENCRYPTED="No"
if [ -f "$BACKUP_DIR/Manifest.plist" ]; then
    if grep -q "IsEncrypted" "$BACKUP_DIR/Manifest.plist" 2>/dev/null; then
        ENCRYPTED="Sí"
        print_warning "El backup parece estar cifrado"
        print_warning "Asegúrate de tener la contraseña disponible"
    fi
fi

print_status "Backup encontrado:"
print_status "  - Directorio: $BACKUP_DIR"
print_status "  - Cifrado: $ENCRYPTED"

# Crear directorio de salida
mkdir -p "$OUTPUT_DIR"

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR"

print_status "Ejecutando WhatsApp Chat Exporter..."
print_status "Salida: $OUTPUT_DIR"

# Determinar si es WhatsApp Business
BUSINESS_FLAG=""
if [ "$1" = "--business" ]; then
    BUSINESS_FLAG="--business"
    print_status "Modo: WhatsApp Business"
else
    print_status "Modo: WhatsApp regular"
fi

# Ejecutar el exporter
COMMAND="poetry run python -m Whatsapp_Chat_Exporter \\
    --ios \\
    --backup \"$BACKUP_DIR\" \\
    --output \"$OUTPUT_DIR\" \\
    --json \"$OUTPUT_DIR/result.json\" \\
    --summary \"$OUTPUT_DIR/summary.json\" \\
    $BUSINESS_FLAG \\
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
    
    # Verificar extracción de media
    if [ -d "$OUTPUT_DIR/AppDomainGroup-group.net.whatsapp.WhatsAppSMB.shared" ]; then
        print_status "Media extraída exitosamente"
    elif [ -d "$OUTPUT_DIR"/*whatsapp* ]; then
        print_status "Media extraída exitosamente"
    else
        print_warning "No se encontró media extraída"
    fi
    
    echo ""
    print_success "Revisa los resultados en: $OUTPUT_DIR"
    
else
    print_error "La exportación falló. Revisa el log en: $OUTPUT_DIR/execution.log"
    print_warning "Posibles problemas:"
    print_warning "  - Backup cifrado sin contraseña"
    print_warning "  - Backup corrupto o incompleto"
    print_warning "  - Dependencias faltantes (iphone_backup_decrypt)"
    exit 1
fi