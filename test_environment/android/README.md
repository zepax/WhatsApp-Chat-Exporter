# Android Test Files

## Estructura Esperada

```
android/
├── databases/
│   ├── msgstore.db              # Base de datos principal de mensajes
│   └── wa.db                    # Base de datos de contactos
├── keys/
│   ├── key                      # Archivo de clave para crypt12/14
│   └── crypt15_key.hex          # Clave hexadecimal para crypt15
└── WhatsApp/
    └── Media/
        ├── WhatsApp Images/     # Imágenes enviadas/recibidas
        ├── WhatsApp Video/      # Videos
        ├── WhatsApp Audio/      # Audios y notas de voz
        ├── WhatsApp Documents/  # Documentos
        ├── WhatsApp Stickers/   # Stickers
        └── WhatsApp Profile Photos/  # Fotos de perfil
```

## Instrucciones

### Archivos de Base de Datos

1. **msgstore.db**: Coloca aquí la base de datos de mensajes
   - Ubicación típica en Android: `/data/data/com.whatsapp/databases/msgstore.db`
   - También puede ser un backup cifrado: `msgstore.db.crypt12/14/15`

2. **wa.db**: Coloca aquí la base de datos de contactos
   - Ubicación típica en Android: `/data/data/com.whatsapp/databases/wa.db`

### Archivos de Claves (para backups cifrados)

1. **key**: Archivo binario de 158 bytes para crypt12/14
   - Ubicación típica: `/data/data/com.whatsapp/files/key`

2. **crypt15_key.hex**: Clave en formato hexadecimal para crypt15
   - Puede ser proporcionada como string hex o archivo

### Archivos de Media

Coloca los archivos de media manteniendo la estructura de directorios original de WhatsApp.

## Ejemplos de Prueba

Los scripts de prueba buscarán automáticamente estos archivos en las ubicaciones especificadas.