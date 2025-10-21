from beanie.odm.fields import IndexedAnnotation
from pydantic import BaseModel
from pymongo import IndexModel


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
    settings_indexes = getattr(getattr(model, "Settings", None), "indexes", [])
    for idx in settings_indexes:
        # Format 1: Single string (field name)
        if isinstance(idx, str):
            indexes.append(IndexInfo(
                field=idx,
                direction=1,
                unique=False,
                sparse=False
            ))
        # Format 3: pymongo.IndexModel
        elif isinstance(idx, IndexModel):
            # IndexModel has .document attribute with the keys
            keys = idx.document.get("key", {})
            kwargs = idx.document.get("unique", False)
            for field, direction in keys.items():
                indexes.append(IndexInfo(
                    field=field,
                    direction=direction,
                    unique=kwargs,
                    sparse=idx.document.get("sparse", False)
                ))
        # Format 2: List of (field, direction) tuples
        elif isinstance(idx, list):
            for item in idx:
                if isinstance(item, tuple) and len(item) >= 2:
                    field, direction = item[0], item[1]
                    indexes.append(IndexInfo(
                        field=field,
                        direction=direction,
                        unique=False,
                        sparse=False
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
