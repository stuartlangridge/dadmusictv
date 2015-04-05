import kivy
kivy.require('1.7.2')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

from Queue import Queue
import threading
from functools import partial

from mpc_tcp import MPC_TCP as MPC

BUTTONHEIGHT = 50

class ButtonWithData(Button):
    def __init__(self, *args, **kwargs):
        self.data = kwargs["data"]
        self.owner_button = kwargs.get("owner_button")
        del(kwargs["data"])
        super(ButtonWithData, self).__init__(*args, **kwargs)

class ScrollableButtonStack(ScrollView):
    def __init__(self, *args, **kwargs):
        data = kwargs.get("data", [])
        if data: del(kwargs["data"])
        super(ScrollableButtonStack, self).__init__(*args, **kwargs)
        self.buttonstack = BoxLayout(orientation="vertical", size_hint=(1,None), spacing=2)
        self.add_widget(self.buttonstack)
        self.UNIQUIFIER = 0
        self.set_data(data)

    def set_data(self, data):
        self.buttonstack.clear_widgets()
        self.buttonstack.height = BUTTONHEIGHT * len(data)
        for i in data:
            nd = i.copy()
            nd["unique"] = self.UNIQUIFIER
            self.UNIQUIFIER += 1
            nd["open"] = False
            b = ButtonWithData(text=i["text"], size_hint_x=0.8, size_y=BUTTONHEIGHT, data=nd)
            self.buttonstack.add_widget(b)
            b.bind(on_press=self.toggle_open)

    def _get_button_at_top_uniquifier(self):
        if not self.buttonstack.children: return None
        scrollable_height = self.buttonstack.height - self.height
        if scrollable_height < 0:
            return self.buttonstack.children[0].data["unique"]
        scrolled_px = scrollable_height * (1-self.scroll_y)
        widget_idx_at_top = int(round(float(scrolled_px) / BUTTONHEIGHT))
        # but buttonstack.children is in reverse order, so
        widget_idx_at_top = len(self.buttonstack.children) - widget_idx_at_top - 1
        print "saving uniq", self.buttonstack.children[widget_idx_at_top].data["unique"]
        return self.buttonstack.children[widget_idx_at_top].data["unique"]

    def _scroll_to_uniquifier(self, uni):
        if uni is None: return
        scrollable_height = self.buttonstack.height - self.height
        idx = None
        counter = 0
        for c in self.buttonstack.children:
            if c.data["unique"] == uni:
                idx = counter
                break
            counter += 1
        if idx is None:
            return
        # but buttonstack.children is in reverse order, so
        idx = len(self.buttonstack.children) - idx - 1
        scroll_position = (idx * BUTTONHEIGHT) / scrollable_height
        print "scroll to widget uni", uni, "which is idx", idx, " posn", scroll_position
        self.scroll_y = 1-scroll_position


    def toggle_open(self, button):
        print "toggling open", button, button.data
        uni = self._get_button_at_top_uniquifier()
        if button.data["open"]:
            # remove all children of this button
            print "Removing children"
            to_remove = [x for x in self.buttonstack.children 
                if x.owner_button 
                and x.owner_button.data["unique"] == button.data["unique"]]
            self.buttonstack.height -= len(to_remove) * BUTTONHEIGHT
            for w in to_remove:
                self.buttonstack.remove_widget(w)
            button.data["open"] = False
        else:
            print "Collapsing all others"
            to_remove = [x for x in self.buttonstack.children 
                if x.owner_button]
            self.buttonstack.height -= len(to_remove) * BUTTONHEIGHT
            for w in to_remove:
                self.buttonstack.remove_widget(w)
            print "Expanding"
            insert_idx = 0
            count = 0
            for w in self.buttonstack.children:
                if w.data["unique"] == button.data["unique"]:
                    insert_idx = count
                    break
                count += 1
            self.buttonstack.height += 1 * BUTTONHEIGHT
            nd = {
                "unique": "load tracks",
            }
            self.UNIQUIFIER += 1
            nbtn = ButtonWithData(text="loading...",
                size_hint_x=1, size_y=BUTTONHEIGHT, data=nd, owner_button=button)
            self.buttonstack.add_widget(nbtn, index=insert_idx)
            self.owner_app.mpc.send(("list_tracks", button.data["unique"]), 'find artist "%s"\n' % button.data["text"])
            button.data["open"] = True
        self._scroll_to_uniquifier(uni)

    def load_tracks(self, tracks):
        # remove the loading button, if present, and get its index
        loading_button = None
        counter = 0
        insert_idx = None
        for b in self.buttonstack.children:
            if b.data["unique"] == "load tracks":
                insert_idx = counter
                loading_button = b
                break
            counter += 1
        if not loading_button: return
        print "removing loading button at idx", insert_idx
        owner = loading_button.owner_button
        self.buttonstack.remove_widget(loading_button)
        for t in tracks:
            nd = {
                "unique": self.UNIQUIFIER,
            }
            nd.update(t)
            self.UNIQUIFIER += 1
            nbtn = ButtonWithData(text=t.get("Title", t.get("file")),
                size_hint_x=0.8, pos_hint={'right':1.0}, size_y=BUTTONHEIGHT, data=nd, owner_button=owner)
            nbtn.bind(on_press=self.queue_song)
            self.buttonstack.add_widget(nbtn, index=insert_idx)

    def queue_song(self, button):
        print "queueing song", button.data
        self.owner_app.mpc.send("add", 'add "%s"\n' % button.data["file"])
        self.owner_app.mpc.send("play", "play\n")

class DadMusicTV(App):

    def swap(self, turn_on, turn_off):
        if turn_on.parent: return
        if turn_off.parent: self.lmain.remove_widget(turn_off)
        self.lmain.add_widget(turn_on)

    def selection_changed(self, la):
        print "selection changed"
        if not la.selection:
            return
        print "there is a selection", la.selection, la.selection[0].itemtype
        if la.selection[0].itemtype == "artist":
            self.artist_chosen(la)

    def monitor_outq(self, outq):
        while 1:
            cmdidx, response = outq.get(True)
            if cmdidx == "list_artists":
                arts = [{"text":x[8:]} for x in sorted(response.split("\n")) if x.startswith("Artist: ") and x[8:]]
                self.lvlibrary.set_data(arts)
            elif len(cmdidx) == 2 and cmdidx[0] == "list_tracks":
                tracks = []
                ntrack = {}
                for line in [x.strip() for x in response.split("\n")]:
                    parts = line.split(":", 1)
                    if len(parts) != 2: continue
                    attr, value = [x.strip() for x in parts]
                    if attr == "file" and ntrack:
                        tracks.append(ntrack)
                        ntrack = {}
                    ntrack[attr] = value
                if ntrack:
                    tracks.append(ntrack)
                self.lvlibrary.load_tracks(tracks)
            else:
                print "got unknown command '%r' with response '%s'" % (cmdidx, response)

    def build(self):
        outq = Queue()
        mon_thr = threading.Thread(target=self.monitor_outq, args=(outq,))
        mon_thr.daemon = True
        mon_thr.start()

        host = "musictv.local"
        port = 6600
        self.mpc = MPC(host, port, outq)

        self.lmain = BoxLayout(orientation='vertical', spacing=2)
        ltop = BoxLayout(orientation='horizontal', spacing=2, size_hint=(1,0.1))
        b1 = Button(text='Library', size_hint=(0.5,1))
        b2 = Button(text='Playlist', size_hint=(0.5,1))
        ltop.add_widget(b1)
        ltop.add_widget(b2)
        self.lmain.add_widget(ltop)

        self.lvlibrary = lvlibrary = ScrollableButtonStack(data=[{"text":"loading..."}], size_hint=(1, 0.9))
        lvlibrary.owner_app = self
        lvplaylist = Label(text="playlist")
        b1.bind(on_press=lambda x:self.swap(lvlibrary, lvplaylist))
        b2.bind(on_press=lambda x:self.swap(lvplaylist, lvlibrary))
        self.swap(lvlibrary, lvplaylist)

        Clock.schedule_once(self.mpc_setup, 0.3)

        return self.lmain

    def mpc_setup(self, dt):
        Clock.schedule_once(lambda x: self.mpc.send("consume", "consume 1\n"), 0)
        Clock.schedule_once(lambda x: self.mpc.send("list_artists", "list artist\n"), 0.3)

if __name__ == '__main__':
    DadMusicTV().run()
