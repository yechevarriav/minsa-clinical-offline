"""
Semantic Search Engine - ACTUALIZADO con mejor modelo para español
Modelo: distiluse-base-multilingual-cased-v2
"""

import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """
    Motor de busqueda semantica para CIE-10
    Optimizado para español médico
    """

    def __init__(
        self,
        catalog_manager,
        model_name: str = "sentence-transformers/distiluse-base-multilingual-cased-v2",
        cache_dir: str = ".cache/semantic_search_v2"  # Nuevo cache para nuevo modelo
    ):
        """
        Args:
            catalog_manager: CatalogManager con CIE-10 cargados
            model_name: Modelo de embeddings (optimizado para español)
            cache_dir: Directorio para guardar índice
        """
        self.catalog = catalog_manager
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.model = None
        self.index = None
        self.code_list = []
        self.descriptions = {}

        self._initialize()

    def _initialize(self):
        """Inicializar modelo y crear/cargar índice"""
        logger.info("Initializing Semantic Search Engine (distiluse-multilingual)...")

        # 1. Cargar modelo
        self._load_embedding_model()

        # 2. Crear o cargar índice
        index_path = self.cache_dir / "faiss_index.bin"
        metadata_path = self.cache_dir / "metadata.pkl"

        if index_path.exists() and metadata_path.exists():
            logger.info("Loading pre-computed FAISS index from cache...")
            self._load_index(index_path, metadata_path)
        else:
            logger.info("Creating FAISS index with new model (first time, ~2-3 minutes)...")
            self._create_index()
            self._save_index(index_path, metadata_path)

        logger.info(f"Semantic Search ready with {len(self.code_list)} CIE-10 codes")

    def _load_embedding_model(self):
        """Cargar modelo sentence-transformers"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _create_index(self):
        """Crear índice FAISS"""
        import faiss

        all_codes = self.catalog.cie10_loader.codes_dict

        texts = []
        codes = []

        for code, description in all_codes.items():
            texts.append(description)
            codes.append(code)
            self.descriptions[code] = description

        logger.info(f"Creating embeddings for {len(texts)} CIE-10 codes...")

        # Generar embeddings (batch)
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalizar automáticamente
        )

        # Crear índice FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (cosine sim)
        self.index.add(embeddings.astype('float32'))

        self.code_list = codes

        logger.info(f"FAISS index created with {len(codes)} vectors (dimension: {dimension})")

    def _save_index(self, index_path: Path, metadata_path: Path):
        """Guardar índice"""
        import faiss

        faiss.write_index(self.index, str(index_path))

        metadata = {
            'code_list': self.code_list,
            'descriptions': self.descriptions,
            'model_name': self.model_name
        }
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        logger.info(f"Index saved to {index_path}")

    def _load_index(self, index_path: Path, metadata_path: Path):
        """Cargar índice pre-calculado"""
        import faiss

        self.index = faiss.read_index(str(index_path))

        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)

        self.code_list = metadata['code_list']
        self.descriptions = metadata['descriptions']

        logger.info(f"Index loaded: {len(self.code_list)} codes")

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.3
    ) -> List[Dict]:
        """
        Buscar por similitud semántica

        Args:
            query: Síntomas (ej: "dolor de cabeza intenso")
            top_k: Máximo resultados
            min_score: Score mínimo (0-1)

        Returns:
            Lista de {code, description, score}
        """
        if not self.model or not self.index:
            raise RuntimeError("Search engine not initialized")

        # Generar embedding
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Buscar en FAISS
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)

        # Procesar resultados
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if score >= min_score:
                code = self.code_list[idx]
                results.append({
                    'code': code,
                    'description': self.descriptions[code],
                    'score': float(score),
                    'relevance': float(score)
                })

        return results

    def search_with_filters(
        self,
        query: str,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
        top_k: int = 10,
        min_score: float = 0.35  # Threshold un poco más alto
    ) -> List[Dict]:
        """Búsqueda con filtros"""
        results = self.search(query, top_k=top_k * 2, min_score=min_score)

        # TODO: Filtrado por edad/sexo

        return results[:top_k]


if __name__ == "__main__":
    """Test con nuevo modelo"""
    import sys
    sys.path.insert(0, 'src')

    logging.basicConfig(level=logging.INFO)

    from offline_clinic.core.excel_loader_minsa import CatalogManager

    print("\n" + "="*80)
    print("SEMANTIC SEARCH - MODELO MEJORADO PARA ESPAÑOL")
    print("Modelo: distiluse-base-multilingual-cased-v2")
    print("="*80)

    catalog = CatalogManager(
        cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
        procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
    )

    engine = SemanticSearchEngine(catalog)

    # Tests
    test_queries = [
        "dolor de cabeza intenso",
        "dificultad para respirar",
        "azucar alta en la sangre",
        "presion arterial elevada",
        "tos persistente"
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: '{query}'")
        print("="*80)

        results = engine.search(query, top_k=5, min_score=0.35)

        if not results:
            print("  ⚠️ No se encontraron resultados (score < 0.35)")
        else:
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['code']}: {r['description'][:70]}...")
                print(f"   Score: {r['score']:.3f}")

    print("\n" + "="*80)
    print("TEST COMPLETED!")
    print("="*80)
