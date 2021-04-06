from gi.repository import GObject, RB, Peas, Gio, GLib, Gdk, Gtk
from yandex_music import Client

class YandexMusic(GObject.Object, Peas.Activatable):
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        super(YandexMusic, self).__init__()

    def do_activate(self):
        print('Yandex.Music plugin activating')
        schema_source = Gio.SettingsSchemaSource.new_from_directory(self.plugin_info.get_data_dir(), Gio.SettingsSchemaSource.get_default(), False)
        schema = schema_source.lookup('org.gnome.rhythmbox.plugins.yandex-music', False)
        self.settings = Gio.Settings.new_full(schema, None, None)
        shell = self.object
        db = shell.props.db
        self.page_group = RB.DisplayPageGroup(shell=shell, id='yandex-music-playlist', name=_('Яндекс')+'.'+_('Music'), category=RB.DisplayPageGroupCategory.TRANSIENT)
        shell.append_display_page(self.page_group, None)
        self.entry_type = YMEntryType()
        db.register_entry_type(self.entry_type)
        iconfile = Gio.File.new_for_path(self.plugin_info.get_data_dir()+'/yandex-music.svg')
        self.source = GObject.new(YMLikesSource, shell=shell, name=_('Мне нравится'), entry_type=self.entry_type, plugin=self, icon=Gio.FileIcon.new(iconfile))
        self.source.setup(db, self.settings)
        shell.register_entry_type_for_source(self.source, self.entry_type)
        shell.append_display_page(self.source, self.page_group)
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.login_yandex)

    def do_deactivate(self):
        print('Yandex.Music plugin deactivating')
        self.source.delete_thyself()
        self.source = None
        self.page_group = None
        self.entry_type = None
        self.client = None
        self.settings = None

    def load_dashboard(self):
        shell = self.object
        db = shell.props.db
        if self.login_yandex():
            dashboard = YMClient.rotor_stations_dashboard()
            for result in dashboard.stations:
                entry_type = YMEntryType()
                source = GObject.new(YMDashboardSource, shell=shell, name=result.station.name, entry_type=entry_type, plugin=self)
                source.setup(db, self.settings, result.station.name)
                shell.register_entry_type_for_source(source, entry_type)
                shell.append_display_page(source, self.page_group)
        return False

    def login_yandex(self):
        global YMClient
        token = self.settings.get_string('token')
        self.iterator = 0
        while len(token) < 1 and self.iterator < 5:
            d = Gtk.Dialog(buttons=(Gtk.STOCK_OK, Gtk.ResponseType.OK))
            label_login = Gtk.Label(_('Login'))
            label_passwd = Gtk.Label(_('Password'))
            input_login = Gtk.Entry(width_chars=25,activates_default=True)
            input_passwd = Gtk.Entry(width_chars=25,activates_default=True)
            d.vbox.pack_start(label_login, expand=True, fill=True, padding=10)
            d.vbox.pack_start(input_login, expand=False, fill=False, padding=10)
            d.vbox.pack_start(label_passwd, expand=True, fill=True, padding=10)
            d.vbox.pack_start(input_passwd, expand=False, fill=False, padding=10)
            d.show_all()
            d.run()
            login = input_login.get_text()
            password = input_passwd.get_text()
            d.destroy()
            if len(login) > 0 and len(password) > 0:
                token = Client.generate_token_by_username_and_password(login, password)
                if len(token) > 0:
                    self.settings.set_string('token', token)
            self.iterator += 1
        if len(token) < 1:
            return False
        else:
            YMClient = Client.from_token(token)
            return False

class YMEntryType(RB.RhythmDBEntryType):
    def __init__(self):
        RB.RhythmDBEntryType.__init__(self, name='ym-entry-type', save_to_disk=False)

    def do_get_playback_uri(self, entry):
        global YMClient
        track_id = entry.get_string(RB.RhythmDBPropType.LOCATION)
        downinfo = YMClient.tracks_download_info(track_id=track_id, get_direct_links=True)
        return downinfo[1].direct_link

    def do_destroy_entry(self, entry):
        global YMClient
        track_id = entry.get_string(RB.RhythmDBPropType.LOCATION)
        return YMClient.users_likes_tracks_remove(track_ids=track_id)

class YMLikesSource(RB.BrowserSource):
    def __init__(self):
        RB.BrowserSource.__init__(self)

    def setup(self, db, settings):
        self.initialised = False
        self.db = db
        self.entry_type = self.props.entry_type
        self.settings = settings

    def do_selected(self):
        if not self.initialised:
            self.initialised = True
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.users_likes_tracks)

    def users_likes_tracks(self):
        global YMClient
        trackslist = YMClient.users_likes_tracks()
        tracks = trackslist.fetch_tracks()
        self.iterator = 0
        self.listcount = len(tracks)
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.add_entry, tracks)
        return False

    def add_entry(self, tracks):
        track = tracks[self.iterator]
        if track.available:
            entry = RB.RhythmDBEntry.new(self.db, self.entry_type, str(track.id)+':'+str(track.albums[0].id))
            if entry is not None:
                self.db.entry_set(entry, RB.RhythmDBPropType.TITLE, track.title)
                self.db.entry_set(entry, RB.RhythmDBPropType.DURATION, track.duration_ms/1000)
                artists = ''
                for artist in track.artists:
                    if len(artists) > 1:
                        artists += ', '+artist.name
                    else:
                        artists = artist.name
                self.db.entry_set(entry, RB.RhythmDBPropType.ARTIST, artists)
                self.db.entry_set(entry, RB.RhythmDBPropType.ALBUM, track.albums[0].title)
                self.db.commit()
        self.iterator += 1
        if self.iterator >= self.listcount:
            return False
        else:
            return True

class YMDashboardSource(RB.BrowserSource):
    def __init__(self):
        RB.BrowserSource.__init__(self)

    def setup(self, db, settings, station):
        self.initialised = False
        self.db = db
        self.entry_type = self.props.entry_type
        self.settings = settings
        self.station = station

    def do_selected(self):
        if not self.initialised:
            self.initialised = True
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.rotor_station_tracks)

    def rotor_station_tracks(self):
        global YMClient
        trackslist = YMClient.rotor_station_tracks(self.station)
        self.iterator = 0
        self.listcount = len(tracks)
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.add_entry, tracks)
        return False

    def add_entry(self, tracks):
        track = tracks[self.iterator]
        if track.available:
            entry = RB.RhythmDBEntry.new(self.db, self.entry_type, str(track.id)+':'+str(track.albums[0].id))
            if entry is not None:
                self.db.entry_set(entry, RB.RhythmDBPropType.TITLE, track.title)
                self.db.entry_set(entry, RB.RhythmDBPropType.DURATION, track.duration_ms/1000)
                artists = ''
                for artist in track.artists:
                    if len(artists) > 1:
                        artists += ', '+artist.name
                    else:
                        artists = artist.name
                self.db.entry_set(entry, RB.RhythmDBPropType.ARTIST, artists)
                self.db.entry_set(entry, RB.RhythmDBPropType.ALBUM, track.albums[0].title)
                self.db.commit()
        self.iterator += 1
        if self.iterator >= self.listcount:
            return False
        else:
            return True

GObject.type_register(YMLikesSource)
