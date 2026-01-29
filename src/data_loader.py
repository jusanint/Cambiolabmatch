"""
Módulo para cargar y validar datos de IDEAS y CONVOCATORIAS.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
import warnings


def cargar_csv(ruta: str, encoding: str = 'utf-8') -> pd.DataFrame:
    """
    Carga un archivo CSV con manejo de diferentes encodings.

    Args:
        ruta: Ruta al archivo CSV
        encoding: Encoding del archivo

    Returns:
        DataFrame con los datos
    """
    encodings_a_probar = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for enc in encodings_a_probar:
        try:
            df = pd.read_csv(ruta, encoding=enc)
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise e

    raise ValueError(f"No se pudo leer el archivo con ningún encoding: {ruta}")


def cargar_excel(ruta: str, hoja: str = None) -> pd.DataFrame:
    """
    Carga un archivo Excel.

    Args:
        ruta: Ruta al archivo Excel
        hoja: Nombre de la hoja (opcional)

    Returns:
        DataFrame con los datos
    """
    if hoja:
        return pd.read_excel(ruta, sheet_name=hoja)
    return pd.read_excel(ruta)


def cargar_datos(ruta: str, hoja: str = None) -> pd.DataFrame:
    """
    Carga datos desde CSV o Excel según la extensión.

    Args:
        ruta: Ruta al archivo
        hoja: Nombre de la hoja (solo para Excel)

    Returns:
        DataFrame con los datos
    """
    path = Path(ruta)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    extension = path.suffix.lower()

    if extension == '.csv':
        return cargar_csv(ruta)
    elif extension in ['.xlsx', '.xls']:
        return cargar_excel(ruta, hoja)
    else:
        raise ValueError(f"Formato de archivo no soportado: {extension}")


def validar_ideas(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Valida y normaliza el DataFrame de IDEAS.

    Args:
        df: DataFrame con datos de ideas

    Returns:
        Tuple de (DataFrame validado, lista de warnings)
    """
    warnings_list = []

    # Columnas requeridas y sus posibles alias
    columnas_requeridas = {
        'id_idea': ['id_idea', 'id', 'idea_id', 'codigo'],
        'nombre': ['nombre', 'nombre_idea', 'titulo', 'name'],
        'descripcion': ['descripcion', 'descripción', 'description', 'desc'],
        'tags': ['tags', 'etiquetas', 'keywords', 'palabras_clave'],
        'tipologia_cliente': ['tipologia_cliente', 'tipo_cliente', 'cliente', 'proponente', 'tipo_proponente'],
        'valor_estimado': ['valor_estimado', 'valor', 'presupuesto', 'monto', 'budget'],
        'moneda': ['moneda', 'currency', 'divisa'],
        'clasificacion_idea': ['clasificacion_idea', 'clasificacion', 'tipo_proyecto', 'categoria'],
        'region': ['region', 'región', 'ubicacion', 'departamento'],
        'ambito': ['ambito', 'ámbito', 'alcance', 'scope'],
    }

    # Normalizar nombres de columnas
    df.columns = df.columns.str.lower().str.strip()

    # Mapear columnas
    for col_std, aliases in columnas_requeridas.items():
        if col_std not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df = df.rename(columns={alias: col_std})
                    break

    # Verificar columnas obligatorias
    obligatorias = ['id_idea', 'nombre', 'tipologia_cliente', 'valor_estimado']
    faltantes = [c for c in obligatorias if c not in df.columns]
    if faltantes:
        warnings_list.append(f"Columnas obligatorias faltantes en IDEAS: {faltantes}")

    # Agregar columnas faltantes con valores por defecto
    for col, _ in columnas_requeridas.items():
        if col not in df.columns:
            df[col] = ""

    # Normalizar valores
    df['moneda'] = df['moneda'].fillna('USD').str.upper()
    df['valor_estimado'] = pd.to_numeric(df['valor_estimado'], errors='coerce').fillna(0)
    df['ambito'] = df['ambito'].fillna('Nacional')

    # Limpiar strings
    for col in ['nombre', 'descripcion', 'tags', 'tipologia_cliente', 'clasificacion_idea', 'region', 'ambito']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

    return df, warnings_list


def validar_convocatorias(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Valida y normaliza el DataFrame de CONVOCATORIAS.

    Args:
        df: DataFrame con datos de convocatorias

    Returns:
        Tuple de (DataFrame validado, lista de warnings)
    """
    warnings_list = []

    # Columnas requeridas y sus posibles alias
    columnas_requeridas = {
        'id_convocatoria': ['id_convocatoria', 'id', 'convocatoria_id', 'codigo'],
        'nombre': ['nombre', 'nombre_convocatoria', 'titulo', 'name'],
        'proposito': ['proposito', 'propósito', 'objetivo', 'description', 'descripcion'],
        'tags': ['tags', 'etiquetas', 'keywords', 'palabras_clave'],
        'quienes_pueden_participar': ['quienes_pueden_participar', 'elegibilidad', 'participantes', 'beneficiarios', 'aplicantes'],
        'monto_maximo': ['monto_maximo', 'monto_máximo', 'presupuesto', 'financiamiento', 'valor_maximo'],
        'moneda': ['moneda', 'currency', 'divisa'],
        'region': ['region', 'región', 'pais', 'ubicacion', 'cobertura'],
        'ambito': ['ambito', 'ámbito', 'alcance', 'scope'],
        'fecha_limite': ['fecha_limite', 'fecha_límite', 'deadline', 'cierre', 'fecha_cierre'],
        'notas_adicionales': ['notas_adicionales', 'notas', 'observaciones', 'requisitos_adicionales', 'comentarios'],
    }

    # Normalizar nombres de columnas
    df.columns = df.columns.str.lower().str.strip()

    # Mapear columnas
    for col_std, aliases in columnas_requeridas.items():
        if col_std not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df = df.rename(columns={alias: col_std})
                    break

    # Verificar columnas obligatorias
    obligatorias = ['id_convocatoria', 'nombre', 'quienes_pueden_participar', 'monto_maximo']
    faltantes = [c for c in obligatorias if c not in df.columns]
    if faltantes:
        warnings_list.append(f"Columnas obligatorias faltantes en CONVOCATORIAS: {faltantes}")

    # Agregar columnas faltantes con valores por defecto
    for col, _ in columnas_requeridas.items():
        if col not in df.columns:
            df[col] = ""

    # Normalizar valores
    df['moneda'] = df['moneda'].fillna('USD').str.upper()
    df['monto_maximo'] = pd.to_numeric(df['monto_maximo'], errors='coerce').fillna(0)
    df['ambito'] = df['ambito'].fillna('Internacional')

    # Limpiar strings
    for col in ['nombre', 'proposito', 'tags', 'quienes_pueden_participar', 'region', 'ambito', 'notas_adicionales']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

    return df, warnings_list


def df_a_lista_dicts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convierte un DataFrame a lista de diccionarios.

    Args:
        df: DataFrame a convertir

    Returns:
        Lista de diccionarios
    """
    return df.to_dict('records')


def cargar_y_validar_datos(
    ruta_ideas: str,
    ruta_convocatorias: str,
    hoja_ideas: str = None,
    hoja_convocatorias: str = None
) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Carga y valida ambos archivos de datos.

    Args:
        ruta_ideas: Ruta al archivo de ideas
        ruta_convocatorias: Ruta al archivo de convocatorias
        hoja_ideas: Nombre de hoja para Excel de ideas
        hoja_convocatorias: Nombre de hoja para Excel de convocatorias

    Returns:
        Tuple de (lista_ideas, lista_convocatorias, warnings)
    """
    all_warnings = []

    # Cargar ideas
    df_ideas = cargar_datos(ruta_ideas, hoja_ideas)
    df_ideas, warnings_ideas = validar_ideas(df_ideas)
    all_warnings.extend(warnings_ideas)

    # Cargar convocatorias
    df_convocatorias = cargar_datos(ruta_convocatorias, hoja_convocatorias)
    df_convocatorias, warnings_conv = validar_convocatorias(df_convocatorias)
    all_warnings.extend(warnings_conv)

    # Convertir a listas de diccionarios
    lista_ideas = df_a_lista_dicts(df_ideas)
    lista_convocatorias = df_a_lista_dicts(df_convocatorias)

    print(f"Datos cargados: {len(lista_ideas)} ideas, {len(lista_convocatorias)} convocatorias")

    if all_warnings:
        for w in all_warnings:
            print(f"Advertencia: {w}")

    return lista_ideas, lista_convocatorias, all_warnings
