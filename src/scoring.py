"""
Módulo de scoring para el matching entre Ideas y Convocatorias.
Implementa las reglas de puntuación según las bandas y criterios definidos.
"""

import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .config import (
    MAPPING_BANDS, CRITERIOS, TIPO_PROPONENTE_SINONIMOS,
    ACTIVIDAD_KEYWORDS, ODS_NOMBRES, DIAS_URGENTE, AMBITOS,
    CATEGORIAS_TEMATICAS
)


@dataclass
class ResultadoCriterio:
    """Resultado de evaluación de un criterio individual."""
    porcentaje_match: float
    nivel: int
    puntaje: int
    evidencia: str


@dataclass
class ResultadoMatch:
    """Resultado completo del matching entre una idea y una convocatoria."""
    id_idea: str
    nombre_idea: str
    id_convocatoria: str
    nombre_convocatoria: str
    tipologia_cliente: str

    puntaje_proposito: int
    puntaje_tipo_actividad: int
    puntaje_elegibilidad: int  # 0-15 o -1 para "No elegible"
    puntaje_valor_vs_monto: int
    puntaje_region: int
    puntaje_total: int

    es_elegible: bool
    es_urgente: bool
    dias_restantes: Optional[int]

    observacion_cualitativa: str
    acciones_sugeridas: str

    # Evidencias detalladas
    evidencia_proposito: str
    evidencia_actividad: str
    evidencia_elegibilidad: str
    evidencia_valor: str
    evidencia_region: str


def porcentaje_a_nivel(porcentaje: float) -> int:
    """Convierte un porcentaje de match a nivel según las bandas definidas."""
    porcentaje = max(0, min(100, porcentaje))
    for min_val, max_val, nivel in MAPPING_BANDS:
        if min_val <= porcentaje <= max_val:
            return nivel
    return 1


def nivel_a_puntaje(nivel: int, criterio: str) -> int:
    """Convierte un nivel a puntaje según el criterio."""
    config = CRITERIOS.get(criterio)
    if not config:
        return 0
    return config.puntos_por_nivel.get(nivel, 0)


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparaciones."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = re.sub(r'[^\w\sáéíóúñü]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def extraer_ods(texto: str) -> List[str]:
    """Extrae referencias a ODS del texto."""
    ods_encontrados = []
    texto_lower = texto.lower()
    for ods_key in ODS_NOMBRES.keys():
        if ods_key.lower() in texto_lower:
            ods_encontrados.append(ods_key)
    return ods_encontrados


def calcular_jaccard(set1: set, set2: set) -> float:
    """Calcula el coeficiente de Jaccard entre dos conjuntos."""
    if not set1 and not set2:
        return 0.0
    interseccion = len(set1 & set2)
    union = len(set1 | set2)
    return (interseccion / union * 100) if union > 0 else 0.0


def identificar_categorias(texto: str) -> set:
    """Identifica las categorías temáticas presentes en un texto."""
    texto_norm = normalizar_texto(texto)
    categorias = set()
    for categoria, keywords in CATEGORIAS_TEMATICAS.items():
        for kw in keywords:
            if kw in texto_norm:
                categorias.add(categoria)
                break
    return categorias


def evaluar_proposito_tematica(
    idea_nombre: str,
    idea_descripcion: str,
    idea_tags: str,
    conv_nombre: str,
    conv_proposito: str,
    conv_tags: str,
    conv_notas: str,
    similarity_func=None
) -> ResultadoCriterio:
    """
    Evalúa la coincidencia de propósito/temática entre idea y convocatoria.
    Usa embeddings si está disponible, sino usa categorías temáticas + Jaccard.
    """
    # Combinar textos
    texto_idea = f"{idea_nombre} {idea_descripcion} {idea_tags}"
    texto_conv = f"{conv_nombre} {conv_proposito} {conv_tags} {conv_notas}"

    # Extraer ODS
    ods_idea = set(extraer_ods(texto_idea))
    ods_conv = set(extraer_ods(texto_conv))
    ods_comunes = ods_idea & ods_conv

    # Identificar categorías temáticas
    categorias_idea = identificar_categorias(texto_idea)
    categorias_conv = identificar_categorias(texto_conv)
    categorias_comunes = categorias_idea & categorias_conv

    # Tokenizar y obtener keywords
    palabras_idea = set(normalizar_texto(texto_idea).split())
    palabras_conv = set(normalizar_texto(texto_conv).split())

    # Eliminar stopwords básicas
    stopwords = {'de', 'la', 'el', 'en', 'y', 'a', 'para', 'con', 'que', 'del', 'los', 'las', 'un', 'una', 'por'}
    palabras_idea = palabras_idea - stopwords
    palabras_conv = palabras_conv - stopwords

    # Calcular similitud
    if similarity_func:
        # Usar embeddings si está disponible
        porcentaje = similarity_func(texto_idea, texto_conv)
    else:
        # Usar Jaccard + bonus por categorías temáticas + bonus por ODS
        porcentaje_jaccard = calcular_jaccard(palabras_idea, palabras_conv)
        bonus_categorias = len(categorias_comunes) * 18  # 18% por categoría común
        bonus_ods = len(ods_comunes) * 12  # 12% bonus por cada ODS común
        porcentaje = min(100, porcentaje_jaccard + bonus_categorias + bonus_ods)

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = nivel_a_puntaje(nivel, "proposito")

    # Generar evidencia
    palabras_comunes = palabras_idea & palabras_conv
    keywords_relevantes = [w for w in palabras_comunes if len(w) > 4][:5]

    evidencia_parts = []
    if categorias_comunes:
        cats_display = [c.replace('_', ' ').title() for c in sorted(categorias_comunes)]
        evidencia_parts.append(f"Temática: {', '.join(cats_display[:3])}")
    if ods_comunes:
        evidencia_parts.append(f"ODS: {', '.join(sorted(ods_comunes))}")
    if keywords_relevantes:
        evidencia_parts.append(f"Keywords: {', '.join(keywords_relevantes)}")
    evidencia_parts.append(f"Match: {porcentaje:.1f}%")

    evidencia = "; ".join(evidencia_parts) if evidencia_parts else "Sin coincidencias significativas"

    return ResultadoCriterio(
        porcentaje_match=porcentaje,
        nivel=nivel,
        puntaje=puntaje,
        evidencia=evidencia
    )


def evaluar_tipo_actividad(
    clasificacion_idea: str,
    idea_descripcion: str,
    conv_proposito: str,
    conv_tags: str,
    conv_notas: str
) -> ResultadoCriterio:
    """
    Evalúa la coincidencia entre el tipo de actividad de la idea y los requisitos
    de la convocatoria usando keywords y verbos.
    """
    clasificacion_norm = normalizar_texto(clasificacion_idea)
    desc_norm = normalizar_texto(idea_descripcion)
    conv_texto = normalizar_texto(f"{conv_proposito} {conv_tags} {conv_notas}")

    # Identificar tipo de actividad de la idea
    tipo_idea = None
    score_max = 0
    for tipo, keywords in ACTIVIDAD_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in clasificacion_norm or kw in desc_norm)
        if score > score_max:
            score_max = score
            tipo_idea = tipo

    # Buscar coincidencias en convocatoria
    matches_conv = []
    for tipo, keywords in ACTIVIDAD_KEYWORDS.items():
        for kw in keywords:
            if kw in conv_texto:
                matches_conv.append((tipo, kw))

    # Calcular porcentaje de match
    if not tipo_idea:
        porcentaje = 20  # Sin clasificación clara, nivel bajo
        evidencia = "Clasificación de idea no identificada claramente"
    elif not matches_conv:
        porcentaje = 30  # No hay keywords de actividad en convocatoria
        evidencia = f"Idea: {tipo_idea}. Convocatoria sin tipo de actividad específico"
    else:
        tipos_conv = set(m[0] for m in matches_conv)
        if tipo_idea in tipos_conv:
            porcentaje = 90 + (score_max * 2)  # Match directo
            keywords_match = [m[1] for m in matches_conv if m[0] == tipo_idea][:3]
            evidencia = f"Match directo: {tipo_idea}. Keywords: {', '.join(keywords_match)}"
        else:
            # Match parcial - tipos relacionados
            porcentaje = 50
            evidencia = f"Idea: {tipo_idea}. Convocatoria acepta: {', '.join(tipos_conv)}"

    porcentaje = min(100, porcentaje)
    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = nivel_a_puntaje(nivel, "tipo_actividad")

    return ResultadoCriterio(
        porcentaje_match=porcentaje,
        nivel=nivel,
        puntaje=puntaje,
        evidencia=evidencia
    )


def evaluar_elegibilidad(
    tipologia_cliente: str,
    quienes_pueden: str,
    conv_notas: str
) -> Tuple[ResultadoCriterio, bool]:
    """
    Evalúa si el tipo de proponente es elegible para la convocatoria.
    Retorna (ResultadoCriterio, es_elegible).
    Si no es elegible, puntaje_total debe ser 0.
    """
    tipo_norm = normalizar_texto(tipologia_cliente)
    quienes_norm = normalizar_texto(quienes_pueden)
    notas_norm = normalizar_texto(conv_notas)

    # Buscar el tipo de cliente en los sinónimos
    tipo_encontrado = None
    for tipo_base, sinonimos in TIPO_PROPONENTE_SINONIMOS.items():
        if tipo_norm in sinonimos or any(s in tipo_norm for s in sinonimos):
            tipo_encontrado = tipo_base
            break

    if not tipo_encontrado:
        tipo_encontrado = tipo_norm

    # Verificar elegibilidad
    es_elegible = False
    nivel_participacion = ""

    # Buscar coincidencia directa
    for tipo_base, sinonimos in TIPO_PROPONENTE_SINONIMOS.items():
        if tipo_norm in [tipo_base] + sinonimos:
            for sinonimo in sinonimos:
                if sinonimo in quienes_norm:
                    es_elegible = True
                    # Determinar nivel de participación
                    if "alianza" in quienes_norm or "consorcio" in quienes_norm:
                        nivel_participacion = "con alianza/consorcio"
                    elif "socio" in quienes_norm or "partner" in quienes_norm:
                        nivel_participacion = "con socio"
                    else:
                        nivel_participacion = "participante principal"
                    break
        if es_elegible:
            break

    # Verificación adicional por texto directo
    if not es_elegible:
        if tipo_norm in quienes_norm or tipo_encontrado in quienes_norm:
            es_elegible = True
            nivel_participacion = "participante directo"

    # Verificar exclusiones en notas
    exclusiones = ["no aplica para", "excluye", "no elegible", "no pueden participar"]
    for excl in exclusiones:
        if excl in notas_norm and tipo_encontrado in notas_norm:
            es_elegible = False
            break

    if not es_elegible:
        return ResultadoCriterio(
            porcentaje_match=0,
            nivel=0,
            puntaje=0,
            evidencia=f"No elegible: {tipologia_cliente} no está en '{quienes_pueden}'"
        ), False

    # Calcular porcentaje según nivel de participación
    if nivel_participacion == "participante principal":
        porcentaje = 95
    elif nivel_participacion == "participante directo":
        porcentaje = 85
    elif nivel_participacion == "con alianza/consorcio":
        porcentaje = 70
    elif nivel_participacion == "con socio":
        porcentaje = 60
    else:
        porcentaje = 50

    # Bonus por menciones especiales en notas
    if tipo_encontrado in notas_norm and ("prioriza" in notas_norm or "preferencia" in notas_norm):
        porcentaje = min(100, porcentaje + 10)

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = nivel_a_puntaje(nivel, "elegibilidad")

    evidencia = f"Elegible como {nivel_participacion}. Match: {porcentaje:.0f}%"

    return ResultadoCriterio(
        porcentaje_match=porcentaje,
        nivel=nivel,
        puntaje=puntaje,
        evidencia=evidencia
    ), True


def evaluar_valor_vs_monto(
    valor_estimado: float,
    moneda_idea: str,
    monto_maximo: float,
    moneda_conv: str
) -> ResultadoCriterio:
    """
    Evalúa la cobertura del monto máximo respecto al valor estimado.
    Normaliza monedas antes de comparar.
    """
    # Tasas de cambio aproximadas a USD (simplificado)
    tasas_usd = {
        "usd": 1.0,
        "eur": 1.10,
        "cop": 0.00025,
        "mxn": 0.055,
        "brl": 0.20,
    }

    # Normalizar a USD
    moneda_idea_norm = moneda_idea.lower().strip() if moneda_idea else "usd"
    moneda_conv_norm = moneda_conv.lower().strip() if moneda_conv else "usd"

    tasa_idea = tasas_usd.get(moneda_idea_norm, 1.0)
    tasa_conv = tasas_usd.get(moneda_conv_norm, 1.0)

    valor_usd = valor_estimado * tasa_idea
    monto_usd = monto_maximo * tasa_conv

    # Calcular % cobertura (capear en 100%)
    if valor_usd <= 0:
        porcentaje_cobertura = 100
    else:
        porcentaje_cobertura = min(100, (monto_usd / valor_usd) * 100)

    nivel = porcentaje_a_nivel(porcentaje_cobertura)
    puntaje = nivel_a_puntaje(nivel, "valor_monto")

    # Generar evidencia
    if valor_usd > monto_usd:
        deficit = valor_usd - monto_usd
        evidencia = f"Cobertura: {porcentaje_cobertura:.1f}%. Déficit: ${deficit:,.0f} USD"
    else:
        evidencia = f"Cobertura: {porcentaje_cobertura:.1f}%. Monto suficiente"

    return ResultadoCriterio(
        porcentaje_match=porcentaje_cobertura,
        nivel=nivel,
        puntaje=puntaje,
        evidencia=evidencia
    )


def evaluar_region_alcance(
    region_idea: str,
    ambito_idea: str,
    region_conv: str,
    ambito_conv: str
) -> ResultadoCriterio:
    """
    Evalúa la coincidencia geográfica entre idea y convocatoria.
    """
    region_idea_norm = normalizar_texto(region_idea) if region_idea else ""
    region_conv_norm = normalizar_texto(region_conv) if region_conv else ""
    ambito_idea_norm = normalizar_texto(ambito_idea) if ambito_idea else ""
    ambito_conv_norm = normalizar_texto(ambito_conv) if ambito_conv else ""

    # Determinar nivel de ámbito
    nivel_idea = AMBITOS.get(ambito_idea_norm, 0)
    nivel_conv = AMBITOS.get(ambito_conv_norm, 0)

    # Evaluar coincidencia
    if not region_idea_norm or not region_conv_norm:
        porcentaje = 20  # Sin datos
        evidencia = "Datos de región incompletos"
    elif region_idea_norm == region_conv_norm:
        porcentaje = 100  # Match exacto
        evidencia = f"Match exacto: {region_idea}"
    elif ambito_conv_norm in ["internacional", "global"]:
        # Convocatoria internacional acepta cualquier región
        porcentaje = 85
        evidencia = f"Convocatoria internacional acepta {region_idea}"
    elif ambito_conv_norm == "nacional" and nivel_idea <= nivel_conv:
        # Convocatoria nacional, idea nacional o menor
        porcentaje = 75
        evidencia = f"Idea {ambito_idea} compatible con convocatoria nacional"
    elif "colombia" in region_conv_norm and any(
        r in region_idea_norm for r in ["antioquia", "bogotá", "cundinamarca", "valle", "medellín"]
    ):
        porcentaje = 70
        evidencia = f"Región {region_idea} dentro de Colombia"
    elif "américa latina" in region_conv_norm or "latinoamérica" in region_conv_norm:
        porcentaje = 80
        evidencia = f"Región {region_idea} dentro de América Latina"
    else:
        porcentaje = 30
        evidencia = f"Divergencia geográfica: {region_idea} vs {region_conv}"

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = nivel_a_puntaje(nivel, "region")

    return ResultadoCriterio(
        porcentaje_match=porcentaje,
        nivel=nivel,
        puntaje=puntaje,
        evidencia=evidencia
    )


def verificar_fecha_limite(fecha_limite_str: str) -> Tuple[bool, bool, Optional[int]]:
    """
    Verifica si la convocatoria está vigente y si es urgente.
    Retorna: (esta_vigente, es_urgente, dias_restantes)
    """
    if not fecha_limite_str:
        return True, False, None

    try:
        fecha_limite = datetime.strptime(fecha_limite_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            fecha_limite = datetime.strptime(fecha_limite_str, "%d/%m/%Y").date()
        except ValueError:
            return True, False, None

    hoy = date.today()
    dias_restantes = (fecha_limite - hoy).days

    esta_vigente = dias_restantes >= 0
    es_urgente = 0 <= dias_restantes <= DIAS_URGENTE

    return esta_vigente, es_urgente, dias_restantes


def generar_observacion(
    resultado: 'ResultadoMatch',
    conv_notas: str
) -> str:
    """Genera la observación cualitativa del match."""
    partes = []

    # Urgencia
    if resultado.es_urgente:
        partes.append(f"URGENTE: {resultado.dias_restantes} días restantes")

    # Elegibilidad
    if not resultado.es_elegible:
        partes.append("NO ELEGIBLE para esta convocatoria")
        return ". ".join(partes)

    # Nivel general
    if resultado.puntaje_total >= 80:
        partes.append("Alta compatibilidad")
    elif resultado.puntaje_total >= 60:
        partes.append("Compatibilidad media-alta")
    elif resultado.puntaje_total >= 40:
        partes.append("Compatibilidad moderada")
    else:
        partes.append("Compatibilidad baja")

    # Fortalezas
    fortalezas = []
    if resultado.puntaje_proposito >= 25:
        fortalezas.append("temática alineada")
    if resultado.puntaje_tipo_actividad >= 25:
        fortalezas.append("tipo de actividad compatible")
    if resultado.puntaje_valor_vs_monto >= 7:
        fortalezas.append("financiamiento adecuado")

    if fortalezas:
        partes.append(f"Fortalezas: {', '.join(fortalezas)}")

    # Consideraciones de notas adicionales
    notas_norm = normalizar_texto(conv_notas) if conv_notas else ""
    if "contrapartida" in notas_norm:
        partes.append("Requiere contrapartida")
    if "rural" in notas_norm:
        partes.append("Énfasis en componente rural")

    return ". ".join(partes)


def generar_acciones(
    resultado: 'ResultadoMatch',
    valor_estimado: float,
    monto_maximo: float,
    conv_notas: str
) -> str:
    """Genera acciones sugeridas basadas en el análisis."""
    acciones = []

    if not resultado.es_elegible:
        acciones.append("Buscar socio elegible o convocatoria alternativa")
        return "; ".join(acciones)

    # Por puntaje de valor
    if resultado.puntaje_valor_vs_monto <= 5 and valor_estimado > monto_maximo:
        deficit = valor_estimado - monto_maximo
        acciones.append(f"Ajustar presupuesto (-${deficit:,.0f}) o buscar cofinanciamiento")

    # Por elegibilidad parcial
    if resultado.puntaje_elegibilidad <= 7:
        acciones.append("Considerar formar alianza o consorcio para fortalecer elegibilidad")

    # Por región
    if resultado.puntaje_region <= 2:
        acciones.append("Evidenciar alcance geográfico compatible")

    # Por propósito
    if resultado.puntaje_proposito <= 17:
        acciones.append("Reforzar alineación temática en la propuesta")

    # Por notas adicionales
    notas_norm = normalizar_texto(conv_notas) if conv_notas else ""
    if "contrapartida" in notas_norm:
        acciones.append("Preparar contrapartida requerida")
    if "rural" in notas_norm and "rural" not in normalizar_texto(resultado.evidencia_proposito):
        acciones.append("Evidenciar componente rural")
    if "mujeres" in notas_norm or "género" in notas_norm:
        acciones.append("Destacar enfoque de género si aplica")
    if "métricas" in notas_norm or "impacto" in notas_norm:
        acciones.append("Preparar métricas de impacto cuantificables")

    # Urgencia
    if resultado.es_urgente:
        acciones.insert(0, "PRIORIZAR - Fecha límite próxima")

    return "; ".join(acciones) if acciones else "Postular sin ajustes mayores"


def calcular_match(
    idea: Dict[str, Any],
    convocatoria: Dict[str, Any],
    similarity_func=None
) -> Optional[ResultadoMatch]:
    """
    Calcula el match completo entre una idea y una convocatoria.
    Retorna None si la convocatoria ya venció.
    """
    # Verificar vigencia
    fecha_limite = convocatoria.get('fecha_limite', '')
    esta_vigente, es_urgente, dias_restantes = verificar_fecha_limite(fecha_limite)

    if not esta_vigente:
        return None  # Excluir convocatorias vencidas

    # Extraer datos de la idea
    id_idea = idea.get('id_idea', '')
    nombre_idea = idea.get('nombre', '')
    descripcion_idea = idea.get('descripcion', '')
    tags_idea = idea.get('tags', '')
    tipologia_cliente = idea.get('tipologia_cliente', '')
    valor_estimado = float(idea.get('valor_estimado', 0) or 0)
    moneda_idea = idea.get('moneda', 'USD')
    clasificacion = idea.get('clasificacion_idea', '')
    region_idea = idea.get('region', '')
    ambito_idea = idea.get('ambito', '')

    # Extraer datos de la convocatoria
    id_conv = convocatoria.get('id_convocatoria', '')
    nombre_conv = convocatoria.get('nombre', '')
    proposito_conv = convocatoria.get('proposito', '')
    tags_conv = convocatoria.get('tags', '')
    quienes_pueden = convocatoria.get('quienes_pueden_participar', '')
    monto_maximo = float(convocatoria.get('monto_maximo', 0) or 0)
    moneda_conv = convocatoria.get('moneda', 'USD')
    region_conv = convocatoria.get('region', '')
    ambito_conv = convocatoria.get('ambito', '')
    notas_adicionales = convocatoria.get('notas_adicionales', '')

    # Evaluar cada criterio
    res_proposito = evaluar_proposito_tematica(
        nombre_idea, descripcion_idea, tags_idea,
        nombre_conv, proposito_conv, tags_conv, notas_adicionales,
        similarity_func
    )

    res_actividad = evaluar_tipo_actividad(
        clasificacion, descripcion_idea,
        proposito_conv, tags_conv, notas_adicionales
    )

    res_elegibilidad, es_elegible = evaluar_elegibilidad(
        tipologia_cliente, quienes_pueden, notas_adicionales
    )

    res_valor = evaluar_valor_vs_monto(
        valor_estimado, moneda_idea,
        monto_maximo, moneda_conv
    )

    res_region = evaluar_region_alcance(
        region_idea, ambito_idea,
        region_conv, ambito_conv
    )

    # Calcular puntaje total
    if es_elegible:
        puntaje_total = (
            res_proposito.puntaje +
            res_actividad.puntaje +
            res_elegibilidad.puntaje +
            res_valor.puntaje +
            res_region.puntaje
        )
    else:
        puntaje_total = 0

    # Crear resultado
    resultado = ResultadoMatch(
        id_idea=id_idea,
        nombre_idea=nombre_idea,
        id_convocatoria=id_conv,
        nombre_convocatoria=nombre_conv,
        tipologia_cliente=tipologia_cliente,
        puntaje_proposito=res_proposito.puntaje,
        puntaje_tipo_actividad=res_actividad.puntaje,
        puntaje_elegibilidad=res_elegibilidad.puntaje if es_elegible else 0,
        puntaje_valor_vs_monto=res_valor.puntaje,
        puntaje_region=res_region.puntaje,
        puntaje_total=puntaje_total,
        es_elegible=es_elegible,
        es_urgente=es_urgente,
        dias_restantes=dias_restantes,
        observacion_cualitativa="",  # Se llena después
        acciones_sugeridas="",  # Se llena después
        evidencia_proposito=res_proposito.evidencia,
        evidencia_actividad=res_actividad.evidencia,
        evidencia_elegibilidad=res_elegibilidad.evidencia,
        evidencia_valor=res_valor.evidencia,
        evidencia_region=res_region.evidencia,
    )

    # Generar observación y acciones
    resultado.observacion_cualitativa = generar_observacion(resultado, notas_adicionales)
    resultado.acciones_sugeridas = generar_acciones(
        resultado, valor_estimado, monto_maximo, notas_adicionales
    )

    return resultado
