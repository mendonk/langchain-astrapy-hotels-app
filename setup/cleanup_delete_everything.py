from common_constants import HOTELS_COLLECTION_NAME, CITIES_COLLECTION_NAME, REVIEWS_COLLECTION_NAME, REVIEW_VECTOR_COLLECTION_NAME, USERS_COLLECTION_NAME
from utils.db import get_astra_db_client

db = get_astra_db_client()

# List of collection names to delete
collection_names = [
    HOTELS_COLLECTION_NAME,
    CITIES_COLLECTION_NAME,
    REVIEWS_COLLECTION_NAME,
    REVIEW_VECTOR_COLLECTION_NAME,
    USERS_COLLECTION_NAME
]

# Function to delete collections
def delete_collections(db, collection_names):
    for collection_name in collection_names:
        try:
            db.delete_collection(collection_name=collection_name)
            print(f"Deleted collection: {collection_name}")
        except Exception as e:
            print(f"Error deleting collection {collection_name}: {str(e)}")

# Delete the collections
delete_collections(db, collection_names)

