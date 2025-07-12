#!/bin/bash

# Script personalizado para analizar tus datos de WhatsApp
# Configurado para manejar grandes volúmenes de datos de manera eficiente

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZER="$SCRIPT_DIR/advanced_content_analyzer.py"
CONFIG="$SCRIPT_DIR/my_data_config.json"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    cat << EOF
🔍 Analizador de Datos Personales de WhatsApp

Uso: $0 [DIRECTORIO_CHATS] [OPCIONES]

Ejemplos:
  $0 /path/to/your/whatsapp/exports                    # Análisis completo
  $0 /path/to/exports --quick                         # Análisis rápido
  $0 /path/to/exports --keywords "trabajo,familia"    # Keywords específicas
  $0 /path/to/exports --performance                   # Test de rendimiento
  $0 --help                                           # Esta ayuda

Opciones:
  --quick       Análisis rápido (menos workers, archivos limitados)
  --keywords    Keywords personalizadas (separadas por comas)
  --performance Test de rendimiento con diferentes configuraciones
  --help        Mostrar esta ayuda

Características:
  🔍 Análisis hasta 25,000 archivos (500MB cada uno)
  📊 75+ patrones regex personalizados para español/inglés
  ⚡ Procesamiento paralelo (4 workers por defecto)
  💾 Análisis streaming para archivos grandes
  📈 Estadísticas avanzadas y frecuencia de palabras
  🎯 Patrones específicos para México/USA/España

EOF
}

check_data_directory() {
    local dir="$1"
    
    if [ ! -d "$dir" ]; then
        print_error "Directorio no encontrado: $dir"
        return 1
    fi
    
    # Verificar si contiene archivos HTML
    local html_count=$(find "$dir" -name "*.html" -o -name "*.htm" | wc -l)
    if [ $html_count -eq 0 ]; then
        print_warning "No se encontraron archivos HTML en: $dir"
        echo "Buscando otros formatos..."
        
        local json_count=$(find "$dir" -name "*.json" | wc -l)
        local txt_count=$(find "$dir" -name "*.txt" | wc -l)
        
        echo "  - Archivos JSON: $json_count"
        echo "  - Archivos TXT: $txt_count"
        echo "  - Archivos HTML: $html_count"
        
        if [ $((html_count + json_count + txt_count)) -eq 0 ]; then
            print_error "No se encontraron archivos compatibles (.html, .json, .txt)"
            return 1
        fi
    else
        print_info "Encontrados $html_count archivos HTML para analizar"
    fi
    
    return 0
}

estimate_processing_time() {
    local dir="$1"
    local file_count=$(find "$dir" -name "*.html" -o -name "*.htm" -o -name "*.json" -o -name "*.txt" | wc -l)
    local total_size=$(find "$dir" -name "*.html" -o -name "*.htm" -o -name "*.json" -o -name "*.txt" -exec stat -c%s {} + 2>/dev/null | awk '{sum += $1} END {print sum/1024/1024}' || echo "0")
    
    echo ""
    echo "📊 Estimación del Análisis:"
    echo "  - Archivos a procesar: $file_count"
    echo "  - Tamaño total: ${total_size:-0} MB"
    
    # Estimación básica: ~1 archivo por segundo para archivos pequeños
    local estimated_seconds=$((file_count / 4))  # 4 workers
    if [ $estimated_seconds -lt 10 ]; then
        echo "  - Tiempo estimado: < 1 minuto"
    elif [ $estimated_seconds -lt 60 ]; then
        echo "  - Tiempo estimado: ~$estimated_seconds segundos"
    else
        local minutes=$((estimated_seconds / 60))
        echo "  - Tiempo estimado: ~$minutes minutos"
    fi
    echo ""
}

run_full_analysis() {
    local chat_dir="$1"
    local keywords="${2:-}"
    
    print_info "🚀 Iniciando análisis completo de tus datos"
    
    local cmd="python3 \"$ANALYZER\" \"$chat_dir\" --config \"$CONFIG\" --output \"my_data_analysis_$(date +%Y%m%d_%H%M%S)\" --verbose"
    
    if [ -n "$keywords" ]; then
        cmd="$cmd --keywords \"$keywords\""
    fi
    
    echo "Ejecutando: $cmd"
    echo ""
    
    eval $cmd
}

run_quick_analysis() {
    local chat_dir="$1"
    
    print_info "⚡ Iniciando análisis rápido"
    
    python3 "$ANALYZER" "$chat_dir" \
        --keywords "trabajo,familia,importante,urgente,love,meeting" \
        --max-files 5000 \
        --parallel-workers 2 \
        --output "quick_analysis_$(date +%Y%m%d_%H%M%S)" \
        --verbose
}

run_performance_test() {
    local chat_dir="$1"
    
    print_info "🏃‍♂️ Test de rendimiento con diferentes configuraciones"
    
    echo ""
    echo "Test 1: 1 worker (secuencial)"
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,performance" \
        --parallel-workers 1 \
        --max-files 1000 \
        --output "perf_test_1worker" \
        > /dev/null 2>&1
    
    echo ""
    echo "Test 2: 2 workers"
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,performance" \
        --parallel-workers 2 \
        --max-files 1000 \
        --output "perf_test_2workers" \
        > /dev/null 2>&1
    
    echo ""
    echo "Test 3: 4 workers"
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,performance" \
        --parallel-workers 4 \
        --max-files 1000 \
        --output "perf_test_4workers" \
        > /dev/null 2>&1
    
    print_info "Tests de rendimiento completados"
    
    # Cleanup
    rm -rf perf_test_*workers
}

main() {
    echo "🔍 Analizador Avanzado de WhatsApp - Datos Personales"
    echo "===================================================="
    echo ""
    
    case "${1:-}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        "")
            print_error "Se requiere el directorio de chats"
            echo ""
            show_usage
            exit 1
            ;;
        *)
            local chat_dir="$1"
            shift
            
            # Verificar que existe el analizador
            if [ ! -f "$ANALYZER" ]; then
                print_error "Analizador no encontrado: $ANALYZER"
                exit 1
            fi
            
            # Verificar directorio
            if ! check_data_directory "$chat_dir"; then
                exit 1
            fi
            
            # Mostrar estimación
            estimate_processing_time "$chat_dir"
            
            # Procesar opciones
            case "${1:-full}" in
                --quick)
                    run_quick_analysis "$chat_dir"
                    ;;
                --keywords)
                    shift
                    local keywords="$1"
                    if [ -z "$keywords" ]; then
                        print_error "Se requieren keywords después de --keywords"
                        exit 1
                    fi
                    run_full_analysis "$chat_dir" "$keywords"
                    ;;
                --performance)
                    run_performance_test "$chat_dir"
                    ;;
                *)
                    run_full_analysis "$chat_dir"
                    ;;
            esac
            ;;
    esac
    
    echo ""
    print_info "✅ Análisis completado"
    echo ""
    echo "📁 Los resultados están en el directorio que se mostró arriba"
    echo "📊 Revisa los archivos .json para datos detallados"
    echo "📝 Revisa los archivos .txt para resúmenes legibles"
}

# Verificar Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 es requerido pero no fue encontrado"
    exit 1
fi

# Ejecutar función principal
main "$@"