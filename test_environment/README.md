# Entorno de Pruebas - WhatsApp Chat Exporter

Este directorio contiene todo lo necesario para realizar pruebas locales del WhatsApp Chat Exporter.

## Estructura de Directorios

```
test_environment/
├── android/                    # Archivos de prueba para Android
│   ├── databases/             # Coloca aquí msgstore.db y wa.db
│   ├── keys/                  # Coloca aquí archivos de claves para crypt12/14/15
│   └── WhatsApp/
│       └── Media/             # Coloca aquí archivos de media de WhatsApp
├── ios/                       # Archivos de prueba para iOS
│   ├── backup/               # Coloca aquí backup de iTunes/Finder
│   └── media/                # Archivos de media extraídos
├── exported/                  # Archivos de chat exportados (.txt)
├── output/                    # Directorio de salida para resultados
├── scripts/                   # Scripts de prueba automatizados
└── configs/                   # Configuraciones para diferentes escenarios
```

## Instrucciones de Uso

### 1. Colocar Archivos de Prueba

**Para Android:**
- Coloca `msgstore.db` en `android/databases/`
- Coloca `wa.db` en `android/databases/`
- Coloca archivos de media en `android/WhatsApp/Media/`
- Si usas backups cifrados, coloca la clave en `android/keys/`

**Para iOS:**
- Coloca el backup de iTunes/Finder en `ios/backup/`
- Los archivos de media se extraerán automáticamente

**Para Chats Exportados:**
- Coloca archivos `.txt` exportados en `exported/`

### 2. Ejecutar Pruebas

Usa los scripts en `scripts/` para ejecutar diferentes tipos de pruebas:

```bash
# Prueba básica Android
./scripts/test_android_basic.sh

# Prueba con backup cifrado
./scripts/test_android_encrypted.sh

# Prueba iOS
./scripts/test_ios_basic.sh

# Prueba chat exportado
./scripts/test_exported_chat.sh
```

### 3. Verificar Resultados

Los resultados se generarán en `output/` con subdirectorios por cada prueba ejecutada.

## Notas Importantes

- Asegúrate de que las dependencias estén instaladas (`poetry install`)
- Revisa los logs en cada directorio de output para debugging
- Los archivos de ejemplo deben ser reales pero sin información sensible