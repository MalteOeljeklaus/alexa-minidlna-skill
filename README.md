# alexa-minidlna-skill

## What is this?
This is a custom skill for Amazon Alexa devices that supports the playback of audio files from a local DLNA media server (e.g. your NAS). So far, it's still in early-beta phase and only the minidlna daemon has been tested, as commercial software such as Plex or Synology offer their own Alexa implementations.

## How does it work?
The skill is implemented as an external Alexa https endoint. It uses the alexa skill kit for python to host a flask webservice that the Alexa cloud can connect to and issue search and playback commands. The endpoint therefore needs to run in the same network as your NAS so that it can search your audio database. Also, the endpoint must be reachable from the internet for the Alexa cloud, so you need to expose it in your internet router. However this applies only for the search and playback commands, the actual audio streams can stay local if both your Alexa devices and your NAS are on the same network.

Currently, you can playback single songs by asking for the artist name and the song title. Albums and playlists are not yet implemented.

## How do I set it up?
- setup minidlna/ReadyMedia on your NAS
- adjust intents.json and template.yml for your preferred language (the preset voice commands are in German).
- adjust config.yml for your local network setup, read up on how to configure SSL [here](https://developer.amazon.com/de-DE/docs/alexa/custom-skills/host-a-custom-skill-as-a-web-service.html#about-ssl-options), use any dyndns service to setup your endpoint domain and configure your router to forward https connections
- run: `pip install -r requirements.txt`
- run: `python3 flask_app.py`
- go to your [Alexa developer console](https://developer.amazon.com/alexa/console/ask) and create a new skill
- copy & paste intents.json into the json editor of your interaction model
- select interfaces from the developer console menu and enable audio player
- select endpoint from the developer console menu and set it to your endpoint domain
- save and build your model, test with any song from your database

## Sources

This skill was inspired by the following projects:

https://gist.github.com/jamespo/0522d39eff41a5acc0491e1cd5e1d957
https://github.com/LilaQ/Alexa-YouTube-Skill
https://github.com/alexa/skill-sample-python-audio-player/blob/master/SingleStream/lambda/py/lambda_function.py