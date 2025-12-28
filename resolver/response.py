from copy import deepcopy
from resolver.contexts import get_context_for_record

def wrap_record(record: dict, include_context: bool = False) -> dict:
    response = deepcopy(record)

    if include_context:
        context_url = get_context_for_record(record)
        if context_url:
            response["@context"] = context_url

    return response
