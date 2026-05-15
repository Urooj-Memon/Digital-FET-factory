"""Gmail channel handler - receives emails via Gmail API + Pub/Sub, sends replies."""

import os
import json
import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from src.kafka_client import FTEKafkaProducer, TOPICS

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_WATCH_TOPIC = os.getenv("GMAIL_PUBSUB_TOPIC", "projects/my-project/topics/gmail-fte")


def get_gmail_service():
    """Authenticate and return the Gmail API service."""
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def setup_gmail_watch(service):
    """Set up Gmail Pub/Sub push notifications for incoming emails."""
    request = {
        "labelIds": ["INBOX"],
        "topicName": GMAIL_WATCH_TOPIC,
    }
    return service.users().watch(userId="me", body=request).execute()


def parse_email_message(service, message_id: str) -> dict:
    """Parse a Gmail message into a structured dict."""
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()

    headers = msg.get("payload", {}).get("headers", [])
    header_map = {h["name"].lower(): h["value"] for h in headers}

    # Extract body
    body = ""
    payload = msg.get("payload", {})
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    break

    return {
        "message_id": message_id,
        "from": header_map.get("from", ""),
        "to": header_map.get("to", ""),
        "subject": header_map.get("subject", "No Subject"),
        "body": body,
        "date": header_map.get("date", ""),
        "thread_id": msg.get("threadId", ""),
    }


async def process_gmail_notification(notification: dict, kafka_producer: FTEKafkaProducer):
    """Process a Gmail Pub/Sub notification and publish to Kafka."""
    data = notification.get("message", {}).get("data", "")
    if data:
        decoded = json.loads(base64.urlsafe_b64decode(data).decode("utf-8"))
        history_id = decoded.get("historyId")

        service = get_gmail_service()

        # Get new messages since the history ID
        history = (
            service.users()
            .history()
            .list(userId="me", startHistoryId=history_id, historyTypes=["messageAdded"])
            .execute()
        )

        for record in history.get("history", []):
            for msg_added in record.get("messagesAdded", []):
                msg_id = msg_added["message"]["id"]
                email_data = parse_email_message(service, msg_id)

                # Extract sender email
                from_field = email_data["from"]
                customer_email = from_field
                if "<" in from_field and ">" in from_field:
                    customer_email = from_field.split("<")[1].split(">")[0]

                # Extract sender name
                customer_name = from_field.split("<")[0].strip().strip('"') if "<" in from_field else ""

                event = {
                    "channel": "email",
                    "customer_email": customer_email,
                    "customer_name": customer_name,
                    "subject": email_data["subject"],
                    "body": email_data["body"],
                    "message_id": email_data["message_id"],
                    "thread_id": email_data["thread_id"],
                }

                await kafka_producer.publish(TOPICS["email_inbound"], event)


def send_email_reply(to: str, subject: str, body: str, thread_id: str = None):
    """Send an email reply via Gmail API."""
    service = get_gmail_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    send_body = {"raw": raw}

    if thread_id:
        send_body["threadId"] = thread_id

    return service.users().messages().send(userId="me", body=send_body).execute()
