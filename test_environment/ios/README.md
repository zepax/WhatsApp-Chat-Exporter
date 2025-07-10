# iOS Test Files

## Estructura Esperada

```
ios/
├── backup/                      # Directorio completo de backup iTunes/Finder
│   ├── Info.plist
│   ├── Manifest.db
│   ├── Manifest.plist
│   └── [archivos con hash]/     # Archivos del backup con nombres hash
└── media/                       # Media extraída automáticamente
```

## Instrucciones

### Backup de iTunes/Finder

1. Coloca el directorio completo del backup en `backup/`
2. El backup debe contener:
   - `Manifest.db` (obligatorio)
   - `Info.plist` (información del dispositivo)
   - `Manifest.plist` (si no está cifrado)
   - Archivos con nombres hash (contenido real)

### Ubicaciones Típicas de Backup

**macOS:**
- `~/Library/Application Support/MobileSync/Backup/[device-id]/`

**Windows:**
- `%APPDATA%\Apple Computer\MobileSync\Backup\[device-id]\`

### Archivos Importantes del Backup

El exporter buscará automáticamente estos archivos por sus hashes conocidos:
- `7c7fba66680ef796b916b067077cc246adacf01d` (ChatStorage.sqlite - mensajes)
- `ContactsV2.sqlite` (contactos)
- Archivos de media (extraídos automáticamente)

### WhatsApp Business

Para WhatsApp Business, usa la flag `--business` en los scripts de prueba.

## Backup Cifrado

Si el backup está cifrado, necesitarás la contraseña del backup. Los scripts de prueba te la pedirán si es necesario.

## Notas

- Los archivos de media se extraerán automáticamente al directorio `media/`
- El proceso puede tardar dependiendo del tamaño del backup