"""
Configuración del sistema de scoring para matching Ideas-Convocatorias.
Define los puntajes máximos, niveles y bandas de mapeo.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

# =============================================================================
# BANDAS DE MAPEO (% de match → Nivel)
# =============================================================================
MAPPING_BANDS: List[Tuple[int, int, int]] = [
    (0, 19, 1),    # Bajo: 0-19% → Nivel 1
    (20, 49, 2),   # Medio-bajo: 20-49% → Nivel 2
    (50, 70, 3),   # Medio: 50-70% → Nivel 3
    (71, 90, 4),   # Medio-alto: 71-90% → Nivel 4
    (91, 100, 5),  # Total: >90% → Nivel 5
]

# =============================================================================
# PUNTAJES POR CRITERIO (Nivel → Puntos)
# =============================================================================
@dataclass
class CriterioConfig:
    nombre: str
    max_puntos: int
    puntos_por_nivel: Dict[int, int]

CRITERIOS = {
    "proposito": CriterioConfig(
        nombre="Propósito / Temática",
        max_puntos=35,
        puntos_por_nivel={1: 0, 2: 10, 3: 17, 4: 25, 5: 35}
    ),
    "tipo_actividad": CriterioConfig(
        nombre="Tipo de Actividad",
        max_puntos=35,
        puntos_por_nivel={1: 0, 2: 10, 3: 17, 4: 25, 5: 35}
    ),
    "elegibilidad": CriterioConfig(
        nombre="Elegibilidad / Tipo de Proponente",
        max_puntos=15,
        puntos_por_nivel={1: 0, 2: 4, 3: 7, 4: 11, 5: 15}
    ),
    "valor_monto": CriterioConfig(
        nombre="Valor vs Monto Máximo",
        max_puntos=10,
        puntos_por_nivel={1: 0, 2: 2, 3: 5, 4: 7, 5: 10}
    ),
    "region": CriterioConfig(
        nombre="Región / Alcance",
        max_puntos=5,
        puntos_por_nivel={1: 0, 2: 1, 3: 2, 4: 3, 5: 5}
    ),
}

# =============================================================================
# MAPEO DE TIPOS DE PROPONENTES
# =============================================================================
TIPO_PROPONENTE_SINONIMOS = {
    "universidad": ["universidades", "universidad", "centros de investigación", "instituciones académicas", "academia"],
    "ong": ["ongs", "ong", "organizaciones sin fines de lucro", "organizaciones de la sociedad civil", "fundaciones"],
    "startup": ["startups", "startup", "emprendimientos", "empresas de base tecnológica", "empresas emergentes"],
    "cooperativa": ["cooperativas", "cooperativa", "asociaciones", "organizaciones de productores", "cooperativas empresariales"],
    "empresa social": ["empresas sociales", "empresa social", "empresas b certificadas", "empresas con impacto"],
    "empresa privada": ["empresas privadas", "empresa privada", "pymes", "empresas", "sector privado"],
    "fundación": ["fundaciones", "fundación", "organizaciones filantrópicas"],
    "gobierno local": ["gobiernos locales", "gobierno local", "municipios", "alcaldías"],
    "comunidad": ["comunidades", "comunidad", "organizaciones comunitarias", "colectivos", "comunidades indígenas", "comunidades locales"],
}

# =============================================================================
# KEYWORDS PARA TIPO DE ACTIVIDAD
# =============================================================================
ACTIVIDAD_KEYWORDS = {
    "prototipo": ["prototipo", "desarrollo tecnológico", "i+d", "investigación", "innovación tecnológica", "mvp"],
    "piloto": ["piloto", "prueba piloto", "validación", "demostración", "escala piloto"],
    "capacitación": ["capacitación", "formación", "entrenamiento", "educación", "talleres", "programa educativo"],
    "consultoría": ["consultoría", "asesoría", "asistencia técnica", "diagnóstico", "estudio"],
    "desarrollo de software": ["software", "aplicación", "app", "plataforma digital", "sistema", "desarrollo de plataforma"],
    "infraestructura": ["infraestructura", "construcción", "instalación", "equipamiento", "centro"],
    "programa": ["programa", "iniciativa", "proyecto", "plan", "aceleración"],
}

# =============================================================================
# OBJETIVOS DE DESARROLLO SOSTENIBLE (ODS)
# =============================================================================
ODS_NOMBRES = {
    "ODS 1": "Fin de la pobreza",
    "ODS 2": "Hambre cero",
    "ODS 3": "Salud y bienestar",
    "ODS 4": "Educación de calidad",
    "ODS 5": "Igualdad de género",
    "ODS 6": "Agua limpia y saneamiento",
    "ODS 7": "Energía asequible y no contaminante",
    "ODS 8": "Trabajo decente y crecimiento económico",
    "ODS 9": "Industria, innovación e infraestructura",
    "ODS 10": "Reducción de las desigualdades",
    "ODS 11": "Ciudades y comunidades sostenibles",
    "ODS 12": "Producción y consumo responsables",
    "ODS 13": "Acción por el clima",
    "ODS 14": "Vida submarina",
    "ODS 15": "Vida de ecosistemas terrestres",
    "ODS 16": "Paz, justicia e instituciones sólidas",
    "ODS 17": "Alianzas para lograr los objetivos",
}

# =============================================================================
# UMBRALES DE URGENCIA (días hasta fecha límite)
# =============================================================================
DIAS_URGENTE = 30  # Marcar como urgente si faltan menos de 30 días

# =============================================================================
# REGIONES DE COLOMBIA
# =============================================================================
REGIONES_COLOMBIA = [
    "antioquia", "cundinamarca", "valle del cauca", "nariño", "cauca",
    "chocó", "boyacá", "bogotá", "medellín", "amazonas", "atlántico",
    "bolívar", "caldas", "caquetá", "casanare", "cesar", "córdoba",
    "guainía", "guaviare", "huila", "la guajira", "magdalena", "meta",
    "norte de santander", "putumayo", "quindío", "risaralda", "san andrés",
    "santander", "sucre", "tolima", "vaupés", "vichada", "arauca"
]

AMBITOS = {
    "local": 1,
    "regional": 2,
    "nacional": 3,
    "internacional": 4,
    "global": 4,
}

# =============================================================================
# CATEGORÍAS TEMÁTICAS PARA MATCHING SEMÁNTICO
# =============================================================================
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
