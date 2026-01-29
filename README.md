# Sistema de Matching Ideas-Convocatorias

Sistema de análisis y matching entre ideas de proyectos y convocatorias de financiamiento, con generación de reportes Excel.

## Descripción

Este sistema evalúa la compatibilidad entre ideas de proyectos y convocatorias de financiamiento utilizando múltiples criterios:

| Criterio | Máx. Puntos | Descripción |
|----------|-------------|-------------|
| Propósito/Temática | 35 | Similitud semántica entre descripción y tags |
| Tipo de Actividad | 35 | Compatibilidad entre clasificación de idea y requisitos |
| Elegibilidad | 15 | Correspondencia de tipo de proponente (regla dura) |
| Valor vs Monto | 10 | Cobertura del financiamiento sobre valor estimado |
| Región/Alcance | 5 | Compatibilidad geográfica |
| **Total** | **100** | |

## Estructura del Proyecto

```
Cambiolabmatch/
├── data/
│   ├── ideas.csv              # Archivo de IDEAS (ejemplo incluido)
│   └── convocatorias.csv      # Archivo de CONVOCATORIAS (ejemplo incluido)
├── output/
│   ├── consolidado.csv        # Tabla consolidada
│   ├── por_cliente/           # Tablas segmentadas por cliente
│   └── resultados_matching.xlsx  # Reporte Excel completo
├── src/
│   ├── config.py              # Configuración de puntajes y bandas
│   ├── data_loader.py         # Carga y validación de datos
│   ├── scoring.py             # Lógica de puntuación
│   ├── nlp_matcher.py         # Matching semántico con embeddings
│   └── excel_generator.py     # Generación de reportes Excel
├── main.py                    # Script principal (con dependencias)
├── run_analysis.py            # Script simplificado (sin dependencias)
└── requirements.txt           # Dependencias Python
```

## Instalación

### Opción 1: Ejecución rápida (sin dependencias pesadas)

```bash
# Solo Python estándar requerido
python run_analysis.py
```

### Opción 2: Instalación completa (con embeddings y Excel)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

## Uso

### Ejecución básica

```bash
# Con archivos por defecto (data/ideas.csv y data/convocatorias.csv)
python run_analysis.py

# O con el script completo
python main.py
```

### Opciones avanzadas (main.py)

```bash
# Especificar archivos de entrada
python main.py --ideas mi_archivo_ideas.csv --convocatorias mis_convocatorias.xlsx

# Especificar archivo de salida
python main.py -o reporte/mi_reporte.xlsx

# Incluir evidencias detalladas
python main.py --con-evidencias

# Desactivar embeddings (más rápido)
python main.py --no-embeddings
```

## Formato de Archivos de Entrada

### IDEAS (archivo A)

| Columna | Descripción | Requerida |
|---------|-------------|-----------|
| id_idea | Identificador único | Sí |
| nombre | Nombre de la idea | Sí |
| descripcion | Descripción detallada | No |
| tags | Etiquetas/palabras clave (incluir ODS) | No |
| tipologia_cliente | Tipo de proponente | Sí |
| valor_estimado | Presupuesto estimado | Sí |
| moneda | Moneda (USD por defecto) | No |
| clasificacion_idea | Tipo de proyecto | No |
| region | Región/ubicación | No |
| ambito | Alcance (Local/Regional/Nacional/Internacional) | No |

### CONVOCATORIAS (archivo B)

| Columna | Descripción | Requerida |
|---------|-------------|-----------|
| id_convocatoria | Identificador único | Sí |
| nombre | Nombre de la convocatoria | Sí |
| proposito | Objetivo/descripción | No |
| tags | Etiquetas (incluir ODS) | No |
| quienes_pueden_participar | Tipos de proponentes elegibles | Sí |
| monto_maximo | Financiamiento máximo | Sí |
| moneda | Moneda (USD por defecto) | No |
| region | Cobertura geográfica | No |
| ambito | Alcance | No |
| fecha_limite | Fecha límite (YYYY-MM-DD) | No |
| notas_adicionales | Requisitos especiales | No |

## Formato de Salida

Las tablas generadas incluyen las siguientes columnas:

- `id_idea` - Identificador de la idea
- `nombre_idea` - Nombre de la idea
- `id_convocatoria` - Identificador de la convocatoria
- `nombre_convocatoria` - Nombre de la convocatoria
- `puntaje_proposito` - Puntos por temática (0-35)
- `puntaje_tipo_actividad` - Puntos por tipo de actividad (0-35)
- `puntaje_elegibilidad` - Puntos por elegibilidad (0-15) o "No elegible"
- `puntaje_valor_vs_monto` - Puntos por cobertura financiera (0-10)
- `puntaje_region` - Puntos por región (0-5)
- `puntaje_total` - Suma total (máx 100)
- `observacion_cualitativa` - Justificación de la puntuación
- `acciones_sugeridas` - Recomendaciones de mejora

## Reglas de Mapeo

### Bandas de Porcentaje a Nivel

| Rango % | Nivel | Descripción |
|---------|-------|-------------|
| 0-19% | 1 | Bajo |
| 20-49% | 2 | Medio-bajo |
| 50-70% | 3 | Medio |
| 71-90% | 4 | Medio-alto |
| >90% | 5 | Total |

### Reglas Especiales

1. **Elegibilidad**: Si el tipo de proponente no está permitido, se marca "No elegible" y el puntaje total es 0.

2. **Fecha límite**:
   - Convocatorias vencidas se excluyen del análisis
   - Si faltan ≤30 días, se marca como "URGENTE"

3. **ODS**: Los Objetivos de Desarrollo Sostenible mencionados en tags otorgan bonus en el matching temático.

4. **Notas adicionales**: Se consideran para ajustar valoraciones y generar acciones sugeridas.

## Ejemplos de Observaciones Generadas

- "URGENTE: 15 días restantes. Alta compatibilidad. Fortalezas: temática alineada, actividad compatible"
- "NO ELEGIBLE para esta convocatoria"
- "Compatibilidad media. Requiere contrapartida"

## Ejemplos de Acciones Sugeridas

- "PRIORIZAR postulación; Preparar contrapartida; Destacar componente rural"
- "Ajustar presupuesto; Formar alianza/consorcio"
- "Buscar socio elegible"
