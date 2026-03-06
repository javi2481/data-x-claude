def render(template: str, context: dict) -> str:
    """
    Renderiza un template de prompt usando str.format_map(context).
    
    Reglas:
    - Renderiza el template usando str.format_map(context)
    - Si falta una clave en el context: lanza KeyError con mensaje claro indicando qué clave falta
    - Nunca silencia errores ni usa valores default — si falta una clave es un bug del caller
    - No contiene ningún string de prompt — solo renderiza lo que recibe
    - Es una función pura, sin estado, sin dependencias externas
    """
    try:
        return template.format_map(context)
    except KeyError as e:
        raise KeyError(f"Missing required key in prompt context: {e}") from e
