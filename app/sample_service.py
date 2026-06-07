import json
import random
from functools import lru_cache

from app.config import SAMPLE_INPUTS_PATH


@lru_cache(maxsize=1)
def load_sample_inputs() -> list[dict]:
    """Charge les exemples d'entrées générés à partir du dataset."""
    with open(SAMPLE_INPUTS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_random_sample_input() -> dict:
    """Retourne un exemple aléatoire compatible avec /predict."""
    samples = load_sample_inputs()

    if not samples:
        raise ValueError("Aucun exemple disponible dans sample_inputs.json.")

    return random.choice(samples)
