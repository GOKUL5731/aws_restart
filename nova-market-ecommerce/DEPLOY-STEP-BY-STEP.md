# NOVA MARKET — Catalog + COD Orders + Email — Git Bash deployment

This release extends the previous **Lambda HTTPS** project. It is a **development/demo** storefront. It keeps Stripe online checkout optional, and implements authenticated **cash-on-delivery orders** that persist to DynamoDB without charging the customer. It generates order confirmation events through EventBridge → SQS → EmailWorker → SES, and admin alerts through SNS. Do not represent COD orders as paid.

## Fixes
- Explicit **empty catalog** messaging, plus `scripts/deploy.sh` to populate eight DynamoDB products.
- `POST /orders/cod` with Cognito JWT authentication, validated products/prices/quantities and Indian delivery details.
- Deterministic idempotency for client-generated UUIDv4 request IDs, preventing duplicate COD orders on retries.
- An order confirmation notification event and emails for COD orders (after SES verification).
- Admin can fulfill COD orders; a separate manual **Record cash received** action is restricted to admin and marks them collected.
- Existing optional Stripe checkout remains, requiring real Stripe test API keys and a verified webhook.

## Start — **in Git Bash**

1. Extract the ZIP to Downloads **in a new directory** (avoid editing your old working copy by mistake):

```bash
cd ~/Downloads
unzip NOVA-MARKET-CATALOG-COD-EMAIL-FIX.zip -d NOVA-MARKET-COD
cd NOVA-MARKET-COD/serverless-commerce
```

2. Confirm the AWS account, region, and existing CloudFormation stack:

```bash
aws sts get-caller-identity
aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query 'Stacks[0].StackStatus' --output text
```

Only proceed if this is your own demo `serverless-commerce` stack and you intend to update it. You do **not** need to delete the stack. Avoid deleting or replacing DynamoDB data.

3. Verify Python dependencies, syntax and tests (Python 3.12 recommended; local tests need boto3):

```bash
python -m pip install --user boto3
python -m unittest discover -s tests -v
sam validate --lint
sam build
```

4. Deploy **an update to the existing stack**. This may incur charges. Review the changeset before typing `y`.

```bash
sam deploy \
  --stack-name serverless-commerce \
  --region us-west-2 \
  --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ParameterKey=SenderEmail,ParameterValue=gokulgokul5731@gmail.com \
    ParameterKey=AdminEmail,ParameterValue=gokulgokul5731@gmail.com \
    ParameterKey=Currency,ParameterValue=inr \
    ParameterKey=StripeMode,ParameterValue=test \
  --confirm-changeset
```

5. When stack status is `UPDATE_COMPLETE` (or `CREATE_COMPLETE` on new install), seed products and verify the catalog:

```bash
bash scripts/deploy.sh serverless-commerce us-west-2
bash scripts/check-store.sh serverless-commerce us-west-2
```

6. Obtain and open your actual HTTPS URL:

```bash
SITE=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='Website'].OutputValue | [0]" --output text)
echo "$SITE"
curl -i "$SITE/products"
cmd.exe /c start "" "$SITE"
```

## Test placing a COD order

1. Sign up using your email on the site; complete the Cognito verification code and sign in.
2. Add a seeded product → Bag → fill recipient, mobile, address, city/state and 6-digit Indian PIN.
3. Click **Place COD order**. The system saves a real order in DynamoDB with status `placed_cod` / `due_on_delivery`, **not paid**; no Stripe credentials required.
4. Open **My orders**, refresh after a few seconds if the DynamoDB owner index hasn't caught up.
5. Use admin account to review the order and set fulfillment status. Record COD cash received **only after physical collection**.

To grant admin access **after registering your own email**:

```bash
POOL=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue | [0]" --output text)
aws cognito-idp admin-add-user-to-group --user-pool-id "$POOL" --username 'gokulgokul5731@gmail.com' --group-name admin --region us-west-2
```

Sign out and back in to receive a new admin access token.

## Make order confirmation emails work

1. Verify the **sender** `gokulgokul5731@gmail.com` in Amazon SES for **us-west-2** (watch your inbox for an SES verification email). Check:

```bash
aws sesv2 get-email-identity --email-identity 'gokulgokul5731@gmail.com' --region us-west-2 --query 'VerificationStatus' --output text
aws sesv2 get-account --region us-west-2 --query 'ProductionAccessEnabled' --output text
```

2. If production access is `False` (SES sandbox), **recipient addresses must also be verified**. Test an order using the same verified sender email first. To send order confirmations to real customers, request SES production access and set up domain-level authentication (SPF/DKIM, bounce handling). AWS SES: https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
3. Confirm the **SNS admin email subscription** in the admin inbox (look for the AWS notification confirmation email). To inspect:

```bash
TOPIC=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='AdminTopicArn'].OutputValue | [0]" --output text)
aws sns list-subscriptions-by-topic --topic-arn "$TOPIC" --region us-west-2 --query 'Subscriptions[].[Protocol,Endpoint,SubscriptionArn]' --output table
```

4. For any order placed **after** the above configuration, SES emails are sent by the `EmailWorker` Lambda triggered through EventBridge and SQS. Emails may be delayed and should not be assumed delivered until SES and worker logs confirm success.

Check logs:

```bash
WORKER=$(aws cloudformation describe-stack-resources --stack-name serverless-commerce --region us-west-2 --query "StackResources[?LogicalResourceId=='EmailWorker'].PhysicalResourceId | [0]" --output text)
MSYS_NO_PATHCONV=1 aws logs tail "/aws/lambda/$WORKER" --since 1h --region us-west-2
```

If emails fail, inspect the SQS DLQ and `Worker failed ...` logs. SES sandbox, sender verification, and SNS subscription confirmation are the most common blockers.

## Order and payment status

- COD checkout: `placed_cod`, `due_on_delivery`, paid amount = 0 online.
- Admin **Record cash received**: `cod_collected` / `collected` only after real collection.
- Stripe checkout (optional): customer must sign in and Stripe must be configured with credentials plus webhook. Orders remain `pending_payment` until the **signed** Stripe webhook confirms payment.

## Quick diagnostics

```bash
# Customer-facing products JSON
curl -i "$SITE/products"

# Backend Lambda logs
API_FN=$(aws cloudformation describe-stack-resources --stack-name serverless-commerce --region us-west-2 --query "StackResources[?LogicalResourceId=='ApiFunction'].PhysicalResourceId | [0]" --output text)
MSYS_NO_PATHCONV=1 aws logs tail "/aws/lambda/$API_FN" --since 30m --region us-west-2

# DynamoDB product count
TABLE=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='DynamoTable'].OutputValue | [0]" --output text)
aws dynamodb query --table-name "$TABLE" --key-condition-expression 'PK = :p' --expression-attribute-values '{":p":{"S":"PRODUCT"}}' --query 'Count' --region us-west-2 --output text
```

## Limitations and billing

Demo application: No automatic tax calculation, delivery carrier integrations, inventory reservation, fraud checks, legal invoice issuing, payment settlement reconciliation, or guaranteed exactly-once notifications. COD orders may need manual merchant approval. Production operation would require additional hardening. AWS charges apply for resources and usage. Never place customer credentials in Git Bash command arguments or GitHub. Use least-privilege IAM rather than attaching additional admin policies.
