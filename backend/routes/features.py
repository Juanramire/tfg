from fastapi import APIRouter, HTTPException

from models.schemas import (
    ValidateRequest,
    PropagateRequest,
    PropagateResponse,
    ModelInfoResponse,
)
from services.flamapy_service import flamapy_service

router = APIRouter(prefix="/api/features", tags=["features"])


@router.get("/tree")
def get_feature_tree():
    """Return the feature model as a nested tree structure."""
    return flamapy_service.get_feature_tree()


@router.get("/info", response_model=ModelInfoResponse)
def get_model_info():
    """Return summary info about the feature model."""
    return ModelInfoResponse(
        satisfiable=flamapy_service.is_satisfiable(),
        num_configurations=flamapy_service.configurations_number(),
        core_features=flamapy_service.core_features(),
        dead_features=flamapy_service.dead_features(),
    )


@router.post("/validate")
def validate_configuration(request: ValidateRequest):
    """Check if a partial configuration can lead to a valid full configuration."""
    unknown = set(request.selected) - flamapy_service.feature_names
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Features desconocidas: {sorted(unknown)}",
        )
    valid = flamapy_service.validate_configuration(request.selected)
    return {"valid": valid}


@router.post("/propagate", response_model=PropagateResponse)
def propagate(request: PropagateRequest):
    """Given selected and deselected features, propagate constraints.

    Returns which features are forced, excluded, and still selectable.
    """
    all_provided = set(request.selected) | set(request.deselected)
    unknown = all_provided - flamapy_service.feature_names
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Features desconocidas: {sorted(unknown)}",
        )
    overlap = set(request.selected) & set(request.deselected)
    if overlap:
        raise HTTPException(
            status_code=400,
            detail=f"Features en ambas listas: {sorted(overlap)}",
        )
    result = flamapy_service.propagate(request.selected, request.deselected)
    return result
