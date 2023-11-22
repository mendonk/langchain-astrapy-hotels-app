import os

import pandas as pd

from common_constants import HOTELS_TABLE_NAME, CITIES_TABLE_NAME
from setup.setup_constants import HOTEL_REVIEW_FILE_NAME, INSERTION_BATCH_SIZE
from utils.db import get_astra_db_client
from utils.batching import batch_iterable


this_dir = os.path.abspath(os.path.dirname(__file__))
astra_db_client = get_astra_db_client()


def create_hotel_table():
    return astra_db_client.create_collection(HOTELS_TABLE_NAME)


def create_city_table():
    return astra_db_client.create_collection(CITIES_TABLE_NAME)


def populate_city_table_from_csv(city_col):
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
    for doc_batch in batch_iterable(docs_to_insert, INSERTION_BATCH_SIZE):
        _docs = list(doc_batch)
        city_col.insert_many(_docs)

    print(f"[3-populate-hotels-and-cities-table.py] Inserted {len(city_centres_df)} cities")


def populate_hotel_table_from_csv(hotel_col):
    # f"insert into {keyspace}.{HOTELS_TABLE_NAME} (id, name, city, country, latitude, longitude) values (?, ?, ?, ?, ?, ?)"
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
            # our _id will be '{country}/{city}/{id}' consistently
            "_id": f"{row['country']}/{row['city']}/{row['id']}",
            # the data:
            "id": row["id"],
            "name": row["name"],
            "city": row["city"],
            "country": row["country"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
        for _, row in hotel_df.iterrows()
    )
    for doc_batch in batch_iterable(docs_to_insert, INSERTION_BATCH_SIZE):
        _docs = list(doc_batch)
        hotel_col.insert_many(_docs)

    print(f"[3-populate-hotels-and-cities-table.py] Inserted {len(hotel_df)} hotels")


if __name__ == "__main__":
    hotel_col = create_hotel_table()
    populate_hotel_table_from_csv(hotel_col)
    city_col = create_city_table()
    populate_city_table_from_csv(city_col)
