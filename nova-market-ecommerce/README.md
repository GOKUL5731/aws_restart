**Current deployment guide:** [`DEPLOY-STEP-BY-STEP.md`](DEPLOY-STEP-BY-STEP.md). The new COD demo order flow does not charge cards and requires verified Cognito login.

# NOVA MARKET — Serverless Commerce on AWS

A deployable, serverless e-commerce **starter application** inspired by the Lambda → API Gateway → SQS → DynamoDB process in `nealdct/serverless-for-beginners`. It is an original implementation, not a modified copy of the tutorial repository. No EC2, RDS, running servers, containers, or paid app host required. **Lambda is the only application compute**; other managed AWS services are necessary for storage, routing, authentication, notifications, and the web UI.

> **Deployment status:** source files supplied, NOT deployed to your AWS account. AWS credentials, your SES verification, SNS subscription, payment processor onboarding and webhook signing secret are required for full end-to-end functionality. This is a serious functional learning/staging starter, **not a production-ready retail platform** (see Limitations).

## Architecture

```text
Browser HTTPS
   └── CloudFront ── private S3 bucket (HTML / CSS / JS)
       ├── Cognito User Pool (signup/login/verification)
       └── API Gateway HTTP API (JWT on protected routes)
               └── Lambda: api.py
                      ├── DynamoDB On-Demand (catalog, orders, support tickets)
                      ├── Stripe Checkout Sessions (hosted card payment)
                      ├── SSM Parameter Store (encrypted Stripe secrets)
                      └── EventBridge (OrderPaid, OrderShipped, TicketCreated, TicketReply)
                               └── SQS (+ DLQ)
                                    └── Lambda: worker.py
                                         ├── SES (transactional emails)
                                         └── SNS (admin alerts / email subscription)
```

**Flow:** User picks products → signs in → backend recalculates all line prices from DynamoDB → Stripe-hosted payment → Stripe webhook verifies HMAC and amount, not the redirect URL → payment marked `paid` in DynamoDB → EventBridge forwards event to SQS → second Lambda sends SES confirmation and publishes admin SNS notice. Support tickets, ticket replies, product management, order history, and fulfillment statuses work through the same authenticated HTTP API.

## 1. Requirements and account safety

1. AWS account, an IAM user/role allowed to create CloudFormation, Lambda, API Gateway, Cognito, S3, CloudFront, DynamoDB, SES, SNS, SQS, EventBridge, SSM parameters and pass Lambda roles; `CAPABILITY_IAM` will be required. **Do not give the storefront your IAM keys.** Do not use AWS root credentials.
2. On Windows: install **AWS CLI v2**, **AWS SAM CLI**, **Python 3.12**, and Git Bash. The commands below assume Git Bash (or Linux/macOS). This project has no external Python packages in the Lambda functions.
3. A **Stripe** account eligible for your business jurisdiction, test-mode secret key (`sk_test_...`), and Dashboard endpoint webhook signing secret (`whsec_...`). Live payments require Stripe account activation and compliance; Stripe charges separate payment processing fees. Never paste a secret into a chat or GitHub repository.
4. An email address under your control for **SenderEmail** and a destination admin address for **AdminEmail**. AWS SES verification and SNS subscription confirmation happen after deployment. SES needs production access for arbitrary customer recipients.
5. Set an **AWS Budget** with low-cost alerts before deploying. AWS Free Tier eligibility and region pricing vary. DynamoDB point-in-time recovery, SES, S3, CloudFront, logs, and other services can accrue charges, even with no EC2.

Use `us-west-2` throughout, or substitute a region that supports each resource.

## 2. Download and verify IAM access

Place or unzip this project into a folder, then open Git Bash there:

```bash
aws configure --profile store-deployer
# Enter access key, secret key, preferred region e.g. us-west-2, output json
export AWS_PROFILE=store-deployer
aws sts get-caller-identity
sam --version
aws --version
```

For increased security, prefer short-lived IAM Identity Center credentials over long-lived IAM access keys. A browser console login by itself does not authenticate your local AWS CLI.

## 3. Deploy infrastructure with AWS SAM

```bash
cd serverless-commerce
sam validate --lint
sam build
sam deploy --guided --stack-name serverless-commerce --region us-west-2 --capabilities CAPABILITY_IAM
```

In the prompts, use these **example parameters** (replace with your real email addresses):

```text
Stack name:               serverless-commerce
AWS Region:               us-west-2
Parameter SenderEmail:    notifications@YOUR-VERIFIED-DOMAIN.com
Parameter AdminEmail:     YOU@YOUR-DOMAIN.com
Parameter Currency:       inr
Parameter StripeMode:     test
Confirm changes before deploy: Y
Allow SAM CLI IAM role creation: Y
Disable rollback: N
Save arguments to samconfig.toml: Y
```

This deploys CloudFront with a default HTTPS `*.cloudfront.net` URL (no domain purchase), a private S3 origin, API Gateway, two Lambda functions, DynamoDB, Cognito, SES identity, SNS subscription, EventBridge rule, SQS and dead-letter queue. CloudFormation creates the IAM execution policies with service-limited access.

> If SAM fails with unavailable Python runtime during `sam build`, install Python 3.12 locally or build inside a compatible SAM Docker build container. CloudFormation does **not** upload the website static files by itself.

## 4. Upload website and sample products

```bash
bash scripts/deploy.sh serverless-commerce us-west-2
```

This command reads CloudFormation outputs, creates `frontend/config.js` with the public API URL/Cognito IDs, uploads the HTML/CSS/JS to S3, invalidates CloudFront, and seeds eight catalog products in DynamoDB. **Public** client IDs are not secret credentials. Keep the generated `config.js` in the deployment, not an IAM access key or Stripe key.

Test the printed **Website** URL. Products should appear even before setting up Stripe. You can register a shopper account, confirm the code mailed by Cognito, and sign in.

## 5. Set up SES and SNS emails

- Check the `SenderEmail` mailbox and follow the **Amazon SES email verification** link. Alternatively verify your domain with DKIM. The SES identity is created by the template in your deployment region.
- Check `AdminEmail` mailbox and click the **SNS Confirm subscription** link for admin notices.
- New AWS accounts normally remain in the **SES sandbox**. In that state, order/ticket receipt emails can only go to **verified recipients**. You can test using verified mailboxes. For actual customer email delivery request SES **production access** in the same region from the SES console.
- In the SQS console, check the main queue and dead-letter queue if emails do not arrive. A failed SES call retries and ultimately moves the notification to the DLQ. Check CloudWatch Logs for `EmailWorker`.
- Sign-up verification is handled by Cognito and is distinct from the SES custom sender identity.

## 6. Connect Stripe payment (required)

In the Stripe Dashboard switch to **test mode**, copy your **secret API key**.

Obtain the exact webhook URL:

```bash
aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`WebhookUrl`].OutputValue | [0]' --output text
```

In **Stripe Dashboard → Developers → Webhooks**, add that endpoint. Subscribe to:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`

Copy the signing secret `whsec_...` that belongs to **this exact webhook endpoint**, not another endpoint or the Stripe CLI's temporary secret.

Store both secrets encrypted in AWS Systems Manager Parameter Store (the script prompts without echoing the values):

```bash
bash scripts/setup-secrets.sh serverless-commerce us-west-2
```

The script writes `/<stack>/stripe-secret` and `/<stack>/stripe-webhook` as **SecureString**, used by Lambda via IAM-authorized `GetParameter(WithDecryption=true)`. It uses the AWS-managed SSM key by default. For tighter requirements, use a customer-managed KMS key and grant Lambda `kms:Decrypt` narrowly.

**Test end-to-end:** add a product → register and confirm email → sign in → checkout → use Stripe's published test payment card data → Stripe success redirect → open **My orders** → verify status becomes `paid` → check DynamoDB and CloudWatch logs → verify SES receipt and SNS admin alert. **The browser redirect never marks an order paid.** Only a valid Stripe webhook does that.

Stripe can be a restricted payment option for some new Indian merchants; before live use check account eligibility, taxes, supported payment methods, and Indian regulatory requirements. This reference implementation uses **Stripe Checkout**, not Razorpay. A Razorpay integration would require an alternative backend checkout and webhook implementation.

## 7. Activate the admin dashboard

After registering **and confirming** your admin email as a normal shopper, get the Cognito pool ID:

```bash
POOL=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue | [0]' --output text)
ADMIN_EMAIL='YOUR-REGISTERED-EMAIL@example.com'
USERNAME=$(aws cognito-idp list-users --user-pool-id "$POOL" --region us-west-2 \
  --filter "email = \"$ADMIN_EMAIL\"" --query 'Users[0].Username' --output text)
if [[ -z "$USERNAME" || "$USERNAME" == None ]]; then echo 'Admin user not found'; else
  aws cognito-idp admin-add-user-to-group --user-pool-id "$POOL" --username "$USERNAME" --group-name admin --region us-west-2
fi
```

Sign **out** and **in again** to get a fresh Cognito JWT with the `admin` group, then open the **Admin** menu. Only members of the server-side Cognito admin group can edit the catalog, update fulfillment status, and handle support tickets.

## 8. API endpoints

| Method and path | Auth | Function |
|---|---|---|
| `GET /products`, `GET /products/{id}` | Public | List/read active products |
| `POST /checkout` | Shopper JWT | Create pending order + Stripe Checkout Session |
| `POST /webhook/stripe` | Stripe HMAC signature | Verify payment event and update order |
| `GET /orders` | Shopper JWT | Current shopper's order history |
| `GET /tickets`, `POST /tickets` | Shopper JWT | List/create support requests |
| `POST /tickets/{id}/reply` | Owner/admin JWT | Reply to a support request |
| `GET /admin/orders`, `PATCH /admin/orders/{id}` | Admin JWT | All orders, fulfillment status |
| `GET /admin/tickets`, `PATCH /admin/tickets/{id}` | Admin JWT | All tickets, update ticket status |
| `POST /admin/products` | Admin JWT | Add catalog product |
| `PUT /admin/products/{id}` | Admin JWT | Edit product |
| `DELETE /admin/products/{id}` | Admin JWT | Soft-delete product |

`POST /checkout` sample request: `{"items":[{"id":"ceramic-mug","quantity":2}]}`. The client **never sends the amount**. Prices are integer minor currency units (paise for INR; cents for USD). Price and cart limits are validated by Lambda. Any anonymous API calls to protected routes are denied by the API Gateway JWT authorizer.

## 9. Debugging commands

```bash
aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 --query 'Stacks[0].StackStatus'
aws cloudformation describe-stack-events --stack-name serverless-commerce --region us-west-2 --max-items 20
aws sts get-caller-identity
aws sesv2 get-account --region us-west-2 --query ProductionAccessEnabled
aws ssm get-parameter --name /serverless-commerce/stripe-secret --region us-west-2 --query Parameter.Name
aws sqs list-queues --region us-west-2
sam logs -n ApiFunction --stack-name serverless-commerce --region us-west-2 --tail
sam logs -n EmailWorker --stack-name serverless-commerce --region us-west-2 --tail
```

Never log the value of Stripe secrets. For webhook debugging check the webhook delivery report in the Stripe Dashboard. If you get 403 on login-protected routes, refresh credentials by signing out and back in. If CloudFront says `AccessDenied`, check that S3 upload finished and the distribution's origin access control policy is intact.

## 10. Costs and cleanup

Usage is metered. AWS Lambda, API Gateway HTTP API, DynamoDB on-demand, EventBridge, SQS, SNS, SES, CloudFront, Cognito, S3, CloudWatch, data transfer, and Stripe all have their own rates and/or free-tier rules; **serverless does not mean always free**. A low-volume personal demo may fit within available free tiers, but monthly bills are not guaranteed to be zero. CloudFront distribution is deployed in pay-as-you-go mode; selecting a flat-rate CloudFront plan is a separate choice. Set a Budget before deployment, enable CloudWatch log retention policies in a production hardening pass, and monitor DLQ and spending.

```bash
# Delete uploaded frontend files before stack removal so S3 bucket deletion succeeds:
BUCKET=$(aws cloudformation describe-stacks --stack-name serverless-commerce --region us-west-2 \
 --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue | [0]' --output text)
aws s3 rm "s3://$BUCKET" --recursive --region us-west-2
sam delete --stack-name serverless-commerce --region us-west-2
aws ssm delete-parameter --name /serverless-commerce/stripe-secret --region us-west-2
aws ssm delete-parameter --name /serverless-commerce/stripe-webhook --region us-west-2
```

**Deleting this stack irreversibly deletes the store's database and data unless backed up separately.** DynamoDB PITR is not an archival backup. CloudFront and non-empty buckets can prevent stack deletion until those resources are properly removed.

## 11. Important limitations before selling real products

The demo includes working catalog CRUD, registration, email confirmation, login, cart, hosted test payments, verified webhook reconciliation, order history, fulfillment status, a support-ticket conversation flow, receipt/notification pipelines, and role checks. It deliberately **does not yet implement** inventory reservations/oversell prevention, refunds/returns, discounts, taxes/GST invoices, shipping rates and courier label integrations, abandoned-checkout cleanup, fraud screening, shipping-provider fulfillment, card disputes, comprehensive security controls (WAF and abuse prevention), rigorous idempotent notification outbox, automatic backups/export and disaster recovery, observability alarms, legal policies, or full end-to-end live payment testing. Stripe's provider redirect can be replayed, so customers should rely on persisted `paid` status. Pending orders are not cleared automatically.

For production, add inventory reservation with conditional DynamoDB transactions, webhook replay tests and event recovery, fulfillment carrier integration, consumer protection and privacy compliance, payment-mode reconciliation, monitoring/alerts, separate dev/test/prod stacks, and a security review. Persist only data needed for legitimate operations and choose suitable retention periods. Don't use this demo as a fully audited checkout handling real customer money without those steps.

## Original tutorial reference

- `https://github.com/nealdct/serverless-for-beginners` — `serverless-app/serverless-app-instructions.md`, SubmitOrderFunction/ProcessOrderFunction, SQS, DynamoDB, API Gateway and static S3. This project follows the same event-driven architecture while adding Cognito, CloudFront, SES, SNS, EventBridge and Stripe.
- Course: `https://learn.digitalcloud.training/course/aws-serverless-for-beginners-with-aws-lambda-api-gateway-sqs-sns-and-eventbridge`
