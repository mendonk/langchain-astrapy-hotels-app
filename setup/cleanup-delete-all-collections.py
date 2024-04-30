from typing import List

import astrapy

from common_constants import (
    CITIES_COLLECTION_NAME,
    HOTELS_COLLECTION_NAME,
    LLM_CACHE_COLLECTION_NAME,
    REVIEW_VECTOR_COLLECTION_NAME,
    REVIEWS_COLLECTION_NAME,
    USERS_COLLECTION_NAME,
)
from utils.db import get_database


# Function to delete collections
def drop_collections(db: astrapy.Database, collection_names: List[str]) -> None:
    for collection_name in collection_names:
        print(f"Dropping collection {collection_name} ... ")
        try:
            db.drop_collection(collection_name)
            print(f"    ==> Dropped collection: {collection_name}")
        except Exception as e:
            print(f"    ==> Error dropping collection {collection_name}: {str(e)}")


if __name__ == "__main__":
    # List of collection names to delete
    collection_names = [
        HOTELS_COLLECTION_NAME,
        CITIES_COLLECTION_NAME,
        REVIEWS_COLLECTION_NAME,
        REVIEW_VECTOR_COLLECTION_NAME,
        USERS_COLLECTION_NAME,
        LLM_CACHE_COLLECTION_NAME,
    ]
    # Get the Astra DB client
    db = get_database()
    # Delete the collections
    drop_collections(db, collection_names)
