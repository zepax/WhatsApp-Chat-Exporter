#!/bin/bash

# Test completo - ejecuta todas las pruebas de formato disponibles
# Genera reportes comparativos de rendimiento y resultados

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$TEST_DIR/output/all_formats_$(date +%Y%m%d_%H%M%S)"

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

echo "🚀 Ejecutando pruebas completas para todos los formatos..."

# Crear directorio de salida
mkdir -p "$OUTPUT_DIR"

# Contadores
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Función para ejecutar una prueba
run_test() {
    local test_name="$1"
    local test_script="$2"
    local test_args="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    print_status "Ejecutando: $test_name"
    
    # Crear subdirectorio para esta prueba
    local test_output="$OUTPUT_DIR/$test_name"
    mkdir -p "$test_output"
    
    # Ejecutar prueba
    local start_time=$(date +%s)
    
    if bash "$test_script" $test_args > "$test_output/output.log" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        print_success "$test_name completada (${duration}s)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Guardar información de la prueba
        echo "{
    \"test_name\": \"$test_name\",
    \"status\": \"PASSED\",
    \"duration\": $duration,
    \"timestamp\": \"$(date -Iseconds)\"
}" > "$test_output/result.json"
        
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        print_error "$test_name falló (${duration}s)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        
        # Guardar información de la prueba
        echo "{
    \"test_name\": \"$test_name\",
    \"status\": \"FAILED\",
    \"duration\": $duration,
    \"timestamp\": \"$(date -Iseconds)\"
}" > "$test_output/result.json"
    fi
}

# Ejecutar pruebas disponibles
echo "Buscando archivos de prueba disponibles..."

# Test Android básico
if [ -f "$TEST_DIR/android/databases/msgstore.db" ]; then
    run_test "android_basic" "$SCRIPT_DIR/test_android_basic.sh" ""
else
    print_warning "Saltando prueba Android básica: msgstore.db no encontrado"
fi

# Test Android cifrado
encrypted_found=false
for ext in crypt12 crypt14 crypt15; do
    if ls "$TEST_DIR/android/databases/"*.$ext 1> /dev/null 2>&1; then
        encrypted_found=true
        break
    fi
done

if [ "$encrypted_found" = true ] && [ -f "$TEST_DIR/android/keys/key" -o -f "$TEST_DIR/android/keys/crypt15_key.hex" ]; then
    run_test "android_encrypted" "$SCRIPT_DIR/test_android_encrypted.sh" ""
else
    print_warning "Saltando prueba Android cifrado: backup cifrado o clave no encontrados"
fi

# Test iOS básico
if [ -d "$TEST_DIR/ios/backup" ] && [ -f "$TEST_DIR/ios/backup/Manifest.db" ]; then
    run_test "ios_basic" "$SCRIPT_DIR/test_ios_basic.sh" ""
    
    # Test iOS Business si está disponible
    run_test "ios_business" "$SCRIPT_DIR/test_ios_basic.sh" "--business"
else
    print_warning "Saltando prueba iOS: backup no encontrado"
fi

# Test chats exportados
if ls "$TEST_DIR/exported/"*.txt 1> /dev/null 2>&1; then
    run_test "exported_basic" "$SCRIPT_DIR/test_exported_chat.sh" ""
    run_test "exported_assume_first" "$SCRIPT_DIR/test_exported_chat.sh" "--assume-first-as-me"
else
    print_warning "Saltando prueba chats exportados: archivos .txt no encontrados"
fi

# Generar reporte final
print_status "Generando reporte final..."

# Reporte JSON
cat > "$OUTPUT_DIR/test_report.json" << EOF
{
    "summary": {
        "total_tests": $TOTAL_TESTS,
        "passed": $PASSED_TESTS,
        "failed": $FAILED_TESTS,
        "success_rate": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0"),
        "timestamp": "$(date -Iseconds)"
    },
    "tests": [
EOF

# Agregar resultados individuales
first=true
for result_file in "$OUTPUT_DIR"/*/result.json; do
    if [ -f "$result_file" ]; then
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$OUTPUT_DIR/test_report.json"
        fi
        cat "$result_file" >> "$OUTPUT_DIR/test_report.json"
    fi
done

echo "    ]
}" >> "$OUTPUT_DIR/test_report.json"

# Reporte en texto
cat > "$OUTPUT_DIR/test_report.txt" << EOF
REPORTE DE PRUEBAS - $(date)
==============================

Resumen:
- Total de pruebas: $TOTAL_TESTS
- Exitosas: $PASSED_TESTS
- Fallidas: $FAILED_TESTS
- Tasa de éxito: $(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")%

Detalle de pruebas:
EOF

for result_file in "$OUTPUT_DIR"/*/result.json; do
    if [ -f "$result_file" ]; then
        python3 -c "
import json
try:
    with open('$result_file', 'r') as f:
        data = json.load(f)
    status_icon = '✓' if data['status'] == 'PASSED' else '✗'
    print(f'{status_icon} {data[\"test_name\"]}: {data[\"status\"]} ({data[\"duration\"]}s)')
except Exception as e:
    print(f'Error procesando $result_file: {e}')
" >> "$OUTPUT_DIR/test_report.txt"
    fi
done

# Mostrar resumen final
echo ""
echo "========================================="
echo "           RESUMEN FINAL"
echo "========================================="
print_status "Total de pruebas ejecutadas: $TOTAL_TESTS"
print_success "Pruebas exitosas: $PASSED_TESTS"
print_error "Pruebas fallidas: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    print_success "¡Todas las pruebas pasaron exitosamente!"
else
    print_warning "Algunas pruebas fallaron. Revisa los logs individuales."
fi

echo ""
print_status "Reportes generados:"
print_status "  - Reporte JSON: $OUTPUT_DIR/test_report.json"
print_status "  - Reporte texto: $OUTPUT_DIR/test_report.txt"
print_status "  - Logs individuales: $OUTPUT_DIR/*/output.log"
echo ""
print_success "Revisa todos los resultados en: $OUTPUT_DIR"