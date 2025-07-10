"""
Web Dashboard for WhatsApp Chat Analyzer
Provides interactive visualization and real-time analysis results
"""

from flask import Flask, render_template, jsonify, request, send_file
import json
from pathlib import Path
import threading
import webbrowser
from datetime import datetime
import plotly.graph_objs as go
import plotly.utils

def create_web_dashboard(analyzer_instance):
    """Create and configure Flask web dashboard."""
    app = Flask(__name__)
    app.secret_key = 'whatsapp_analyzer_secret_key_2024'
    
    @app.route('/')
    def dashboard_home():
        """Main dashboard page."""
        return render_template('dashboard.html')
    
    @app.route('/api/analysis_summary')
    def get_analysis_summary():
        """API endpoint for analysis summary."""
        try:
            summary = analyzer_instance.generate_summary_report()
            return jsonify(summary)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/file_details/<file_name>')
    def get_file_details(file_name):
        """API endpoint for detailed file analysis."""
        try:
            for result in analyzer_instance.results:
                if hasattr(result, 'file_name') and result.file_name == file_name:
                    return jsonify({
                        'file_name': result.file_name,
                        'total_messages': result.total_messages,
                        'total_words': result.total_words,
                        'keyword_matches': result.keyword_matches,
                        'sentiment_score': getattr(result, 'sentiment_score', None),
                        'language_detected': getattr(result, 'language_detected', None),
                        'participants': getattr(result, 'participants', []),
                        'topics_detected': getattr(result, 'topics_detected', []),
                        'processing_time': getattr(result, 'processing_time', 0),
                        'file_size_kb': getattr(result, 'file_size_kb', 0)
                    })
            return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/keywords')
    def get_keywords_chart():
        """Generate keywords frequency chart."""
        try:
            # Aggregate keyword data
            all_keywords = {}
            for result in analyzer_instance.results:
                for keyword, count in result.keyword_matches.items():
                    all_keywords[keyword] = all_keywords.get(keyword, 0) + count
            
            # Create chart
            if all_keywords:
                keywords = list(all_keywords.keys())[:10]  # Top 10
                counts = [all_keywords[k] for k in keywords]
                
                fig = go.Figure(data=[
                    go.Bar(x=keywords, y=counts, name='Keyword Frequency')
                ])
                fig.update_layout(
                    title='Top Keywords Frequency',
                    xaxis_title='Keywords',
                    yaxis_title='Frequency'
                )
                
                return jsonify(plotly.utils.PlotlyJSONEncoder().encode(fig))
            else:
                return jsonify({'error': 'No keyword data available'})
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/sentiment')
    def get_sentiment_chart():
        """Generate sentiment analysis chart."""
        try:
            sentiments = []
            files = []
            
            for result in analyzer_instance.results:
                if hasattr(result, 'sentiment_score') and result.sentiment_score is not None:
                    sentiments.append(result.sentiment_score)
                    files.append(result.file_name[:20] + '...' if len(result.file_name) > 20 else result.file_name)
            
            if sentiments:
                fig = go.Figure(data=[
                    go.Scatter(x=files, y=sentiments, mode='markers+lines', name='Sentiment Score')
                ])
                fig.update_layout(
                    title='Sentiment Analysis by Conversation',
                    xaxis_title='Conversations',
                    yaxis_title='Sentiment Score (-1 to 1)',
                    yaxis=dict(range=[-1, 1])
                )
                
                return jsonify(plotly.utils.PlotlyJSONEncoder().encode(fig))
            else:
                return jsonify({'error': 'No sentiment data available'})
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/progress')
    def get_progress():
        """Get current analysis progress."""
        try:
            if hasattr(analyzer_instance, 'current_file_count') and hasattr(analyzer_instance, 'total_file_count'):
                progress = {
                    'current': analyzer_instance.current_file_count,
                    'total': analyzer_instance.total_file_count,
                    'percentage': (analyzer_instance.current_file_count / analyzer_instance.total_file_count * 100) if analyzer_instance.total_file_count > 0 else 0
                }
                return jsonify(progress)
            else:
                return jsonify({'current': 0, 'total': 0, 'percentage': 0})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

def create_dashboard_template():
    """Create HTML template for dashboard."""
    template_dir = Path("templates")
    template_dir.mkdir(exist_ok=True)
    
    dashboard_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 WhatsApp Chat Analyzer Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
        }
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }
        .refresh-btn {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            z-index: 1000;
        }
        .progress-container {
            margin-bottom: 1rem;
        }
    </style>
</head>
<body class="bg-light">
    <div class="dashboard-header">
        <div class="container">
            <div class="row">
                <div class="col-md-8">
                    <h1>📊 WhatsApp Chat Analyzer</h1>
                    <p class="lead">Análisis avanzado de conversaciones en tiempo real</p>
                </div>
                <div class="col-md-4 text-end">
                    <div class="progress-container">
                        <div class="progress">
                            <div class="progress-bar" id="analysisProgress" role="progressbar" style="width: 0%"></div>
                        </div>
                        <small id="progressText" class="text-light">Cargando...</small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Summary Statistics -->
        <div class="row" id="statsContainer">
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-primary" id="totalFiles">-</h3>
                    <p class="mb-0">Archivos Analizados</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-success" id="totalMessages">-</h3>
                    <p class="mb-0">Mensajes Totales</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-warning" id="totalWords">-</h3>
                    <p class="mb-0">Palabras Totales</p>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stat-card text-center">
                    <h3 class="text-info" id="matchedFiles">-</h3>
                    <p class="mb-0">Con Coincidencias</p>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    <h5>📈 Frecuencia de Palabras Clave</h5>
                    <div id="keywordsChart"></div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    <h5>😊 Análisis de Sentimientos</h5>
                    <div id="sentimentChart"></div>
                </div>
            </div>
        </div>

        <!-- File Details -->
        <div class="row">
            <div class="col-12">
                <div class="chart-container">
                    <h5>📁 Detalles de Archivos</h5>
                    <div class="table-responsive">
                        <table class="table table-striped" id="filesTable">
                            <thead>
                                <tr>
                                    <th>Archivo</th>
                                    <th>Mensajes</th>
                                    <th>Palabras</th>
                                    <th>Coincidencias</th>
                                    <th>Sentimiento</th>
                                    <th>Idioma</th>
                                    <th>Tamaño</th>
                                </tr>
                            </thead>
                            <tbody>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Refresh Button -->
    <button class="btn btn-primary refresh-btn btn-floating" onclick="refreshDashboard()">
        🔄 Actualizar
    </button>

    <script>
        let refreshInterval;

        function formatNumber(num) {
            return num.toLocaleString('es-ES');
        }

        function refreshDashboard() {
            // Update progress
            $.get('/api/progress', function(data) {
                if (data.total > 0) {
                    $('#analysisProgress').css('width', data.percentage + '%');
                    $('#progressText').text(`${data.current}/${data.total} archivos (${data.percentage.toFixed(1)}%)`);
                }
            });

            // Update summary
            $.get('/api/analysis_summary', function(data) {
                $('#totalFiles').text(formatNumber(data.total_files_analyzed || 0));
                $('#totalMessages').text(formatNumber(data.total_messages || 0));
                $('#totalWords').text(formatNumber(data.total_words || 0));
                $('#matchedFiles').text(formatNumber(data.files_with_keyword_matches || 0));

                // Update files table
                updateFilesTable(data.conversation_breakdown || []);
            });

            // Update charts
            $.get('/api/charts/keywords', function(data) {
                if (!data.error) {
                    Plotly.newPlot('keywordsChart', JSON.parse(data));
                }
            });

            $.get('/api/charts/sentiment', function(data) {
                if (!data.error) {
                    Plotly.newPlot('sentimentChart', JSON.parse(data));
                }
            });
        }

        function updateFilesTable(conversations) {
            const tbody = $('#filesTable tbody');
            tbody.empty();

            conversations.forEach(function(conv) {
                const sentimentIcon = conv.sentiment_score !== null ? 
                    (conv.sentiment_score > 0.1 ? '😊' : conv.sentiment_score < -0.1 ? '😞' : '😐') : '-';
                
                const row = `
                    <tr>
                        <td><strong>${conv.file_name}</strong></td>
                        <td>${formatNumber(conv.total_messages)}</td>
                        <td>${formatNumber(conv.total_words)}</td>
                        <td><span class="badge bg-primary">${conv.keyword_count}</span></td>
                        <td>${sentimentIcon}</td>
                        <td>${conv.language_detected || '-'}</td>
                        <td>${conv.file_size_kb ? conv.file_size_kb.toFixed(1) + ' KB' : '-'}</td>
                    </tr>
                `;
                tbody.append(row);
            });
        }

        // Initialize dashboard
        $(document).ready(function() {
            refreshDashboard();
            
            // Auto-refresh every 5 seconds
            refreshInterval = setInterval(refreshDashboard, 5000);
        });

        // Stop auto-refresh when page is hidden
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                clearInterval(refreshInterval);
            } else {
                refreshInterval = setInterval(refreshDashboard, 5000);
            }
        });
    </script>
</body>
</html>'''

    template_file = template_dir / "dashboard.html"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    return template_file

def start_dashboard_server(analyzer_instance, port=5000, auto_open=True):
    """Start the web dashboard server."""
    try:
        # Create template
        create_dashboard_template()
        
        # Create Flask app
        app = create_web_dashboard(analyzer_instance)
        
        # Start server in separate thread
        def run_server():
            app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Open browser
        if auto_open:
            dashboard_url = f"http://127.0.0.1:{port}"
            threading.Timer(1.0, lambda: webbrowser.open(dashboard_url)).start()
            print(f"🚀 Dashboard iniciado en: {dashboard_url}")
        
        return server_thread
        
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        return None