#!/usr/bin/env python3
"""
Script simplificado para ejecutar el análisis de matching.
No requiere instalación de dependencias pesadas como sentence-transformers.

Uso:
    python run_analysis.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date
import csv
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Configuración
DIAS_URGENTE = 30

# Bandas de mapeo
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

# Puntajes por criterio
PUNTAJES = {
    "proposito": {1: 0, 2: 10, 3: 17, 4: 25, 5: 35},
    "tipo_actividad": {1: 0, 2: 10, 3: 17, 4: 25, 5: 35},
    "elegibilidad": {1: 0, 2: 4, 3: 7, 4: 11, 5: 15},
    "valor_monto": {1: 0, 2: 2, 3: 5, 4: 7, 5: 10},
    "region": {1: 0, 2: 1, 3: 2, 4: 3, 5: 5},
}

# Sinónimos para tipos de proponente
TIPO_SINONIMOS = {
    "universidad": ["universidades", "universidad", "centros de investigación", "instituciones académicas"],
    "ong": ["ongs", "ong", "organizaciones sin fines de lucro", "fundaciones"],
    "startup": ["startups", "startup", "empresas de base tecnológica", "emprendimientos"],
    "cooperativa": ["cooperativas", "cooperativa", "asociaciones", "organizaciones de productores"],
    "empresa social": ["empresas sociales", "empresa social", "empresas b certificadas"],
    "empresa privada": ["empresas privadas", "empresa privada", "pymes", "empresas"],
    "fundación": ["fundaciones", "fundación"],
}

# Keywords para tipo de actividad
ACTIVIDAD_KEYWORDS = {
    "prototipo": ["prototipo", "i+d", "innovación", "tecnológico"],
    "piloto": ["piloto", "prueba", "validación", "demostración"],
    "capacitación": ["capacitación", "formación", "educación", "talleres"],
    "consultoría": ["consultoría", "asesoría", "diagnóstico"],
    "software": ["software", "aplicación", "app", "plataforma", "digital"],
    "infraestructura": ["infraestructura", "construcción", "equipamiento"],
    "programa": ["programa", "iniciativa", "aceleración"],
}

# Categorías temáticas para matching semántico
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


@dataclass
class Resultado:
    id_idea: str
    nombre_idea: str
    id_convocatoria: str
    nombre_convocatoria: str
    tipologia_cliente: str
    puntaje_proposito: int
    puntaje_tipo_actividad: int
    puntaje_elegibilidad: Any  # int o "No elegible"
    puntaje_valor_vs_monto: int
    puntaje_region: int
    puntaje_total: int
    es_elegible: bool
    es_urgente: bool
    dias_restantes: Optional[int]
    observacion_cualitativa: str
    acciones_sugeridas: str


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
    if not fecha_str:
        return True, False, None
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except:
        try:
            fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
        except:
            return True, False, None

    hoy = date.today()
    dias = (fecha - hoy).days
    return dias >= 0, 0 <= dias <= DIAS_URGENTE, dias


def identificar_categorias(texto: str) -> set:
    """Identifica las categorías temáticas presentes en un texto."""
    texto_norm = normalizar(texto)
    categorias = set()
    for categoria, keywords in CATEGORIAS_TEMATICAS.items():
        for kw in keywords:
            if kw in texto_norm:
                categorias.add(categoria)
                break
    return categorias


def evaluar_proposito(idea: Dict, conv: Dict) -> Tuple[int, str]:
    texto_idea = f"{idea.get('nombre', '')} {idea.get('descripcion', '')} {idea.get('tags', '')}"
    texto_conv = f"{conv.get('nombre', '')} {conv.get('proposito', '')} {conv.get('tags', '')} {conv.get('notas_adicionales', '')}"

    # ODS
    ods_idea = extraer_ods(texto_idea)
    ods_conv = extraer_ods(texto_conv)
    ods_comunes = ods_idea & ods_conv

    # Categorías temáticas
    categorias_idea = identificar_categorias(texto_idea)
    categorias_conv = identificar_categorias(texto_conv)
    categorias_comunes = categorias_idea & categorias_conv

    # Keywords directas
    stopwords = {'de', 'la', 'el', 'en', 'y', 'a', 'para', 'con', 'que', 'del', 'los', 'las', 'un', 'una', 'por'}
    palabras_idea = set(normalizar(texto_idea).split()) - stopwords
    palabras_conv = set(normalizar(texto_conv).split()) - stopwords
    palabras_idea = {p for p in palabras_idea if len(p) > 3}
    palabras_conv = {p for p in palabras_conv if len(p) > 3}

    # Calcular porcentaje base por Jaccard
    porcentaje_jaccard = calcular_jaccard(palabras_idea, palabras_conv)

    # Bonus por categorías temáticas comunes (más importante)
    bonus_categorias = len(categorias_comunes) * 18

    # Bonus por ODS comunes
    bonus_ods = len(ods_comunes) * 12

    # Porcentaje final
    porcentaje = porcentaje_jaccard + bonus_categorias + bonus_ods
    porcentaje = min(100, porcentaje)

    nivel = porcentaje_a_nivel(porcentaje)
    puntaje = PUNTAJES["proposito"][nivel]

    # Generar evidencia
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
    clasificacion = normalizar(idea.get('clasificacion_idea', ''))
    desc = normalizar(idea.get('descripcion', ''))
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
    tipo_cliente = normalizar(idea.get('tipologia_cliente', ''))
    quienes = normalizar(conv.get('quienes_pueden_participar', ''))
    notas = normalizar(conv.get('notas_adicionales', ''))

    es_elegible = False
    for tipo_base, sinonimos in TIPO_SINONIMOS.items():
        if tipo_cliente in [tipo_base] + sinonimos:
            for sin in sinonimos:
                if sin in quienes:
                    es_elegible = True
                    break
        if es_elegible:
            break

    # Verificación directa
    if not es_elegible and tipo_cliente in quienes:
        es_elegible = True

    if not es_elegible:
        return 0, False, f"No elegible: {idea.get('tipologia_cliente', '')} no permitido"

    # Determinar nivel
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
    region_idea = normalizar(idea.get('region', ''))
    ambito_idea = normalizar(idea.get('ambito', ''))
    region_conv = normalizar(conv.get('region', ''))
    ambito_conv = normalizar(conv.get('ambito', ''))

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


def calcular_match(idea: Dict, conv: Dict) -> Optional[Resultado]:
    # Verificar vigencia
    vigente, urgente, dias = verificar_fecha(conv.get('fecha_limite', ''))
    if not vigente:
        return None

    # Evaluar criterios
    p_proposito, ev_proposito = evaluar_proposito(idea, conv)
    p_actividad, ev_actividad = evaluar_actividad(idea, conv)
    p_elegibilidad, es_elegible, ev_elegibilidad = evaluar_elegibilidad(idea, conv)
    p_valor, ev_valor = evaluar_valor(idea, conv)
    p_region, ev_region = evaluar_region(idea, conv)

    if es_elegible:
        total = p_proposito + p_actividad + p_elegibilidad + p_valor + p_region
    else:
        total = 0

    # Observación
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

    # Acciones
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

        notas = normalizar(conv.get('notas_adicionales', ''))
        if "contrapartida" in notas:
            acciones.append("Preparar contrapartida")
        if "rural" in notas:
            acciones.append("Destacar componente rural")
        if "mujeres" in notas or "género" in notas:
            acciones.append("Evidenciar enfoque de género")

    return Resultado(
        id_idea=idea.get('id_idea', ''),
        nombre_idea=idea.get('nombre', ''),
        id_convocatoria=conv.get('id_convocatoria', ''),
        nombre_convocatoria=conv.get('nombre', ''),
        tipologia_cliente=idea.get('tipologia_cliente', ''),
        puntaje_proposito=p_proposito,
        puntaje_tipo_actividad=p_actividad,
        puntaje_elegibilidad=p_elegibilidad if es_elegible else "No elegible",
        puntaje_valor_vs_monto=p_valor,
        puntaje_region=p_region,
        puntaje_total=total,
        es_elegible=es_elegible,
        es_urgente=urgente,
        dias_restantes=dias,
        observacion_cualitativa=". ".join(obs_parts),
        acciones_sugeridas="; ".join(acciones) if acciones else "Sin ajustes mayores"
    )


def cargar_csv(ruta: str) -> List[Dict]:
    datos = []
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for enc in encodings:
        try:
            with open(ruta, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalizar nombres de columnas
                    row_norm = {k.lower().strip(): v for k, v in row.items()}
                    datos.append(row_norm)
            return datos
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {ruta}")


def generar_csv(resultados: List[Resultado], ruta: str):
    columnas = [
        'id_idea', 'nombre_idea', 'id_convocatoria', 'nombre_convocatoria',
        'puntaje_proposito', 'puntaje_tipo_actividad', 'puntaje_elegibilidad',
        'puntaje_valor_vs_monto', 'puntaje_region', 'puntaje_total',
        'observacion_cualitativa', 'acciones_sugeridas'
    ]

    os.makedirs(os.path.dirname(ruta) or '.', exist_ok=True)

    with open(ruta, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columnas)

        for r in sorted(resultados, key=lambda x: -x.puntaje_total):
            writer.writerow([
                r.id_idea, r.nombre_idea, r.id_convocatoria, r.nombre_convocatoria,
                r.puntaje_proposito, r.puntaje_tipo_actividad, r.puntaje_elegibilidad,
                r.puntaje_valor_vs_monto, r.puntaje_region, r.puntaje_total,
                r.observacion_cualitativa, r.acciones_sugeridas
            ])


def generar_csvs_por_cliente(resultados: List[Resultado], directorio: str):
    os.makedirs(directorio, exist_ok=True)

    # Agrupar por cliente
    por_cliente = {}
    for r in resultados:
        cliente = r.tipologia_cliente or "Sin_clasificar"
        if cliente not in por_cliente:
            por_cliente[cliente] = []
        por_cliente[cliente].append(r)

    # Generar CSV por cliente
    for cliente, res_cliente in por_cliente.items():
        nombre_archivo = cliente.replace(' ', '_').replace('/', '-')
        ruta = os.path.join(directorio, f"{nombre_archivo}.csv")
        generar_csv(res_cliente, ruta)
        print(f"  - {ruta}: {len(res_cliente)} cruces")


def main():
    print("=" * 60)
    print("ANÁLISIS DE MATCHING IDEAS-CONVOCATORIAS")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Rutas
    ruta_ideas = "data/ideas.csv"
    ruta_convocatorias = "data/convocatorias.csv"

    # Cargar datos
    print("Cargando datos...")
    ideas = cargar_csv(ruta_ideas)
    convocatorias = cargar_csv(ruta_convocatorias)
    print(f"  Ideas: {len(ideas)}")
    print(f"  Convocatorias: {len(convocatorias)}")

    # Ejecutar matching
    print(f"\nAnalizando {len(ideas) * len(convocatorias)} cruces...")
    resultados = []
    excluidos = 0

    for idea in ideas:
        for conv in convocatorias:
            res = calcular_match(idea, conv)
            if res:
                resultados.append(res)
            else:
                excluidos += 1

    print(f"  Cruces válidos: {len(resultados)}")
    print(f"  Excluidos (vencidos): {excluidos}")

    # Estadísticas
    elegibles = [r for r in resultados if r.es_elegible]
    no_elegibles = len(resultados) - len(elegibles)
    urgentes = sum(1 for r in resultados if r.es_urgente)
    alto = sum(1 for r in elegibles if r.puntaje_total >= 70)
    medio = sum(1 for r in elegibles if 40 <= r.puntaje_total < 70)

    print(f"\nEstadísticas:")
    print(f"  Elegibles: {len(elegibles)}")
    print(f"  No elegibles: {no_elegibles}")
    print(f"  Urgentes: {urgentes}")
    print(f"  Alto potencial (≥70): {alto}")
    print(f"  Potencial medio (40-69): {medio}")

    # Top 5
    top5 = sorted(elegibles, key=lambda x: x.puntaje_total, reverse=True)[:5]
    print(f"\nTop 5 mejores matches:")
    for i, r in enumerate(top5, 1):
        urg = " [URGENTE]" if r.es_urgente else ""
        print(f"  {i}. {r.nombre_idea[:35]}... + {r.nombre_convocatoria[:30]}...")
        print(f"     Puntaje: {r.puntaje_total}/100{urg}")

    # Generar CSVs
    print(f"\nGenerando archivos...")
    generar_csv(resultados, "output/consolidado.csv")
    print(f"  - output/consolidado.csv: {len(resultados)} cruces")

    generar_csvs_por_cliente(resultados, "output/por_cliente")

    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)
    print("\nArchivos generados en carpeta 'output/'")
    print("Para exportar a Excel, abra los CSV en Excel y guarde como .xlsx")


if __name__ == '__main__':
    main()
