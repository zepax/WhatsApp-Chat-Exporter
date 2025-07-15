# Template Optimizado de WhatsApp

El template optimizado (`whatsapp_optimized.html`) es una versión mejorada del template de WhatsApp que incluye funcionalidades avanzadas de búsqueda y navegación.

## 🚀 Características Principales

### ✨ Búsqueda Avanzada
- **Búsqueda en tiempo real**: Busca mensajes mientras escribes
- **Navegación entre resultados**: Usa los botones o atajos de teclado
- **Resaltado inteligente**: Los términos encontrados se destacan visualmente
- **Estadísticas de búsqueda**: Muestra "X de Y resultados"

### 🎨 Diseño Moderno
- **Interfaz tipo WhatsApp**: Colores y diseño fieles a la aplicación original
- **Responsive**: Se adapta perfectamente a móviles y tablets
- **Animaciones suaves**: Transiciones y efectos visuales mejorados
- **Modo oscuro preparado**: Variables CSS para futura implementación

### ⚡ Rendimiento Optimizado
- **Lazy loading**: Los videos se cargan solo cuando son visibles
- **Scroll suave**: Navegación fluida entre mensajes
- **Highlighting eficiente**: Búsqueda optimizada sin bloquear la interfaz

## 📚 Uso

### Activación del Template
```bash
# Usar el template optimizado por defecto
wtsexporter -i -d database.sqlite -o output/

# Especificar explícitamente el template optimizado  
wtsexporter -i -d database.sqlite -o output/ --template optimized

# Usar template básico si prefieres la versión simple
wtsexporter -i -d database.sqlite -o output/ --template basic
```

### Atajos de Teclado
- **Ctrl+F / Cmd+F**: Abrir búsqueda
- **Enter**: Ir al siguiente resultado
- **Shift+Enter**: Ir al resultado anterior  
- **Escape**: Cerrar búsqueda

### Navegación
- **Clic en respuestas**: Salta automáticamente al mensaje original
- **Enlaces internos**: Navegación suave entre mensajes referenciados
- **Botones de navegación**: Anterior/Siguiente chat en la parte superior

## 🛠️ Características Técnicas

### Estructura CSS
- **Variables CSS**: Fácil personalización de colores y espaciados
- **Flexbox moderno**: Layout responsive y flexible
- **Grid CSS**: Organización eficiente de elementos
- **Custom scrollbars**: Scrollbars estilizados que coinciden con el tema

### JavaScript Avanzado
- **Búsqueda incremental**: Algoritmo de búsqueda optimizado
- **Gestión de estado**: Manejo inteligente del estado de búsqueda
- **Event delegation**: Manejo eficiente de eventos
- **Intersection Observer**: Para lazy loading de videos

### Accesibilidad
- **Navegación por teclado**: Totalmente accesible sin mouse
- **ARIA labels**: Etiquetas apropiadas para lectores de pantalla
- **Contraste optimizado**: Colores que cumplen estándares de accesibilidad
- **Focus management**: Manejo inteligente del foco durante la búsqueda

## 🎯 Comparación con Templates

| Característica | Básico | Nuevo | **Optimizado** |
|----------------|--------|-------|----------------|
| Búsqueda | ❌ | ❌ | ✅ **Avanzada** |
| Diseño moderno | ❌ | ✅ | ✅ **Mejorado** |
| Responsive | ⚠️ Básico | ✅ | ✅ **Completo** |
| Navegación | ⚠️ Básica | ✅ | ✅ **Avanzada** |
| Rendimiento | ✅ | ✅ | ✅ **Optimizado** |
| Accesibilidad | ⚠️ Básica | ✅ | ✅ **Completa** |

## 🔧 Personalización

### Variables CSS Principales
```css
:root {
    --whatsapp-primary: #25D366;    /* Color principal */
    --whatsapp-dark: #075E54;       /* Color del header */
    --whatsapp-light: #DCF8C6;      /* Burbujas propias */
    --whatsapp-bg: #E5DDD5;         /* Fondo del chat */
    --whatsapp-white: #FFFFFF;      /* Burbujas ajenas */
}
```

### Personalizar Búsqueda
```css
.search-highlight {
    background: #FFE066;    /* Color de resaltado */
    color: #333;           /* Color del texto resaltado */
}

.search-match {
    background: rgba(37, 211, 102, 0.1);  /* Fondo del resultado actual */
    border: 1px solid rgba(37, 211, 102, 0.3);  /* Borde del resultado actual */
}
```

## 📱 Compatibilidad

### Navegadores Soportados
- ✅ **Chrome/Chromium 88+**
- ✅ **Firefox 85+** 
- ✅ **Safari 14+**
- ✅ **Edge 88+**
- ⚠️ Internet Explorer: No soportado

### Dispositivos
- ✅ **Desktop**: Experiencia completa
- ✅ **Tablet**: Interfaz adaptada
- ✅ **Mobile**: Optimizado para pantallas pequeñas
- ✅ **Touch devices**: Gestos táctiles soportados

## 🐛 Solución de Problemas

### La búsqueda no funciona
- Verifica que JavaScript esté habilitado
- Comprueba la consola del navegador para errores
- Algunos bloqueadores de contenido pueden interferir

### Las imágenes no cargan
- Verifica que la carpeta `media/` esté en la ubicación correcta
- Comprueba los permisos de archivos
- Asegúrate de que las rutas no contengan caracteres especiales

### El diseño se ve mal en móvil
- Asegúrate de que el viewport meta tag esté presente
- Verifica que no haya CSS personalizado que interfiera
- Comprueba que el navegador soporte CSS Grid y Flexbox

## 🔄 Historial de Versiones

### v1.0.0
- ✅ Implementación inicial
- ✅ Búsqueda avanzada
- ✅ Diseño responsive
- ✅ Atajos de teclado
- ✅ Navegación optimizada
- ✅ Lazy loading para videos
- ✅ Accesibilidad mejorada