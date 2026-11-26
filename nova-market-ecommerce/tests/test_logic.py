import hashlib
import hmac
import importlib
import os
import sys
import time
import unittest
from unittest.mock import patch

os.environ.setdefault('AWS_ACCESS_KEY_ID', 'local-testing-key')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'local-testing-secret')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-west-2')
os.environ.setdefault('DATA_TABLE', 'test-table')
os.environ.setdefault('USER_POOL_ID', 'us-west-2_test')
os.environ.setdefault('STRIPE_WEBHOOK_PARAMETER', '/x/webhook')
os.environ.setdefault('STRIPE_KEY_PARAMETER', '/x/key')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
api = importlib.import_module('api')


class CheckoutSecurityTests(unittest.TestCase):
    def test_valid_webhook_signature(self):
        timestamp = int(time.time())
        payload = b'{"type":"checkout.session.completed"}'
        sig = hmac.new(b'whsec_unit_test', str(timestamp).encode() + b'.' + payload, hashlib.sha256).hexdigest()
        with patch.object(api, 'stripe_secret', return_value='whsec_unit_test'):
            self.assertTrue(api.verify_stripe_signature(payload, f't={timestamp},v1={sig}'))
            self.assertFalse(api.verify_stripe_signature(payload + b' ', f't={timestamp},v1={sig}'))
            self.assertFalse(api.verify_stripe_signature(payload, f't={timestamp-3600},v1={sig}'))

    def test_product_price_integer_minor_units(self):
        body = dict(name='Test product', category='Home', description='Reliable everyday item', price=1500)
        self.assertEqual(api.validate_product(body)['price'], 1500)
        for price in ('1000', 120.5, 0, -50, True):
            with self.assertRaises(ValueError):
                api.validate_product(dict(body, price=price))

    def test_admin_group_validation(self):
        def ev(group):
            return {'requestContext': {'authorizer': {'jwt': {'claims': {'sub': 'abc', 'token_use': 'access', 'cognito:groups': group}}}}}
        self.assertTrue(api.is_admin(ev('[admin, staff]')))
        self.assertFalse(api.is_admin(ev('[superadmin]')))
        self.assertFalse(api.is_admin(ev('[]')))

    def test_unauthorized_no_subject(self):
        with self.assertRaises(PermissionError):
            api.current_user({})

    def test_site_config_uses_gateway_host(self):
        import importlib.util
        import json
        from pathlib import Path
        module_path = Path(__file__).resolve().parents[1] / 'frontend' / 'storefront_handler.py'
        spec = importlib.util.spec_from_file_location('storefront_handler', module_path)
        site = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(site)
        event = {'rawPath': '/config.js', 'requestContext': {
            'domainName': 'shop.execute-api.us-west-2.amazonaws.com',
            'stage': '$default'}}
        with patch.dict(os.environ, {'USER_POOL_CLIENT_ID': 'testclient',
                                     'USER_POOL_ID': 'us-west-2_test',
                                     'STORE_REGION': 'us-west-2'}):
            res = site.lambda_handler(event, None)
        self.assertEqual(res['statusCode'], 200)
        cfg = json.loads(res['body'].split(' = ', 1)[1].rstrip(';'))
        self.assertEqual(cfg['apiUrl'], 'https://shop.execute-api.us-west-2.amazonaws.com')

    def test_checkout_never_trusts_client_price(self):
        ev = {'body': '{"items":[{"id":"test", "quantity":1, "price":1}]}',
              'requestContext': {'domainName': 'example.execute-api.us-west-2.amazonaws.com', 'stage': '$default'}}
        with patch.object(api, 'current_user', return_value='customer'), patch.object(api, 'user_email', return_value='u@example.org'), patch.object(api, 'get_product', return_value={'name': 'Product', 'price': 2000}), patch.object(api, 'stripe_post', return_value={'id': 'cs_test_123','url': 'https://checkout.stripe.com/pay/123'}), patch.object(api.DB, 'put_item'), patch.object(api.DB, 'update_item'):
            data = api.checkout(ev)
            self.assertIn('checkoutUrl', data['body'])




class CodOrderTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            'body': __import__('json').dumps({
                'items': [{'id': 'ceramic-mug', 'quantity': 2, 'price': 1}],
                'clientOrderId': 'a157b445-5c11-4d8c-8f19-21d183b9f789',
                'shipping': {'name': 'Test Customer', 'phone': '9876543210',
                             'address1': '12 Sample Street', 'city': 'Chennai',
                             'state': 'Tamil Nadu', 'postalCode': '600001'}
            })
        }

    def test_cod_order_uses_catalog_price_and_emits_mail_event(self):
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        with patch.object(api, 'current_user', return_value='sub-123'), \
             patch.object(api, 'user_email', return_value='customer@example.com'), \
             patch.object(api, 'get_product', return_value={'name': 'Mug', 'price': 59900}), \
             patch.object(api, 'DB', mock_db), \
             patch.object(api, 'emit') as emit:
            result = api.place_cod_order(self.request)
        self.assertEqual(result['statusCode'], 201)
        order = mock_db.put_item.call_args.kwargs['Item']
        self.assertEqual(order['amount'], 119800)
        self.assertEqual(order['status'], 'placed_cod')
        self.assertEqual(order['paymentStatus'], 'due_on_delivery')
        self.assertEqual(order['shippingAddress']['postalCode'], '600001')
        emit.assert_called_once()
        self.assertEqual(emit.call_args.args[0], 'OrderPlaced')

    def test_cod_rejects_invalid_pin_and_phone(self):
        for bad_key, bad_value in [('postalCode', '12345'), ('phone', '1234')]:
            shipping = {'name': 'Test Customer', 'phone': '9876543210',
                        'address1': '12 Sample Street', 'city': 'Chennai',
                        'state': 'Tamil Nadu', 'postalCode': '600001'}
            shipping[bad_key] = bad_value
            with self.assertRaises(ValueError):
                api.validate_cod_shipping(shipping)

    def test_cod_identical_retry_returns_existing_order(self):
        from unittest.mock import MagicMock
        from botocore.exceptions import ClientError
        duplicate = ClientError({'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'exists'}}, 'PutItem')
        mock_db = MagicMock()
        mock_db.put_item.side_effect = duplicate
        mock_db.get_item.return_value = {'Item': {'userId': 'sub-123', 'paymentMethod': 'cod', 'status': 'placed_cod'}}
        with patch.object(api, 'current_user', return_value='sub-123'), \
             patch.object(api, 'user_email', return_value='customer@example.com'), \
             patch.object(api, 'get_product', return_value={'name': 'Mug', 'price': 59900}), \
             patch.object(api, 'DB', mock_db), \
             patch.object(api, 'emit') as emit:
            result = api.place_cod_order(self.request)
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('"alreadyPlaced": true', result['body'])
        emit.assert_not_called()


class NotificationTests(unittest.TestCase):
    def test_cod_order_notifications_send_email_and_admin_alert(self):
        import importlib.util
        from pathlib import Path
        module_path = Path(__file__).resolve().parents[1] / 'backend' / 'worker.py'
        spec = importlib.util.spec_from_file_location('notification_worker', module_path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'EMAIL_FROM': 'merchant@example.org',
                                     'NOTIFY_TOPIC_ARN': 'arn:aws:sns:us-west-2:111111111111:demo'}):
            spec.loader.exec_module(module)
        with patch.object(module, 'send_email') as mail, patch.object(module, 'notify_admin') as notice:
            module.handle({'detail-type': 'OrderPlaced', 'detail': {
                'orderId': 'aaaaaaaa-1111', 'email': 'shopper@example.org',
                'amount': 119800, 'currency': 'inr',
                'items': [{'name': 'Mug', 'quantity': 2}]}})
        mail.assert_called_once()
        notice.assert_called_once()
        self.assertIn('NOT PAID',mail.call_args.args[2])
