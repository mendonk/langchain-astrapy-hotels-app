from utils.db import get_astra_db_client

from common_constants import HOTELS_TABLE_NAME
from typing import List, Optional
from utils.models import Hotel


def find_hotels_by_location(city: str, country: str) -> List[Hotel]:
    astra_db_client = get_astra_db_client()
    hotels_col = astra_db_client.collection(HOTELS_TABLE_NAME)

    hotel_docs = hotels_col.find(
        filter={
            "city": city,
            "country": country,
        },
        projection={
            "name": 1,
            "_id": 1,
        },
        options={
            "limit": 15,
        },
    )["data"]["documents"]

    hotels = [
        Hotel(
            city=city,
            country=country,
            name=hotel_doc["name"],
            id=hotel_doc["_id"],
        )
        for hotel_doc in hotel_docs
    ]

    return hotels


def find_hotel_by_id(hotel_id: str) -> Optional[Hotel]:
    astra_db_client = get_astra_db_client()
    hotels_col = astra_db_client.collection(HOTELS_TABLE_NAME)

    hotel_doc = hotels_col.find_one(
        filter={
            "_id": hotel_id,
        },
        projection={
            "city": 1,
            "country": 1,
            "name": 1,
            "_id": 1,
        },
    )["data"]["document"]

    if hotel_doc is not None:
        return Hotel(
            city=hotel_doc["city"],
            country=hotel_doc["country"],
            name=hotel_doc["name"],
            id=hotel_doc["_id"],
        )
    else:
        return None
