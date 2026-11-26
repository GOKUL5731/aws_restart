#!/usr/bin/env bash
# Non-mutating diagnostics for NOVA MARKET. Requires AWS CLI, curl, Python 3.
set -euo pipefail
STACK="${1:-serverless-commerce}"
REGION="${2:-us-west-2}"
get_output() { AWS_PAGER='' aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue | [0]" --output text; }
STATUS="$(AWS_PAGER='' aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" --query 'Stacks[0].StackStatus' --output text)"
echo "Stack: $STACK ($STATUS)"
[[ "$STATUS" == CREATE_COMPLETE || "$STATUS" == UPDATE_COMPLETE ]] || { echo 'Stack not ready' >&2; exit 2; }
TABLE="$(get_output DynamoTable)"
SITE="$(get_output Website)"
echo "Site: $SITE"
echo "Table: $TABLE"
COUNT="$(AWS_PAGER='' aws dynamodb query --table-name "$TABLE" --key-condition-expression 'PK = :p' --expression-attribute-values '{":p":{"S":"PRODUCT"}}' --region "$REGION" --query 'Count' --output text)"
echo "Products in DynamoDB: $COUNT"
[[ "$COUNT" -gt 0 ]] || { echo 'Run bash scripts/deploy.sh to seed products' >&2; exit 3; }
echo 'Checking public product API ...'
JSON="$(curl --fail-with-body --silent --show-error --max-time 20 "$SITE/products")"
PRODUCTS_JSON="$JSON" python - <<'PY'
import os,json
result=json.loads(os.environ['PRODUCTS_JSON'])
products=result.get('products', [])
print('Products visible in API:',len(products))
for p in products[:5]: print(' -',p.get('name'),p.get('price'))
if not products: raise SystemExit('ERROR: API returned no products')
PY
printf 'Success: public catalog available at %s\n' "$SITE"
