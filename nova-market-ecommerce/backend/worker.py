"""SQS-triggered notification Lambda; handles events forwarded by EventBridge."""
import json
import os
import boto3

SES = boto3.client('ses')
SNS = boto3.client('sns')
SOURCE = os.environ['EMAIL_FROM']
TOPIC = os.environ['NOTIFY_TOPIC_ARN']


def send_email(destination, subject, body):
    SES.send_email(Source=SOURCE, Destination={'ToAddresses': [destination]},
                   Message={'Subject': {'Data': subject[:200], 'Charset': 'UTF-8'},
                            'Body': {'Text': {'Data': body[:15000], 'Charset': 'UTF-8'}}})


def notify_admin(subject, body):
    SNS.publish(TopicArn=TOPIC, Subject=subject[:100], Message=body[:20000])


def handle(message):
    detail = message.get('detail') or {}
    kind = message.get('detail-type')
    if kind == 'OrderPlaced':
        lines = [f"{x['quantity']} x {x['name']}" for x in detail['items']]
        amount = int(detail['amount']) / 100
        body = (f"Order placed: {detail['orderId']}\n\n" + '\n'.join(lines) +
                f"\nTotal: {detail['currency'].upper()} {amount:.2f}\n"
                "Payment: Cash on delivery (NOT PAID).\n"
                "An administrator must confirm shipping. Thank you for your order.")
        send_email(detail['email'], 'COD order placed ' + detail['orderId'][:8], body)
        notify_admin('New COD order', body + '\nCustomer: ' + detail['email'])
    elif kind == 'CodPaymentCollected':
        amount = int(detail['amount']) / 100
        send_email(detail['email'], 'COD cash received ' + detail['orderId'][:8],
                   f"We recorded cash collected for order {detail['orderId']}.\n"
                   f"Amount: {detail['currency'].upper()} {amount:.2f}")
    elif kind == 'OrderPaid':
        lines = [f"{x['quantity']} x {x['name']}" for x in detail['items']]
        amount = int(detail['amount']) / 100
        body = f"Payment confirmed!\n\nOrder: {detail['orderId']}\n" + '\n'.join(lines)
        body += f"\nTotal: {detail['currency'].upper()} {amount:.2f}\n\nThank you for shopping."
        send_email(detail['email'], 'Order confirmation ' + detail['orderId'][:8], body)
        notify_admin('New paid order', body + '\nCustomer: ' + detail['email'])
    elif kind == 'OrderShipped':
        send_email(detail['email'], 'Your order has shipped ' + detail['orderId'][:8],
                   'Your order ' + detail['orderId'] + ' is marked as shipped. Please contact support for details.')
    elif kind == 'TicketCreated':
        send_email(detail['email'], 'Ticket received ' + detail['ticketId'][:8],
                   'We received your support request: ' + detail['subject'] + '\nTicket: ' + detail['ticketId'])
        notify_admin('New support ticket', 'Ticket: ' + detail['ticketId'] + '\n' + detail['subject'] + '\n' + detail['email'])
    elif kind == 'TicketReply':
        body = 'Ticket: ' + detail['ticketId'] + '\nSubject: ' + detail['subject'] + '\n\n' + detail['message']
        if detail['sender'] == 'admin':
            send_email(detail['email'], 'Support replied ' + detail['ticketId'][:8], body)
        else:
            notify_admin('Support ticket reply', body + '\nFrom: ' + detail['email'])


def lambda_handler(event, context):
    failed = []
    for rec in event.get('Records', []):
        try:
            handle(json.loads(rec['body']))
        except Exception as exc:
            print('Worker failed', rec['messageId'], type(exc).__name__, str(exc)[:160])
            failed.append({'itemIdentifier': rec['messageId']})
    return {'batchItemFailures': failed}
