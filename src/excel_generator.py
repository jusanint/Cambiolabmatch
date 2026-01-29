"""
Módulo para generar archivos Excel con los resultados del matching.
Genera tablas segmentadas por cliente y tabla consolidada.
"""

import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

from .scoring import ResultadoMatch


def resultado_a_dict(resultado: ResultadoMatch) -> Dict[str, Any]:
    """Convierte un ResultadoMatch a diccionario para DataFrame."""
    return {
        'id_idea': resultado.id_idea,
        'nombre_idea': resultado.nombre_idea,
        'id_convocatoria': resultado.id_convocatoria,
        'nombre_convocatoria': resultado.nombre_convocatoria,
        'puntaje_proposito': resultado.puntaje_proposito,
        'puntaje_tipo_actividad': resultado.puntaje_tipo_actividad,
        'puntaje_elegibilidad': resultado.puntaje_elegibilidad if resultado.es_elegible else "No elegible",
        'puntaje_valor_vs_monto': resultado.puntaje_valor_vs_monto,
        'puntaje_region': resultado.puntaje_region,
        'puntaje_total': resultado.puntaje_total,
        'observacion_cualitativa': resultado.observacion_cualitativa,
        'acciones_sugeridas': resultado.acciones_sugeridas,
    }


def resultado_a_dict_detallado(resultado: ResultadoMatch) -> Dict[str, Any]:
    """Convierte un ResultadoMatch a diccionario con evidencias detalladas."""
    base = resultado_a_dict(resultado)
    base.update({
        'tipologia_cliente': resultado.tipologia_cliente,
        'es_urgente': "Sí" if resultado.es_urgente else "No",
        'dias_restantes': resultado.dias_restantes if resultado.dias_restantes else "N/A",
        'evidencia_proposito': resultado.evidencia_proposito,
        'evidencia_actividad': resultado.evidencia_actividad,
        'evidencia_elegibilidad': resultado.evidencia_elegibilidad,
        'evidencia_valor': resultado.evidencia_valor,
        'evidencia_region': resultado.evidencia_region,
    })
    return base


def aplicar_formato_excel(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame):
    """Aplica formato profesional a la hoja de Excel."""
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # Formatos
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#2E7D32',
        'font_color': 'white',
        'border': 1,
        'text_wrap': True,
        'valign': 'vcenter',
        'align': 'center'
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'text_wrap': True
    })

    number_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'align': 'center',
        'num_format': '0'
    })

    urgente_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'text_wrap': True,
        'bg_color': '#FFCDD2'
    })

    alto_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'align': 'center',
        'bg_color': '#C8E6C9',
        'num_format': '0'
    })

    bajo_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'align': 'center',
        'bg_color': '#FFECB3',
        'num_format': '0'
    })

    no_elegible_format = workbook.add_format({
        'border': 1,
        'valign': 'vcenter',
        'align': 'center',
        'bg_color': '#FFCDD2',
        'font_color': '#B71C1C'
    })

    # Aplicar formato a encabezados
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Definir anchos de columna
    anchos = {
        'id_idea': 12,
        'nombre_idea': 35,
        'id_convocatoria': 15,
        'nombre_convocatoria': 40,
        'puntaje_proposito': 12,
        'puntaje_tipo_actividad': 14,
        'puntaje_elegibilidad': 14,
        'puntaje_valor_vs_monto': 14,
        'puntaje_region': 12,
        'puntaje_total': 12,
        'observacion_cualitativa': 50,
        'acciones_sugeridas': 50,
        'tipologia_cliente': 18,
        'es_urgente': 10,
        'dias_restantes': 12,
        'evidencia_proposito': 40,
        'evidencia_actividad': 40,
        'evidencia_elegibilidad': 40,
        'evidencia_valor': 35,
        'evidencia_region': 35,
    }

    for col_num, col_name in enumerate(df.columns):
        ancho = anchos.get(col_name, 15)
        worksheet.set_column(col_num, col_num, ancho)

    # Aplicar formato condicional a celdas de datos
    for row_num in range(len(df)):
        for col_num, col_name in enumerate(df.columns):
            valor = df.iloc[row_num, col_num]

            # Determinar formato según columna y valor
            if col_name == 'puntaje_elegibilidad' and valor == "No elegible":
                fmt = no_elegible_format
            elif col_name == 'puntaje_total':
                if isinstance(valor, (int, float)):
                    if valor >= 70:
                        fmt = alto_format
                    elif valor <= 30:
                        fmt = bajo_format
                    else:
                        fmt = number_format
                else:
                    fmt = cell_format
            elif col_name in ['puntaje_proposito', 'puntaje_tipo_actividad',
                              'puntaje_valor_vs_monto', 'puntaje_region']:
                fmt = number_format
            elif col_name == 'observacion_cualitativa' and 'URGENTE' in str(valor):
                fmt = urgente_format
            else:
                fmt = cell_format

            worksheet.write(row_num + 1, col_num, valor, fmt)

    # Congelar primera fila
    worksheet.freeze_panes(1, 0)

    # Altura de filas
    worksheet.set_default_row(25)
    worksheet.set_row(0, 35)


def generar_excel(
    resultados: List[ResultadoMatch],
    output_path: str = "output/resultados_matching.xlsx",
    incluir_evidencias: bool = False
) -> str:
    """
    Genera archivo Excel con tablas segmentadas por cliente y consolidada.

    Args:
        resultados: Lista de ResultadoMatch
        output_path: Ruta del archivo de salida
        incluir_evidencias: Si incluir columnas de evidencia detallada

    Returns:
        Ruta del archivo generado
    """
    # Crear directorio de salida si no existe
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convertir resultados a diccionarios
    if incluir_evidencias:
        datos = [resultado_a_dict_detallado(r) for r in resultados]
    else:
        datos = [resultado_a_dict(r) for r in resultados]

    # Crear DataFrame consolidado
    df_consolidado = pd.DataFrame(datos)

    # Ordenar por puntaje total descendente
    df_consolidado = df_consolidado.sort_values(
        by=['puntaje_total'],
        ascending=False,
        key=lambda x: pd.to_numeric(x, errors='coerce').fillna(-1)
    )

    # Agrupar por tipología de cliente para tablas segmentadas
    if incluir_evidencias:
        clientes = df_consolidado['tipologia_cliente'].unique()
    else:
        # Necesitamos agregar tipologia_cliente temporalmente
        datos_con_cliente = [resultado_a_dict_detallado(r) for r in resultados]
        df_temp = pd.DataFrame(datos_con_cliente)
        clientes = df_temp['tipologia_cliente'].unique()
        # Crear mapeo idea -> cliente
        cliente_map = df_temp.set_index('id_idea')['tipologia_cliente'].to_dict()
        df_consolidado['_tipologia_cliente'] = df_consolidado['id_idea'].map(cliente_map)

    # Generar Excel con múltiples hojas
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        # Columnas para la salida estándar
        columnas_salida = [
            'id_idea', 'nombre_idea', 'id_convocatoria', 'nombre_convocatoria',
            'puntaje_proposito', 'puntaje_tipo_actividad', 'puntaje_elegibilidad',
            'puntaje_valor_vs_monto', 'puntaje_region', 'puntaje_total',
            'observacion_cualitativa', 'acciones_sugeridas'
        ]

        # 1. Hoja consolidada
        df_salida = df_consolidado[columnas_salida].copy()
        df_salida.to_excel(writer, sheet_name='Consolidado', index=False)
        aplicar_formato_excel(writer, 'Consolidado', df_salida)

        # 2. Hojas por cliente
        col_cliente = 'tipologia_cliente' if incluir_evidencias else '_tipologia_cliente'
        for cliente in sorted(clientes):
            # Filtrar por cliente
            mask = df_consolidado[col_cliente] == cliente
            df_cliente = df_consolidado.loc[mask, columnas_salida].copy()

            if len(df_cliente) == 0:
                continue

            # Limpiar nombre para hoja (max 31 caracteres)
            nombre_hoja = cliente[:31].replace('/', '-').replace('\\', '-')
            nombre_hoja = ''.join(c for c in nombre_hoja if c.isalnum() or c in ' -_')

            df_cliente.to_excel(writer, sheet_name=nombre_hoja, index=False)
            aplicar_formato_excel(writer, nombre_hoja, df_cliente)

        # 3. Hoja de resumen
        crear_hoja_resumen(writer, resultados, clientes)

        # 4. Hoja con evidencias detalladas (opcional)
        if incluir_evidencias:
            columnas_evidencia = columnas_salida + [
                'evidencia_proposito', 'evidencia_actividad',
                'evidencia_elegibilidad', 'evidencia_valor', 'evidencia_region'
            ]
            df_evidencias = df_consolidado[columnas_evidencia].copy()
            df_evidencias.to_excel(writer, sheet_name='Evidencias', index=False)
            aplicar_formato_excel(writer, 'Evidencias', df_evidencias)

    return output_path


def crear_hoja_resumen(
    writer: pd.ExcelWriter,
    resultados: List[ResultadoMatch],
    clientes: List[str]
):
    """Crea una hoja de resumen con estadísticas."""
    workbook = writer.book
    worksheet = workbook.add_worksheet('Resumen')

    # Formatos
    titulo_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'bg_color': '#1B5E20',
        'font_color': 'white',
        'align': 'center',
        'valign': 'vcenter'
    })

    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#E8F5E9',
        'border': 1
    })

    cell_format = workbook.add_format({
        'border': 1
    })

    number_format = workbook.add_format({
        'border': 1,
        'num_format': '0'
    })

    # Título
    worksheet.merge_range('A1:F1', 'RESUMEN DE ANÁLISIS - MATCHING IDEAS-CONVOCATORIAS', titulo_format)
    worksheet.set_row(0, 30)

    # Fecha de generación
    worksheet.write('A3', f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M")}')

    # Estadísticas generales
    total_matches = len(resultados)
    elegibles = sum(1 for r in resultados if r.es_elegible)
    no_elegibles = total_matches - elegibles
    urgentes = sum(1 for r in resultados if r.es_urgente)
    alto_match = sum(1 for r in resultados if r.puntaje_total >= 70)
    medio_match = sum(1 for r in resultados if 40 <= r.puntaje_total < 70)

    row = 5
    worksheet.write(row, 0, 'ESTADÍSTICAS GENERALES', header_format)
    worksheet.merge_range(row, 0, row, 2, 'ESTADÍSTICAS GENERALES', header_format)

    stats = [
        ('Total de cruces analizados', total_matches),
        ('Cruces elegibles', elegibles),
        ('Cruces no elegibles', no_elegibles),
        ('Convocatorias urgentes', urgentes),
        ('Matches de alto potencial (≥70)', alto_match),
        ('Matches de potencial medio (40-69)', medio_match),
    ]

    for i, (label, value) in enumerate(stats):
        worksheet.write(row + 1 + i, 0, label, cell_format)
        worksheet.write(row + 1 + i, 1, value, number_format)

    # Estadísticas por cliente
    row = row + len(stats) + 3
    worksheet.write(row, 0, 'ESTADÍSTICAS POR CLIENTE', header_format)
    worksheet.merge_range(row, 0, row, 4, 'ESTADÍSTICAS POR CLIENTE', header_format)

    headers = ['Cliente', 'Total Cruces', 'Elegibles', 'Alto Potencial', 'Urgentes']
    for col, h in enumerate(headers):
        worksheet.write(row + 1, col, h, header_format)

    row_offset = row + 2
    for i, cliente in enumerate(sorted(clientes)):
        res_cliente = [r for r in resultados if r.tipologia_cliente == cliente]
        worksheet.write(row_offset + i, 0, cliente, cell_format)
        worksheet.write(row_offset + i, 1, len(res_cliente), number_format)
        worksheet.write(row_offset + i, 2, sum(1 for r in res_cliente if r.es_elegible), number_format)
        worksheet.write(row_offset + i, 3, sum(1 for r in res_cliente if r.puntaje_total >= 70), number_format)
        worksheet.write(row_offset + i, 4, sum(1 for r in res_cliente if r.es_urgente), number_format)

    # Top 10 mejores matches
    row = row_offset + len(clientes) + 2
    worksheet.write(row, 0, 'TOP 10 MEJORES MATCHES', header_format)
    worksheet.merge_range(row, 0, row, 5, 'TOP 10 MEJORES MATCHES', header_format)

    top_headers = ['Idea', 'Convocatoria', 'Puntaje', 'Cliente', 'Estado']
    for col, h in enumerate(top_headers):
        worksheet.write(row + 1, col, h, header_format)

    top_10 = sorted(
        [r for r in resultados if r.es_elegible],
        key=lambda x: x.puntaje_total,
        reverse=True
    )[:10]

    for i, r in enumerate(top_10):
        estado = "URGENTE" if r.es_urgente else "Normal"
        worksheet.write(row + 2 + i, 0, r.nombre_idea[:40], cell_format)
        worksheet.write(row + 2 + i, 1, r.nombre_convocatoria[:40], cell_format)
        worksheet.write(row + 2 + i, 2, r.puntaje_total, number_format)
        worksheet.write(row + 2 + i, 3, r.tipologia_cliente, cell_format)
        worksheet.write(row + 2 + i, 4, estado, cell_format)

    # Ajustar anchos
    worksheet.set_column('A:A', 35)
    worksheet.set_column('B:B', 40)
    worksheet.set_column('C:E', 15)
    worksheet.set_column('F:F', 12)
