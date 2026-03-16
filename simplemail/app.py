#!/usr/bin/env python3
"""SimpleMail - Tillgänglig e-postklient med piktogramstöd och uppläsning."""

import json
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk, Pango  # noqa: E402

from simplemail.i18n import setup_i18n  # noqa: E402
from simplemail.mail_backend import MailBackend, MailConfig, MailMessage, save_password, get_password  # noqa: E402
from simplemail.tts import TTSEngine  # noqa: E402

_ = setup_i18n()

CONFIG_DIR = os.path.join(GLib.get_user_config_dir(), "simplemail")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Large font CSS for accessibility
CSS = b"""
.large-button {
    min-height: 56px;
    min-width: 56px;
    font-size: 18px;
    font-weight: bold;
    padding: 12px 20px;
    border-radius: 12px;
}
.large-button image {
    -gtk-icon-size: 32px;
}
.mail-subject {
    font-size: 18px;
    font-weight: bold;
}
.mail-sender {
    font-size: 15px;
}
.mail-date {
    font-size: 13px;
    opacity: 0.7;
}
.mail-body {
    font-size: 17px;
    padding: 16px;
}
.mail-row {
    padding: 12px 16px;
    min-height: 60px;
}
.mail-row-unread {
    font-weight: bold;
}
.welcome-label {
    font-size: 22px;
    font-weight: bold;
}
.status-label {
    font-size: 14px;
    padding: 6px 12px;
}
.compose-entry {
    font-size: 16px;
    min-height: 44px;
}
.pictogram-icon {
    min-width: 40px;
    min-height: 40px;
}
"""


def _load_config() -> MailConfig:
    """Load mail configuration from disk."""
    config = MailConfig()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            config.imap_server = data.get("imap_server", "")
            config.imap_port = data.get("imap_port", 993)
            config.smtp_server = data.get("smtp_server", "")
            config.smtp_port = data.get("smtp_port", 587)
            config.email_address = data.get("email_address", "")
        except Exception:
            pass
    return config


def _save_config(config: MailConfig):
    """Save mail configuration to disk."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    data = {
        "imap_server": config.imap_server,
        "imap_port": config.imap_port,
        "smtp_server": config.smtp_server,
        "smtp_port": config.smtp_port,
        "email_address": config.email_address,
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _icon_button(icon_name: str, label: str, tooltip: str = "") -> Gtk.Button:
    """Create a large, accessible button with icon and label."""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    image = Gtk.Image.new_from_icon_name(icon_name)
    image.set_pixel_size(32)
    image.add_css_class("pictogram-icon")
    box.append(image)
    lbl = Gtk.Label(label=label)
    box.append(lbl)
    btn = Gtk.Button()
    btn.set_child(box)
    btn.add_css_class("large-button")
    btn.set_tooltip_text(tooltip or label)
    return btn


class SettingsDialog(Adw.Window):
    """Dialog for configuring email account settings."""

    def __init__(self, parent, config: MailConfig, on_save):
        super().__init__(
            title=_("Email Settings"),
            default_width=500,
            default_height=520,
            modal=True,
            transient_for=parent,
        )
        self._config = config
        self._on_save = on_save

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        # IMAP settings
        group_imap = Adw.PreferencesGroup(title="IMAP")
        self._imap_server = Adw.EntryRow(title=_("IMAP Server:"))
        self._imap_server.set_text(config.imap_server)
        group_imap.add(self._imap_server)
        self._imap_port = Adw.EntryRow(title=_("IMAP Port:"))
        self._imap_port.set_text(str(config.imap_port))
        group_imap.add(self._imap_port)
        box.append(group_imap)

        # SMTP settings
        group_smtp = Adw.PreferencesGroup(title="SMTP")
        self._smtp_server = Adw.EntryRow(title=_("SMTP Server:"))
        self._smtp_server.set_text(config.smtp_server)
        group_smtp.add(self._smtp_server)
        self._smtp_port = Adw.EntryRow(title=_("SMTP Port:"))
        self._smtp_port.set_text(str(config.smtp_port))
        group_smtp.add(self._smtp_port)
        box.append(group_smtp)

        # Account
        group_account = Adw.PreferencesGroup(title=_("Email:"))
        self._email = Adw.EntryRow(title=_("Email:"))
        self._email.set_text(config.email_address)
        group_account.add(self._email)
        self._password = Adw.PasswordEntryRow(title=_("Password:"))
        existing_pw = get_password(config.email_address) or ""
        self._password.set_text(existing_pw)
        group_account.add(self._password)
        box.append(group_account)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.END)

        cancel_btn = _icon_button("window-close-symbolic", _("Cancel"))
        cancel_btn.connect("clicked", lambda _: self.close())
        btn_box.append(cancel_btn)

        save_btn = _icon_button("document-save-symbolic", _("Save"))
        save_btn.connect("clicked", self._on_save_clicked)
        save_btn.add_css_class("suggested-action")
        btn_box.append(save_btn)

        box.append(btn_box)
        toolbar.set_content(box)
        self.set_content(toolbar)

    def _on_save_clicked(self, _btn):
        self._config.imap_server = self._imap_server.get_text()
        try:
            self._config.imap_port = int(self._imap_port.get_text())
        except ValueError:
            self._config.imap_port = 993
        self._config.smtp_server = self._smtp_server.get_text()
        try:
            self._config.smtp_port = int(self._smtp_port.get_text())
        except ValueError:
            self._config.smtp_port = 587
        self._config.email_address = self._email.get_text()

        pw = self._password.get_text()
        if pw:
            save_password(self._config.email_address, pw)

        _save_config(self._config)
        self._on_save(self._config)
        self.close()


class ComposeDialog(Adw.Window):
    """Dialog for composing a new email."""

    def __init__(self, parent, on_send, reply_to: str = "", reply_subject: str = ""):
        super().__init__(
            title=_("Compose"),
            default_width=600,
            default_height=550,
            modal=True,
            transient_for=parent,
        )
        self._on_send = on_send

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        # To field
        to_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        to_label = Gtk.Label(label=_("To:"))
        to_label.set_xalign(0)
        to_label.set_size_request(80, -1)
        self._to_entry = Gtk.Entry()
        self._to_entry.set_hexpand(True)
        self._to_entry.add_css_class("compose-entry")
        self._to_entry.set_text(reply_to)
        to_box.append(to_label)
        to_box.append(self._to_entry)
        box.append(to_box)

        # Subject field
        subj_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        subj_label = Gtk.Label(label=_("Subject:"))
        subj_label.set_xalign(0)
        subj_label.set_size_request(80, -1)
        self._subject_entry = Gtk.Entry()
        self._subject_entry.set_hexpand(True)
        self._subject_entry.add_css_class("compose-entry")
        if reply_subject:
            prefix = "Re: " if not reply_subject.startswith("Re:") else ""
            self._subject_entry.set_text(f"{prefix}{reply_subject}")
        subj_box.append(subj_label)
        subj_box.append(self._subject_entry)
        box.append(subj_box)

        # Message body
        msg_label = Gtk.Label(label=_("Message:"))
        msg_label.set_xalign(0)
        box.append(msg_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_min_content_height(200)
        self._body_view = Gtk.TextView()
        self._body_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._body_view.add_css_class("mail-body")
        scroll.set_child(self._body_view)
        box.append(scroll)

        # Send button
        send_btn = _icon_button("mail-send-symbolic", _("Send"), _("Send"))
        send_btn.add_css_class("suggested-action")
        send_btn.set_halign(Gtk.Align.END)
        send_btn.connect("clicked", self._on_send_clicked)
        box.append(send_btn)

        toolbar.set_content(box)
        self.set_content(toolbar)

    def _on_send_clicked(self, _btn):
        to = self._to_entry.get_text().strip()
        subject = self._subject_entry.get_text().strip()
        buf = self._body_view.get_buffer()
        body = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        if to:
            self._on_send(to, subject, body)
            self.close()


class SimpleMailWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, app):
        super().__init__(application=app, title="SimpleMail", default_width=1000, default_height=700)
        self._config = _load_config()
        self._backend = MailBackend(self._config)
        self._tts = TTSEngine()
        self._messages: list[MailMessage] = []
        self._selected_message: MailMessage | None = None

        self._apply_css()
        self._build_ui()
        self._update_status()

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        toolbar_view = Adw.ToolbarView()
        header = Adw.HeaderBar()

        # Header buttons
        settings_btn = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_btn.set_tooltip_text(_("Settings"))
        settings_btn.connect("clicked", self._on_settings)
        header.pack_start(settings_btn)

        about_btn = Gtk.Button(icon_name="help-about-symbolic")
        about_btn.set_tooltip_text(_("About"))
        about_btn.connect("clicked", self._on_about)
        header.pack_end(about_btn)

        toolbar_view.add_top_bar(header)

        # Main content: split pane
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(380)
        paned.set_shrink_start_child(False)
        paned.set_shrink_end_child(False)

        # --- Left panel: action buttons + message list ---
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left_box.set_size_request(320, -1)
        left_box.set_margin_top(8)
        left_box.set_margin_start(8)
        left_box.set_margin_end(4)
        left_box.set_margin_bottom(8)

        # Action button bar
        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        action_bar.set_homogeneous(True)

        self._connect_btn = _icon_button("network-transmit-symbolic", _("Connect"))
        self._connect_btn.connect("clicked", self._on_connect)
        action_bar.append(self._connect_btn)

        refresh_btn = _icon_button("view-refresh-symbolic", _("Refresh"))
        refresh_btn.connect("clicked", self._on_refresh)
        action_bar.append(refresh_btn)

        compose_btn = _icon_button("mail-message-new-symbolic", _("Compose"))
        compose_btn.connect("clicked", self._on_compose)
        action_bar.append(compose_btn)

        left_box.append(action_bar)

        # Status label
        self._status_label = Gtk.Label()
        self._status_label.add_css_class("status-label")
        self._status_label.set_xalign(0)
        left_box.append(self._status_label)

        # Message list
        scroll_list = Gtk.ScrolledWindow()
        scroll_list.set_vexpand(True)
        self._mail_list = Gtk.ListBox()
        self._mail_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._mail_list.connect("row-selected", self._on_message_selected)
        self._mail_list.set_placeholder(Gtk.Label(label=_("No messages")))
        scroll_list.set_child(self._mail_list)
        left_box.append(scroll_list)

        paned.set_start_child(left_box)

        # --- Right panel: message view ---
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right_box.set_margin_top(8)
        right_box.set_margin_start(4)
        right_box.set_margin_end(8)
        right_box.set_margin_bottom(8)

        # Message action buttons
        msg_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._tts_btn = _icon_button("audio-speakers-symbolic", _("Read Aloud"))
        self._tts_btn.connect("clicked", self._on_tts)
        msg_actions.append(self._tts_btn)

        reply_btn = _icon_button("mail-reply-sender-symbolic", _("Reply"))
        reply_btn.connect("clicked", self._on_reply)
        msg_actions.append(reply_btn)

        delete_btn = _icon_button("user-trash-symbolic", _("Delete"))
        delete_btn.connect("clicked", self._on_delete)
        delete_btn.add_css_class("destructive-action")
        msg_actions.append(delete_btn)

        right_box.append(msg_actions)

        # Message header info
        self._msg_header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._msg_header_box.set_margin_start(8)
        self._from_label = Gtk.Label(xalign=0)
        self._from_label.add_css_class("mail-sender")
        self._msg_header_box.append(self._from_label)
        self._subject_label = Gtk.Label(xalign=0)
        self._subject_label.add_css_class("mail-subject")
        self._subject_label.set_wrap(True)
        self._msg_header_box.append(self._subject_label)
        self._date_label = Gtk.Label(xalign=0)
        self._date_label.add_css_class("mail-date")
        self._msg_header_box.append(self._date_label)

        right_box.append(self._msg_header_box)
        right_box.append(Gtk.Separator())

        # Message body
        scroll_body = Gtk.ScrolledWindow()
        scroll_body.set_vexpand(True)
        self._body_view = Gtk.TextView()
        self._body_view.set_editable(False)
        self._body_view.set_cursor_visible(False)
        self._body_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._body_view.add_css_class("mail-body")
        scroll_body.set_child(self._body_view)
        right_box.append(scroll_body)

        # Welcome message
        self._show_welcome()

        paned.set_end_child(right_box)
        toolbar_view.set_content(paned)
        self.set_content(toolbar_view)

    def _show_welcome(self):
        self._from_label.set_text("")
        self._subject_label.set_text(_("Welcome to SimpleMail!"))
        self._subject_label.add_css_class("welcome-label")
        self._date_label.set_text(_("Select a message to read it"))
        buf = self._body_view.get_buffer()
        buf.set_text("")

    def _update_status(self):
        if self._backend.is_connected:
            self._status_label.set_text(f"✅ {_('Connected')} — {self._config.email_address}")
            # Update connect button
            box = self._connect_btn.get_child()
            children = []
            child = box.get_first_child()
            while child:
                children.append(child)
                child = child.get_next_sibling()
            if len(children) >= 2:
                children[1].set_text(_("Disconnect"))
        else:
            self._status_label.set_text(f"⚪ {_('Not connected')}")
            box = self._connect_btn.get_child()
            children = []
            child = box.get_first_child()
            while child:
                children.append(child)
                child = child.get_next_sibling()
            if len(children) >= 2:
                children[1].set_text(_("Connect"))

    def _populate_mail_list(self, messages: list[MailMessage]):
        """Fill the message list (must run on main thread)."""
        self._messages = messages
        # Clear existing rows
        while True:
            row = self._mail_list.get_row_at_index(0)
            if row is None:
                break
            self._mail_list.remove(row)

        for msg in messages:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row_box.add_css_class("mail-row")

            # Mail icon
            icon = Gtk.Image.new_from_icon_name(
                "mail-read-symbolic" if msg.is_read else "mail-unread-symbolic"
            )
            icon.set_pixel_size(28)
            row_box.append(icon)

            # Text info
            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text_box.set_hexpand(True)
            subj = Gtk.Label(label=msg.subject, xalign=0)
            subj.set_ellipsize(Pango.EllipsizeMode.END)
            subj.add_css_class("mail-subject")
            text_box.append(subj)

            sender = Gtk.Label(label=msg.sender, xalign=0)
            sender.set_ellipsize(Pango.EllipsizeMode.END)
            sender.add_css_class("mail-sender")
            text_box.append(sender)

            if not msg.is_read:
                subj.add_css_class("mail-row-unread")

            row_box.append(text_box)
            self._mail_list.append(row_box)

        self._update_status()

    def _display_message(self, msg: MailMessage):
        """Show a message in the reading pane."""
        self._selected_message = msg
        self._subject_label.remove_css_class("welcome-label")
        self._from_label.set_text(f"{_('From:')} {msg.sender}")
        self._subject_label.set_text(msg.subject)
        self._date_label.set_text(f"{_('Date:')} {msg.date}")
        buf = self._body_view.get_buffer()
        buf.set_text(msg.body)

    def _show_toast(self, message: str):
        toast = Adw.Toast(title=message, timeout=3)
        # Find or create toast overlay - use a simple approach
        # Just show in status label as fallback
        self._status_label.set_text(message)

    # --- Signal handlers ---

    def _on_settings(self, _btn):
        dialog = SettingsDialog(self, self._config, self._on_config_saved)
        dialog.present()

    def _on_config_saved(self, config: MailConfig):
        self._config = config
        self._backend = MailBackend(config)
        self._update_status()

    def _on_connect(self, _btn):
        if self._backend.is_connected:
            self._backend.disconnect()
            self._update_status()
            return

        if not self._config.is_valid():
            self._on_settings(None)
            return

        self._status_label.set_text(_("Loading..."))

        def _done(success):
            def _update():
                if success:
                    self._update_status()
                    self._on_refresh(None)
                else:
                    self._status_label.set_text(f"❌ {_('Could not connect')}")
            GLib.idle_add(_update)

        import threading
        threading.Thread(
            target=lambda: _done(self._backend.connect()), daemon=True
        ).start()

    def _on_refresh(self, _btn):
        if not self._backend.is_connected:
            return
        self._status_label.set_text(_("Loading..."))

        def _on_messages(messages):
            GLib.idle_add(self._populate_mail_list, messages)

        self._backend.fetch_messages_async(_on_messages)

    def _on_compose(self, _btn):
        dialog = ComposeDialog(self, self._send_message)
        dialog.present()

    def _on_reply(self, _btn):
        if not self._selected_message:
            return
        msg = self._selected_message
        # Extract reply-to email
        sender = msg.sender
        if "<" in sender:
            sender = sender.split("<")[1].rstrip(">")
        dialog = ComposeDialog(self, self._send_message, reply_to=sender, reply_subject=msg.subject)
        dialog.present()

    def _send_message(self, to: str, subject: str, body: str):
        if not self._backend.is_connected:
            self._show_toast(_("Could not send message"))
            return

        def _on_sent(success):
            def _update():
                if success:
                    self._show_toast(_("Message sent!"))
                else:
                    self._show_toast(_("Could not send message"))
            GLib.idle_add(_update)

        self._backend.send_message_async(to, subject, body, _on_sent)

    def _on_delete(self, _btn):
        if not self._selected_message:
            return
        # Confirm deletion
        dialog = Adw.AlertDialog(
            heading=_("Delete Message"),
            body=_("Are you sure you want to delete this message?"),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("delete", _("Delete"))
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_delete_confirmed)
        dialog.present(self)

    def _on_delete_confirmed(self, dialog, response):
        if response != "delete" or not self._selected_message:
            return
        uid = self._selected_message.uid
        if self._backend.delete_message(uid):
            self._show_welcome()
            self._selected_message = None
            self._on_refresh(None)

    def _on_tts(self, _btn):
        if self._tts.is_speaking:
            self._tts.stop()
            # Update button label
            box = self._tts_btn.get_child()
            child = box.get_first_child()
            while child:
                if isinstance(child, Gtk.Label):
                    child.set_text(_("Read Aloud"))
                    break
                child = child.get_next_sibling()
            return

        if not self._selected_message:
            return

        # Read subject + body
        text = f"{self._selected_message.subject}. {self._selected_message.body}"
        self._tts.speak(text)

        # Update button label
        box = self._tts_btn.get_child()
        child = box.get_first_child()
        while child:
            if isinstance(child, Gtk.Label):
                child.set_text(_("Stop Reading"))
                break
            child = child.get_next_sibling()

    def _on_message_selected(self, _listbox, row):
        if row is None:
            return
        idx = row.get_index()
        if 0 <= idx < len(self._messages):
            self._display_message(self._messages[idx])

    def _on_about(self, _btn):
        about = Adw.AboutDialog(
            application_name="SimpleMail",
            application_icon="mail-send-symbolic",
            version="1.0.0",
            comments=_("Accessible email client with pictogram support"),
            developer_name="SimpleMail Team",
            license_type=Gtk.License.GPL_3_0,
        )
        about.present(self)

    def cleanup(self):
        self._tts.cleanup()
        self._backend.disconnect()


class SimpleMailApp(Adw.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id="se.simplemail.app",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._window = None

    def do_activate(self):
        if not self._window:
            self._window = SimpleMailWindow(self)
        self._window.present()

    def do_shutdown(self):
        if self._window:
            self._window.cleanup()
        Adw.Application.do_shutdown(self)


def main():
    app = SimpleMailApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
