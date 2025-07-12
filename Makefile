# 🚀 WhatsApp Chat Exporter - Makefile Optimizado
.PHONY: help install test test-cov clean lint format feature finish status

# Variables
PYTHON := poetry run python
PYTEST := poetry run pytest

# Colores para output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

help: ## 📖 Mostrar ayuda
	@echo -e "$(CYAN)🚀 WhatsApp Chat Exporter - Comandos Disponibles$(NC)"
	@echo -e "$(CYAN)================================================$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## 📦 Instalar todas las dependencias
	@echo -e "$(CYAN)📦 Instalando dependencias...$(NC)"
	poetry install --extras="all"
	@echo -e "$(GREEN)✅ Dependencias instaladas$(NC)"

test: ## 🧪 Correr todos los tests
	@echo -e "$(CYAN)🧪 Ejecutando tests...$(NC)"
	$(PYTEST) Whatsapp_Chat_Exporter/ --tb=short -v
	@echo -e "$(GREEN)✅ Tests completados$(NC)"

test-cov: ## 📊 Tests con cobertura completa
	@echo -e "$(CYAN)📊 Tests con cobertura...$(NC)"
	$(PYTEST) Whatsapp_Chat_Exporter/ \
		--tb=short \
		--cov=Whatsapp_Chat_Exporter \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-fail-under=50
	@echo -e "$(GREEN)✅ Cobertura generada en htmlcov/$(NC)"

lint: ## 🔍 Linting con ruff
	@echo -e "$(CYAN)🔍 Ejecutando linting...$(NC)"
	poetry run ruff check .
	@echo -e "$(GREEN)✅ Linting completado$(NC)"

format: ## ✨ Formatear código
	@echo -e "$(CYAN)✨ Formateando código...$(NC)"
	poetry run black .
	poetry run ruff check --fix .
	@echo -e "$(GREEN)✅ Código formateado$(NC)"

clean: ## 🧹 Limpiar archivos temporales
	@echo -e "$(CYAN)🧹 Limpiando archivos temporales...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage 2>/dev/null || true
	@echo -e "$(GREEN)✅ Limpieza completada$(NC)"

quick-commit: ## 💨 Commit rápido con mensaje
	@read -p "Mensaje del commit: " msg; \
	git add -A && \
	git commit -m "$$msg" && \
	echo -e "$(GREEN)✅ Commit realizado: $$msg$(NC)"

push: ## 📤 Push a rama actual
	@branch=$$(git branch --show-current); \
	git push origin $$branch && \
	echo -e "$(GREEN)✅ Push completado en $$branch$(NC)"

feature: ## 🌿 Crear nueva feature branch
	@read -p "Nombre de la feature: " name; \
	git checkout main && \
	git pull origin main && \
	git checkout -b feature/$$name && \
	echo -e "$(GREEN)✅ Feature branch creada: feature/$$name$(NC)"

status: ## 📊 Status detallado del repositorio
	@echo -e "$(CYAN)📊 Estado del Repositorio$(NC)"
	@echo -e "$(CYAN)========================$(NC)"
	@echo -e "🌿 Rama actual: $(GREEN)$$(git branch --show-current)$(NC)"
	@echo -e "\n📁 Archivos modificados:"
	@git status --porcelain | head -10 || echo "  Ninguno"
	@echo -e "\n🕐 Último commit:"
	@git log --oneline -1
	@echo -e "\n🌿 Ramas locales:"
	@git branch

dev-setup: ## 🔧 Configuración inicial de desarrollo
	@echo -e "$(CYAN)🔧 Configurando entorno de desarrollo...$(NC)"
	@make install
	@make format
	@make test
	@echo -e "$(GREEN)✅ Entorno configurado y validado$(NC)"

ci: ## 🤖 Pipeline completo de CI
	@echo -e "$(CYAN)🤖 Ejecutando pipeline de CI...$(NC)"
	@make format
	@make lint
	@make test-cov
	@echo -e "$(GREEN)✅ Pipeline de CI completado$(NC)"

# Workflow avanzado
workflow-feature: ## 🚀 Workflow completo para nueva feature
	@.dev/workflow.sh feature $(filter-out $@,$(MAKECMDGOALS))

workflow-finish: ## 🏁 Finalizar feature actual
	@.dev/workflow.sh finish $(filter-out $@,$(MAKECMDGOALS))

# Capturar argumentos adicionales
%:
	@:
