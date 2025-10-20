from beanie.odm.fields import IndexedAnnotation
from pydantic import BaseModel


class IndexInfo(BaseModel):
    field: str
    direction: int = 1
    unique: bool = False
    sparse: bool = False

def get_model_indexes(model: type[BaseModel]) -> list[IndexInfo]:
    """
    Return a list of IndexInfo models describing indexes in a Beanie model.
    """
    indexes = []

    # Indexed fields from field metadata
    for field_name, field in model.model_fields.items():
        for meta in field.metadata:
            if isinstance(meta, IndexedAnnotation):
                direction = meta._indexed[0] if meta._indexed else 1
                options = meta._indexed[1] if meta._indexed and len(meta._indexed) > 1 else {}
                indexes.append(IndexInfo(
                    field=field_name,
                    direction=direction,
                    unique=options.get("unique", False),
                    sparse=options.get("sparse", False)
                ))

    # Indexes from Settings.indexes
    for idx in getattr(model.Settings, "indexes", []):
        for field, direction_or_opts in idx:
            if isinstance(direction_or_opts, dict):
                direction = direction_or_opts.get("direction", 1)
                options = direction_or_opts
            else:
                direction = direction_or_opts
                options = {}
            indexes.append(IndexInfo(
                field=field,
                direction=direction,
                unique=options.get("unique", False),
                sparse=options.get("sparse", False)
            ))

    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_indexes = []
    for idx in indexes:
        key = (idx.field, idx.direction)
        if key not in seen:
            unique_indexes.append(idx)
            seen.add(key)

    return unique_indexes
