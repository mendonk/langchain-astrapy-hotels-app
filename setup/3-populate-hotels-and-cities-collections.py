import os

import pandas as pd

from common_constants import HOTELS_COLLECTION_NAME, CITIES_COLLECTION_NAME
from setup.setup_constants import HOTEL_REVIEW_FILE_NAME, INSERT_MANY_CONCURRENCY
from utils.db import get_database


this_dir = os.path.abspath(os.path.dirname(__file__))
database = get_database()


def create_hotel_collection():
    return database.create_collection(
        HOTELS_COLLECTION_NAME,
        indexing={"allow": ["_id", "city", "country"]},
    )


def create_city_collection():
    return database.create_collection(
        CITIES_COLLECTION_NAME,
        indexing={"deny": ["*"]},
    )


def populate_city_collection_from_csv(city_col):
    hotel_review_file_path = os.path.join(this_dir, HOTEL_REVIEW_FILE_NAME)
    hotel_review_data = pd.read_csv(hotel_review_file_path)
    city_centres = pd.DataFrame(
        hotel_review_data,
        columns=[
            "hotel_city",
            "hotel_country",
            "hotel_latitude",
            "hotel_longitude",
        ],
    ).rename(
        columns={
            "hotel_city": "city",
            "hotel_country": "country",
            "hotel_latitude": "latitude",
            "hotel_longitude": "longitude",
        }
    )
    city_centres_df = city_centres.groupby(["country", "city"], as_index=False).mean()


    docs_to_insert = (
        {
            # our _id will be '{country}/{city}' consistently
            "_id": f"{row['country']}/{row['city']}",
            # the data:
            "country": row["country"],
            "city": row["city"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
        for _, row in city_centres_df.iterrows()
    )
    insert_result = city_col.insert_many(
        docs_to_insert,
        ordered=False,
        concurrency=INSERT_MANY_CONCURRENCY,
    )

    print(f"[3-populate-hotels-and-cities-collections.py] Inserted {len(insert_result.inserted_ids)} cities")


def populate_hotel_collection_from_csv(hotel_col):
    hotel_review_file_path = os.path.join(this_dir, HOTEL_REVIEW_FILE_NAME)
    hotel_review_data = pd.read_csv(hotel_review_file_path)
    chosen_columns = pd.DataFrame(
        hotel_review_data,
        columns=[
            "hotel_id",
            "hotel_name",
            "hotel_city",
            "hotel_country",
            "hotel_latitude",
            "hotel_longitude",
        ],
    )
    renamed_columns = chosen_columns.rename(
        columns={
            "hotel_id": "id",
            "hotel_name": "name",
            "hotel_city": "city",
            "hotel_country": "country",
            "hotel_latitude": "latitude",
            "hotel_longitude": "longitude",
        }
    )
    hotel_df = renamed_columns.drop_duplicates()

    docs_to_insert = (
        {
            # it so happens that the hotel ID is globally unique
            "_id": row["id"],
            # the data:
            "name": row["name"],
            "city": row["city"],
            "country": row["country"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
        for _, row in hotel_df.iterrows()
    )
    insert_result = hotel_col.insert_many(
        docs_to_insert,
        ordered=False,
        concurrency=INSERT_MANY_CONCURRENCY,
    )

    print(f"[3-populate-hotels-and-cities-collections.py] Inserted {len(insert_result.inserted_ids)} hotels")


if __name__ == "__main__":
    hotel_col = create_hotel_collection()
    populate_hotel_collection_from_csv(hotel_col)
    city_col = create_city_collection()
    populate_city_collection_from_csv(city_col)
