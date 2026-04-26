"""
Semantic Search Engine - MODELO MEDICO EN ESPANOL
Modelo: PlanTL-GOB-ES/roberta-base-biomedical-clinical-es
Entrenado por Gobierno de Espana en textos clinicos espanoles
"""

import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class MedicalSemanticSearchEngine:
    """
    Motor de busqueda semantica MEDICO en espanol
    Usa RoBERTa biomedical-clinical-es (PlanTL Gobierno de Espana)
    """

    def __init__(
        self,
        catalog_manager,
        model_name: str = "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es",
        cache_dir: str = ".cache/medical_search"
    ):
        self.catalog = catalog_manager
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.tokenizer = None
        self.model = None
        self.index = None
        self.code_list = []
        self.descriptions = {}

        self._initialize()

    def _initialize(self):
        """Inicializar modelo y crear/cargar indice"""
        logger.info("Initializing Medical Semantic Search Engine...")
        logger.info(f"Model: {self.model_name}")

        self._load_model()

        index_path = self.cache_dir / "faiss_index.bin"
        metadata_path = self.cache_dir / "metadata.pkl"

        if index_path.exists() and metadata_path.exists():
            logger.info("Loading pre-computed index from cache...")
            self._load_index(index_path, metadata_path)
        else:
            logger.info("Creating index (first time, ~3-4 minutes)...")
            self._create_index()
            self._save_index(index_path, metadata_path)

        logger.info(f"Medical Search ready with {len(self.code_list)} CIE-10 codes")

    def _load_model(self):
        """Cargar modelo RoBERTa biomedical en espanol"""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch

            logger.info("Downloading/loading medical model...")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.eval()

            logger.info("Medical model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load medical model: {e}")
            raise

    def _encode_texts(self, texts: List[str], batch_size: int = 16) -> np.ndarray:
        """Generar embeddings usando el modelo medico"""
        import torch

        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Tokenize
            inputs = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors='pt'
            )

            # Generate embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Mean pooling sobre tokens (excluyendo padding)
                attention_mask = inputs['attention_mask'].unsqueeze(-1)
                embeddings = (outputs.last_hidden_state * attention_mask).sum(dim=1)
                embeddings = embeddings / attention_mask.sum(dim=1)

                # Normalizar para cosine similarity
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

                all_embeddings.append(embeddings.numpy())

            # Log progress
            current_batch = (i // batch_size) + 1
            if current_batch % 50 == 0 or current_batch == total_batches:
                logger.info(f"  Processed batch {current_batch}/{total_batches}")

        return np.vstack(all_embeddings)

    def _create_index(self):
        """Crear indice FAISS desde cero"""
        import faiss

        all_codes = self.catalog.cie10_loader.codes_dict

        texts = []
        codes = []

        for code, description in all_codes.items():
            texts.append(description)
            codes.append(code)
            self.descriptions[code] = description

        logger.info(f"Encoding {len(texts)} CIE-10 codes with medical model...")
        logger.info("This will take ~3-4 minutes (only first time)")

        # Generar embeddings
        embeddings = self._encode_texts(texts)

        # Crear indice FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype('float32'))

        self.code_list = codes

        logger.info(f"FAISS index created: {len(codes)} vectors, {dimension} dimensions")

    def _save_index(self, index_path: Path, metadata_path: Path):
        """Guardar indice y metadata"""
        import faiss

        faiss.write_index(self.index, str(index_path))

        metadata = {
            'code_list': self.code_list,
            'descriptions': self.descriptions,
            'model_name': self.model_name
        }
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        logger.info(f"Index saved to {self.cache_dir}")

    def _load_index(self, index_path: Path, metadata_path: Path):
        """Cargar indice pre-calculado"""
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
        min_score: float = 0.5
    ) -> List[Dict]:
        """
        Busqueda por similitud semantica medica

        Args:
            query: Sintomas (ej: "dolor de cabeza")
            top_k: Maximo resultados
            min_score: Score minimo (0-1)
        """
        if not self.model or not self.index:
            raise RuntimeError("Search engine not initialized")

        # Generar embedding del query
        query_embedding = self._encode_texts([query])

        # Buscar en FAISS
        scores, indices = self.index.search(
            query_embedding.astype('float32'),
            top_k
        )

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
        min_score: float = 0.5
    ) -> List[Dict]:
        """Busqueda con filtros (TODO: implementar filtrado real)"""
        results = self.search(query, top_k=top_k, min_score=min_score)
        return results


if __name__ == "__main__":
    """Test"""
    import sys
    sys.path.insert(0, 'src')

    logging.basicConfig(level=logging.INFO)

    from offline_clinic.core.excel_loader_minsa import CatalogManager

    print("\n" + "="*80)
    print("MEDICAL SEMANTIC SEARCH - TEST")
    print("Modelo: roberta-base-biomedical-clinical-es")
    print("="*80)

    catalog = CatalogManager(
        cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
        procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
    )

    engine = MedicalSemanticSearchEngine(catalog)

    test_queries = [
        "dolor de cabeza",
        "asma",
        "fiebre alta",
        "presion arterial alta",
        "azucar alta en sangre"
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: '{query}'")
        print("="*80)

        results = engine.search(query, top_k=5)

        if not results:
            print("  No results found")
        else:
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['code']}: {r['description'][:70]}...")
                print(f"   Score: {r['score']:.3f}")

    print("\nTEST COMPLETED!")
