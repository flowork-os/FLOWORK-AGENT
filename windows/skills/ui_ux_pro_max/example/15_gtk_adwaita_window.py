import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

class SovereignWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(800, 500)
        self.set_title("Sovereign Node Console")

        header = Adw.HeaderBar()
        self.set_content(header)

        clamp = Adw.Clamp(maximum_size=600)
        group = Adw.PreferencesGroup(title="Active Engine Settings")
        row = Adw.ActionRow(title="Zero-Trust Enforcement", subtitle="Mechanical exit code 0 gatekeeper")
        group.add(row)
        clamp.set_child(group)
