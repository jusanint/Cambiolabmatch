#!/usr/bin/env python3
"""
Sistema de Matching Ideas-Convocatorias
========================================

Este script ejecuta el análisis de matching entre ideas de proyectos
y convocatorias de financiamiento, generando reportes Excel con
puntajes y recomendaciones.

Uso:
    python main.py --ideas data/ideas.csv --convocatorias data/convocatorias.csv
    python main.py --help
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_loader import cargar_y_validar_datos
from src.scoring import calcular_match, ResultadoMatch
from src.excel_generator import generar_excel
from src.nlp_matcher import crear_funcion_similitud, EMBEDDINGS_DISPONIBLES


def ejecutar_matching(
    ideas: List[dict],
    convocatorias: List[dict],
    usar_embeddings: bool = True
) -> List[ResultadoMatch]:
    """
    Ejecuta el matching entre todas las ideas y convocatorias.

    Args:
        ideas: Lista de diccionarios con datos de ideas
        convocatorias: Lista de diccionarios con datos de convocatorias
        usar_embeddings: Si usar embeddings para matching semántico

    Returns:
        Lista de ResultadoMatch
    """
    resultados = []

    # Intentar cargar función de similitud con embeddings
    similarity_func = None
    if usar_embeddings and EMBEDDINGS_DISPONIBLES:
        print("Inicializando modelo de embeddings para matching semántico...")
        similarity_func = crear_funcion_similitud()
        if similarity_func:
            print("Modelo de embeddings cargado correctamente")
        else:
            print("No se pudo cargar el modelo de embeddings. Usando matching por keywords.")
    else:
        print("Matching por keywords (embeddings no disponibles o deshabilitados)")

    total_cruces = len(ideas) * len(convocatorias)
    print(f"\nAnalizando {total_cruces} cruces posibles...")

    cruces_procesados = 0
    cruces_excluidos = 0

    for idea in ideas:
        for convocatoria in convocatorias:
            resultado = calcular_match(idea, convocatoria, similarity_func)

            if resultado is None:
                cruces_excluidos += 1  # Convocatoria vencida
            else:
                resultados.append(resultado)

            cruces_procesados += 1

            # Mostrar progreso cada 50 cruces
            if cruces_procesados % 50 == 0:
                print(f"  Procesados: {cruces_procesados}/{total_cruces}")

    print(f"\nAnálisis completado:")
    print(f"  - Cruces válidos: {len(resultados)}")
    print(f"  - Excluidos (convocatorias vencidas): {cruces_excluidos}")

    return resultados


def generar_estadisticas(resultados: List[ResultadoMatch]) -> dict:
    """Genera estadísticas del análisis."""
    if not resultados:
        return {}

    elegibles = [r for r in resultados if r.es_elegible]
    no_elegibles = [r for r in resultados if not r.es_elegible]

    puntajes = [r.puntaje_total for r in elegibles]

    stats = {
        'total_cruces': len(resultados),
        'elegibles': len(elegibles),
        'no_elegibles': len(no_elegibles),
        'urgentes': sum(1 for r in resultados if r.es_urgente),
        'alto_potencial': sum(1 for r in elegibles if r.puntaje_total >= 70),
        'medio_potencial': sum(1 for r in elegibles if 40 <= r.puntaje_total < 70),
        'bajo_potencial': sum(1 for r in elegibles if r.puntaje_total < 40),
        'puntaje_promedio': sum(puntajes) / len(puntajes) if puntajes else 0,
        'puntaje_max': max(puntajes) if puntajes else 0,
        'puntaje_min': min(puntajes) if puntajes else 0,
    }

    return stats


def imprimir_resumen(resultados: List[ResultadoMatch], stats: dict):
    """Imprime un resumen del análisis en consola."""
    print("\n" + "=" * 60)
    print("RESUMEN DEL ANÁLISIS")
    print("=" * 60)

    print(f"\nEstadísticas generales:")
    print(f"  Total de cruces analizados: {stats['total_cruces']}")
    print(f"  Cruces elegibles: {stats['elegibles']}")
    print(f"  Cruces no elegibles: {stats['no_elegibles']}")
    print(f"  Convocatorias urgentes: {stats['urgentes']}")

    print(f"\nDistribución por potencial:")
    print(f"  Alto potencial (≥70): {stats['alto_potencial']}")
    print(f"  Potencial medio (40-69): {stats['medio_potencial']}")
    print(f"  Bajo potencial (<40): {stats['bajo_potencial']}")

    print(f"\nPuntajes:")
    print(f"  Promedio: {stats['puntaje_promedio']:.1f}")
    print(f"  Máximo: {stats['puntaje_max']}")
    print(f"  Mínimo: {stats['puntaje_min']}")

    # Top 5 mejores matches
    top_5 = sorted(
        [r for r in resultados if r.es_elegible],
        key=lambda x: x.puntaje_total,
        reverse=True
    )[:5]

    if top_5:
        print(f"\nTop 5 mejores matches:")
        for i, r in enumerate(top_5, 1):
            urgente = " [URGENTE]" if r.es_urgente else ""
            print(f"  {i}. {r.nombre_idea[:30]}... + {r.nombre_convocatoria[:30]}...")
            print(f"     Puntaje: {r.puntaje_total}/100{urgente}")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Sistema de Matching Ideas-Convocatorias',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py --ideas data/ideas.csv --convocatorias data/convocatorias.csv
  python main.py -i data/ideas.xlsx -c data/convocatorias.xlsx -o output/reporte.xlsx
  python main.py --ideas data/ideas.csv --convocatorias data/convocatorias.csv --no-embeddings
        """
    )

    parser.add_argument(
        '-i', '--ideas',
        default='data/ideas.csv',
        help='Ruta al archivo de IDEAS (CSV o Excel)'
    )

    parser.add_argument(
        '-c', '--convocatorias',
        default='data/convocatorias.csv',
        help='Ruta al archivo de CONVOCATORIAS (CSV o Excel)'
    )

    parser.add_argument(
        '-o', '--output',
        default='output/resultados_matching.xlsx',
        help='Ruta del archivo Excel de salida'
    )

    parser.add_argument(
        '--hoja-ideas',
        default=None,
        help='Nombre de la hoja para Excel de ideas'
    )

    parser.add_argument(
        '--hoja-convocatorias',
        default=None,
        help='Nombre de la hoja para Excel de convocatorias'
    )

    parser.add_argument(
        '--no-embeddings',
        action='store_true',
        help='Desactivar uso de embeddings (más rápido pero menos preciso)'
    )

    parser.add_argument(
        '--con-evidencias',
        action='store_true',
        help='Incluir columnas de evidencia detallada en el Excel'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("SISTEMA DE MATCHING IDEAS-CONVOCATORIAS")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Verificar archivos de entrada
    if not Path(args.ideas).exists():
        print(f"Error: No se encontró el archivo de ideas: {args.ideas}")
        sys.exit(1)

    if not Path(args.convocatorias).exists():
        print(f"Error: No se encontró el archivo de convocatorias: {args.convocatorias}")
        sys.exit(1)

    # Cargar datos
    print("Cargando datos...")
    try:
        ideas, convocatorias, warnings = cargar_y_validar_datos(
            args.ideas,
            args.convocatorias,
            args.hoja_ideas,
            args.hoja_convocatorias
        )
    except Exception as e:
        print(f"Error cargando datos: {e}")
        sys.exit(1)

    if not ideas:
        print("Error: No se encontraron ideas válidas")
        sys.exit(1)

    if not convocatorias:
        print("Error: No se encontraron convocatorias válidas")
        sys.exit(1)

    # Ejecutar matching
    resultados = ejecutar_matching(
        ideas,
        convocatorias,
        usar_embeddings=not args.no_embeddings
    )

    if not resultados:
        print("No se generaron resultados. Verifique que las convocatorias no estén vencidas.")
        sys.exit(1)

    # Generar estadísticas
    stats = generar_estadisticas(resultados)

    # Imprimir resumen
    imprimir_resumen(resultados, stats)

    # Generar Excel
    print(f"\nGenerando archivo Excel: {args.output}")
    try:
        ruta_salida = generar_excel(
            resultados,
            args.output,
            incluir_evidencias=args.con_evidencias
        )
        print(f"Archivo generado exitosamente: {ruta_salida}")
    except Exception as e:
        print(f"Error generando Excel: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)


if __name__ == '__main__':
    main()
