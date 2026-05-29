import logging
from pathlib import Path

from flamapy.metamodels.fm_metamodel.transformations import UVLReader
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat
from flamapy.metamodels.pysat_metamodel.operations import (
    PySATSatisfiable,
    PySATSatisfiableConfiguration,
    PySATCoreFeatures,
    PySATDeadFeatures,
    PySATConfigurationsNumber,
)
from flamapy.core.discover import Configuration

logger = logging.getLogger(__name__)

UVL_PATH = Path(__file__).resolve().parent.parent / "data" / "modelo.uvl"


class FlamapyService:
    def __init__(self, uvl_path: Path = UVL_PATH):
        self._fm = UVLReader(str(uvl_path)).transform()
        self._sat = FmToPysat(self._fm).transform()

        self._feature_names: set[str] = {f.name for f in self._fm.get_features()}
        self._feature_map: dict[str, object] = {
            f.name: f for f in self._fm.get_features()
        }
        self._cached_num_configs: int | None = None

        logger.info(
            "FlamaPy model loaded: %d features, %d constraints",
            len(self._feature_names),
            len(self._fm.get_constraints()),
        )

    @property
    def feature_names(self) -> set[str]:
        return self._feature_names

    def get_feature_tree(self) -> dict:
        """Devuelve el modelo de características como un dict anidado para el frontend."""
        return self._feature_to_dict(self._fm.root)

    def is_satisfiable(self) -> bool:
        op = PySATSatisfiable()
        op.execute(self._sat)
        return op.get_result()

    def core_features(self) -> list[str]:
        op = PySATCoreFeatures()
        op.execute(self._sat)
        return op.get_result()

    def dead_features(self) -> list[str]:
        op = PySATDeadFeatures()
        op.execute(self._sat)
        return op.get_result()

    def configurations_number(self) -> int:
        if self._cached_num_configs is None:
            op = PySATConfigurationsNumber()
            op.execute(self._sat)
            self._cached_num_configs = op.get_result()
        return self._cached_num_configs

    def validate_configuration(self, selected: list[str]) -> bool:
        """Comprueba si una configuración parcial (features seleccionadas) puede derivar en una configuración válida completa."""
        elements = {name: True for name in selected}
        config = Configuration(elements)
        op = PySATSatisfiableConfiguration()
        op.set_configuration(config)
        op.execute(self._sat)
        return op.get_result()

    def propagate(self, selected: list[str], deselected: list[str]) -> dict:
        """Dado un conjunto de features seleccionadas/deseleccionadas, determina qué features
        están forzadas a verdadero, forzadas a falso o aún son seleccionables.

        Devuelve un dict con las claves: forced, excluded, selectable.
        """
        forced = set(selected)
        excluded = set(deselected)
        selectable = set()

        remaining = self._feature_names - forced - excluded

        for fname in remaining:
            # ¿Se puede seleccionar esta feature?
            can_select = self.validate_configuration(list(forced | {fname}))
            # ¿Se puede deseleccionar esta feature?
            test_deselected = {name: True for name in forced}
            test_deselected[fname] = False
            config = Configuration(test_deselected)
            op = PySATSatisfiableConfiguration()
            op.set_configuration(config)
            op.execute(self._sat)
            can_deselect = op.get_result()

            if can_select and not can_deselect:
                forced.add(fname)
            elif not can_select and can_deselect:
                excluded.add(fname)
            elif not can_select and not can_deselect:
                excluded.add(fname)
            else:
                selectable.add(fname)

        return {
            "forced": sorted(forced),
            "excluded": sorted(excluded),
            "selectable": sorted(selectable),
        }

    def _feature_to_dict(self, feature) -> dict:
        """Convierte recursivamente una Feature en un dict."""
        children = []
        for relation in feature.get_relations():
            group_type = self._relation_type(relation)
            group_children = [
                self._feature_to_dict(child) for child in relation.children
            ]
            children.append({"type": group_type, "children": group_children})

        return {
            "name": feature.name,
            "is_abstract": feature.is_abstract,
            "groups": children,
        }

    @staticmethod
    def _relation_type(relation) -> str:
        if relation.is_alternative():
            return "alternative"
        if relation.is_or():
            return "or"
        if relation.is_mandatory():
            return "mandatory"
        if relation.is_optional():
            return "optional"
        return "unknown"


flamapy_service = FlamapyService()
