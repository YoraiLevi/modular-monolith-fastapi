#! /bin/bash
mkdir -p ./logs/
# generate api client
uv pip uninstall generated/api
uv pip uninstall modular_monolith_api
rm -r generated/api; \
npx -g openapi-generator-cli generate \
 --additional-properties=generateSourceCodeOnly=false,packageName=modular_monolith_api \
 -g python --library asyncio \
 -i generated/openapi.json -o generated/api
uv pip install generated/api

uv pip uninstall generated/pet_service/api
uv pip uninstall pet_service_api
rm -r generated/pet_service/api; \
npx -g openapi-generator-cli generate \
 --additional-properties=generateSourceCodeOnly=false,packageName=pet_service_api \
 -g python --library asyncio \
 -i generated/pet_service/openapi.json -o generated/pet_service/api
uv pip install generated/pet_service/api

uv pip uninstall generated/user_service/api
uv pip uninstall user_service_api
rm -r generated/user_service/api; \
npx -g openapi-generator-cli generate \
 --additional-properties=generateSourceCodeOnly=false,packageName=user_service_api \
 -g python --library asyncio \
 -i generated/user_service/openapi.json -o generated/user_service/api
uv pip install generated/user_service/api
# run app
python -m app --config ./config.yaml --reload --reload-include '*.yaml' --reload-include '*.json' --reload-exclude 'generated/*' --reload-exclude 'logs/*'

