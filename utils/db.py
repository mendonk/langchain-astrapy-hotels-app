import os

from dotenv import find_dotenv, load_dotenv
#
from astrapy.db import AstraDB


dotenv_file = find_dotenv(".env")
load_dotenv(dotenv_file)


astra_db_client = None


def get_astra_db_client():
    global astra_db_client
    if astra_db_client is None:
        astra_db_client = AstraDB(
            api_endpoint=os.environ["ASTRA_DB_API_ENDPOINT"],
            token=os.environ["ASTRA_DB_APPLICATION_TOKEN"],
            namespace=os.environ.get("ASTRA_DB_KEYSPACE"),
        )
    return astra_db_client
