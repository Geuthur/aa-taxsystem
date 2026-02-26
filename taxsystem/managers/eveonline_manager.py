# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models

# AA TaxSystem
from taxsystem.providers import esi

if TYPE_CHECKING:
    # AA TaxSystem
    from taxsystem.models.general import EveEntity


class EveEntityNameResolver:
    """
    Container with a mapping between entity Ids and entity names and a performant API
    """

    def __init__(self, names_map: dict[int, str]) -> None:
        self._names_map = names_map

    def to_name(self, eve_id: int) -> str:
        """Resolved an entity ID to a name

        Args:
            eve_id: ID of the Eve entity to resolve

        Returns:
            name for corresponding entity ID if known else an empty string
        """
        try:
            name = self._names_map[eve_id]
        except KeyError:
            name = ""

        return name


class EveEntityManager(models.Manager["EveEntity"]):
    def bulk_resolve_names(self, ids: list[int]) -> EveEntityNameResolver:
        """Bulk resolve Eve IDs to names and categories using ESI."""
        if not ids:
            return EveEntityNameResolver({})

        names_map = {
            entity.id: entity.name
            for entity in self.filter(id__in=ids).only("id", "name")
        }
        new_ids = set(ids).difference(names_map.keys())

        if new_ids:
            response = esi.client.Universe.PostUniverseNames(
                body=list(new_ids)
            ).results()
            new_entities = []

            for entity_data in response:
                new_entities.append(
                    self.model(
                        id=entity_data.id,
                        name=entity_data.name,
                        category=entity_data.category,
                    )
                )
                names_map[entity_data.id] = entity_data.name

            if new_entities:
                self.bulk_create(new_entities, batch_size=500, ignore_conflicts=True)
        return EveEntityNameResolver(names_map)
