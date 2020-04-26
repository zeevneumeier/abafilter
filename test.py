import os
import sys
import syslog

from gtts import gTTS
from io import BytesIO
import pygame
import hashlib
import pydub

def playNag(message):
    
    print("nagger.playNag(%s)" % message)
    
    filename = "/tmp/abafilter_nag_%s.wav" % hashlib.md5(message.encode('utf-8')).hexdigest()
    
    if not os.path.exists(filename):
        print (filename, "not found. Generating")
    
        myobj = gTTS(text=message, lang='en', slow=False)
        myobj.save("/tmp/abafilter_nag_temp.mp3")
        sound = pydub.AudioSegment.from_mp3("/tmp/abafilter_nag_temp.mp3")
        sound.export(filename, format="wav")
    
    pygame.mixer.init(24000, -16, 1, 2048)
    clock = pygame.time.Clock()

    try:
        pygame.mixer.music.load(filename)
    except pygame.error:
        print("nagger.playNag(%s) ERROR" % message, pygame.get_error())
        return
    
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        # check if playback has finished
        clock.tick(30)
    
    print("nagger.playNag(%s) done" % message)


playNag("this is a test")
