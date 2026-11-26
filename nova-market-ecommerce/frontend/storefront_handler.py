"""Serve static assets and generated configuration through HTTPS API Gateway."""
import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent
FILES = {'/': ('index.html', 'text/html; charset=utf-8'),
         '/index.html': ('index.html', 'text/html; charset=utf-8'),
         '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
         '/app.js': ('app.js', 'application/javascript; charset=utf-8')}


def lambda_handler(event, context):
    path = event.get('rawPath', '/')
    if path == '/config.js':
        rc = event.get('requestContext') or {}
        domain = rc.get('domainName')
        if not domain or not all(c.isalnum() or c in '.-' for c in domain):
            return {'statusCode': 500, 'body': 'API Gateway host unavailable'}
        stage = rc.get('stage', '$default')
        api_base = 'https://' + domain + (('/' + stage) if stage and stage != '$default' else '')
        cfg = {'apiUrl': api_base,
               'userPoolId': os.environ['USER_POOL_ID'],
               'clientId': os.environ['USER_POOL_CLIENT_ID'],
               'region': os.environ['STORE_REGION'], 'currency': 'inr'}
        return {'statusCode': 200,
                'headers': {'content-type': 'application/javascript; charset=utf-8',
                            'cache-control': 'no-store', 'x-content-type-options': 'nosniff'},
                'body': 'window.STORE_CONFIG = ' + json.dumps(cfg) + ';'}
    if path not in FILES:
        return {'statusCode': 404, 'body': 'Not found'}
    filename, mime = FILES[path]
    return {'statusCode': 200,
            'headers': {'content-type': mime, 'cache-control': 'public,max-age=60',
                        'x-content-type-options': 'nosniff'},
            'body': (BASE / filename).read_text(encoding='utf-8')}
