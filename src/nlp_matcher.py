"""
Módulo de NLP para matching semántico usando embeddings.
Proporciona funciones de similitud basadas en sentence-transformers.
"""

import warnings
from typing import List, Optional, Dict, Tuple
from functools import lru_cache
import numpy as np

# Flag para indicar si embeddings están disponibles
EMBEDDINGS_DISPONIBLES = False
modelo_embeddings = None

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    EMBEDDINGS_DISPONIBLES = True
except ImportError:
    warnings.warn(
        "sentence-transformers no está instalado. "
        "El matching usará métodos basados en keywords. "
        "Para mejor precisión, instale: pip install sentence-transformers"
    )


def inicializar_modelo(nombre_modelo: str = "paraphrase-multilingual-MiniLM-L12-v2") -> bool:
    """
    Inicializa el modelo de embeddings.

    Args:
        nombre_modelo: Nombre del modelo de sentence-transformers a usar.
                      Default es multilingüe para español.

    Returns:
        True si el modelo se cargó correctamente, False en caso contrario.
    """
    global modelo_embeddings, EMBEDDINGS_DISPONIBLES

    if not EMBEDDINGS_DISPONIBLES:
        return False

    try:
        modelo_embeddings = SentenceTransformer(nombre_modelo)
        return True
    except Exception as e:
        warnings.warn(f"Error cargando modelo de embeddings: {e}")
        EMBEDDINGS_DISPONIBLES = False
        return False


@lru_cache(maxsize=1000)
def obtener_embedding(texto: str) -> Optional[np.ndarray]:
    """
    Obtiene el embedding de un texto.
    Usa cache para evitar recalcular embeddings repetidos.

    Args:
        texto: Texto a convertir en embedding

    Returns:
        Vector numpy con el embedding o None si no está disponible
    """
    global modelo_embeddings

    if not EMBEDDINGS_DISPONIBLES or modelo_embeddings is None:
        return None

    try:
        embedding = modelo_embeddings.encode(texto, convert_to_numpy=True)
        return embedding
    except Exception:
        return None


def calcular_similitud_semantica(texto1: str, texto2: str) -> float:
    """
    Calcula la similitud semántica entre dos textos usando embeddings.

    Args:
        texto1: Primer texto
        texto2: Segundo texto

    Returns:
        Porcentaje de similitud (0-100)
    """
    if not EMBEDDINGS_DISPONIBLES or modelo_embeddings is None:
        return -1  # Indicador de que no está disponible

    emb1 = obtener_embedding(texto1)
    emb2 = obtener_embedding(texto2)

    if emb1 is None or emb2 is None:
        return -1

    # Calcular similitud del coseno
    similitud = cosine_similarity(
        emb1.reshape(1, -1),
        emb2.reshape(1, -1)
    )[0][0]

    # Convertir a porcentaje (cosine similarity va de -1 a 1)
    porcentaje = ((similitud + 1) / 2) * 100

    return porcentaje


def calcular_similitud_batch(
    textos_ideas: List[str],
    textos_convocatorias: List[str]
) -> Optional[np.ndarray]:
    """
    Calcula matriz de similitud entre listas de textos.

    Args:
        textos_ideas: Lista de textos de ideas
        textos_convocatorias: Lista de textos de convocatorias

    Returns:
        Matriz numpy de similitudes (ideas x convocatorias)
    """
    if not EMBEDDINGS_DISPONIBLES or modelo_embeddings is None:
        return None

    try:
        emb_ideas = modelo_embeddings.encode(textos_ideas, convert_to_numpy=True)
        emb_convocatorias = modelo_embeddings.encode(textos_convocatorias, convert_to_numpy=True)

        # Calcular matriz de similitud
        matriz_similitud = cosine_similarity(emb_ideas, emb_convocatorias)

        # Convertir a porcentaje
        matriz_porcentaje = ((matriz_similitud + 1) / 2) * 100

        return matriz_porcentaje
    except Exception as e:
        warnings.warn(f"Error calculando similitud batch: {e}")
        return None


class MatcherSemantico:
    """
    Clase para realizar matching semántico con cache y optimizaciones.
    """

    def __init__(self, nombre_modelo: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Inicializa el matcher semántico.

        Args:
            nombre_modelo: Nombre del modelo de embeddings a usar
        """
        self.modelo_nombre = nombre_modelo
        self.modelo_cargado = False
        self._cache_embeddings: Dict[str, np.ndarray] = {}

    def cargar_modelo(self) -> bool:
        """Carga el modelo de embeddings."""
        self.modelo_cargado = inicializar_modelo(self.modelo_nombre)
        return self.modelo_cargado

    def _get_embedding_cached(self, texto: str) -> Optional[np.ndarray]:
        """Obtiene embedding con cache local."""
        if texto in self._cache_embeddings:
            return self._cache_embeddings[texto]

        emb = obtener_embedding(texto)
        if emb is not None:
            self._cache_embeddings[texto] = emb
        return emb

    def similitud(self, texto1: str, texto2: str) -> float:
        """
        Calcula similitud entre dos textos.

        Returns:
            Porcentaje de similitud (0-100) o -1 si no disponible
        """
        if not self.modelo_cargado:
            return -1

        return calcular_similitud_semantica(texto1, texto2)

    def encontrar_mejores_matches(
        self,
        texto_query: str,
        textos_candidatos: List[str],
        top_k: int = 5
    ) -> List[Tuple[int, float]]:
        """
        Encuentra los mejores matches para un texto query.

        Args:
            texto_query: Texto a buscar
            textos_candidatos: Lista de textos candidatos
            top_k: Número de mejores resultados a retornar

        Returns:
            Lista de tuplas (índice, similitud)
        """
        if not self.modelo_cargado or not textos_candidatos:
            return []

        similitudes = []
        for i, texto in enumerate(textos_candidatos):
            sim = self.similitud(texto_query, texto)
            if sim >= 0:
                similitudes.append((i, sim))

        # Ordenar por similitud descendente
        similitudes.sort(key=lambda x: x[1], reverse=True)

        return similitudes[:top_k]

    def limpiar_cache(self):
        """Limpia el cache de embeddings."""
        self._cache_embeddings.clear()
        obtener_embedding.cache_clear()


# Función de conveniencia para usar como callback en scoring
def crear_funcion_similitud() -> Optional[callable]:
    """
    Crea una función de similitud para usar en el módulo de scoring.

    Returns:
        Función de similitud o None si embeddings no están disponibles
    """
    if not EMBEDDINGS_DISPONIBLES:
        return None

    if not inicializar_modelo():
        return None

    def similitud_func(texto1: str, texto2: str) -> float:
        sim = calcular_similitud_semantica(texto1, texto2)
        return sim if sim >= 0 else 0

    return similitud_func


# Sinonimos y expansión semántica para keywords
SINONIMOS_TEMATICOS = {
    # Medio ambiente
    "medio ambiente": ["ambiental", "ecológico", "verde", "sostenible", "sustentable"],
    "cambio climático": ["clima", "calentamiento global", "emisiones", "carbono"],
    "biodiversidad": ["especies", "fauna", "flora", "ecosistemas"],

    # Tecnología
    "tecnología": ["digital", "tech", "innovación tecnológica", "tic"],
    "iot": ["internet de las cosas", "sensores", "conectividad"],
    "inteligencia artificial": ["ia", "machine learning", "ml", "ai"],

    # Social
    "inclusión": ["inclusivo", "equidad", "acceso", "vulnerable"],
    "género": ["mujeres", "femenino", "igualdad de género", "equidad de género"],
    "educación": ["formación", "capacitación", "aprendizaje", "enseñanza"],

    # Económico
    "emprendimiento": ["startup", "empresa", "negocio", "emprendedor"],
    "economía circular": ["reciclaje", "reutilización", "residuos", "circular"],
    "agricultura": ["agro", "agrícola", "cultivo", "rural"],
}


def expandir_texto_con_sinonimos(texto: str) -> str:
    """
    Expande un texto agregando sinónimos relevantes.
    Útil para mejorar el matching cuando no hay embeddings.

    Args:
        texto: Texto original

    Returns:
        Texto expandido con sinónimos
    """
    texto_lower = texto.lower()
    expansiones = []

    for termino, sinonimos in SINONIMOS_TEMATICOS.items():
        if termino in texto_lower:
            expansiones.extend(sinonimos)
        for sinonimo in sinonimos:
            if sinonimo in texto_lower:
                expansiones.append(termino)
                break

    if expansiones:
        return f"{texto} {' '.join(set(expansiones))}"
    return texto
