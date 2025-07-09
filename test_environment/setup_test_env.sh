#!/bin/bash

# Setup Test Environment for WhatsApp Chat Exporter
# Este script configura todo lo necesario para ejecutar pruebas locales

set -e

echo "🚀 Configurando entorno de pruebas para WhatsApp Chat Exporter..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "../pyproject.toml" ]; then
    print_error "Este script debe ejecutarse desde el directorio test_environment/"
    exit 1
fi

# Verificar Poetry
if ! command -v poetry &> /dev/null; then
    print_error "Poetry no está instalado. Instálalo primero:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

print_success "Poetry encontrado"

# Instalar dependencias
print_status "Instalando dependencias del proyecto..."
cd ..
poetry install --all-extras
cd test_environment

print_success "Dependencias instaladas"

# Verificar instalación
print_status "Verificando instalación..."
if poetry run python -c "import Whatsapp_Chat_Exporter; print('✓ Módulo importado correctamente')" 2>/dev/null; then
    print_success "Instalación verificada"
else
    print_warning "Hay problemas con la instalación. Verifica las dependencias."
fi

# Crear directorios adicionales si no existen
print_status "Creando directorios adicionales..."
mkdir -p output/{android,ios,exported,json,html,logs}
mkdir -p android/WhatsApp/Media/{WhatsApp\ Images,WhatsApp\ Video,WhatsApp\ Audio,WhatsApp\ Documents,WhatsApp\ Stickers,WhatsApp\ Profile\ Photos}

print_success "Directorios creados"

# Verificar permisos de scripts
print_status "Configurando permisos de scripts..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x setup_test_env.sh

print_success "Permisos configurados"

# Información final
echo ""
echo "🎉 Entorno de pruebas configurado exitosamente!"
echo ""
echo "📁 Estructura creada:"
echo "   - android/: Archivos de prueba para Android"
echo "   - ios/: Archivos de prueba para iOS"
echo "   - exported/: Chats exportados (.txt)"
echo "   - output/: Resultados de las pruebas"
echo "   - scripts/: Scripts de prueba automatizados"
echo "   - configs/: Configuraciones para diferentes escenarios"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Coloca tus archivos de prueba en los directorios correspondientes"
echo "   2. Ejecuta los scripts de prueba desde scripts/"
echo "   3. Revisa los resultados en output/"
echo ""
echo "💡 Usa 'poetry run' para ejecutar comandos del proyecto"
echo "   Ejemplo: poetry run python -m Whatsapp_Chat_Exporter --help"