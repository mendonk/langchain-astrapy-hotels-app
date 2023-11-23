from utils.db import get_astra_db_client

from common_constants import USERS_COLLECTION_NAME


astra_db_client = get_astra_db_client()


def create_user_collection():
    return astra_db_client.create_collection(USERS_COLLECTION_NAME)


if __name__ == "__main__":
    _ = create_user_collection()
