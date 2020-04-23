import os
import sys
import syslog

from gtts import gTTS
from io import BytesIO
import pygame as pg

#import pyglet

# The text that you want to convert to audio
mytext = 'Welcome to geeksforgeeks!'
  
# Language in which you want to convert
language = 'en'
  
# Passing the text and language to the engine,
# here we have marked slow=False. Which tells
# the module that the converted audio should
# have a high speed
myobj = gTTS(text=mytext, lang=language, slow=False)
  
# Saving the converted audio in a mp3 file named
# welcome
#myobj.save("welcome.mp3")

mp3_fp = BytesIO()
myobj.write_to_fp(mp3_fp)
mp3_fp.seek(0)
  
# Playing the converted file



def play_music(music_file, volume=0.8):
    '''
    stream music with mixer.music module in a blocking manner
    this will stream the sound from disk while playing
    '''
    # set up the mixer
    freq = 24000     # audio CD quality
    bitsize = -16    # unsigned 16 bit
    channels = 1     # 1 is mono, 2 is stereo
    buffer = 2048    # number of samples (experiment to get best sound)
    pg.mixer.init(freq, bitsize, channels, buffer)
    #pg.init()
    #pg.mixer.init()
    # volume value 0.0 to 1.0
    
    #pg.mixer.music.set_volume(volume)
    clock = pg.time.Clock()

    
    
    try:
        
        pg.mixer.music.load(mp3_fp)
        print("Music file {} loaded!".format(music_file))
    except pg.error:
        print("File {} not found! ({})".format(music_file, pg.get_error()))
        return
    pg.mixer.music.play()
    
    
    while pg.mixer.music.get_busy():
        # check if playback has finished
        clock.tick(30)
# pick a MP3 music file you have in the working folder
# otherwise give the full file path
# (try other sound file formats too)

# optional volume 0 to 1.0
volume = 1
play_music("welcome.mp3", volume)

