#!/bin/bash

# Analizador de Chats de WhatsApp en Español
# Optimizado específicamente para conversaciones en español mexicano/latinoamericano

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZER="$SCRIPT_DIR/advanced_content_analyzer.py"
CONFIG_ESPANOL="$SCRIPT_DIR/spanish_config.json"

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
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

mostrar_uso() {
    cat << EOF
🇪🇸 Analizador de Chats de WhatsApp en Español

Uso: $0 [DIRECTORIO_CHATS] [OPCIONES]

Ejemplos:
  $0 /ruta/a/tus/chats                           # Análisis completo en español
  $0 /ruta/a/chats --rapido                     # Análisis rápido
  $0 /ruta/a/chats --palabras "amor,trabajo"    # Palabras específicas
  $0 /ruta/a/chats --familia                    # Enfoque en conversaciones familiares
  $0 /ruta/a/chats --trabajo                    # Enfoque en conversaciones de trabajo
  $0 --ayuda                                    # Esta ayuda

Opciones:
  --rapido      Análisis rápido (5,000 archivos máximo)
  --familia     Enfoque en conversaciones familiares
  --trabajo     Enfoque en conversaciones de trabajo
  --palabras    Palabras clave personalizadas (separadas por comas)
  --rendimiento Test de rendimiento
  --ayuda       Mostrar esta ayuda

Características Específicas para Español:
  🇲🇽 Optimizado para español mexicano/latinoamericano
  📱 Detecta teléfonos mexicanos (+52, 55, etc.)
  💬 Reconoce expresiones mexicanas (órale, ándale, híjole, etc.)
  📅 Maneja fechas en español (15 de marzo, etc.)
  💰 Detecta montos en pesos mexicanos
  😊 Identifica emociones en español
  👨‍👩‍👧‍👦 Términos familiares específicos
  🏢 Vocabulario de trabajo en español
  🍽️ Comida y lugares típicos mexicanos

Patrones Incluidos:
  • 80+ palabras clave en español
  • 35+ patrones regex especializados
  • Expresiones coloquiales mexicanas
  • Saludos y despedidas en español
  • Emociones positivas/negativas
  • Términos de familia, trabajo, comida
  • Detección de lugares y transporte

EOF
}

verificar_directorio() {
    local dir="$1"
    
    if [ ! -d "$dir" ]; then
        print_error "Directorio no encontrado: $dir"
        return 1
    fi
    
    # Contar archivos
    local html_count=$(find "$dir" -name "*.html" -o -name "*.htm" | wc -l)
    local total_size=$(find "$dir" -name "*.html" -o -name "*.htm" -exec stat -c%s {} + 2>/dev/null | awk '{sum += $1} END {print sum/1024/1024}' || echo "0")
    
    if [ $html_count -eq 0 ]; then
        print_warning "No se encontraron archivos HTML en: $dir"
        
        local json_count=$(find "$dir" -name "*.json" | wc -l)
        local txt_count=$(find "$dir" -name "*.txt" | wc -l)
        
        echo "  📊 Archivos encontrados:"
        echo "     - HTML: $html_count"
        echo "     - JSON: $json_count" 
        echo "     - TXT: $txt_count"
        
        if [ $((html_count + json_count + txt_count)) -eq 0 ]; then
            print_error "No se encontraron archivos compatibles"
            return 1
        fi
    else
        print_info "📁 Encontrados $html_count archivos HTML (${total_size:-0} MB total)"
    fi
    
    return 0
}

estimar_tiempo() {
    local dir="$1"
    local file_count=$(find "$dir" -name "*.html" -o -name "*.htm" -o -name "*.json" -o -name "*.txt" | wc -l)
    
    echo ""
    echo "⏱️  Estimación del Análisis:"
    echo "   📁 Archivos a procesar: $file_count"
    
    if [ $file_count -lt 100 ]; then
        echo "   ⏰ Tiempo estimado: 1-2 minutos"
    elif [ $file_count -lt 1000 ]; then
        echo "   ⏰ Tiempo estimado: 2-5 minutos"
    elif [ $file_count -lt 5000 ]; then
        echo "   ⏰ Tiempo estimado: 5-15 minutos"
    else
        echo "   ⏰ Tiempo estimado: 15+ minutos"
    fi
    echo ""
}

analisis_completo() {
    local chat_dir="$1"
    local palabras="${2:-}"
    
    print_info "🚀 Iniciando análisis completo en español"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_dir="analisis_español_$timestamp"
    
    local cmd="python3 \"$ANALYZER\" \"$chat_dir\" --config \"$CONFIG_ESPANOL\" --output \"$output_dir\" --verbose"
    
    if [ -n "$palabras" ]; then
        cmd="$cmd --keywords \"$palabras\""
    fi
    
    echo "🔍 Ejecutando análisis..."
    echo ""
    
    eval $cmd
    
    echo ""
    print_info "✅ Análisis completado. Resultados en: $output_dir"
}

analisis_rapido() {
    local chat_dir="$1"
    
    print_info "⚡ Análisis rápido en español"
    
    python3 "$ANALYZER" "$chat_dir" \
        --keywords "amor,familia,trabajo,importante,urgente,feliz,gracias" \
        --max-files 5000 \
        --parallel-workers 4 \
        --output "analisis_rapido_$(date +%Y%m%d_%H%M%S)" \
        --verbose
}

analisis_familia() {
    local chat_dir="$1"
    
    print_info "👨‍👩‍👧‍👦 Análisis enfocado en familia"
    
    # Keywords específicas para familia
    local palabras_familia="familia,papá,mamá,hijo,hija,hermano,hermana,amor,te quiero,te amo,casa,cumpleaños,navidad,vacaciones,primo,prima,tío,tía,abuelo,abuela"
    
    python3 "$ANALYZER" "$chat_dir" \
        --config "$CONFIG_ESPANOL" \
        --keywords "$palabras_familia" \
        --output "analisis_familia_$(date +%Y%m%d_%H%M%S)" \
        --verbose
}

analisis_trabajo() {
    local chat_dir="$1"
    
    print_info "🏢 Análisis enfocado en trabajo"
    
    # Keywords específicas para trabajo
    local palabras_trabajo="trabajo,chamba,jale,oficina,jefe,proyecto,reunión,junta,tarea,pendiente,deadline,entrega,cliente,empresa,negocio,dinero,pesos"
    
    python3 "$ANALYZER" "$chat_dir" \
        --config "$CONFIG_ESPANOL" \
        --keywords "$palabras_trabajo" \
        --output "analisis_trabajo_$(date +%Y%m%d_%H%M%S)" \
        --verbose
}

test_rendimiento() {
    local chat_dir="$1"
    
    print_info "🏃‍♂️ Test de rendimiento en español"
    
    echo ""
    echo "Test 1: 2 workers"
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,prueba,rendimiento" \
        --parallel-workers 2 \
        --max-files 1000 \
        --output "test_2workers" \
        > /dev/null 2>&1
    
    echo ""
    echo "Test 2: 4 workers"  
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,prueba,rendimiento" \
        --parallel-workers 4 \
        --max-files 1000 \
        --output "test_4workers" \
        > /dev/null 2>&1
    
    echo ""
    echo "Test 3: 6 workers"
    time python3 "$ANALYZER" "$chat_dir" \
        --keywords "test,prueba,rendimiento" \
        --parallel-workers 6 \
        --max-files 1000 \
        --output "test_6workers" \
        > /dev/null 2>&1
    
    print_info "Tests completados"
    
    # Limpiar archivos de test
    rm -rf test_*workers
}

main() {
    echo "🇪🇸 Analizador de Chats de WhatsApp en Español"
    echo "=============================================="
    echo ""
    
    case "${1:-}" in
        --ayuda|-h)
            mostrar_uso
            exit 0
            ;;
        "")
            print_error "Se requiere el directorio de chats"
            echo ""
            mostrar_uso
            exit 1
            ;;
        *)
            local chat_dir="$1"
            shift
            
            # Verificar analizador
            if [ ! -f "$ANALYZER" ]; then
                print_error "Analizador no encontrado: $ANALYZER"
                exit 1
            fi
            
            # Verificar configuración
            if [ ! -f "$CONFIG_ESPANOL" ]; then
                print_error "Configuración en español no encontrada: $CONFIG_ESPANOL"
                exit 1
            fi
            
            # Verificar directorio
            if ! verificar_directorio "$chat_dir"; then
                exit 1
            fi
            
            # Mostrar estimación
            estimar_tiempo "$chat_dir"
            
            # Procesar opciones
            case "${1:-completo}" in
                --rapido)
                    analisis_rapido "$chat_dir"
                    ;;
                --familia)
                    analisis_familia "$chat_dir"
                    ;;
                --trabajo)
                    analisis_trabajo "$chat_dir"
                    ;;
                --palabras)
                    shift
                    local palabras="$1"
                    if [ -z "$palabras" ]; then
                        print_error "Se requieren palabras después de --palabras"
                        exit 1
                    fi
                    analisis_completo "$chat_dir" "$palabras"
                    ;;
                --rendimiento)
                    test_rendimiento "$chat_dir"
                    ;;
                *)
                    analisis_completo "$chat_dir"
                    ;;
            esac
            ;;
    esac
    
    echo ""
    print_info "🎉 ¡Análisis terminado!"
    echo ""
    echo "💡 Consejos:"
    echo "   📊 Revisa los archivos .json para datos detallados"
    echo "   📝 Revisa los archivos .txt para resúmenes"
    echo "   🔍 Busca patrones específicos en los resultados"
}

# Verificar Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 es requerido pero no fue encontrado"
    exit 1
fi

# Ejecutar función principal
main "$@"