# 🚀 Workflow Optimizado - WhatsApp Chat Exporter

## 🎯 Filosofía del Workflow

- **Simplicidad**: Máximo 2-3 ramas activas
- **Velocidad**: Comandos de 1-2 palabras
- **Limpieza**: Auto-eliminación de ramas
- **Calidad**: Tests automáticos antes de merge

## ⚡ Comandos Súper Rápidos

### **Desarrollo Diario**

```bash
# Crear nueva feature
make feature
# o
./.dev/workflow.sh feature nueva-funcionalidad

# Commit rápido
make quick-commit
# o
git quick "mensaje del commit"

# Push actual branch
make push
# o
git push
```

### **Workflow Completo de Feature**

```bash
# 1. Crear feature
./.dev/workflow.sh feature mi-nueva-funcionalidad

# 2. Desarrollar (repetir según necesario)
git quick "agregada funcionalidad X"
git quick "tests para funcionalidad X"
git quick "documentación actualizada"

# 3. Finalizar (auto-test + merge + limpieza)
./.dev/workflow.sh finish feature/mi-nueva-funcionalidad
```

### **Testing y Calidad**

```bash
# Tests rápidos
make test

# Tests con cobertura completa
make test-cov

# Formatear código
make format

# Pipeline completo de CI
make ci
```

### **Mantenimiento**

```bash
# Limpiar repositorio
make clean
./.dev/workflow.sh clean

# Sincronizar con proyecto original
./.dev/workflow.sh sync

# Status mejorado
make status
./.dev/workflow.sh status
```

## 🛠️ Git Aliases Configurados

```bash
git co       # checkout
git br       # branch
git ci       # commit
git st       # status
git quick    # add + commit + push
git feature  # crear feature branch
git finish   # merge + limpiar rama
```

## 📊 Estructura del Workflow

```
main (siempre estable)
  ├── feature/nueva-func-1  ← trabajas aquí
  ├── feature/nueva-func-2  ← o aquí
  └── hotfix/bug-critico    ← solo para bugs urgentes
```

## 🔄 Flujo Típico de Desarrollo

1. **Sincronizar**: `git pull origin main`
2. **Feature**: `./.dev/workflow.sh feature nombre`
3. **Desarrollar**: `git quick "mensaje"` (repetir)
4. **Finalizar**: `./.dev/workflow.sh finish feature/nombre`
5. **Limpiar**: Se hace automáticamente

## 🚨 Reglas de Oro

- ✅ **NUNCA** trabajar directamente en `main`
- ✅ **SIEMPRE** crear rama para cada feature
- ✅ **ELIMINAR** ramas inmediatamente después del merge
- ✅ **CORRER** tests antes de cada merge
- ✅ **MANTENER** máximo 3 ramas activas

## 🎛️ Configuración Automática

### GitHub Auto-Delete (Recomendado)
1. Ve a Settings > General > Pull requests
2. Activa "Automatically delete head branches"

### Pre-commit Hooks
```bash
# Instalar
poetry run pre-commit install

# Configurar para skip en emergencias
git commit -m "mensaje" --no-verify
```

## 📈 Métricas de Eficiencia

- **Tiempo crear feature**: 5 segundos
- **Tiempo commit+push**: 3 segundos
- **Tiempo finalizar feature**: 30 segundos
- **Ramas activas**: 1-3 máximo
- **Tests automáticos**: 100% coverage

## 🚀 Pro Tips

1. **Usar aliases siempre**: `git quick` en lugar de `git add && git commit && git push`
2. **Commits frecuentes**: Mejor 10 commits pequeños que 1 grande
3. **Nombres descriptivos**: `feature/fix-ios-export` no `feature/fix`
4. **Tests primero**: Desarrolla con TDD cuando sea posible
5. **Limpieza continua**: Elimina ramas semanalmente

## 🆘 Comandos de Emergencia

```bash
# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Limpiar todo y volver a main
git checkout main && git reset --hard origin/main

# Ver qué cambiarías antes de merge
git diff main..feature/mi-rama

# Buscar en commits
git log --grep="palabra-clave"
```

---

**🎯 Objetivo**: Máxima productividad con mínima fricción. ¡A desarrollar eficientemente! 🚀
