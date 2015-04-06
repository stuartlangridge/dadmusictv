import time
from mpd import MPDClient
client=MPDClient()
while 1:
    try:
        client.connect('localhost',6600)
        break
    except:
        print "Couldn't connect to music; waiting a bit and trying again"
        time.sleep(5)

import os, random
import pygame
from pygame.locals import *

class pyscope:
    screen = None;

    def __init__(self):
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)
        
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['x11','fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            setdriver = driver
            break
        if not found:
            raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "screen size: %d x %d, on driver %s" % (size[0], size[1], setdriver)
        if setdriver == "x11":
            size = (640, 480)
            self.screen = pygame.display.set_mode(size)
        else:
            print "Setting up initial screen on framebuffer"
            self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        self.size = size
        print "Clearing to start"
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        print "Initialising fonts..."
        pygame.font.init()
        # Render the screen
        print "First screen"
        pygame.display.update()
        pygame.mouse.set_visible(False)

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def get_font_surface(self, text, mw, mh, col):
        font_size = 200
        while 1:
            font = pygame.font.SysFont(None, font_size)
            reqd = font.size(text)
            if reqd[0] < mw and reqd[1] < mh:
                break
            font_size -= 5
        return font.render(text, True, col), reqd

    def test(self):
        grey = (85, 91, 103)
        green = (93, 190, 127)
        white = (255, 255, 255)

        print "Now running"

        while 1:
            s = client.status()
            print s
            if s["state"] == "play":
                status = None
                c = client.currentsong()
                artist = c["artist"]
                title = c["title"]
                pllength = s.get("playlistlength", 0)
                if pllength == "1":
                    pllength = "1 song in playlist"
                else:
                    pllength = "%s songs in playlist" % pllength
            elif s["state"] == "pause":
                status = "PAUSED"
                c = client.currentsong()
                artist = c["artist"]
                title = c["title"]
                pllength = s.get("playlistlength", 0)
                if pllength == "1":
                    pllength = "1 song in playlist"
                else:
                    pllength = "%s songs in playlist" % pllength
            elif s["state"] == "stop":
                status = "NOT PLAYING"
                artist = None
                title = None
                pllength = None
            else:
                status = "error? (%s)" % s["state"]
                artist = None
                title = None
                pllength = None

            print "Drawing for", status, artist, title, pllength

            self.screen.fill(grey)

            if title:
                try:
                    title_surface, size = self.get_font_surface(title, self.size[0] * 0.7, self.size[1]/2, green)
                    self.screen.blit(title_surface, (self.size[0] * 0.15, (self.size[1] / 2) - size[1] - 25))
                except:
                    pass
            if artist:
                try:
                    artist_surface, size = self.get_font_surface(artist, size[0] * 0.7, self.size[1]/2, white)
                    self.screen.blit(artist_surface, (self.size[0] * 0.15, (self.size[1] / 2) + 25))
                except:
                    pass
            if status:
                try:
                    status_surface, size = self.get_font_surface(status, self.size[0] * 0.3, 50, white)
                    self.screen.blit(status_surface, (self.size[0] - size[0] - 5, 5))
                except:
                    pass
            if artist:
                try:
                    pllength_surface, size = self.get_font_surface(pllength, size[0] * 0.4, 80, white)
                    self.screen.blit(pllength_surface, (10, self.size[1] - 30))
                except:
                    pass

            # Update the display
            pygame.display.update()

            client.idle()

# Create an instance of the PyScope class
scope = pyscope()
scope.test()
time.sleep(10)
