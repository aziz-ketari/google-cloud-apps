# [START functions_ocr_translate]
import base64
import json
import os

from google.cloud import pubsub_v1
from google.cloud import translate

translate_client = translate.Client()
publisher_client = pubsub_v1.PublisherClient()

# SET VARIABLES
project_id = os.environ['GCP_PROJECT']
RESULT_TOPIC = "audio-to-text-results"

# [START translate transcripte text]
def translate_text(event, context):
    """
    This Cloud Function will be triggered when a message is published on the 
    PubSub topic of interest. It will call Translate API.
    args:
        event (dict): Metadata of the event, received from Pub/Sub.
        context (google.cloud.functions.Context): Metadata of triggering event.
    returns:
        None; the output is written to stdout and Stackdriver Logging
    """
    if event.get('data'):
        message_data = base64.b64decode(event['data']).decode('utf-8')
        message = json.loads(message_data)
    else:
        raise ValueError('Data sector is missing in the Pub/Sub message.')

    text = message.get('text')
    filename = message.get('filename')
    target_lang = message.get('lang')
    src_lang = message.get('src_lang')

    print('Translating text into {}.'.format(target_lang))
    translated_text = translate_client.translate(text,
                                                 target_language=target_lang,
                                                 source_language=src_lang)
    topic_name = RESULT_TOPIC
    message = {
        'text': translated_text['translatedText'],
        'filename': filename,
        'lang': target_lang,
    }
    message_data = json.dumps(message).encode('utf-8')
    topic_path = publisher_client.topic_path(project_id, topic_name)
    future = publisher_client.publish(topic_path, data=message_data)
    future.result()

# [END functions_ocr_translate]