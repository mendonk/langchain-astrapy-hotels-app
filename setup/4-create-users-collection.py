import astrapy

from common_constants import USERS_COLLECTION_NAME
from utils.db import get_database

database = get_database()


def create_user_collection() -> astrapy.Collection:
    coll: astrapy.Collection = database.create_collection(
        USERS_COLLECTION_NAME,
        indexing={"allow": ["_id"]},
    )
    return coll


if __name__ == "__main__":
    create_user_collection()
