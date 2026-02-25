# Standard Library
from typing import TYPE_CHECKING

# Django
from django.db import models

# Alliance Auth
from allianceauth.eveonline.providers import ObjectNotFound

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
        # Implementation would go here, e.g. using ESI's /universe/names/ endpoint
        # For now, this is a placeholder to show where the logic would be implemented.
        _existing_ids = set(self.filter(id__in=ids).values_list("id", flat=True))
        new_ids = set(ids).difference(_existing_ids)

        if new_ids:
            # Call ESI to resolve new_ids and create EveEntity instances
            response = esi.client.Universe.PostUniverseNames(
                body=list(new_ids)
            ).results()
            if len(response) != len(new_ids):
                raise ObjectNotFound(list(new_ids), "unknown_type")

            new_entities = []

            for entity_data in response:
                new_entities.append(
                    self.model(
                        id=entity_data.id,
                        name=entity_data.name,
                        category=entity_data.category,
                    )
                )
            self.bulk_create(new_entities, batch_size=500, ignore_conflicts=True)
            return EveEntityNameResolver(
                {entity.id: entity.name for entity in new_entities}
            )
        return None
