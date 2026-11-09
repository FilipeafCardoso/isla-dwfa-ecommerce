"""Ajustes ao schema OpenAPI gerado pelo drf-spectacular."""


def require_response_fields(result, generator, request, public):
    """Nas respostas, todos os campos são obrigatórios.

    O DRF serializa sempre todos os `fields`; o drf-spectacular só marca como
    `required` os read_only, e campos com default no modelo (ex.: `stock`) saíam
    opcionais na resposta. Com COMPONENT_SPLIT_REQUEST, os componentes de pedido
    terminam em "Request" e ficam como estão.
    """
    for name, component in result.get("components", {}).get("schemas", {}).items():
        properties = component.get("properties")
        if properties and not name.endswith("Request"):
            component["required"] = list(properties)
    return result
