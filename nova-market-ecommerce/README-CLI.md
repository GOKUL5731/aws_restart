> **Latest catalog + COD order + email release:** Follow `DEPLOY-STEP-BY-STEP.md` for the current steps. It supports cash-on-delivery test orders without Stripe, and EventBridge/SQS/SES customer notification after SES verification.

# NOVA MARKET — Git Bash / AWS CLI deployment guide

This edition avoids CloudFront account verification and S3 public website hosting. Both frontend and backend are hosted at the **same HTTPS API Gateway URL** using Lambda; the backend uses DynamoDB, Cognito, EventBridge, SQS, SES and SNS. The public catalog works as soon as products are seeded. Payments require separate Stripe merchant enrollment, credentials and webhook configuration. Use Stripe *test* mode first.

## Prerequisites

- Windows Git Bash, AWS CLI v2, SAM CLI, Python 3.12, AWS IAM credentials already configured.
- Confirm that the account and IAM identity are authorized for CloudFormation, IAM role creation/PassRole, Lambda, API Gateway, DynamoDB, Cognito, SES, SNS, SQS, EventBridge, CloudWatch Logs, SSM and S3 (SAM artifacts). No AWS IAM keys go into the webpage or repository. AdministratorAccess is **not** needed if appropriate scoped deployment permissions exist.
- Create a small AWS Budget and billing alert first. API Gateway, Lambda, DynamoDB, Cognito, logs, SNS, SES and other services can incur costs.

## Circular-dependency fix (2026-10-09)

This release removes `ShopApi` references from the `ApiFunction` and `SiteFunction` environment variables. Both Lambda handlers derive the HTTPS base URL from API Gateway's trusted `event.requestContext.domainName` and `stage`. This avoids the `E3004 ApiFunction <-> ShopApi` circular dependency triggered by SAM's generated HTTP API integrations.

If upgrading an extracted copy, replace its three affected files (`template.yaml`, `backend/api.py`, `frontend/site.py`) from this fixed archive and rerun `sam validate --lint`, tests, and `sam build` before deploying.

## HTTPS 500 error fix (2026-10-09)

If your deployment returns `{"message":"Internal Server Error"}` on `/`, a likely cause is naming the frontend Lambda module `site.py`: the Python runtime already imports a standard-library module named `site`, so `Handler: site.lambda_handler` can resolve to the wrong module. This release renames it to `frontend/storefront_handler.py` and updates the handler to `storefront_handler.lambda_handler`. Verify the exact cause in CloudWatch logs if the error persists.

To update an existing extracted project using Git Bash without downloading the full new ZIP:

```bash
cd ~/Downloads/NOVA-MARKET-NEW/serverless-commerce
mv frontend/site.py frontend/storefront_handler.py
sed -i 's/Handler: site.lambda_handler/Handler: storefront_handler.lambda_handler/' template.yaml
sed -i "s@/ 'site.py'@/ 'storefront_handler.py'@; s/spec_from_file_location('site', module_path)/spec_from_file_location('storefront_handler', module_path)/" tests/test_logic.py
sam validate --lint && python -m unittest discover -s tests -v && sam build
```

Then redeploy with the full stack, region, and parameter options documented below.

## Deployment commands — run one section at a time

1. Unzip `NOVA-MARKET-Lambda-HTTPS-CLI.zip`, then `cd` into the `serverless-commerce` directory. For Git Bash:

```bash
aws sts get-caller-identity
sam --version
python --version
aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query 'Stacks[0].StackStatus' --output text
```

If the stack does not exist, an AWS validation error is expected. If the stack is `ROLLBACK_COMPLETE`, delete it and wait, only if it is the failed *demo* stack (irreversible loss of its data). If it has `CREATE_COMPLETE`, inspect it before replacing it.

```bash
aws cloudformation delete-stack --stack-name serverless-commerce --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name serverless-commerce --region us-west-2
```

2. Validate, unit-test and build:

```bash
sam validate
python -m unittest discover -s tests -v
sam build
```

3. Deploy. Review the resulting CloudFormation changeset before confirming creation. The stack creates billable resources.

```bash
sam deploy --stack-name serverless-commerce --region us-west-2 --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides ParameterKey=SenderEmail,ParameterValue=gokulgokul5731@gmail.com ParameterKey=AdminEmail,ParameterValue=gokulgokul5731@gmail.com ParameterKey=Currency,ParameterValue=inr ParameterKey=StripeMode,ParameterValue=test --confirm-changeset
```

4. Verify stack and seed products. `scripts/deploy.sh` writes **8 sample products** to DynamoDB; if a retry occurs, it checks unprocessed writes. Do not use the original project's CloudFront/S3 deploy script.

```bash
aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query 'Stacks[0].StackStatus' --output text
bash scripts/deploy.sh serverless-commerce us-west-2
```

5. Get/open HTTPS URL and verify catalog API:

```bash
SITE=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='Website'].OutputValue | [0]" --output text)
echo "$SITE"
curl -i "$SITE/"
curl -s "$SITE/products"
cmd.exe /c start "" "$SITE"
```

6. Create an admin user (use your own real email), then verify email through the site's sign-up flow before assigning admin privileges:

```bash
POOL=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue | [0]" --output text)
aws cognito-idp admin-add-user-to-group --user-pool-id "$POOL" --username 'YOUR_VERIFIED_EMAIL@example.com' --group-name admin --region us-west-2
```

Sign out and sign back in to refresh group claims. Customers can register on the website and confirm email with their verification code. Login, orders and support use Cognito JWT-protected API routes.

7. Configure Stripe checkout. First open a Stripe account and obtain a **test** secret key, then configure webhook event delivery to the URL below (subscribe to `checkout.session.completed` and `checkout.session.async_payment_succeeded`). Use the endpoint's signing secret **from Stripe**. For Indian merchant accounts, eligibility may be limited; a processor integration that supports your merchant account may be necessary.

```bash
aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='WebhookUrl'].OutputValue | [0]" --output text
bash scripts/setup-secrets.sh serverless-commerce us-west-2
```

Verify sender identity through the AWS SES email, and confirm the SNS email subscription. SES sandbox restrictions may block email to customers until production access is approved. Only a signed, verified Stripe webhook changes an order's payment status to `paid`. An attempted checkout before setup will return a service error, not create a completed purchase.

8. Troubleshooting commands:

```bash
aws cloudformation describe-stack-events --stack-name serverless-commerce --region us-west-2 --query "StackEvents[?contains(ResourceStatus,'FAILED')].[LogicalResourceId,ResourceStatusReason]" --output table
TABLE=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query "Stacks[0].Outputs[?OutputKey=='DynamoTable'].OutputValue | [0]" --output text)
aws dynamodb query --table-name "$TABLE" --key-condition-expression 'PK = :pk' --expression-attribute-values '{":pk":{"S":"PRODUCT"}}' --region us-west-2 --query 'Count' --output text
aws cloudformation describe-stack-resources --stack-name serverless-commerce --region us-west-2 --query 'StackResources[?ResourceType==`AWS::Lambda::Function`].[LogicalResourceId,PhysicalResourceId]' --output table
```

For Lambda errors, find its name from the preceding command, then:

```bash
aws logs tail "/aws/lambda/YOUR_FUNCTION_NAME" --since 30m --region us-west-2
```

## Billing cleanup (irreversible)

Delete the *demo* stack, after first ensuring it is not carrying important data:

```bash
aws cloudformation delete-stack --stack-name serverless-commerce --region us-west-2
aws cloudformation wait stack-delete-complete --stack-name serverless-commerce --region us-west-2
```

If any resources fail to delete, inspect `DELETE_FAILED` stack events. The separately owned SAM artifact S3 bucket, SSM parameters and retained logs may require separate cleanup. Budget alerts, cost explorer and bill verification remain essential.

## Limitations

This is a deployable learning/staging project, not a production-certified commerce system. It lacks stock reservations, tax/GST invoices, shipping provider integration, fraud/rate-limit protections beyond gateway throttling, and returns/refunds. The storefront HTTPS endpoint and catalog become usable after stack deployment and seeding; **real checkout is not functional until you configure and test Stripe**, and email depends on SES. Some AWS accounts have restrictions that prevent resource creation even with IAM permission.
