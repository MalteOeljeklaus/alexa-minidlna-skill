import logging, yaml, json

from flask import Flask, Response

from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.interfaces.audioplayer import (PlayDirective, PlayBehavior, StopDirective, AudioItem, Stream)

from minidlna_query import MinidlnaQueryHelper

# define global variables
playlist_string = None 
invocation_name = None

def set_log_level(log_level):
    # set the log level globally for this script and other modules (flask, upnp)
    logging.getLogger().setLevel(log_level)
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

def load_invocation_name():
    # read the invocation name either from the config.yml file or from the alexa interaction model in intents.json
    global invocation_name
    if 'invocation_name' in config.keys():
        invocation_name = config['invocation_name']
    else:
        with open('intents.json','r') as f:
            invocation_name = json.loads(f.read())['interactionModel']['languageModel']['invocationName']
    logging.info('invocation name is set to {}'.format(invocation_name))

config = yaml.safe_load(open('./config.yml'))
set_log_level(logging.DEBUG if 'log_level' not in config.keys() else config['log_level'])
logging.info('Alexa skill endpoint for dlna player was launched')

templates = yaml.safe_load(open('./templates.yml'))
app = Flask(__name__)
skill_builder = SkillBuilder()
query = MinidlnaQueryHelper()

### Register your intent handlers to the skill_builder object

@skill_builder.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
#@skill_builder.request_handler(can_handle_func=is_intent_name("LaunchNativeAppIntent"))
#def launch_intent_handler(handler_input):
    """Handler for Skill Launch."""
    # type: (HandlerInput) -> Response
    logging.debug('LaunchRequest()')
    speech_text = templates['welcome']

    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard(invocation_name, speech_text)).set_should_end_session(
        False).response

@skill_builder.request_handler(can_handle_func=is_intent_name("AMAZON.NavigateHomeIntent"))
def navigate_home_intent_handler(handler_input):
    """Handler for Pause Intent."""
    # type: (HandlerInput) -> Response
    logging.debug('navigate_home_intent_handler() called')
    speech_text = templates['not_yet_implemented']

    return handler_input.response_builder.speak(speech_text).ask(
        speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

@skill_builder.request_handler(can_handle_func=is_intent_name("AMAZON.ResumeIntent"))
def resume_intent_handler(handler_input):
    """Handler for Resume Intent."""
    # type: (HandlerInput) -> Response
    logging.debug('resume_intent_handler() called')
    speech_text = templates['not_yet_implemented']

    return handler_input.response_builder.speak(speech_text).ask(
        speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

@skill_builder.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.PauseIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    logging.debug('CancelOrStopIntent() called')
    return handler_input.response_builder.add_directive(StopDirective()).set_should_end_session(True).response

@skill_builder.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = templates['help']

    return handler_input.response_builder.speak(speech_text).ask(
        speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

@skill_builder.request_handler(can_handle_func=is_intent_name("SearchTitleArtistIntent"))
def search_title_artist_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    global playlist_string

    def return_spoken_answer(answer_text): # helper function that returns with a spoken statement
        return handler_input.response_builder.speak(answer_text).ask(
            answer_text).set_card(SimpleCard(invocation_name, answer_text)).response

    title = handler_input.request_envelope.request.intent.slots['title'].value   # get song title from request
    artist = handler_input.request_envelope.request.intent.slots['artist'].value # get artist name from request

    if title==None or title == '': return return_spoken_answer(templates['title_not_provided'])
    if artist==None or artist == '': return return_spoken_answer(templates['artist_not_provided'])

    logging.debug('SearchTitleArtistIntent(): title='+str(title)+', artist='+str(artist))
    status, matched_title, matched_artist, title_url = query.query_artist_title(artist, title)

    if status == -1: return return_spoken_answer(templates['artist_list_empty'])
    if status == -2: return return_spoken_answer(templates['artist_not_found'])
    if status == -3: return return_spoken_answer(templates['title_list_empty'])
    if status == -4: return return_spoken_answer(templates['title_not_found'])

    assert status == 0, 'MinidlnaQueryHelper.query_artist_title() returned unexpected status'

    logging.debug('SearchTitleArtistIntent(): matched_title='+str(matched_title)+', matched_artist='+str(matched_artist)+', url='+str(title_url))
    playlist_string = title_url # save the url that the dlna server returned for the requested song

    return handler_input.response_builder.add_directive(
             PlayDirective(
                 play_behavior=PlayBehavior.REPLACE_ALL,
                 audio_item=AudioItem(
                  stream=Stream(
                   token='https://'+config['endpoint_domain']+'/playlist.m3u', # amazon doesn't allow to play local http urls, but we can play a m3u
                   url='https://'+config['endpoint_domain']+'/playlist.m3u',   # playlist that contains local http urls so we use this workaround
                   offset_in_milliseconds=0,
                   expected_previous_token=None),
                  metadata=None))).set_should_end_session(True).response

@skill_builder.request_handler(can_handle_func=is_intent_name("SearchAlbumArtistIntent"))
def search_album_artist_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    global playlist_string

    def return_spoken_answer(answer_text): # helper function that returns with a spoken statement
        return handler_input.response_builder.speak(answer_text).ask(
            answer_text).set_card(SimpleCard(invocation_name, answer_text)).response

    album = handler_input.request_envelope.request.intent.slots['album'].value   # get song title from request
    artist = handler_input.request_envelope.request.intent.slots['artist'].value # get artist name from request

    if album==None or album == '': return return_spoken_answer(templates['album_not_provided'])
    if artist==None or artist == '': return return_spoken_answer(templates['artist_not_provided'])

    logging.debug('SearchAlbumArtistIntent(): album='+str(album)+', artist='+str(artist))
    status, matched_album, matched_artist, title_urls = query.query_artist_album(artist, album)

    if status == -1: return return_spoken_answer(templates['artist_list_empty'])
    if status == -2: return return_spoken_answer(templates['artist_not_found'])
    if status == -3: return return_spoken_answer(templates['album_list_empty'])
    if status == -4: return return_spoken_answer(templates['album_not_found'])

    assert status == 0, 'MinidlnaQueryHelper.query_artist_album() returned unexpected status'

    logging.debug('SearchAlbumArtistIntent(): matched_album='+str(matched_album)+', matched_artist='+str(matched_artist)+', urls='+str(title_urls))
    playlist_string = '\n'.join(title_urls) # save the urls that the dlna server returned for the requested album

    return handler_input.response_builder.add_directive(
             PlayDirective(
                 play_behavior=PlayBehavior.REPLACE_ALL,
                 audio_item=AudioItem(
                  stream=Stream(
                   token='https://'+config['endpoint_domain']+'/playlist.m3u', # amazon doesn't allow to play local http urls, but we can play a m3u
                   url='https://'+config['endpoint_domain']+'/playlist.m3u',   # playlist that contains local http urls so we use this workaround
                   offset_in_milliseconds=0,
                   expected_previous_token=None),
                  metadata=None))).set_should_end_session(True).response

skill_adapter = SkillAdapter(
    skill=skill_builder.create(), skill_id=config['skill_id'], app=app)

#@app.route("/")
@app.route("/", methods=['POST'])
def invoke_skill():
    logging.debug('invoke_skill()')
    return skill_adapter.dispatch_request()

@app.route("/playlist.m3u", methods=['GET'])
def get_playlist():
    logging.debug('get_playlist()')
    if playlist_string == None: # should never be true in normal use
        logging.warn('received a playlist request before a song was queried, returning default jingle')
        return Response('#EXTINF:-1, test\nhttps://www.musicscreen.org/MP3-OGG/Jingles/Tesla-Jingle.mp3', mimetype='audio/x-mpegurl')
    else:
        return Response('#EXTINF:-1, test\n'+playlist_string, mimetype='audio/x-mpegurl')

if __name__ == '__main__':
    app.run(host=config['bind_ip_address'], port=config['port'], ssl_context= (config['ssl_certificate'], config['ssl_private_key']), debug=False)
