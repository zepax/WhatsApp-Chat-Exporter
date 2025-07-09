#!/bin/bash

# Script de verificación del entorno de pruebas
# Verifica que todo esté configurado correctamente

set -e

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

echo "🔍 Verificando configuración del entorno de pruebas..."

# Verificar estructura de directorios
print_status "Verificando estructura de directorios..."

required_dirs=(
    "android/databases"
    "android/keys"
    "android/WhatsApp/Media"
    "ios/backup"
    "ios/media"
    "exported"
    "output"
    "scripts"
    "configs"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_success "Directorio $dir existe"
    else
        print_error "Directorio $dir no existe"
    fi
done

# Verificar archivos de configuración
print_status "Verificando archivos de configuración..."

config_files=(
    "configs/android_basic.json"
    "configs/android_encrypted.json"
    "configs/ios_basic.json"
    "configs/exported_chat.json"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "Configuración $file existe"
    else
        print_error "Configuración $file no existe"
    fi
done

# Verificar scripts
print_status "Verificando scripts de prueba..."

scripts=(
    "scripts/test_android_basic.sh"
    "scripts/test_android_encrypted.sh"
    "scripts/test_ios_basic.sh"
    "scripts/test_exported_chat.sh"
    "scripts/test_all_formats.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        print_success "Script $script existe y es ejecutable"
    elif [ -f "$script" ]; then
        print_warning "Script $script existe pero no es ejecutable"
        chmod +x "$script"
        print_success "Permisos corregidos para $script"
    else
        print_error "Script $script no existe"
    fi
done

# Verificar dependencias del proyecto
print_status "Verificando dependencias del proyecto..."

cd ..
if command -v poetry &> /dev/null; then
    print_success "Poetry está disponible"
    
    if poetry env info &> /dev/null; then
        print_success "Entorno virtual de Poetry está configurado"
        
        # Verificar módulo principal
        if poetry run python -c "import Whatsapp_Chat_Exporter" 2>/dev/null; then
            print_success "Módulo principal se importa correctamente"
        else
            print_error "Error al importar módulo principal"
        fi
        
        # Verificar dependencias opcionales
        optional_deps=(
            "pycryptodome:Crypto"
            "javaobj-py3:javaobj"
            "iphone_backup_decrypt:iphone_backup_decrypt"
        )
        
        for dep in "${optional_deps[@]}"; do
            package="${dep%:*}"
            module="${dep#*:}"
            
            if poetry run python -c "import $module" 2>/dev/null; then
                print_success "Dependencia opcional $package disponible"
            else
                print_warning "Dependencia opcional $package no disponible"
            fi
        done
        
    else
        print_error "Entorno virtual de Poetry no está configurado"
    fi
else
    print_error "Poetry no está instalado"
fi

cd test_environment

# Verificar archivos de prueba disponibles
print_status "Verificando archivos de prueba disponibles..."

android_files_found=0
ios_files_found=0
exported_files_found=0

# Android
if [ -f "android/databases/msgstore.db" ]; then
    print_success "Base de datos Android encontrada"
    android_files_found=1
fi

for ext in crypt12 crypt14 crypt15; do
    if ls android/databases/*.$ext 1> /dev/null 2>&1; then
        print_success "Backup cifrado Android encontrado (.$ext)"
        android_files_found=1
        break
    fi
done

if [ -f "android/keys/key" ] || [ -f "android/keys/crypt15_key.hex" ]; then
    print_success "Clave de descifrado Android encontrada"
fi

# iOS
if [ -d "ios/backup" ] && [ -f "ios/backup/Manifest.db" ]; then
    print_success "Backup iOS encontrado"
    ios_files_found=1
fi

# Exportados
if ls exported/*.txt 1> /dev/null 2>&1; then
    print_success "Archivos de chat exportados encontrados"
    exported_files_found=1
fi

# Resumen
echo ""
echo "========================================="
echo "           RESUMEN DE VERIFICACIÓN"
echo "========================================="

total_tests=0
available_tests=0

if [ $android_files_found -eq 1 ]; then
    print_success "Pruebas Android: DISPONIBLES"
    available_tests=$((available_tests + 1))
else
    print_warning "Pruebas Android: NO DISPONIBLES (falta msgstore.db)"
fi
total_tests=$((total_tests + 1))

if [ $ios_files_found -eq 1 ]; then
    print_success "Pruebas iOS: DISPONIBLES"
    available_tests=$((available_tests + 1))
else
    print_warning "Pruebas iOS: NO DISPONIBLES (falta backup)"
fi
total_tests=$((total_tests + 1))

if [ $exported_files_found -eq 1 ]; then
    print_success "Pruebas Exportadas: DISPONIBLES"
    available_tests=$((available_tests + 1))
else
    print_warning "Pruebas Exportadas: NO DISPONIBLES (falta archivos .txt)"
fi
total_tests=$((total_tests + 1))

echo ""
print_status "Pruebas disponibles: $available_tests de $total_tests"

if [ $available_tests -gt 0 ]; then
    echo ""
    print_success "¡Entorno configurado correctamente!"
    print_status "Puedes ejecutar las pruebas disponibles con:"
    print_status "  ./scripts/test_all_formats.sh"
    print_status "  O pruebas individuales según archivos disponibles"
else
    echo ""
    print_warning "No hay archivos de prueba disponibles"
    print_status "Coloca archivos de prueba en los directorios correspondientes:"
    print_status "  - android/databases/msgstore.db"
    print_status "  - ios/backup/"
    print_status "  - exported/*.txt"
fi

echo ""
print_status "Para más información, consulta:"
print_status "  - README.md: Información general"
print_status "  - TESTING_GUIDE.md: Guía detallada de pruebas"
print_status "  - android/README.md: Archivos Android"
print_status "  - ios/README.md: Archivos iOS"
print_status "  - exported/README.md: Archivos exportados"