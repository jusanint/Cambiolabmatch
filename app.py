#!/usr/bin/env python3
"""
Interfaz gráfica web para el Sistema de Matching Ideas-Convocatorias.
Ejecutar con: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# =============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Matching Ideas-Convocatorias",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# ESTILOS CSS
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1B5E20;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .score-high {
        background-color: #C8E6C9;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .score-medium {
        background-color: #FFF9C4;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
    }
    .score-low {
        background-color: #FFCDD2;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
    }
    .urgent-badge {
        background-color: #FF5722;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
    }
    .no-elegible {
        background-color: #FFCDD2;
        color: #B71C1C;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTES Y CONFIGURACIÓN
# =============================================================================
DIAS_URGENTE = 30

PUNTAJES = {
    "proposito": {1: 0, 2: 10, 3: 17, 4: 25, 5: 35},
    "tipo_actividad": {1: 0, 2: 10, 3: 17, 4: 25, 5: 35},
    "elegibilidad": {1: 0, 2: 4, 3: 7, 4: 11, 5: 15},
    "valor_monto": {1: 0, 2: 2, 3: 5, 4: 7, 5: 10},
    "region": {1: 0, 2: 1, 3: 2, 4: 3, 5: 5},
}

TIPO_SINONIMOS = {
    "universidad": ["universidades", "universidad", "centros de investigación", "instituciones académicas"],
    "ong": ["ongs", "ong", "organizaciones sin fines de lucro", "fundaciones"],
    "startup": ["startups", "startup", "empresas de base tecnológica", "emprendimientos"],
    "cooperativa": ["cooperativas", "cooperativa", "asociaciones", "organizaciones de productores"],
    "empresa social": ["empresas sociales", "empresa social", "empresas b certificadas"],
    "empresa privada": ["empresas privadas", "empresa privada", "pymes", "empresas"],
    "fundación": ["fundaciones", "fundación"],
}

ACTIVIDAD_KEYWORDS = {
    "prototipo": ["prototipo", "i+d", "innovación", "tecnológico"],
    "piloto": ["piloto", "prueba", "validación", "demostración"],
    "capacitación": ["capacitación", "formación", "educación", "talleres"],
    "consultoría": ["consultoría", "asesoría", "diagnóstico"],
    "software": ["software", "aplicación", "app", "plataforma", "digital"],
    "infraestructura": ["infraestructura", "construcción", "equipamiento"],
    "programa": ["programa", "iniciativa", "aceleración"],
}

CATEGORIAS_TEMATICAS = {
    "medio_ambiente": [
        "medio ambiente", "ambiental", "ecológico", "sostenible", "sustentable",
        "verde", "cambio climático", "clima", "emisiones", "carbono", "biodiversidad",
        "ecosistema", "conservación", "restauración", "reforestación", "deforestación"
    ],
    "energia": [
        "energía", "energético", "renovable", "solar", "eólica", "biogas", "biogás",
        "biodigestor", "eficiencia energética", "transición energética", "limpia"
    ],
    "agricultura": [
        "agricultura", "agrícola", "agro", "cultivo", "rural", "campesino",
        "productor", "cosecha", "alimentaria", "alimentación", "seguridad alimentaria"
    ],
    "tecnologia": [
        "tecnología", "tecnológico", "digital", "iot", "sensor", "sensores",
        "inteligencia artificial", "software", "aplicación", "app", "plataforma",
        "innovación", "i+d", "investigación"
    ],
    "salud": [
        "salud", "médico", "telemedicina", "sanitario", "hospital", "clínica",
        "bienestar", "enfermedad", "paciente", "atención médica"
    ],
    "educacion": [
        "educación", "educativo", "escuela", "estudiante", "aprendizaje",
        "formación", "capacitación", "academia", "stem", "laboratorio"
    ],
    "social": [
        "social", "comunidad", "comunitario", "inclusión", "inclusivo",
        "vulnerable", "pobreza", "desigualdad", "equidad", "impacto social"
    ],
    "genero": [
        "género", "mujer", "mujeres", "femenino", "feminismo", "empoderamiento",
        "igualdad de género", "equidad de género"
    ],
    "emprendimiento": [
        "emprendimiento", "emprendedor", "startup", "empresa", "negocio",
        "aceleración", "aceleradora", "incubación", "innovación empresarial"
    ],
    "gestion_riesgo": [
        "riesgo", "desastre", "emergencia", "alerta", "inundación", "sismo",
        "resiliencia", "prevención", "mitigación", "adaptación"
    ],
    "cultura": [
        "cultura", "cultural", "artesanía", "artesanal", "arte", "patrimonio",
        "indígena", "étnico", "tradición", "tradicional", "economía naranja"
    ],
    "economia_circular": [
        "circular", "reciclaje", "reutilización", "residuo", "residuos",
        "basura", "desperdicio", "sostenible", "reusar"
    ],
}

# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================
def porcentaje_a_nivel(porcentaje: float) -> int:
    if porcentaje <= 19:
        return 1
    elif porcentaje <= 49:
        return 2
    elif porcentaje <= 70:
        return 3
    elif porcentaje <= 90:
        return 4
    else:
        return 5


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    return texto.lower().strip()


def extraer_ods(texto: str) -> set:
    ods = set()
    for i in range(1, 18):
        if f"ods {i}" in texto.lower() or f"ods{i}" in texto.lower():
            ods.add(f"ODS {i}")
    return ods


def calcular_jaccard(set1: set, set2: set) -> float:
    if not set1 and not set2:
        return 0.0
    interseccion = len(set1 & set2)
    union = len(set1 | set2)
    return (interseccion / union * 100) if union > 0 else 0.0


def verificar_fecha(fecha_str: str) -> Tuple[bool, bool, Optional[int]]:
    if not fecha_str or pd.isna(fecha_str):
        return True, False, None
    try:
        if isinstance(fecha_str, str):
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        else:
            fecha = pd.to_datetime(fecha_str).date()
    except:
        try:
            fecha = datetime.strptime(str(fecha_str), "%d/%m/%Y").date()
        except:
            return True, False, None

    hoy = date.today()
    dias = (fecha - hoy).days
    return dias >= 0, 0 <= dias <= DIAS_URGENTE, dias


def identificar_categorias(texto: str) -> set:
    texto_norm = normalizar(texto)
    categorias = set()
    for categoria, keywords in CATEGORIAS_TEMATICAS.items():
        for kw in keywords:
            if kw in texto_norm:
                categorias.add(categoria)
                break
    return categorias


# =============================================================================
# FUNCIONES DE EVALUACIÓN
# =============================================================================
def evaluar_proposito(idea: Dict, conv: Dict) -> Tuple[int, str]:
    texto_idea = f"{idea.get('nombre', '')} {idea.get('descripcion', '')} {idea.get('tags', '')}"
    texto_conv = f"{conv.get('nombre', '')} {conv.get('proposito', '')} {conv.get('tags', '')} {conv.get('notas_adicionales', '')}"

    ods_idea = extraer_ods(texto_idea)
    ods_conv = extraer_ods(texto_conv)
    ods_comunes = ods_idea & ods_conv

    categorias_idea = identificar_categorias(texto_idea)
    categorias_conv = identificar_categorias(texto_conv)
    categorias_comunes = categorias_idea & categorias_conv

    stopwords = {'de', 'la', 'el', 'en', 'y', 'a', 'para', 'con', 'que', 'del', 'los', 'las', 'un', 'una', 'por'}
    palabras_idea = set(normalizar(texto_idea).split()) - stopwords
    palabras_conv = set(normalizar(texto_conv).split()) - stopwords
    palabras_idea = {p for p in palabras_idea if len(p) > 3}
    palabras_conv = {p for p in palabras_conv if len(p) > 3}

    porcentaje_jaccard = calcular_jaccard(palabras_idea, palabras_conv)
    bonus_categorias = len(categorias_comunes) * 18
    bonus_ods = len(ods_comunes) * 12
    porcentaje = min(100, porcentaje_jaccard + bonus_categorias + bonus_ods)

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = PUNTAJES["proposito"][nivel]

    evidencia_parts = []
    if categorias_comunes:
        cats_display = [c.replace('_', ' ').title() for c in sorted(categorias_comunes)]
        evidencia_parts.append(f"Temática: {', '.join(cats_display[:3])}")
    if ods_comunes:
        evidencia_parts.append(f"ODS: {', '.join(sorted(ods_comunes))}")
    keywords = sorted(palabras_idea & palabras_conv)[:4]
    if keywords:
        evidencia_parts.append(f"Keywords: {', '.join(keywords)}")
    evidencia_parts.append(f"Match: {porcentaje:.0f}%")

    return puntaje, "; ".join(evidencia_parts)


def evaluar_actividad(idea: Dict, conv: Dict) -> Tuple[int, str]:
    clasificacion = normalizar(str(idea.get('clasificacion_idea', '')))
    desc = normalizar(str(idea.get('descripcion', '')))
    conv_texto = normalizar(f"{conv.get('proposito', '')} {conv.get('tags', '')} {conv.get('notas_adicionales', '')}")

    tipo_idea = None
    for tipo, kws in ACTIVIDAD_KEYWORDS.items():
        if any(kw in clasificacion or kw in desc for kw in kws):
            tipo_idea = tipo
            break

    tipos_conv = []
    for tipo, kws in ACTIVIDAD_KEYWORDS.items():
        if any(kw in conv_texto for kw in kws):
            tipos_conv.append(tipo)

    if not tipo_idea:
        porcentaje = 25
        evidencia = "Clasificación no identificada"
    elif tipo_idea in tipos_conv:
        porcentaje = 92
        evidencia = f"Match directo: {tipo_idea}"
    elif tipos_conv:
        porcentaje = 55
        evidencia = f"Idea: {tipo_idea}. Convocatoria: {', '.join(tipos_conv[:2])}"
    else:
        porcentaje = 40
        evidencia = f"Idea: {tipo_idea}. Convocatoria sin tipo específico"

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = PUNTAJES["tipo_actividad"][nivel]

    return puntaje, evidencia


def evaluar_elegibilidad(idea: Dict, conv: Dict) -> Tuple[int, bool, str]:
    tipo_cliente = normalizar(str(idea.get('tipologia_cliente', '')))
    quienes = normalizar(str(conv.get('quienes_pueden_participar', '')))
    notas = normalizar(str(conv.get('notas_adicionales', '')))

    es_elegible = False
    for tipo_base, sinonimos in TIPO_SINONIMOS.items():
        if tipo_cliente in [tipo_base] + sinonimos:
            for sin in sinonimos:
                if sin in quienes:
                    es_elegible = True
                    break
        if es_elegible:
            break

    if not es_elegible and tipo_cliente in quienes:
        es_elegible = True

    if not es_elegible:
        return 0, False, f"No elegible: {idea.get('tipologia_cliente', '')} no permitido"

    if "alianza" in quienes or "consorcio" in quienes:
        porcentaje = 72
        modo = "con alianza"
    else:
        porcentaje = 90
        modo = "directo"

    if tipo_cliente in notas and ("prioriza" in notas or "preferencia" in notas):
        porcentaje = min(100, porcentaje + 10)

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = PUNTAJES["elegibilidad"][nivel]

    return puntaje, True, f"Elegible ({modo}). Match: {porcentaje:.0f}%"


def evaluar_valor(idea: Dict, conv: Dict) -> Tuple[int, str]:
    valor = float(idea.get('valor_estimado', 0) or 0)
    monto = float(conv.get('monto_maximo', 0) or 0)

    if valor <= 0:
        cobertura = 100
    else:
        cobertura = min(100, (monto / valor) * 100)

    nivel = porcentaje_a_nivel(cobertura)
    puntaje = PUNTAJES["valor_monto"][nivel]

    if valor > monto:
        deficit = valor - monto
        evidencia = f"Cobertura: {cobertura:.0f}%. Déficit: ${deficit:,.0f}"
    else:
        evidencia = f"Cobertura: {cobertura:.0f}%. Suficiente"

    return puntaje, evidencia


def evaluar_region(idea: Dict, conv: Dict) -> Tuple[int, str]:
    region_idea = normalizar(str(idea.get('region', '')))
    ambito_idea = normalizar(str(idea.get('ambito', '')))
    region_conv = normalizar(str(conv.get('region', '')))
    ambito_conv = normalizar(str(conv.get('ambito', '')))

    if not region_idea or not region_conv:
        porcentaje = 25
        evidencia = "Datos de región incompletos"
    elif region_idea == region_conv:
        porcentaje = 100
        evidencia = f"Match exacto: {region_idea}"
    elif ambito_conv in ["internacional", "global"]:
        porcentaje = 85
        evidencia = f"Convocatoria {ambito_conv} acepta {region_idea}"
    elif "colombia" in region_conv:
        porcentaje = 75
        evidencia = f"{region_idea} dentro de Colombia"
    elif "américa latina" in region_conv or "latinoamérica" in region_conv:
        porcentaje = 80
        evidencia = f"{region_idea} en América Latina"
    else:
        porcentaje = 35
        evidencia = f"Divergencia: {region_idea} vs {region_conv}"

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = PUNTAJES["region"][nivel]

    return puntaje, evidencia


def calcular_match(idea: Dict, conv: Dict) -> Optional[Dict]:
    vigente, urgente, dias = verificar_fecha(conv.get('fecha_limite', ''))
    if not vigente:
        return None

    p_proposito, ev_proposito = evaluar_proposito(idea, conv)
    p_actividad, ev_actividad = evaluar_actividad(idea, conv)
    p_elegibilidad, es_elegible, ev_elegibilidad = evaluar_elegibilidad(idea, conv)
    p_valor, ev_valor = evaluar_valor(idea, conv)
    p_region, ev_region = evaluar_region(idea, conv)

    if es_elegible:
        total = p_proposito + p_actividad + p_elegibilidad + p_valor + p_region
    else:
        total = 0

    obs_parts = []
    if urgente:
        obs_parts.append(f"URGENTE: {dias} días restantes")
    if not es_elegible:
        obs_parts.append("NO ELEGIBLE")
    elif total >= 70:
        obs_parts.append("Alta compatibilidad")
    elif total >= 50:
        obs_parts.append("Compatibilidad media")
    else:
        obs_parts.append("Compatibilidad baja")

    fortalezas = []
    if p_proposito >= 25:
        fortalezas.append("temática alineada")
    if p_actividad >= 25:
        fortalezas.append("actividad compatible")
    if fortalezas:
        obs_parts.append(f"Fortalezas: {', '.join(fortalezas)}")

    acciones = []
    if not es_elegible:
        acciones.append("Buscar socio elegible")
    else:
        if p_valor <= 5:
            acciones.append("Ajustar presupuesto")
        if p_elegibilidad <= 7:
            acciones.append("Formar alianza/consorcio")
        if p_region <= 2:
            acciones.append("Evidenciar alcance geográfico")
        if urgente:
            acciones.insert(0, "PRIORIZAR postulación")

        notas = normalizar(str(conv.get('notas_adicionales', '')))
        if "contrapartida" in notas:
            acciones.append("Preparar contrapartida")
        if "rural" in notas:
            acciones.append("Destacar componente rural")
        if "mujeres" in notas or "género" in notas:
            acciones.append("Evidenciar enfoque de género")

    return {
        'id_idea': idea.get('id_idea', ''),
        'nombre_idea': idea.get('nombre', ''),
        'id_convocatoria': conv.get('id_convocatoria', ''),
        'nombre_convocatoria': conv.get('nombre', ''),
        'tipologia_cliente': idea.get('tipologia_cliente', ''),
        'puntaje_proposito': p_proposito,
        'puntaje_tipo_actividad': p_actividad,
        'puntaje_elegibilidad': p_elegibilidad if es_elegible else "No elegible",
        'puntaje_valor_vs_monto': p_valor,
        'puntaje_region': p_region,
        'puntaje_total': total,
        'es_elegible': es_elegible,
        'es_urgente': urgente,
        'dias_restantes': dias,
        'observacion_cualitativa': ". ".join(obs_parts),
        'acciones_sugeridas': "; ".join(acciones) if acciones else "Sin ajustes mayores"
    }


# =============================================================================
# FUNCIONES DE CARGA DE DATOS
# =============================================================================
@st.cache_data
def cargar_archivo(uploaded_file) -> pd.DataFrame:
    """Carga un archivo CSV o Excel."""
    if uploaded_file is None:
        return None

    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df.columns = df.columns.str.lower().str.strip()
        return df
    except Exception as e:
        st.error(f"Error al cargar archivo: {e}")
        return None


def validar_ideas(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Valida y normaliza el DataFrame de IDEAS."""
    warnings = []
    columnas_map = {
        'id_idea': ['id_idea', 'id', 'idea_id', 'codigo'],
        'nombre': ['nombre', 'nombre_idea', 'titulo', 'name'],
        'descripcion': ['descripcion', 'descripción', 'description'],
        'tags': ['tags', 'etiquetas', 'keywords'],
        'tipologia_cliente': ['tipologia_cliente', 'tipo_cliente', 'cliente', 'proponente'],
        'valor_estimado': ['valor_estimado', 'valor', 'presupuesto', 'monto'],
        'moneda': ['moneda', 'currency'],
        'clasificacion_idea': ['clasificacion_idea', 'clasificacion', 'tipo_proyecto'],
        'region': ['region', 'región', 'ubicacion'],
        'ambito': ['ambito', 'ámbito', 'alcance'],
    }

    for col_std, aliases in columnas_map.items():
        if col_std not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df = df.rename(columns={alias: col_std})
                    break

    for col in columnas_map.keys():
        if col not in df.columns:
            df[col] = ""

    obligatorias = ['id_idea', 'nombre', 'tipologia_cliente', 'valor_estimado']
    faltantes = [c for c in obligatorias if c not in df.columns or df[c].isna().all()]
    if faltantes:
        warnings.append(f"Columnas faltantes o vacías: {faltantes}")

    df['valor_estimado'] = pd.to_numeric(df['valor_estimado'], errors='coerce').fillna(0)

    return df, warnings


def validar_convocatorias(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Valida y normaliza el DataFrame de CONVOCATORIAS."""
    warnings = []
    columnas_map = {
        'id_convocatoria': ['id_convocatoria', 'id', 'convocatoria_id'],
        'nombre': ['nombre', 'nombre_convocatoria', 'titulo'],
        'proposito': ['proposito', 'propósito', 'objetivo', 'descripcion'],
        'tags': ['tags', 'etiquetas', 'keywords'],
        'quienes_pueden_participar': ['quienes_pueden_participar', 'elegibilidad', 'participantes'],
        'monto_maximo': ['monto_maximo', 'monto_máximo', 'presupuesto'],
        'moneda': ['moneda', 'currency'],
        'region': ['region', 'región', 'pais'],
        'ambito': ['ambito', 'ámbito', 'alcance'],
        'fecha_limite': ['fecha_limite', 'fecha_límite', 'deadline'],
        'notas_adicionales': ['notas_adicionales', 'notas', 'observaciones'],
    }

    for col_std, aliases in columnas_map.items():
        if col_std not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df = df.rename(columns={alias: col_std})
                    break

    for col in columnas_map.keys():
        if col not in df.columns:
            df[col] = ""

    obligatorias = ['id_convocatoria', 'nombre', 'quienes_pueden_participar', 'monto_maximo']
    faltantes = [c for c in obligatorias if c not in df.columns or df[c].isna().all()]
    if faltantes:
        warnings.append(f"Columnas faltantes o vacías: {faltantes}")

    df['monto_maximo'] = pd.to_numeric(df['monto_maximo'], errors='coerce').fillna(0)

    return df, warnings


# =============================================================================
# FUNCIÓN PRINCIPAL DE ANÁLISIS
# =============================================================================
def ejecutar_analisis(df_ideas: pd.DataFrame, df_convocatorias: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta el análisis de matching."""
    ideas = df_ideas.to_dict('records')
    convocatorias = df_convocatorias.to_dict('records')

    resultados = []
    progress_bar = st.progress(0)
    total = len(ideas) * len(convocatorias)

    for i, idea in enumerate(ideas):
        for j, conv in enumerate(convocatorias):
            resultado = calcular_match(idea, conv)
            if resultado:
                resultados.append(resultado)

            progress = (i * len(convocatorias) + j + 1) / total
            progress_bar.progress(progress)

    progress_bar.empty()

    if not resultados:
        return pd.DataFrame()

    df_resultados = pd.DataFrame(resultados)
    df_resultados = df_resultados.sort_values('puntaje_total', ascending=False)

    return df_resultados


# =============================================================================
# FUNCIONES DE VISUALIZACIÓN
# =============================================================================
def mostrar_metricas(df: pd.DataFrame):
    """Muestra métricas resumen."""
    col1, col2, col3, col4, col5 = st.columns(5)

    total = len(df)
    elegibles = df[df['es_elegible'] == True]
    no_elegibles = total - len(elegibles)
    urgentes = len(df[df['es_urgente'] == True])
    alto_potencial = len(elegibles[elegibles['puntaje_total'] >= 70])
    promedio = elegibles['puntaje_total'].mean() if len(elegibles) > 0 else 0

    with col1:
        st.metric("Total Cruces", total)
    with col2:
        st.metric("Elegibles", len(elegibles))
    with col3:
        st.metric("No Elegibles", no_elegibles)
    with col4:
        st.metric("Urgentes", urgentes, help="Convocatorias con menos de 30 días")
    with col5:
        st.metric("Alto Potencial (≥70)", alto_potencial)


def colorear_puntaje(val):
    """Aplica color según el puntaje."""
    if isinstance(val, str):
        return 'background-color: #FFCDD2; color: #B71C1C'
    elif val >= 70:
        return 'background-color: #C8E6C9'
    elif val >= 40:
        return 'background-color: #FFF9C4'
    else:
        return 'background-color: #FFCDD2'


def crear_excel_descarga(df: pd.DataFrame, clientes: List[str]) -> bytes:
    """Crea un archivo Excel con múltiples hojas."""
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja consolidada
        columnas_salida = [
            'id_idea', 'nombre_idea', 'id_convocatoria', 'nombre_convocatoria',
            'puntaje_proposito', 'puntaje_tipo_actividad', 'puntaje_elegibilidad',
            'puntaje_valor_vs_monto', 'puntaje_region', 'puntaje_total',
            'observacion_cualitativa', 'acciones_sugeridas'
        ]
        df[columnas_salida].to_excel(writer, sheet_name='Consolidado', index=False)

        # Hojas por cliente
        for cliente in clientes:
            df_cliente = df[df['tipologia_cliente'] == cliente]
            if len(df_cliente) > 0:
                # Limpiar nombre para hoja de Excel (max 31 caracteres, sin caracteres inválidos)
                nombre_hoja = str(cliente)[:31].replace('/', '-').replace('\\', '-').replace('*', '').replace('?', '').replace('[', '').replace(']', '').replace(':', '')
                nombre_hoja = ''.join(c for c in nombre_hoja if c.isprintable()).strip()
                # Si el nombre queda vacío, usar un nombre por defecto
                if not nombre_hoja:
                    nombre_hoja = "Sin_clasificar"
                df_cliente[columnas_salida].to_excel(writer, sheet_name=nombre_hoja, index=False)

    output.seek(0)
    return output.getvalue()


# =============================================================================
# APLICACIÓN PRINCIPAL
# =============================================================================
def main():
    # Header
    st.markdown('<p class="main-header">🎯 Sistema de Matching Ideas-Convocatorias</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Analiza la compatibilidad entre ideas de proyectos y convocatorias de financiamiento</p>', unsafe_allow_html=True)

    # Sidebar - Carga de archivos
    with st.sidebar:
        st.header("📁 Cargar Archivos")

        st.subheader("Archivo de IDEAS")
        uploaded_ideas = st.file_uploader(
            "Selecciona archivo CSV o Excel",
            type=['csv', 'xlsx', 'xls'],
            key='ideas',
            help="Debe contener: id_idea, nombre, tipologia_cliente, valor_estimado"
        )

        st.subheader("Archivo de CONVOCATORIAS")
        uploaded_convocatorias = st.file_uploader(
            "Selecciona archivo CSV o Excel",
            type=['csv', 'xlsx', 'xls'],
            key='convocatorias',
            help="Debe contener: id_convocatoria, nombre, quienes_pueden_participar, monto_maximo"
        )

        st.divider()

        # Usar archivos de ejemplo
        usar_ejemplo = st.checkbox("Usar archivos de ejemplo", value=False)

        st.divider()

        # Información
        with st.expander("ℹ️ Criterios de Evaluación"):
            st.markdown("""
            | Criterio | Máx |
            |----------|-----|
            | Propósito/Temática | 35 |
            | Tipo de Actividad | 35 |
            | Elegibilidad | 15 |
            | Valor vs Monto | 10 |
            | Región/Alcance | 5 |
            | **Total** | **100** |
            """)

    # Cargar datos
    df_ideas = None
    df_convocatorias = None

    if usar_ejemplo:
        try:
            df_ideas = pd.read_csv('data/ideas.csv')
            df_convocatorias = pd.read_csv('data/convocatorias.csv')
            df_ideas.columns = df_ideas.columns.str.lower().str.strip()
            df_convocatorias.columns = df_convocatorias.columns.str.lower().str.strip()
            st.sidebar.success("✅ Archivos de ejemplo cargados")
        except Exception as e:
            st.sidebar.error(f"Error cargando ejemplos: {e}")
    else:
        if uploaded_ideas:
            df_ideas = cargar_archivo(uploaded_ideas)
            if df_ideas is not None:
                df_ideas, warnings_ideas = validar_ideas(df_ideas)
                st.sidebar.success(f"✅ Ideas: {len(df_ideas)} registros")
                if warnings_ideas:
                    for w in warnings_ideas:
                        st.sidebar.warning(w)

        if uploaded_convocatorias:
            df_convocatorias = cargar_archivo(uploaded_convocatorias)
            if df_convocatorias is not None:
                df_convocatorias, warnings_conv = validar_convocatorias(df_convocatorias)
                st.sidebar.success(f"✅ Convocatorias: {len(df_convocatorias)} registros")
                if warnings_conv:
                    for w in warnings_conv:
                        st.sidebar.warning(w)

    # Contenido principal
    if df_ideas is not None and df_convocatorias is not None:
        # Pestañas
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Datos Cargados", "🔍 Análisis", "📈 Resultados", "📥 Descargar"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("IDEAS")
                st.dataframe(df_ideas, use_container_width=True, height=300)
            with col2:
                st.subheader("CONVOCATORIAS")
                st.dataframe(df_convocatorias, use_container_width=True, height=300)

        with tab2:
            st.subheader("Ejecutar Análisis de Matching")

            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"Se analizarán **{len(df_ideas)} ideas** x **{len(df_convocatorias)} convocatorias** = **{len(df_ideas) * len(df_convocatorias)} cruces posibles**")

            with col2:
                ejecutar = st.button("🚀 Ejecutar Análisis", type="primary", use_container_width=True)

            if ejecutar:
                with st.spinner("Analizando compatibilidad..."):
                    df_resultados = ejecutar_analisis(df_ideas, df_convocatorias)

                    if len(df_resultados) > 0:
                        st.session_state['resultados'] = df_resultados
                        st.success(f"✅ Análisis completado: {len(df_resultados)} cruces válidos")
                    else:
                        st.warning("No se encontraron cruces válidos. Verifica que las convocatorias no estén vencidas.")

        with tab3:
            if 'resultados' in st.session_state:
                df_resultados = st.session_state['resultados']

                st.subheader("Resumen del Análisis")
                mostrar_metricas(df_resultados)

                st.divider()

                # Filtros
                col1, col2, col3 = st.columns(3)
                with col1:
                    filtro_cliente = st.multiselect(
                        "Filtrar por Cliente",
                        options=df_resultados['tipologia_cliente'].unique(),
                        default=[]
                    )
                with col2:
                    filtro_elegibilidad = st.selectbox(
                        "Elegibilidad",
                        options=["Todos", "Solo elegibles", "Solo no elegibles"]
                    )
                with col3:
                    filtro_puntaje = st.slider(
                        "Puntaje mínimo",
                        min_value=0,
                        max_value=100,
                        value=0
                    )

                # Aplicar filtros
                df_filtrado = df_resultados.copy()
                if filtro_cliente:
                    df_filtrado = df_filtrado[df_filtrado['tipologia_cliente'].isin(filtro_cliente)]
                if filtro_elegibilidad == "Solo elegibles":
                    df_filtrado = df_filtrado[df_filtrado['es_elegible'] == True]
                elif filtro_elegibilidad == "Solo no elegibles":
                    df_filtrado = df_filtrado[df_filtrado['es_elegible'] == False]
                df_filtrado = df_filtrado[df_filtrado['puntaje_total'] >= filtro_puntaje]

                st.subheader(f"Resultados ({len(df_filtrado)} cruces)")

                # Tabla de resultados
                columnas_mostrar = [
                    'id_idea', 'nombre_idea', 'id_convocatoria', 'nombre_convocatoria',
                    'puntaje_proposito', 'puntaje_tipo_actividad', 'puntaje_elegibilidad',
                    'puntaje_valor_vs_monto', 'puntaje_region', 'puntaje_total',
                    'observacion_cualitativa', 'acciones_sugeridas'
                ]

                st.dataframe(
                    df_filtrado[columnas_mostrar].style.applymap(
                        colorear_puntaje,
                        subset=['puntaje_total']
                    ),
                    use_container_width=True,
                    height=500
                )

                # Top 10
                st.subheader("🏆 Top 10 Mejores Matches")
                top10 = df_resultados[df_resultados['es_elegible'] == True].head(10)

                for i, row in top10.iterrows():
                    urgente = "🔴 URGENTE" if row['es_urgente'] else ""
                    col1, col2, col3 = st.columns([4, 4, 2])
                    with col1:
                        st.write(f"**{row['nombre_idea'][:50]}...**")
                    with col2:
                        st.write(f"{row['nombre_convocatoria'][:50]}...")
                    with col3:
                        st.write(f"**{row['puntaje_total']}**/100 {urgente}")

            else:
                st.info("👆 Ve a la pestaña **Análisis** y ejecuta el análisis para ver los resultados.")

        with tab4:
            if 'resultados' in st.session_state:
                df_resultados = st.session_state['resultados']

                st.subheader("Descargar Resultados")

                col1, col2 = st.columns(2)

                with col1:
                    # CSV
                    csv = df_resultados.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📄 Descargar CSV Consolidado",
                        data=csv,
                        file_name=f"matching_resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                with col2:
                    # Excel
                    clientes = df_resultados['tipologia_cliente'].unique().tolist()
                    excel_data = crear_excel_descarga(df_resultados, clientes)
                    st.download_button(
                        label="📊 Descargar Excel (con hojas por cliente)",
                        data=excel_data,
                        file_name=f"matching_resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                st.divider()

                st.subheader("Descargar por Cliente")
                for cliente in sorted(df_resultados['tipologia_cliente'].unique()):
                    df_cliente = df_resultados[df_resultados['tipologia_cliente'] == cliente]
                    csv_cliente = df_cliente.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📄 {cliente} ({len(df_cliente)} cruces)",
                        data=csv_cliente,
                        file_name=f"matching_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key=f"download_{cliente}"
                    )
            else:
                st.info("👆 Ejecuta el análisis primero para poder descargar los resultados.")

    else:
        # Instrucciones cuando no hay datos
        st.markdown("""
        ### 👋 Bienvenido al Sistema de Matching

        Para comenzar, sigue estos pasos:

        1. **Carga tus archivos** en la barra lateral izquierda
           - Archivo de **IDEAS** (CSV o Excel)
           - Archivo de **CONVOCATORIAS** (CSV o Excel)

        2. O marca la casilla **"Usar archivos de ejemplo"** para probar el sistema

        3. Ve a la pestaña **Análisis** y ejecuta el matching

        4. Explora los **Resultados** y **Descarga** los reportes

        ---

        ### 📋 Formato esperado de los archivos

        **IDEAS debe contener:**
        - `id_idea`: Identificador único
        - `nombre`: Nombre de la idea
        - `descripcion`: Descripción detallada
        - `tags`: Etiquetas (incluir ODS si aplica)
        - `tipologia_cliente`: Tipo de proponente
        - `valor_estimado`: Presupuesto estimado
        - `clasificacion_idea`: Tipo de proyecto
        - `region`: Ubicación geográfica
        - `ambito`: Alcance (Local/Regional/Nacional/Internacional)

        **CONVOCATORIAS debe contener:**
        - `id_convocatoria`: Identificador único
        - `nombre`: Nombre de la convocatoria
        - `proposito`: Objetivo/descripción
        - `tags`: Etiquetas (incluir ODS si aplica)
        - `quienes_pueden_participar`: Tipos de proponentes elegibles
        - `monto_maximo`: Financiamiento máximo
        - `region`: Cobertura geográfica
        - `fecha_limite`: Fecha límite (YYYY-MM-DD)
        - `notas_adicionales`: Requisitos especiales
        """)


if __name__ == "__main__":
    main()
