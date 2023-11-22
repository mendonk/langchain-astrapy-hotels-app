from utils.db import get_astra_db_client

from common_constants import USERS_TABLE_NAME


astra_db_client = get_astra_db_client()


def create_user_table():
    return astra_db_client.create_collection(USERS_TABLE_NAME)


if __name__ == "__main__":
    _ = create_user_table()
