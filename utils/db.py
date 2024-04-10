import os
from typing import Dict, Optional
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

import astrapy
from astrapy import DataAPIClient


dotenv_file = find_dotenv(".env")
load_dotenv(dotenv_file)


astra_database: Optional[astrapy.Database] = None
collection_cache: Dict[str, astrapy.Collection] = {}


@dataclass
class AstraCredentials:
    token: str
    api_endpoint: str
    namespace: Optional[str]


def get_astra_credentials() -> AstraCredentials:
    return AstraCredentials(
        token=os.environ["ASTRA_DB_APPLICATION_TOKEN"],
        api_endpoint=os.environ["ASTRA_DB_API_ENDPOINT"],
        namespace=os.environ.get("ASTRA_DB_KEYSPACE"),
    )


def get_database() -> astrapy.Database:
    global astra_database
    if astra_database is None:
        credentials = get_astra_credentials()
        astra_database = DataAPIClient(
            token=credentials.token,
        ).get_database_by_api_endpoint(
            api_endpoint=credentials.api_endpoint,
            namespace=credentials.namespace,
        )
    return astra_database


def get_collection(name: str) -> astrapy.Collection:
    global collection_cache
    if name not in collection_cache:
        collection_cache[name] = get_database().get_collection(name)
    return collection_cache[name]
