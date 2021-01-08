import logging
import yaml, json

from flask import Flask

from ask_sdk_core.skill_builder import SkillBuilder
from flask_ask_sdk.skill_adapter import SkillAdapter

from ask_sdk_core.utils import is_intent_name, is_request_type

from ask_sdk_model.ui import SimpleCard

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

skill_adapter = SkillAdapter(
    skill=skill_builder.create(), skill_id='amzn1.ask.skill.7e368f9d-5d94-435a-9e7a-7cb44e9638f4', app=app)

#@app.route("/")
@app.route("/", methods=['POST'])
def invoke_skill():
    logging.debug('invoke_skill()')
    return skill_adapter.dispatch_request()

if __name__ == '__main__':
#    app.run(host='0.0.0.0', port='443', ssl_context= (config['ssl_certificate'], config['ssl_private_key']), debug=True) # ipv4
    app.run(host='::', port=config['port'], ssl_context= (config['ssl_certificate'], config['ssl_private_key']), debug=True) # ipv6
