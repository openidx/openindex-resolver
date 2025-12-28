CONTEXT_MAP = {
    "namespace": "https://openindex.id/contexts/namespace.jsonld",
    "Work": "https://openindex.id/contexts/work.jsonld",
    "Edition": "https://openindex.id/contexts/edition.jsonld",
    "DigitalObject": "https://openindex.id/contexts/digital-object.jsonld"
}

def get_context_for_record(record: dict) -> str | None:
    record_type = record.get("type")
    return CONTEXT_MAP.get(record_type)
