import logging
import yaml, json

from flask import Flask

from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter

from ask_sdk_core.utils import is_intent_name, is_request_type

from ask_sdk_model.ui import SimpleCard

from ask_sdk_model.interfaces.audioplayer import (PlayDirective, PlayBehavior, AudioItem, Stream)

from minidlna_query import MinidlnaQueryHelper

app = Flask(__name__)

skill_builder = SkillBuilder()

config = yaml.safe_load(open('./config.yml'))

log_level = logging.DEBUG if 'log_level' not in config.keys() else config['log_level']
logging.getLogger().setLevel(log_level)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

if 'invocation_name' in config.keys():
    invocation_name = config['invocation_name']
else:
    with open('intents.json','r') as f:
        invocation_name = json.loads(f.read())['interactionModel']['languageModel']['invocationName']
logging.info('invocation name is set to {}'.format(invocation_name))

templates = yaml.safe_load(open('./templates.yml'))

query = MinidlnaQueryHelper()

# Register your intent handlers to the skill_builder object
 
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

@skill_builder.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = templates['stop']

    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard(invocation_name, speech_text)).response

@skill_builder.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = templates['help']

    return handler_input.response_builder.speak(speech_text).ask(
        speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

@skill_builder.request_handler(can_handle_func=is_intent_name("SearchImmediatelyIntent"))
def search_immediately_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response

    title = handler_input.request_envelope.request.intent.slots['title'].value
    artist = handler_input.request_envelope.request.intent.slots['artist'].value

    if title==None or title == '':
        speech_text = templates['title_not_provided']

        return handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

    if artist==None or artist == '':
        speech_text = templates['artist_not_provided']

        return handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

    logging.debug('SearchImmediatelyIntent(): title='+str(title)+', artist='+str(artist))
    status, matched_title, matched_artist, title_url = query.query_artist_title(artist, title)

    if status == -1:
        speech_text = templates['artist_list_empty']

        return handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

    if status == -2:
        speech_text = templates['artist_not_found']

        return handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

    if status == -3:
        speech_text = templates['title_list_empty']

        return handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

    if status == -4:
        speech_text = templates['title_not_found']

        return handler_input.response_builder.speak(speech_text).ask(
            speech_text).set_card(SimpleCard(invocation_name, speech_text)).response

    assert status == 0

#    speech_text = 'song gefunden!'
    logging.debug('SearchImmediatelyIntent(): matched_title='+str(matched_title)+', matched_artist='+str(matched_artist)+', url='+str(title_url))

#    return handler_input.response_builder.speak(speech_text).ask(
#        speech_text).set_card(SimpleCard(invocation_name, speech_text)).response
    return handler_input.response_builder.add_directive(
                PlayDirective(
                    play_behavior=PlayBehavior.REPLACE_ALL,
                    audio_item=AudioItem(
                        stream=Stream(
                            token='http://drogensong.de/dr.mp3',
                            url='http://drogensong.de/dr.mp3',
                            offset_in_milliseconds=0,
                            expected_previous_token=None),
                        metadata=add_screen_background(card_data) if card_data else None
                    )
                )
            ).set_should_end_session(True).response

skill_adapter = SkillAdapter(
    skill=skill_builder.create(), skill_id=config['skill_id'], app=app)

#@app.route("/")
@app.route("/", methods=['POST'])
def invoke_skill():
    logging.debug('invoke_skill()')
    return skill_adapter.dispatch_request()

if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=config['port'], ssl_context= (config['ssl_certificate'], config['ssl_private_key']), debug=True) # ipv4
    app.run(host='::', port=config['port'], ssl_context= (config['ssl_certificate'], config['ssl_private_key']), debug=True) # ipv6
