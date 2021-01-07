# -*- coding: utf-8 -*-
import logging
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session, audio, current_stream
#import subprocess
#import json
from minidlna_query import MinidlnaQueryHelper
app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

query = MinidlnaQueryHelper()

@ask.launch
def welcome():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)

###################################################################
#                                                                 #  
#   "Alexa, öffne ReadyMedia und spiele Bon Voyage von Deichkind  #
#                                                                 # 
###################################################################   

@ask.intent("SearchImmediatelyIntent", convert={'artist': str, 'title': str})
def search_immediately_term(artist, title):
    audio().stop()
    status, matched_title, matched_artist, title_url = query.query_artist_title(artist, title)
    if status==0:
        return play_song(title_url)
    else:
        return -1

###################################################################################
#                                                                                 #
#   Spiele Song ab (Helper Function)                                              #
#                                                                                 #
###################################################################################

def play_song(uri):
#    response = subprocess.Popen(["youtube-dl", uri, "-j"], stdout=subprocess.PIPE)
#    raw = json.loads(response.stdout.read())
#    source = ''
#    for format in raw['formats']:
#        if format['ext'] == 'mp4':
#            source = format['url']
    return audio().play(uri)


@ask.intent('AMAZON.PauseIntent')
def pause():
    return audio().stop()


@ask.intent('AMAZON.ResumeIntent')
def resume():
    return audio().resume()


@ask.intent('AMAZON.StopIntent')
def stop():
    return audio().clear_queue(stop=True)


if __name__ == '__main__':
    app.run(port=2097, debug=True)