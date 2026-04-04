from pydantic import BaseModel, Field


class ProductoSpec(BaseModel):
    """Especificaciones técnicas variables según la categoría del producto."""

    # Procesadores
    nucleos: int | None = None
    hilos: int | None = None
    frecuencia_base: str | None = None
    frecuencia_boost: str | None = None
    tdp: int | None = None

    # RAM
    velocidad: str | None = None
    modulos: str | None = None

    # Almacenamiento
    capacidad: str | None = None
    lectura: str | None = None
    escritura: str | None = None

    # GPU
    vram: str | None = None

    # PSU
    certificacion: str | None = None
    modular: bool | None = None

    # Chasis
    ventiladores_incluidos: int | None = None

    # Refrigeración
    tipo_radiador: str | None = None


class Producto(BaseModel):
    nombre: str
    marca: str
    categoria: str = Field(
        description="Tipo de componente: Procesador, PlacaBase, MemoriaRAM, etc."
    )
    features: list[str] = Field(
        description="Features del modelo UVL que satisface este producto"
    )
    precio: float
    imagen: str = ""
    specs: ProductoSpec = ProductoSpec()
