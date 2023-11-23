#!/bin/bash

REPO_HOME="/workspace/langchain-astrapy-hotels-app"

# source /home/gitpod/.astra/cli/astra-init.sh
clear
echo    "=========================="

ASTRA_TOKEN="$(${REPO_HOME}/scripts/read_and_output_nonempty_secret.sh "Enter your Astra DB Token ('AstraCS:...')")";
echo -e "\nOK"
echo -e "ASTRA_DB_APPLICATION_TOKEN=\"${ASTRA_TOKEN}\"\n" > .env

API_ENDPOINT=""
while [ -z "${API_ENDPOINT}" ]; do
  echo -n "Enter your Astra DB API Endpoint ('https://....apps.astra.datastax.com'): "
  read API_ENDPOINT
done
echo -e "\nOK"
echo -e "ASTRA_DB_API_ENDPOINT=\"${API_ENDPOINT}\"\n" >> .env

echo -n "Enter your Astra DB keyspace (*optional*, you can probably leave to default): "
read KEYSPACE
echo -e "\nOK"
if [ ! -z "${KEYSPACE}" ]; then
  echo -e "ASTRA_DB_KEYSPACE=\"${KEYSPACE}\"\n" >> .env
fi

${REPO_HOME}/scripts/ingest_openai_key.sh ${REPO_HOME}/.env

cd ${REPO_HOME}
pip install -r requirements.txt

# provision DB (i.e. all necessary steps in sequence)
python -m setup.2-populate-review-vector-collection
python -m setup.3-populate-hotels-and-cities-collections
python -m setup.4-create-users-collection
python -m setup.5-populate-reviews-collection

# friendly message to user
CLIENT_URL=$(gp url 3000)
echo -e "\n\n** AFTER THE API IS UP YOU CAN OPEN THE CLIENT IN A NEW TAB:\n    ${CLIENT_URL}\n\n";

# start the actual api
uvicorn api:app
