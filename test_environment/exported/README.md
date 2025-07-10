# Exported Chat Test Files

## Estructura Esperada

```
exported/
├── chat_example.txt             # Archivo de chat exportado
├── chat_with_media/
│   ├── WhatsApp Chat - Contact.txt
│   ├── IMG-20231201-WA0001.jpg
│   ├── VID-20231201-WA0001.mp4
│   └── AUD-20231201-WA0001.ogg
└── group_chat.txt               # Chat de grupo exportado
```

## Instrucciones

### Archivos de Chat Exportados

1. Coloca aquí los archivos `.txt` exportados directamente desde WhatsApp
2. Los archivos deben tener el formato estándar de WhatsApp:
   ```
   [DD/MM/YYYY, HH:MM:SS] Contact Name: Message content
   ```

### Archivos de Media

Si el chat exportado incluye referencias a archivos multimedia:
1. Coloca los archivos de media en el mismo directorio que el archivo `.txt`
2. Mantén los nombres originales (IMG-*, VID-*, AUD-*, etc.)

### Formatos Soportados

- **Texto**: Archivos `.txt` con formato de WhatsApp
- **Imágenes**: JPG, PNG, GIF, WEBP
- **Videos**: MP4, AVI, MOV, 3GP
- **Audio**: OGG, MP3, WAV, AAC
- **Documentos**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX

## Características Especiales

### Detección de Participantes

Los scripts pueden:
- Asumir que el primer mensaje es tuyo (`--assume-first-as-me`)
- Preguntar interactivamente quién eres (`--prompt-user`)

### Chats de Grupo

Los chats de grupo se procesan automáticamente identificando múltiples participantes.

## Ejemplo de Formato

```
[01/12/2023, 10:30:45] Juan Pérez: Hola, ¿cómo estás?
[01/12/2023, 10:31:02] Tú: ¡Hola! Todo bien, gracias
[01/12/2023, 10:31:15] Juan Pérez: <Media omitido>
[01/12/2023, 10:31:20] Tú: 😊 Perfecto
```