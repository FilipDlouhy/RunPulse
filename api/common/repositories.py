"""
Generic repository base for data access, wrapping Django ORM operations.
"""
from django.db.models import Model


class BaseRepository[T: Model]:
    """Generic CRUD operations for Django models."""

    model: type[T]

    def get_by_id(self, pk) -> T | None:
        return self.model.objects.filter(pk=pk).first()

    def get_by_id_for_update(self, pk) -> T | None:
        return self.model.objects.select_for_update().filter(pk=pk).first()

    def get_all(self) -> list[T]:
        return list(self.model.objects.all())

    def count(self) -> int:
        return self.model.objects.count()

    def save(self, instance: T, *, update_fields: list[str] | None = None, validate: bool = True) -> T:
        if validate:
            instance.full_clean()
        instance.save(update_fields=update_fields)
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()

    def bulk_create(self, instances: list[T], *, ignore_conflicts: bool = False) -> list[T]:
        return self.model.objects.bulk_create(instances, ignore_conflicts=ignore_conflicts)

    def bulk_update(self, instances: list[T], fields: list[str]) -> None:
        self.model.objects.bulk_update(instances, fields)
