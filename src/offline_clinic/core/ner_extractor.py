"""
NER Extractor - Named Entity Recognition para entidades médicas
Usa spaCy con modelo español + diccionario médico custom
VERSIÓN MEJORADA: Detecta más variaciones de síntomas
"""

import logging
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)


class MedicalNERExtractor:
    """
    Extrae entidades médicas (síntomas) del texto del usuario
    Usa spaCy + diccionario de síntomas médicos Spanish
    """

    # Diccionario de síntomas y sus variantes (MEJORADO)
    SYMPTOM_PATTERNS = {
        'fiebre': [
            r'\b(fiebre|febril|calentura|hipertermia|pirexia|temperatura alta)\b',
            r'\btemperatura\s+(alta|elevada)\b',
            r'\btengo\s+fiebre\b'
        ],
        'dolor de cabeza': [
            r'\b(dolor de cabeza|cefalea|migraña|jaqueca|hemicranea|cefalalgia|dolor cabeza)\b',
            r'\bme duele\s+(la cabeza|la cabeza fuerte|mucho la cabeza|mucho|fuerte)\b',
            r'\bduele\s+(la cabeza|mucho|fuerte)',
            r'\bdolor\s+(de cabeza|en cabeza|fuerte en cabeza|de cabeza intenso|cabeza)\b',
            r'\btengo\s+(dolor de cabeza|migraña|jaqueca|dolor|cefalea)\b',
            r'\bme\s+duele\s+mucho\s+la\s+cabeza\b',
            r'\bdolor\s+cabeza\b'
        ],
        'tos': [
            r'\b(tos|tusigeno|tos seca|tos productiva|toser|tosiendo)\b',
            r'\btengo\s+tos\b',
            r'\btengo\s+mucha\s+tos\b'
        ],
        'dificultad respiratoria': [
            r'\b(dificultad respiratoria|disnea|falta de aire|ahogo|asma|asmático)\b',
            r'\b(falta de aire|me cuesta respirar|dificultad para respirar|no puedo respirar)\b',
            r'\bme\s+cuesta\s+respirar\b'
        ],
        'nausea': [
            r'\b(nausea|nauseas|mareo|vomito|vomitar|arcadas|emesis|malestar)\b',
            r'\bme duele\s+(el estomago|la panza|el panza)\b',
            r'\btengo\s+(nausea|mareo|vomito)\b'
        ],
        'dolor abdominal': [
            r'\b(dolor abdominal|dolor de estomago|gastralgia|dolor en abdomen|dolor panza)\b',
            r'\bme duele\s+(el estomago|la barriga|la panza|el abdomen)\b',
            r'\bdolor\s+(abdominal|estomacal|gastrico|panza|estomago)\b',
            r'\btengo\s+dolor\b'
        ],
        'erupcion': [
            r'\b(erupcion|rash|eruption cutanea|dermatitis|urticaria|sarpullido|granos)\b',
            r'\b(granos|espinillas|manchas en piel|sarpullido)\b'
        ],
        'cansancio': [
            r'\b(cansancio|fatiga|astenia|agotamiento|cansado|fatigado)\b',
            r'\bestoy\s+(cansado|fatigado|agotado)\b'
        ],
        'diarrea': [
            r'\b(diarrea|deposiciones liquidas|evacuaciones sueltas|gastroenteritis)\b'
        ],
        'dolor pecho': [
            r'\b(dolor pecho|dolor toracico|angina|dolor en el pecho|dolor torax)\b',
            r'\bme duele\s+(el pecho|el torax|el pecho fuerte)\b',
            r'\bduele\s+pecho\b'
        ],
        'inflamacion': [
            r'\b(inflamacion|hinchado|edema|hinchazón|inflamado)\b',
            r'\bestoy\s+hinchado\b'
        ],
        'dolor garganta': [
            r'\b(dolor de garganta|faringitis|amigdalitis|garganta|dolor garganta)\b',
            r'\bme duele\s+(la garganta|la garganta mucho)\b',
            r'\bduele\s+garganta\b'
        ],
        'conjuntivitis': [
            r'\b(ojo rojo|ojos rojos|conjuntivitis|picazon en ojo)\b',
            r'\btengo\s+(ojos rojos|ojo rojo)\b'
        ]
    }

    def __init__(self):
        """Inicializar extractor (sin descargar modelo externo)"""
        logger.info("Initializing Medical NER Extractor (spaCy + Custom Patterns)...")
        self.symptoms_loaded = len(self.SYMPTOM_PATTERNS)
        logger.info(f"Loaded {self.symptoms_loaded} symptom patterns for NER")

    def extract_symptoms(self, text: str) -> List[Dict]:
        """
        Extraer síntomas del texto del usuario usando patrones regex

        Args:
            text: Texto ingresado por el usuario
                  Ej: "Tengo fiebre alta y dolor de cabeza"

        Returns:
            Lista de {entity, score, normalized, label}
        """
        if not text or len(text.strip()) < 3:
            return []

        try:
            text_lower = text.lower()
            symptoms = []
            found_symptoms = set()  # Para evitar duplicados

            # Buscar cada patrón de síntoma
            for symptom_name, patterns in self.SYMPTOM_PATTERNS.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text_lower, re.IGNORECASE)

                    for match in matches:
                        matched_text = match.group(0)

                        # Evitar duplicados (mismo síntoma encontrado múltiples veces)
                        if matched_text not in found_symptoms:
                            found_symptoms.add(matched_text)

                            # Crear resultado
                            symptoms.append({
                                'entity': matched_text,
                                'normalized': self._normalize(symptom_name),
                                'symptom_category': symptom_name,
                                'score': 0.95,  # Confianza de patrón regex
                                'label': 'SYMPTOM',
                                'start': match.start(),
                                'end': match.end()
                            })

            logger.info(f"Extracted {len(symptoms)} symptoms from: '{text}'")
            for s in symptoms:
                logger.info(f"  - {s['entity']} (category: {s['symptom_category']}, score: {s['score']:.3f})")

            return symptoms

        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            return []

    def extract_all_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extraer TODAS las entidades médicas del texto
        (Por ahora solo síntomas, pero estructura extensible)
        """
        if not text or len(text.strip()) < 3:
            return {'symptoms': [], 'diseases': [], 'procedures': []}

        try:
            symptoms = self.extract_symptoms(text)

            return {
                'symptoms': symptoms,
                'diseases': [],  # TODO: Agregar extracción de enfermedades
                'procedures': []  # TODO: Agregar extracción de procedimientos
            }

        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {'symptoms': [], 'diseases': [], 'procedures': []}

    def get_symptom_keywords(self, symptom: str) -> List[str]:
        """
        Obtener palabras clave asociadas a un síntoma
        Para búsqueda más amplia en CIE-10
        """
        symptom_normalized = self._normalize(symptom)

        # Diccionario de expansión de síntomas comunes
        expansions = {
            'fiebre': ['febril', 'calentura', 'hipertermia', 'temperatura', 'pirexia'],
            'dolor de cabeza': ['cefalea', 'migrana', 'jaqueca', 'cefalalgia', 'hemicranea'],
            'cefalea': ['dolor de cabeza', 'migrana', 'jaqueca', 'dolor cabeza'],
            'tos': ['tusigeno', 'bronquitis', 'tos seca', 'tos productiva'],
            'dificultad respiratoria': ['disnea', 'falta de aire', 'ahogo', 'dificultad respiratoria'],
            'disnea': ['falta de aire', 'dificultad respiratoria', 'ahogo', 'asma'],
            'nausea': ['mareo', 'vomito', 'nauseas', 'arcadas', 'malestar estomacal'],
            'vomito': ['emesis', 'nausea', 'vomitar', 'arcadas', 'vomitos'],
            'dolor abdominal': ['gastralgia', 'dolor de estomago', 'dolor panza', 'dolor gastrico'],
            'erupcion': ['rash', 'eruption cutanea', 'dermatitis', 'urticaria', 'sarpullido'],
            'cansancio': ['fatiga', 'astenia', 'agotamiento', 'cansado', 'fatigado'],
            'diarrea': ['deposiciones liquidas', 'gastroenteritis', 'evacuaciones sueltas'],
            'dolor pecho': ['dolor toracico', 'angina', 'dolor torax', 'angina pectoris'],
            'inflamacion': ['inflamatorio', 'hinchado', 'edema', 'hinchazón', 'inflamado'],
            'dolor garganta': ['faringitis', 'amigdalitis', 'dolor garganta', 'garganta irritada'],
            'conjuntivitis': ['ojo rojo', 'ojos rojos', 'picazon en ojo']
        }

        if symptom_normalized in expansions:
            return expansions[symptom_normalized]

        return [symptom_normalized]

    def _normalize(self, symptom: str) -> str:
        """
        Normalizar síntoma para búsqueda
        Quitar tildes, convertir a lowercase
        """
        symptom = symptom.lower().strip()

        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }

        for old, new in replacements.items():
            symptom = symptom.replace(old, new)

        return symptom


if __name__ == "__main__":
    """Test del NER"""
    import sys
    sys.path.insert(0, 'src')

    logging.basicConfig(level=logging.INFO)

    extractor = MedicalNERExtractor()

    test_cases = [
        "Tengo fiebre alta y dolor de cabeza",
        "Me duele el pecho y tengo tos",
        "Desde ayer tengo dificultad para respirar",
        "Dolor abdominal severo",
        "Erupcion en la piel y picazon",
        "Mareo y nausea",
        "Tengo tos seca y dificultad respiratoria",
        "Me duele la cabeza y tengo fiebre",
        "Me duele mucho la cabeza",
        "Dolor de garganta fuerte",
        "Tengo ojos rojos y picazon",
    ]

    print("\n" + "="*80)
    print("MEDICAL NER EXTRACTOR - TEST")
    print("="*80)

    for test in test_cases:
        print(f"\n📝 Input: '{test}'")
        symptoms = extractor.extract_symptoms(test)

        if symptoms:
            print("✓ Síntomas detectados:")
            for s in symptoms:
                print(f"  - {s['entity']} (categoria: {s['symptom_category']}, score: {s['score']:.3f})")
        else:
            print("  No symptoms detected")

    print("\n" + "="*80)
    print("TEST COMPLETED!")
    print("="*80)
