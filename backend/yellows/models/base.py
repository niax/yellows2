from typing_extensions import Self
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model
from pynamodb.attributes import DiscriminatorAttribute, NumberAttribute, UnicodeAttribute, VersionAttribute
from pynamodb.pagination import ResultIterator

from yellows.config import get_config


class InvertedIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'InvertedIndex'
        projection = AllProjection()
    sk = UnicodeAttribute(attr_name="SK", hash_key=True)
    pk = UnicodeAttribute(attr_name="PK", range_key=True)

class TypeOrderedIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'TypeIndexOrder'
        projection = AllProjection()
    type_ = UnicodeAttribute(attr_name="Type", hash_key=True)
    index_sort_order = NumberAttribute(attr_name="IndexSortOrder", range_key=True)

class BaseItem(Model):
    class Meta:
        table_name = get_config().get_dynamo_table_name()
    pynamo_discriminator = DiscriminatorAttribute(attr_name="__PDB_DISCRIM")
    pk = UnicodeAttribute(attr_name="PK", hash_key=True)
    sk = UnicodeAttribute(attr_name="SK", range_key=True)
    type_ = UnicodeAttribute(attr_name="Type", null=True)
    index_sort_order = NumberAttribute(attr_name="IndexSortOrder", null=True)
    inverted_index = InvertedIndex()
    type_ordered_index = TypeOrderedIndex()
    version = VersionAttribute(attr_name="Version")

    @classmethod
    def _build_key(cls, *components: str) -> str:
        type_str = cls.pynamo_discriminator.get_discriminator(cls)
        if type_str is None:
            raise ValueError("Don't know type of {}".format(type(cls)))
        return '_'.join([type_str] + list(components))

    @classmethod
    def list_ordered(cls, *args, **kwargs) -> ResultIterator[Self]:
        type_str = cls.pynamo_discriminator.get_discriminator(cls)
        return cls.type_ordered_index.query(type_str, *args, **kwargs)
