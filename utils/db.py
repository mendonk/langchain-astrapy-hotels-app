import os

from dotenv import find_dotenv, load_dotenv

import astrapy
from astrapy import DataAPIClient


dotenv_file = find_dotenv(".env")
load_dotenv(dotenv_file)


astra_database: astrapy.Database = None


def get_astra_credentials(alternative_db=False):
    if not alternative_db:
        return {
            "token": os.environ["ASTRA_DB_APPLICATION_TOKEN"],
            "api_endpoint": os.environ["ASTRA_DB_API_ENDPOINT"],
            "namespace": os.environ.get("ASTRA_DB_KEYSPACE"),
        }
    else:
        if "ASTRA_DB_API_ENDPOINT_ALT" in os.environ and "ASTRA_DB_APPLICATION_TOKEN_ALT" in os.environ:
            return {
                "token": os.environ["ASTRA_DB_APPLICATION_TOKEN_ALT"],
                "api_endpoint": os.environ["ASTRA_DB_API_ENDPOINT_ALT"],
                "namespace": os.environ.get("ASTRA_DB_KEYSPACE_ALT"),
            }
        else:
            return None


def get_database():
    global astra_database
    if astra_database is None:
        credentials = get_astra_credentials()
        astra_database = DataAPIClient(
            token=credentials["token"],
        ).get_database_by_api_endpoint(
            api_endpoint=credentials["api_endpoint"],
            namespace=credentials["namespace"],
        )
    return astra_database
