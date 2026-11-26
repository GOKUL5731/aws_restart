#!/usr/bin/env bash
# Seed products and show HTTPS site URL after SAM deploy.
set -euo pipefail
STACK="${1:-serverless-commerce}"; REGION="${2:-us-west-2}"
get_output() { aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" --output text; }
TABLE="$(get_output DynamoTable)"; SITE="$(get_output Website)"; API="$(get_output ApiUrl)"
[[ -n "$TABLE" && "$TABLE" != None ]] || { echo 'DynamoDB table output missing'; exit 1; }
export TABLE
python - <<'PYSEED'
import os,json
with open('scripts/seed-template.json',encoding='utf-8') as f: data=json.load(f)
with open('scripts/seed.json','w',encoding='utf-8') as f: json.dump({os.environ['TABLE']:data['__TABLE_NAME__']},f,ensure_ascii=True)
PYSEED
for attempt in 1 2 3 4 5; do
  aws dynamodb batch-write-item --request-items file://scripts/seed.json --region "$REGION" > scripts/seed-result.json
  python - <<'PYUNPROCESSED'
import json
r=json.load(open('scripts/seed-result.json',encoding='utf-8'))
json.dump(r.get('UnprocessedItems',{}),open('scripts/seed.json','w',encoding='utf-8'))
PYUNPROCESSED
  REMAINING="$(python -c 'import json;print(sum(map(len,json.load(open("scripts/seed.json")).values())))')"
  [[ "$REMAINING" == 0 ]] && break
  sleep "$attempt"
done
[[ "$REMAINING" == 0 ]] || { echo "$REMAINING products not seeded; re-run deployment script";exit 1; }
COUNT="$(AWS_PAGER='' aws dynamodb query --table-name "$TABLE" --key-condition-expression 'PK = :p' --expression-attribute-values '{":p":{"S":"PRODUCT"}}' --region "$REGION" --query 'Count' --output text)"
echo "Catalog products in DynamoDB: $COUNT"
[[ "$COUNT" -ge 8 ]] || { echo 'WARNING: expected eight or more seeded products' >&2; exit 1; }
echo "HTTPS WEBSITE: $SITE"
echo "PUBLIC PRODUCTS API: $API/products"
echo "Note: Checkout needs Stripe keys and a signed webhook; see README-CLI.md."
