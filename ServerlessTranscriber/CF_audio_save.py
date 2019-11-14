import base64
import json

from google.cloud import storage

storage_client = storage.Client()

# SET VARIABLES
RESULT_BUCKET = "sound_2_text_2_translate"

# [START save transcribed audio]
def save_result(event, context):
    """
    This Cloud Function will be triggered when a message is published on the 
    PubSub topic of interest. It will save the translated text to GCS.
    Args:
        file (dict): Metadata of the changed file, provided by the triggering
                                 Cloud Storage event.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to stdout and Stackdriver Logging
    """
    if event.get('data'):
        message_data = base64.b64decode(event['data']).decode('utf-8')
        message = json.loads(message_data)
    else:
        raise ValueError('Data sector is missing in the Pub/Sub message.')

    text = message.get('text')
    filename = message.get('filename')
    lang = message.get('lang')

    print('Received request to save file {}.'.format(filename))

    bucket_name = RESULT_BUCKET
    result_filename = '{}_{}.txt'.format(filename, lang)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(result_filename)

    print('Saving result to {} in bucket {}.'.format(result_filename,
                                                     bucket_name))

    theHeader = f"content_type='text/plain'; charset='utf-8'; content_lang='{lang}'"
    blob.upload_from_string(text, theHeader)

    print('File saved.')
# [END save transcribed audio]