# 📊 WhatsApp Chat Analyzer Professional 2.0

**La herramienta más avanzada y completa para el análisis profesional de conversaciones de WhatsApp**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Professional Grade](https://img.shields.io/badge/Grade-Professional-green.svg)](https://github.com)

## 🌟 Características Principales

### 🔍 **Análisis Avanzado**
- **Búsqueda inteligente** con soporte para expresiones regulares y operadores booleanos
- **Análisis de sentimientos** usando TextBlob para detectar emociones en conversaciones
- **Detección automática de idiomas** para análisis multilingüe
- **Extracción de temas** automática basada en contenido
- **Análisis de participantes** y frecuencia de mensajes
- **Detección de medios** (fotos, videos, documentos, audio)

### ⚡ **Rendimiento Optimizado**
- **Procesamiento paralelo** con múltiples workers para máxima velocidad
- **Sistema de caché inteligente** para evitar reprocesar archivos
- **Análisis incremental** - solo procesa archivos nuevos o modificados
- **División automática** de archivos grandes para mejor rendimiento del navegador
- **Optimización de memoria** para manejar conjuntos de datos masivos

### 📊 **Exportación Profesional**
- **Reportes Excel avanzados** con múltiples hojas, gráficos y formato profesional
- **Reportes PDF** con visualizaciones y análisis detallado
- **Dashboard web interactivo** con gráficos en tiempo real
- **Exportación JSON** estructurada para integración con otras herramientas
- **Exportación CSV** compatible con herramientas de análisis de datos

### 🔐 **Seguridad y Privacidad**
- **Anonimización automática** de datos personales (GDPR compliant)
- **Encriptación** de archivos de salida con AES-256
- **Eliminación segura** de archivos temporales
- **Auditoría completa** de todas las operaciones
- **Reportes de cumplimiento** GDPR/CCPA

### 🤖 **Automatización Completa**
- **Programación automática** de análisis (diario, semanal, mensual)
- **Notificaciones** por email, Slack y Discord
- **Limpieza automática** de archivos antiguos
- **Monitoreo de carpetas** para procesamiento automático
- **Respaldo automático** de resultados

### ⚙️ **Configuración Avanzada**
- **Perfiles de configuración** guardables y reutilizables
- **Plantillas predefinidas** para casos de uso comunes
- **Configuración por línea de comandos** o archivos
- **Importación/exportación** de configuraciones
- **Variables de entorno** para implementaciones corporativas

## 🚀 Instalación Rápida

### Prerequisitos
- Python 3.8 o superior
- 4GB RAM recomendados
- 1GB espacio en disco

### Instalación Automática
```bash
# Clona o descarga los archivos
git clone https://github.com/tu-usuario/whatsapp-analyzer-pro.git
cd whatsapp-analyzer-pro

# Ejecuta el script de instalación
python setup.py

# O para instalación mínima
python setup.py --install-type minimal
```

### Instalación Manual
```bash
# Instala dependencias básicas
pip install beautifulsoup4 lxml pandas

# Instala características avanzadas (opcional)
pip install openpyxl textblob matplotlib seaborn plotly reportlab flask schedule cryptography

# Descarga datos de NLP
python -m textblob.download_corpora
```

## 📖 Uso Básico

### Análisis Simple
```bash
# Análisis básico de una carpeta
python content_analyzer.py /ruta/a/exportaciones/whatsapp

# Con configuración personalizada
python content_analyzer.py /ruta/a/chats --config mi_config.json

# Generar dashboard web
python content_analyzer.py /ruta/a/chats --generate-dashboard
```

### Análisis Avanzado
```bash
# Análisis completo con todas las características
python content_analyzer.py /ruta/a/chats \
    --config profesional_config.json \
    --copy-filtered \
    --split-large \
    --generate-excel \
    --generate-pdf \
    --generate-dashboard \
    --sentiment-analysis \
    --anonymize-data

# Análisis programado
python content_analyzer.py /ruta/a/chats \
    --schedule-analysis \
    --frequency weekly \
    --time "02:00" \
    --email-notifications
```

## 🎯 Casos de Uso

### 🏢 **Empresarial**
```bash
# Análisis de comunicaciones corporativas
python content_analyzer.py /comunicaciones/empresa \
    --config empresa_config.json \
    --anonymize-data \
    --encrypt-output \
    --generate-compliance-report \
    --audit-logging
```

### 🔬 **Investigación**
```bash
# Análisis académico con características avanzadas
python content_analyzer.py /datos/investigacion \
    --sentiment-analysis \
    --language-detection \
    --topic-extraction \
    --generate-excel \
    --statistical-analysis
```

### 🏠 **Personal**
```bash
# Análisis personal de conversaciones familiares
python content_analyzer.py /chats/familia \
    --config personal_config.json \
    --generate-dashboard \
    --copy-filtered \
    --keywords "cumpleaños,vacaciones,reunión"
```

### 🛡️ **Forense/Legal**
```bash
# Análisis forense con máxima seguridad
python content_analyzer.py /evidencia/chats \
    --config forense_config.json \
    --anonymize-data \
    --encrypt-output \
    --audit-logging \
    --hash-verification \
    --compliance-mode
```

## ⚙️ Configuración Detallada

### Archivo de Configuración
```json
{
  "analysis": {
    "keywords": ["urgente", "importante", "reunión", "proyecto"],
    "use_regex": true,
    "case_sensitive": false,
    "sentiment_analysis": true,
    "language_detection": true,
    "topic_extraction": true,
    "date_from": "2024-01-01",
    "date_to": "2024-12-31",
    "participants_filter": ["Juan", "María"]
  },
  "processing": {
    "max_workers": 8,
    "use_cache": true,
    "cache_directory": ".cache",
    "timeout_seconds": 300
  },
  "output": {
    "generate_excel": true,
    "generate_pdf": true,
    "generate_dashboard": true,
    "output_directory": "resultados_analisis"
  },
  "security": {
    "anonymize_data": true,
    "encrypt_output": true,
    "master_password": "mi_password_seguro",
    "secure_deletion": true
  },
  "automation": {
    "auto_cleanup": true,
    "cleanup_after_days": 30,
    "auto_backup": true,
    "backup_location": "/backup/whatsapp_analysis"
  },
  "notifications": {
    "email_enabled": true,
    "email_recipients": ["admin@empresa.com"],
    "slack_webhook_url": "https://hooks.slack.com/...",
    "discord_webhook_url": "https://discord.com/api/webhooks/..."
  },
  "scheduling": {
    "enabled": true,
    "frequency": "weekly",
    "time": "02:00",
    "days_of_week": ["sunday"]
  }
}
```

### Patrones de Búsqueda Avanzados
```json
{
  "keywords": [
    "\\b(urgente|URGENTE)\\b",
    "reun(ión|ion).*mañana",
    "(?i)proyecto\\s+\\w+",
    "\\d{2}/\\d{2}/\\d{4}.*deadline",
    "(?:cliente|customer).*(?:molesto|angry)"
  ],
  "use_regex": true,
  "case_sensitive": false
}
```

## 📊 Formatos de Salida

### Dashboard Web Interactivo
- **Gráficos en tiempo real** con Plotly
- **Filtros dinámicos** por fecha, participante, palabra clave
- **Estadísticas en vivo** durante el análisis
- **Exportación** de gráficos y datos
- **Interfaz responsive** para móviles y tablets

### Reportes Excel Profesionales
- **Hoja de resumen ejecutivo** con métricas clave
- **Análisis detallado** por conversación
- **Matriz de palabras clave** con código de colores
- **Gráficos integrados** (barras, círculos, líneas)
- **Formato profesional** listo para presentaciones

### Reportes PDF
- **Formato corporativo** con logo y branding
- **Gráficos y visualizaciones** integradas
- **Análisis estadístico** detallado
- **Cumplimiento GDPR** con disclaimers
- **Anexos técnicos** opcionales

## 🔐 Características de Seguridad

### Anonimización
- **Participantes**: USER_A1B2C3D4
- **Números de teléfono**: [PHONE_REDACTED]
- **Emails**: [EMAIL_REDACTED]
- **URLs**: [URL_REDACTED]
- **Tarjetas de crédito**: [CARD_REDACTED]

### Encriptación
- **AES-256** para archivos de salida
- **PBKDF2** para derivación de claves
- **Salt único** por instalación
- **Eliminación segura** de claves temporales

### Auditoría
```json
{
  "timestamp": "2024-07-10T15:30:00",
  "action": "analysis_completed",
  "user_hash": "abc123def456",
  "files_processed": 25,
  "security_measures": ["anonymization", "encryption"],
  "compliance_status": "gdpr_compliant"
}
```

## 🤖 Automatización

### Programación de Análisis
```python
# Análisis automático cada domingo a las 2:00 AM
from automation_manager import AutomationManager

automation = AutomationManager(config_manager)
automation.schedule_analysis(
    analyzer.analyze_directory,
    "/ruta/a/chats",
    frequency="weekly",
    time="02:00",
    days_of_week=["sunday"]
)
```

### Notificaciones
```python
# Configurar notificaciones múltiples
notifications = {
    "email": {
        "enabled": True,
        "recipients": ["admin@empresa.com", "manager@empresa.com"],
        "smtp_server": "smtp.empresa.com"
    },
    "slack": {
        "enabled": True,
        "webhook_url": "https://hooks.slack.com/services/...",
        "channel": "#analytics"
    }
}
```

## 📈 Métricas y Monitoreo

### Métricas de Rendimiento
- **Velocidad de procesamiento**: mensajes/segundo
- **Uso de memoria**: RAM actual y pico
- **Uso de CPU**: porcentaje por core
- **Cache hit ratio**: eficiencia del caché
- **Tiempo de respuesta**: latencia por archivo

### Métricas de Análisis
- **Cobertura de palabras clave**: % de keywords encontradas
- **Distribución de sentimientos**: positivo/neutro/negativo
- **Participación por usuario**: mensajes por participante
- **Actividad temporal**: mensajes por hora/día/mes
- **Tipos de contenido**: texto/imagen/video/documento

## 🆘 Resolución de Problemas

### Problemas Comunes

#### Error de Memoria
```bash
# Reduce workers o activa modo de bajo consumo
python content_analyzer.py /ruta/a/chats --max-workers 2 --low-memory-mode
```

#### Archivos Corruptos
```bash
# Activa modo de recuperación de errores
python content_analyzer.py /ruta/a/chats --error-recovery --skip-corrupted
```

#### Rendimiento Lento
```bash
# Optimiza configuración para velocidad
python content_analyzer.py /ruta/a/chats --performance-mode --disable-sentiment
```

### Logs y Debugging
```bash
# Modo verbose para debugging
python content_analyzer.py /ruta/a/chats --verbose --debug-mode

# Los logs se guardan en: logs/analyzer_YYYYMMDD_HHMMSS.log
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
export WHATSAPP_ANALYZER_CONFIG_DIR="/etc/whatsapp-analyzer"
export WHATSAPP_ANALYZER_CACHE_DIR="/var/cache/whatsapp-analyzer"
export WHATSAPP_ANALYZER_LOG_LEVEL="INFO"
export WHATSAPP_ANALYZER_MAX_WORKERS="8"
```

### Integración con CI/CD
```yaml
# GitHub Actions example
name: WhatsApp Analysis
on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: python setup.py --install-type full
      - name: Run analysis
        run: |
          python content_analyzer.py /data/chats \
            --config production_config.json \
            --generate-reports \
            --upload-results
```

### Docker Support
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python setup.py --install-type full --no-optional

ENTRYPOINT ["python", "content_analyzer.py"]
```

## 📚 API Reference

### Python API
```python
from content_analyzer import AdvancedContentAnalyzer, AnalysisConfig

# Configuración programática
config = AnalysisConfig(
    keywords=["importante", "urgente"],
    sentiment_analysis=True,
    language_detection=True,
    generate_excel=True
)

# Crear analizador
analyzer = AdvancedContentAnalyzer(config=config)

# Ejecutar análisis
analyzer.analyze_directory("/ruta/a/chats")

# Generar reportes
analyzer.generate_excel_report("reportes/")
analyzer.generate_pdf_report("reportes/")
analyzer.start_web_dashboard()
```

### REST API (opcional)
```python
# Iniciar servidor API
from api_server import create_api_server

app = create_api_server(analyzer)
app.run(host='0.0.0.0', port=8080)
```

```bash
# Endpoints disponibles
GET /api/status
POST /api/analyze
GET /api/results
GET /api/reports
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Desarrollo Local
```bash
# Configurar entorno de desarrollo
git clone https://github.com/tu-usuario/whatsapp-analyzer-pro.git
cd whatsapp-analyzer-pro
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements-dev.txt
python setup.py --install-type full

# Ejecutar tests
pytest tests/ -v

# Formatear código
black .
isort .
```

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👥 Créditos

- Desarrollado por: [Tu Nombre]
- Contribuidores: [Lista de contribuidores]
- Inspirado en: WhatsApp Chat Exporter original
- Librerías utilizadas: BeautifulSoup, Pandas, TextBlob, Flask, Plotly, ReportLab

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/whatsapp-analyzer-pro/issues)
- **Documentación**: [Wiki](https://github.com/tu-usuario/whatsapp-analyzer-pro/wiki)
- **Email**: support@whatsapp-analyzer-pro.com
- **Discord**: [Servidor de Discord](https://discord.gg/tu-servidor)

## 🗺️ Roadmap

### Versión 2.1 (Próximamente)
- [ ] Integración con bases de datos (PostgreSQL, MongoDB)
- [ ] API REST completa
- [ ] Soporte para Telegram y Signal
- [ ] Machine Learning avanzado para clasificación
- [ ] Exportación a Power BI y Tableau

### Versión 2.2
- [ ] Análisis de redes sociales
- [ ] Detección de emociones avanzada
- [ ] Soporte multi-idioma completo
- [ ] Clustering automático de conversaciones
- [ ] Integración con herramientas forenses

---

**⭐ Si este proyecto te ha sido útil, por favor considera darle una estrella en GitHub!**

**📢 Comparte con otros que puedan beneficiarse de esta herramienta profesional.**