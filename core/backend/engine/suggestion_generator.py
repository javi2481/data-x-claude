from typing import List


def normalize_suggestions(suggestions: List[str]) -> List[str]:
    """Ensure exactly 3 non-empty suggestions. Truncate or pad with generic fallbacks in Spanish.
    Core remains domain-agnostic; fallbacks are generic exploration prompts.
    """
    cleaned = [s.strip() for s in suggestions if isinstance(s, str) and s.strip()]
    cleaned = cleaned[:3]

    fallbacks = [
        "Profundizá en los factores más influyentes.",
        "Buscá patrones temporales o estacionales.",
        "Identificá outliers y explicá su impacto.",
    ]
    i = 0
    while len(cleaned) < 3 and i < len(fallbacks):
        # Avoid duplicates
        if fallbacks[i] not in cleaned:
            cleaned.append(fallbacks[i])
        i += 1

    # Guarantee exactly 3
    return cleaned[:3]
