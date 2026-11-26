#!/usr/bin/env bash
# Safely store Stripe test secrets in Systems Manager Parameter Store.
set -euo pipefail
STACK="${1:-serverless-commerce}"; REGION="${2:-us-west-2}"
umask 077
set +x
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT
for KIND in secret webhook; do
  if [[ "$KIND" == secret ]]; then LABEL='Stripe test secret key (sk_test_...)'; else LABEL='Stripe webhook signing secret (whsec_...)'; fi
  printf '%s: ' "$LABEL" >&2
  IFS= read -rs VALUE
  printf '\n' >&2
  [[ -n "$VALUE" ]] || { echo 'Secret required' >&2; exit 1; }
  export VALUE KIND STACK
  python - "$TMP" <<'PY'
import json,os,sys
with open(sys.argv[1],'w',encoding='utf-8') as f:
    json.dump({'Name':'/'+os.environ['STACK']+'/stripe-'+os.environ['KIND'],
               'Type':'SecureString','Value':os.environ['VALUE'],'Overwrite':True},f)
PY
  unset VALUE
  aws ssm put-parameter --cli-input-json "file://$TMP" --region "$REGION" --output none
  : > "$TMP"
  echo "Stored /$STACK/stripe-$KIND"
done
