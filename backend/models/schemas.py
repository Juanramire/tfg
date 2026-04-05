from pydantic import BaseModel


class ValidateRequest(BaseModel):
    selected: list[str]


class PropagateRequest(BaseModel):
    selected: list[str] = []
    deselected: list[str] = []


class PropagateResponse(BaseModel):
    forced: list[str]
    excluded: list[str]
    selectable: list[str]


class ModelInfoResponse(BaseModel):
    satisfiable: bool
    num_configurations: int
    core_features: list[str]
    dead_features: list[str]


class PresupuestoRequest(BaseModel):
    presupuesto: float
    selected: list[str] = []
    deselected: list[str] = []


class PerfilRequest(BaseModel):
    perfil: str
    presupuesto: float | None = None
