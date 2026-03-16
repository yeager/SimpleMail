"""IMAP/SMTP backend for SimpleMail with secure credential handling."""

import email
import email.header
import email.utils
import imaplib
import smtplib
import ssl
import threading
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Callable, Optional

import keyring

SERVICE_NAME = "simplemail"


@dataclass
class MailMessage:
    """Represents an email message."""

    uid: str = ""
    sender: str = ""
    subject: str = ""
    date: str = ""
    body: str = ""
    is_read: bool = False
    raw: bytes = b""


@dataclass
class MailConfig:
    """Email server configuration."""

    imap_server: str = ""
    imap_port: int = 993
    smtp_server: str = ""
    smtp_port: int = 587
    email_address: str = ""

    def is_valid(self) -> bool:
        return bool(self.imap_server and self.smtp_server and self.email_address)


def save_password(email_address: str, password: str):
    """Store password securely using system keyring."""
    keyring.set_password(SERVICE_NAME, email_address, password)


def get_password(email_address: str) -> Optional[str]:
    """Retrieve password from system keyring."""
    return keyring.get_password(SERVICE_NAME, email_address)


def delete_password(email_address: str):
    """Remove stored password."""
    try:
        keyring.delete_password(SERVICE_NAME, email_address)
    except keyring.errors.PasswordDeleteError:
        pass


def _decode_header(raw_header: str) -> str:
    """Decode an email header value."""
    if not raw_header:
        return ""
    parts = email.header.decode_header(raw_header)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_body(msg: email.message.Message) -> str:
    """Extract the plain-text body from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        # Fallback: try HTML
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


class MailBackend:
    """Handles IMAP/SMTP operations."""

    def __init__(self, config: MailConfig):
        self.config = config
        self._imap: Optional[imaplib.IMAP4_SSL] = None
        self._lock = threading.Lock()

    @property
    def is_connected(self) -> bool:
        return self._imap is not None

    def connect(self) -> bool:
        """Connect to IMAP server using SSL."""
        password = get_password(self.config.email_address)
        if not password:
            return False
        try:
            ctx = ssl.create_default_context()
            self._imap = imaplib.IMAP4_SSL(
                self.config.imap_server, self.config.imap_port, ssl_context=ctx
            )
            self._imap.login(self.config.email_address, password)
            return True
        except Exception:
            self._imap = None
            return False

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self._imap:
            try:
                self._imap.logout()
            except Exception:
                pass
            self._imap = None

    def fetch_messages(self, folder: str = "INBOX", limit: int = 50) -> list[MailMessage]:
        """Fetch recent messages from the given folder."""
        if not self._imap:
            return []
        messages = []
        try:
            with self._lock:
                self._imap.select(folder, readonly=True)
                _, data = self._imap.search(None, "ALL")
                uids = data[0].split()
                # Get most recent messages
                for uid in reversed(uids[-limit:]):
                    _, msg_data = self._imap.fetch(uid, "(RFC822 FLAGS)")
                    if not msg_data or not msg_data[0]:
                        continue
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)

                    flags_data = msg_data[0][0] if msg_data[0][0] else b""
                    is_read = b"\\Seen" in flags_data

                    mail_msg = MailMessage(
                        uid=uid.decode(),
                        sender=_decode_header(msg.get("From", "")),
                        subject=_decode_header(msg.get("Subject", "(inget ämne)")),
                        date=msg.get("Date", ""),
                        body=_extract_body(msg),
                        is_read=is_read,
                        raw=raw,
                    )
                    messages.append(mail_msg)
        except Exception:
            pass
        return messages

    def send_message(self, to: str, subject: str, body: str) -> bool:
        """Send an email via SMTP with STARTTLS."""
        password = get_password(self.config.email_address)
        if not password:
            return False
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config.email_address
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            ctx = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=ctx)
                server.login(self.config.email_address, password)
                server.send_message(msg)
            return True
        except Exception:
            return False

    def delete_message(self, uid: str, folder: str = "INBOX") -> bool:
        """Mark a message as deleted."""
        if not self._imap:
            return False
        try:
            with self._lock:
                self._imap.select(folder)
                self._imap.store(uid.encode(), "+FLAGS", "\\Deleted")
                self._imap.expunge()
            return True
        except Exception:
            return False

    def fetch_messages_async(
        self, callback: Callable, folder: str = "INBOX", limit: int = 50
    ):
        """Fetch messages in a background thread."""
        def _worker():
            messages = self.fetch_messages(folder, limit)
            callback(messages)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def send_message_async(
        self, to: str, subject: str, body: str, callback: Callable
    ):
        """Send a message in a background thread."""
        def _worker():
            success = self.send_message(to, subject, body)
            callback(success)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
