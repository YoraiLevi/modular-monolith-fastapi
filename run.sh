#! /bin/bash
mkdir -p ./logs/
# generate api client
uv pip uninstall generated/api
python src/app/subapp.openapi.py > generated/openapi.json
rm -r generated/api; \
npx -g openapi-generator-cli generate \
 --additional-properties=generateSourceCodeOnly=false,packageName=modular_monolith_api \
 -g python --library asyncio \
 -i generated/openapi.json -o generated/api
uv pip install generated/api
# run app
uvicorn main:app --reload --log-config log_config.json --reload-include '*.json' --reload-dir 'src'
