"""AWS Lambda HTTP API backend, Python 3.12. Prices are always server-side minor units."""
import base64
import hashlib
import hmac
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

DB = boto3.resource('dynamodb').Table(os.environ['DATA_TABLE'])
SSM = boto3.client('ssm')
EVENTS = boto3.client('events')
COGNITO = boto3.client('cognito-idp')
CURRENCY = os.environ.get('CURRENCY', 'inr')
SECRETS = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def reply(status, data):
    return {'statusCode': status, 'headers': {'Content-Type': 'application/json', 'Cache-Control': 'no-store'}, 'body': json.dumps(data, default=str)}


def problem(status, message):
    return reply(status, {'error': message})


def parse_body(event):
    raw = event.get('body') or '{}'
    if event.get('isBase64Encoded'):
        raw = base64.b64decode(raw).decode('utf-8')
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError('Expected a JSON object')
    return obj


def claims(event):
    return event.get('requestContext', {}).get('authorizer', {}).get('jwt', {}).get('claims', {})


def current_user(event):
    c = claims(event)
    if not c.get('sub') or c.get('token_use') != 'access':
        raise PermissionError('Sign in is required')
    return c['sub']


def is_admin(event):
    groups = claims(event).get('cognito:groups', '')
    if isinstance(groups, list):
        return 'admin' in groups
    return 'admin' in re.split(r'[^a-zA-Z0-9_-]+', str(groups))


def admin_only(event):
    current_user(event)
    if not is_admin(event):
        raise PermissionError('Admin account required')


def user_email(event):
    # Resolve the email server-side rather than trusting an address sent by the browser.
    c = claims(event)
    user = COGNITO.admin_get_user(UserPoolId=os.environ['USER_POOL_ID'], Username=c['sub'])
    attrs = {a['Name']: a['Value'] for a in user['UserAttributes']}
    if attrs.get('email_verified') != 'true':
        raise ValueError('Verify your email address before proceeding')
    return attrs['email']


def ddb_json(obj):
    return json.loads(json.dumps(obj, default=lambda x: int(x) if isinstance(x, Decimal) else str(x)))


def get_product(product_id):
    p = DB.get_item(Key={'PK': 'PRODUCT', 'SK': product_id}).get('Item')
    if not p or not p.get('active', False):
        return None
    return ddb_json(p)


def list_products():
    result = DB.query(KeyConditionExpression=Key('PK').eq('PRODUCT'))
    items = result.get('Items', [])
    while result.get('LastEvaluatedKey'):
        result = DB.query(KeyConditionExpression=Key('PK').eq('PRODUCT'), ExclusiveStartKey=result['LastEvaluatedKey'])
        items.extend(result.get('Items', []))
    return [ddb_json(p) for p in items if p.get('active', False)]


def list_pk(pk, limit=100):
    result = DB.query(KeyConditionExpression=Key('PK').eq(pk), Limit=limit, ScanIndexForward=False)
    return [ddb_json(x) for x in result.get('Items', [])]


def list_user(sub, prefix):
    r = DB.query(IndexName='ByOwner', KeyConditionExpression=Key('GSI1PK').eq('USER#' + sub) & Key('GSI1SK').begins_with(prefix), ScanIndexForward=False, Limit=100)
    return [ddb_json(x) for x in r.get('Items', [])]


def stripe_secret(name):
    envname = 'STRIPE_KEY_PARAMETER' if name == 'key' else 'STRIPE_WEBHOOK_PARAMETER'
    if envname not in SECRETS:
        SECRETS[envname] = SSM.get_parameter(Name=os.environ[envname], WithDecryption=True)['Parameter']['Value'].strip()
    value = SECRETS[envname]
    if name == 'key':
        expected = 'sk_live_' if os.environ.get('STRIPE_MODE', 'test') == 'live' else 'sk_test_'
        if not value.startswith(expected):
            raise ValueError(f'Stripe key must match configured {os.environ.get("STRIPE_MODE", "test")} mode')
    return value


def stripe_post(params):
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request('https://api.stripe.com/v1/checkout/sessions', data=data, method='POST', headers={
        'Authorization': 'Bearer ' + stripe_secret('key'),
        'Content-Type': 'application/x-www-form-urlencoded',
        'Idempotency-Key': params['client_reference_id'],
    })
    try:
        with urllib.request.urlopen(req, timeout=9) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        # Do not return provider internals or the credential to callers.
        raise RuntimeError('Payment provider rejected the checkout request (' + str(exc.code) + ')') from None


def checkout(event):
    sub = current_user(event)
    email = user_email(event)
    body = parse_body(event)
    incoming = body.get('items')
    if not isinstance(incoming, list) or not 1 <= len(incoming) <= 15:
        raise ValueError('Cart must contain 1 to 15 products')
    merged = {}
    for item in incoming:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str):
            raise ValueError('Invalid product in cart')
        qty = item.get('quantity')
        if type(qty) is not int or not 1 <= qty <= 10:
            raise ValueError('Quantity must be between 1 and 10')
        merged[item['id']] = merged.get(item['id'], 0) + qty
    if any(q > 10 for q in merged.values()):
        raise ValueError('Maximum 10 units of each product')
    products = []
    total = 0
    for product_id, qty in merged.items():
        p = get_product(product_id)
        if not p:
            raise ValueError('A selected product is unavailable; refresh your cart')
        price = int(p['price'])
        total += price * qty
        products.append({'id': product_id, 'name': str(p['name']), 'price': price, 'quantity': qty})
    if total < (50 if CURRENCY == 'inr' else 50) or total > 50000000:
        raise ValueError('Order total is outside the supported limits')
    order_id = str(uuid.uuid4())
    created = now()
    order = {'PK': 'ORDER', 'SK': order_id, 'GSI1PK': 'USER#' + sub, 'GSI1SK': 'ORDER#' + created + '#' + order_id,
             'userId': sub, 'email': email, 'createdAt': created, 'orderId': order_id, 'items': products,
             'amount': total, 'currency': CURRENCY, 'status': 'pending_payment', 'paymentMethod': 'stripe', 'paymentStatus': 'unpaid', 'fulfillmentStatus': 'unfulfilled'}
    DB.put_item(Item=order, ConditionExpression='attribute_not_exists(PK)')
    # Derive canonical API Gateway URL from the trusted request context to avoid
    # a CloudFormation ShopApi <-> ApiFunction circular dependency.
    rc = event.get('requestContext') or {}
    domain = rc.get('domainName')
    if not domain or not re.fullmatch(r'[a-zA-Z0-9.-]+', domain):
        raise ValueError('API Gateway domain is unavailable')
    stage = rc.get('stage', '$default')
    url = 'https://' + domain + (('/' + stage) if stage and stage != '$default' else '')
    params = {'mode': 'payment', 'client_reference_id': order_id,
              'success_url': url + '/?checkout=success&session_id={CHECKOUT_SESSION_ID}',
              'cancel_url': url + '/?checkout=cancel',
              'customer_email': email,
              'billing_address_collection': 'required',
              'phone_number_collection[enabled]': 'true',
              'shipping_address_collection[allowed_countries][0]': 'IN',
              'shipping_address_collection[allowed_countries][1]': 'US',
              'metadata[order_id]': order_id,
              'metadata[user_id]': sub,
              'expires_at': str(int(time.time()) + 1800)}
    for i, p in enumerate(products):
        prefix = f'line_items[{i}]'
        params.update({f'{prefix}[price_data][currency]': CURRENCY,
                       f'{prefix}[price_data][unit_amount]': str(p['price']),
                       f'{prefix}[price_data][product_data][name]': p['name'][:200],
                       f'{prefix}[quantity]': str(p['quantity'])})
    try:
        session = stripe_post(params)
        if not session.get('id') or not session.get('url'):
            raise RuntimeError('Payment provider did not return a checkout URL')
        DB.update_item(Key={'PK': 'ORDER', 'SK': order_id},
                       UpdateExpression='SET stripeSession=:s', ExpressionAttributeValues={':s': session['id']})
        return reply(200, {'checkoutUrl': session['url'], 'orderId': order_id})
    except Exception:
        DB.update_item(Key={'PK': 'ORDER', 'SK': order_id}, UpdateExpression='SET #s=:x',
                       ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':x': 'checkout_error'})
        raise



def validate_cod_shipping(data):
    """Only allow a minimum, validated Indian domestic delivery address."""
    if not isinstance(data, dict):
        raise ValueError('Delivery details are required')
    name = text_field(data.get('name'), 'Recipient name', 2, 100)
    address1 = text_field(data.get('address1'), 'Address', 8, 160)
    city = text_field(data.get('city'), 'City', 2, 80)
    state = text_field(data.get('state'), 'State', 2, 80)
    postal = str(data.get('postalCode') or '').strip()
    phone = re.sub(r'[\s-]', '', str(data.get('phone') or ''))
    if not re.fullmatch(r'[1-9][0-9]{5}', postal):
        raise ValueError('Enter a valid six-digit Indian PIN code')
    if not re.fullmatch(r'(?:\+91)?[6-9][0-9]{9}', phone):
        raise ValueError('Enter a valid Indian mobile number')
    return {'name': name, 'phone': phone, 'address1': address1,
            'city': city, 'state': state, 'postalCode': postal, 'country': 'IN'}


def place_cod_order(event):
    """Save a real unpaid cash-on-delivery order; does not charge a customer."""
    user_id = current_user(event)
    email = user_email(event)
    body = parse_body(event)
    items = body.get('items')
    if not isinstance(items, list) or not 1 <= len(items) <= 15:
        raise ValueError('Cart must contain 1 to 15 products')
    shipping = validate_cod_shipping(body.get('shipping'))
    raw_order_id = body.get('clientOrderId')
    try:
        validated_id = uuid.UUID(raw_order_id, version=4)
        if str(validated_id) != raw_order_id:
            raise ValueError('Incorrect order ID')
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Invalid order request identifier') from None
    # Derive the order ID from the authenticated user + client retry token.
    # It cannot collide with an order belonging to another user.
    order_id = str(uuid.uuid5(uuid.NAMESPACE_URL, user_id + ':' + raw_order_id))
    quantities = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str):
            raise ValueError('Invalid product in cart')
        qty = item.get('quantity')
        if type(qty) is not int or not 1 <= qty <= 10:
            raise ValueError('Quantity must be between 1 and 10')
        quantities[item['id']] = quantities.get(item['id'], 0) + qty
    if any(q > 10 for q in quantities.values()):
        raise ValueError('Maximum 10 of each product')
    order_items = []
    total = 0
    for product_id, qty in quantities.items():
        product = get_product(product_id)
        if not product:
            raise ValueError('A product is unavailable; please refresh your cart')
        price = int(product['price'])
        total += price * qty
        order_items.append({'id': product_id, 'name': str(product['name']),
                            'price': price, 'quantity': qty})
    if total < 50 or total > 50000000:
        raise ValueError('Order total is outside supported limits')
    created = now()
    order = {'PK': 'ORDER', 'SK': order_id, 'orderId': order_id,
             'GSI1PK': 'USER#' + user_id, 'GSI1SK': 'ORDER#' + created + '#' + order_id,
             'userId': user_id, 'email': email, 'items': order_items, 'amount': total,
             'currency': CURRENCY, 'status': 'placed_cod', 'paymentMethod': 'cod',
             'paymentStatus': 'due_on_delivery', 'fulfillmentStatus': 'unfulfilled',
             'shippingAddress': shipping, 'createdAt': created}
    try:
        DB.put_item(Item=order, ConditionExpression='attribute_not_exists(PK)')
    except ClientError as exc:
        if exc.response['Error']['Code'] != 'ConditionalCheckFailedException':
            raise
        existing = DB.get_item(Key={'PK': 'ORDER', 'SK': order_id}, ConsistentRead=True).get('Item')
        if existing and existing.get('userId') == user_id and existing.get('paymentMethod') == 'cod':
            return reply(200, {'orderId': order_id, 'status': existing['status'], 'alreadyPlaced': True})
        return problem(409, 'The order reference is already in use')
    # Persist the order before publishing notifications. SES failures do not
    # undo an accepted order; inspect the DLQ/logs if emails do not arrive.
    try:
        emit('OrderPlaced', {'orderId': order_id, 'email': email,
                             'amount': total, 'currency': CURRENCY, 'items': order_items})
    except Exception as exc:
        print('Order saved; notification event failure', type(exc).__name__)
    return reply(201, {'orderId': order_id, 'status': 'placed_cod', 'paymentMethod': 'cod',
                       'paymentStatus': 'due_on_delivery', 'message': 'Order placed, cash due on delivery'})


def verify_stripe_signature(payload, header):
    fields = {}
    for element in header.split(','):
        if '=' in element:
            k, v = element.split('=', 1)
            fields.setdefault(k.strip(), []).append(v.strip())
    try:
        timestamp = int(fields['t'][0])
    except (KeyError, TypeError, ValueError):
        return False
    if abs(int(time.time()) - timestamp) > 300:
        return False
    signed = str(timestamp).encode() + b'.' + payload
    expected = hmac.new(stripe_secret('webhook').encode(), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, v) for v in fields.get('v1', []))


def emit(kind, detail):
    response = EVENTS.put_events(Entries=[{'Source': 'serverless.commerce', 'DetailType': kind, 'Detail': json.dumps(detail), 'EventBusName': 'default'}])
    if response.get('FailedEntryCount', 0):
        raise RuntimeError('Notification event was not accepted')


def webhook(event):
    raw = event.get('body') or ''
    payload = base64.b64decode(raw) if event.get('isBase64Encoded') else raw.encode('utf-8')
    headers = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
    if not verify_stripe_signature(payload, headers.get('stripe-signature', '')):
        return problem(400, 'Invalid payment signature')
    data = json.loads(payload)
    if data.get('type') not in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        return reply(200, {'received': True})
    session = data.get('data', {}).get('object', {})
    if session.get('payment_status') != 'paid':
        return reply(200, {'received': True})
    order_id = session.get('metadata', {}).get('order_id')
    if not order_id:
        return problem(400, 'Order reference missing')
    order = DB.get_item(Key={'PK': 'ORDER', 'SK': order_id}, ConsistentRead=True).get('Item')
    if not order:
        return problem(404, 'Order not found')
    # Server-side amount and identity verification; browser success URLs do NOT mark an order paid.
    if (session.get('id') != order.get('stripeSession') or
        str(session.get('currency', '')).lower() != order['currency'] or
        int(session.get('amount_total') or -1) != int(order['amount']) or
        session.get('client_reference_id') != order_id):
        return problem(400, 'Payment details do not match the order')
    if order['status'] == 'paid':
        return reply(200, {'received': True})
    try:
        shipping = (session.get('collected_information') or {}).get('shipping_details') or session.get('shipping_details') or {}
        address = shipping.get('address') or {}
        # Store only shipping/fulfillment information, never card details.
        shipping_record = {'name': str(shipping.get('name') or '')[:150],
                           'phone': str(shipping.get('phone') or '')[:35],
                           'address': {k: str(address.get(k) or '')[:160]
                                       for k in ('line1', 'line2', 'city', 'state', 'postal_code', 'country')}}
        DB.update_item(Key={'PK': 'ORDER', 'SK': order_id},
                       UpdateExpression='SET #s=:paid, paymentStatus=:pstatus, paidAt=:date, stripePaymentIntent=:pi, shippingAddress=:ship',
                       ConditionExpression='#s=:pending', ExpressionAttributeNames={'#s': 'status'},
                       ExpressionAttributeValues={':paid': 'paid', ':pstatus': 'paid', ':pending': 'pending_payment',
                                                  ':date': now(), ':pi': session.get('payment_intent') or '', ':ship': shipping_record})
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return reply(200, {'received': True})
        raise
    emit('OrderPaid', {'orderId': order_id, 'email': order['email'], 'amount': int(order['amount']),
                       'currency': order['currency'], 'items': order['items']})
    return reply(200, {'received': True})


def text_field(value, field, min_len, max_len):
    if not isinstance(value, str) or not min_len <= len(value.strip()) <= max_len:
        raise ValueError(f'{field} must contain {min_len} to {max_len} characters')
    return value.strip()


def validate_product(body, product_id=None):
    name = text_field(body.get('name'), 'Name', 2, 120)
    category = text_field(body.get('category'), 'Category', 2, 50)
    description = text_field(body.get('description'), 'Description', 5, 700)
    price = body.get('price')
    if type(price) is not int or price < 50 or price > 100000000:
        raise ValueError('Price must be an integer in the currency minor unit (e.g., paise)')
    image_url = body.get('imageUrl') or ''
    if not isinstance(image_url, str) or len(image_url) > 600 or (image_url and not image_url.startswith('https://')):
        raise ValueError('Product image URL must be a valid HTTPS URL (maximum 600 characters)')
    icon = str(body.get('icon') or '📦')[:8]
    item = {'PK': 'PRODUCT', 'SK': product_id or str(uuid.uuid4()), 'name': name,
            'description': description, 'category': category, 'price': price,
            'icon': icon, 'imageUrl': image_url, 'active': True, 'updatedAt': now()}
    return item


def create_ticket(event):
    sub = current_user(event)
    email = user_email(event)
    body = parse_body(event)
    subject = text_field(body.get('subject'), 'Subject', 3, 120)
    message = text_field(body.get('message'), 'Message', 5, 1500)
    ticket_id, timestamp = str(uuid.uuid4()), now()
    ticket = {'PK': 'TICKET', 'SK': ticket_id, 'GSI1PK': 'USER#' + sub,
              'GSI1SK': 'TICKET#' + timestamp + '#' + ticket_id, 'ticketId': ticket_id,
              'userId': sub, 'email': email, 'subject': subject, 'status': 'open',
              'messages': [{'sender': 'customer', 'message': message, 'at': timestamp}],
              'createdAt': timestamp, 'updatedAt': timestamp}
    DB.put_item(Item=ticket, ConditionExpression='attribute_not_exists(PK)')
    emit('TicketCreated', {'ticketId': ticket_id, 'subject': subject, 'email': email})
    return reply(201, {'ticket': ddb_json(ticket)})


def reply_ticket(event, ticket_id):
    sub = current_user(event)
    ticket = DB.get_item(Key={'PK': 'TICKET', 'SK': ticket_id}).get('Item')
    if not ticket:
        return problem(404, 'Ticket not found')
    admin = is_admin(event)
    if not admin and ticket['userId'] != sub:
        raise PermissionError('Ticket belongs to a different customer')
    if ticket['status'] == 'closed':
        raise ValueError('Reopen the ticket before replying')
    if len(ticket.get('messages', [])) >= 40:
        raise ValueError('Ticket message limit reached; open a new ticket')
    msg = text_field(parse_body(event).get('message'), 'Message', 2, 1500)
    role = 'admin' if admin else 'customer'
    DB.update_item(Key={'PK': 'TICKET', 'SK': ticket_id},
                   UpdateExpression='SET messages=list_append(messages,:m), updatedAt=:t, #s=:s',
                   ExpressionAttributeNames={'#s': 'status'},
                   ExpressionAttributeValues={':m': [{'sender': role, 'message': msg, 'at': now()}],
                                              ':t': now(), ':s': 'in_progress'})
    emit('TicketReply', {'ticketId': ticket_id, 'email': ticket['email'],
                         'subject': ticket['subject'], 'message': msg, 'sender': role})
    return reply(200, {'message': 'Reply sent'})


def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '').rstrip('/') or '/'
    params = event.get('pathParameters') or {}
    try:
        if method == 'GET' and path == '/products':
            return reply(200, {'products': list_products(), 'currency': CURRENCY})
        if method == 'GET' and re.fullmatch(r'/products/[^/]+', path):
            p = get_product(params.get('id') or path.rsplit('/', 1)[-1])
            return reply(200, {'product': p}) if p else problem(404, 'Product not found')
        if method == 'POST' and path == '/webhook/stripe':
            return webhook(event)
        if method == 'POST' and path == '/checkout':
            return checkout(event)
        if method == 'POST' and path == '/orders/cod':
            return place_cod_order(event)
        if method == 'GET' and path == '/orders':
            return reply(200, {'orders': list_user(current_user(event), 'ORDER#')})
        if method == 'GET' and path == '/tickets':
            return reply(200, {'tickets': list_user(current_user(event), 'TICKET#')})
        if method == 'POST' and path == '/tickets':
            return create_ticket(event)
        if method == 'POST' and re.fullmatch(r'/tickets/[^/]+/reply', path):
            return reply_ticket(event, params.get('id') or path.split('/')[2])
        if path.startswith('/admin/'):
            admin_only(event)
            if method == 'GET' and path == '/admin/orders':
                return reply(200, {'orders': list_pk('ORDER')})
            if method == 'GET' and path == '/admin/tickets':
                return reply(200, {'tickets': list_pk('TICKET')})
            if method == 'PATCH' and re.fullmatch(r'/admin/orders/[^/]+', path):
                oid = params.get('id') or path.rsplit('/', 1)[-1]
                status = parse_body(event).get('fulfillmentStatus')
                if status not in ('unfulfilled', 'processing', 'shipped', 'delivered'):
                    raise ValueError('Unsupported fulfillment status')
                order = DB.get_item(Key={'PK': 'ORDER', 'SK': oid}, ConsistentRead=True).get('Item')
                if not order:
                    return problem(404, 'Order not found')
                if order['status'] not in ('paid', 'placed_cod', 'cod_collected'):
                    raise ValueError('Only placed orders may be fulfilled')
                was_shipped = order.get('fulfillmentStatus') == 'shipped'
                DB.update_item(Key={'PK': 'ORDER', 'SK': oid},
                               UpdateExpression='SET fulfillmentStatus=:s, updatedAt=:t',
                               ExpressionAttributeValues={':s': status, ':t': now()})
                if status == 'shipped' and not was_shipped:
                    emit('OrderShipped', {'email': order['email'], 'orderId': oid})
                return reply(200, {'fulfillmentStatus': status})
            if method == 'PATCH' and re.fullmatch(r'/admin/orders/[^/]+/collect', path):
                oid = params.get('id') or path.split('/')[3]
                # The administrator must physically receive cash before using this action.
                try:
                    updated = DB.update_item(
                        Key={'PK': 'ORDER', 'SK': oid},
                        UpdateExpression='SET #s=:collected, paymentStatus=:paid, paymentCollectedAt=:t',
                        ConditionExpression='#s=:cod AND paymentMethod=:method',
                        ExpressionAttributeNames={'#s': 'status'},
                        ExpressionAttributeValues={':collected': 'cod_collected', ':paid': 'collected',
                                                   ':t': now(), ':cod': 'placed_cod', ':method': 'cod'},
                        ReturnValues='ALL_NEW')['Attributes']
                except ClientError as exc:
                    if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
                        return problem(409, 'Order is not an unpaid COD order')
                    raise
                try:
                    emit('CodPaymentCollected', {'email': updated['email'], 'orderId': oid,
                                                 'amount': int(updated['amount']),
                                                 'currency': updated['currency']})
                except Exception as exc:
                    print('Payment status updated; notification failure', type(exc).__name__)
                return reply(200, {'status': 'cod_collected', 'paymentStatus': 'collected'})
            if method == 'POST' and path == '/admin/products':
                item = validate_product(parse_body(event))
                DB.put_item(Item=item, ConditionExpression='attribute_not_exists(PK)')
                return reply(201, {'product': ddb_json(item)})
            if method == 'PUT' and re.fullmatch(r'/admin/products/[^/]+', path):
                pid = params.get('id') or path.rsplit('/', 1)[-1]
                prior = DB.get_item(Key={'PK': 'PRODUCT', 'SK': pid}).get('Item')
                if not prior:
                    return problem(404, 'Product not found')
                item = validate_product(parse_body(event), pid)
                DB.put_item(Item=item)
                return reply(200, {'product': ddb_json(item)})
            if method == 'DELETE' and re.fullmatch(r'/admin/products/[^/]+', path):
                pid = params.get('id') or path.rsplit('/', 1)[-1]
                DB.update_item(Key={'PK': 'PRODUCT', 'SK': pid},
                               UpdateExpression='SET active=:f', ConditionExpression='attribute_exists(PK)',
                               ExpressionAttributeValues={':f': False})
                return reply(200, {'deleted': True})
            if method == 'PATCH' and re.fullmatch(r'/admin/tickets/[^/]+', path):
                status = parse_body(event).get('status')
                if status not in ('open', 'in_progress', 'closed'):
                    raise ValueError('Unsupported ticket status')
                tid = params.get('id') or path.rsplit('/', 1)[-1]
                DB.update_item(Key={'PK': 'TICKET', 'SK': tid},
                               UpdateExpression='SET #s=:s, updatedAt=:t',
                               ConditionExpression='attribute_exists(PK)',
                               ExpressionAttributeNames={'#s': 'status'},
                               ExpressionAttributeValues={':s': status, ':t': now()})
                return reply(200, {'status': status})
        return problem(404, 'Route not found')
    except PermissionError as exc:
        return problem(403, str(exc))
    except (ValueError, json.JSONDecodeError) as exc:
        return problem(400, str(exc))
    except ClientError as exc:
        if exc.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return problem(409, 'Resource was changed or does not exist')
        print('AWS operation failed', exc.response['Error']['Code'])
        return problem(503, 'A service is temporarily unavailable')
    except Exception as exc:
        print('API exception', type(exc).__name__, str(exc)[:150])
        return problem(503, 'Unable to complete this operation at the moment')
