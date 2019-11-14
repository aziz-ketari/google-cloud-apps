import json
import os

from google.cloud import pubsub_v1
from google.cloud import translate
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums

speech_client = speech_v1p1beta1.SpeechClient()
translate_client = translate.Client()
publisher_client = pubsub_v1.PublisherClient()


# SET VARIABLES
project_id = os.environ['GCP_PROJECT']
RESULT_TOPIC = "audio-to-text-results"
TRANSLATE_TOPIC = "audio-to-text-translation"
TO_LANG = ["en", "fr", "es", "ar", "ru", "hi"]


# [START audio trancription helper function]
def transcribe_and_translate_audio(bucket, filename):
    """
    This funciton is a helper function that will call the 
    required APIs in due time. It will make a call to Speech-to-text
    and subsequently publish messages to a Pub/Sub topic.
    Args:
        bucket: str - Name of the source bucket of audio files
        filename: str - title of the audio blob 
    Returns:
        None; the output is written to stdout and Stackdriver Logging
    """   
    print('Transcribing text from this raw audio file: {}'.format(filename))

    futures = []

    # audio_uri 
    audio = {"uri": 'gs://{}/{}'.format(bucket, filename)}

    # Sample rate in Hertz of the audio data sent
    # 16 kHz is used in most VoIP products
    sample_rate_hertz = 16000

    # The possible language of the supplied audio
    language_code = "en"

    # 3 additional languages as possible alternative languages
    # of the supplied audio.
    alternative_language_codes_element = "es"
    alternative_language_codes_element_2 = "fr"
    alternative_language_codes_element_3 = "it"
    alternative_language_codes = [
        alternative_language_codes_element,
        alternative_language_codes_element_2,
        alternative_language_codes_element_3,
    ]

    # Encoding of audio data sent
    audio_file_fomat = filename.split('.')[-1]

    # Verify file's encoding
    if audio_file_fomat in ['flac','wav']:
        config = {
            "sample_rate_hertz": sample_rate_hertz,
            "language_code": language_code,
            "alternative_language_codes": alternative_language_codes,
        }
    else:
        encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
        config = {
            "sample_rate_hertz": sample_rate_hertz,
            "language_code": language_code,
            "alternative_language_codes": alternative_language_codes,
            "encoding": encoding,
        }

    operation = speech_client.long_running_recognize(config, audio)

    print("Waiting for operation to complete...")
    response = operation.result()

    # Extract results from the transcription
    for result in response.results:
        detected_language = result.language_code
        print("Detected language: {}".format(detected_language))
        # First alternative is the most probable result
        alternative = result.alternatives[0]
        text = alternative.transcript
        print("Transcript: {}".format(text))

    # Send the transcribed text to be translated
    print('Translating  text from this raw audio file: {}'.format(filename))
    detect_language_response = translate_client.detect_language(text)
    src_lang = detect_language_response['language']
    print('Detected language {} for text {}.'.format(src_lang, text))

    # Publish a message to pubsub to translate for each language of interest
    for target_lang in TO_LANG:
        topic_name = TRANSLATE_TOPIC

        # Take care of the case when the audio language is 
        # part of the list of languages of interest
        if src_lang == target_lang or src_lang == 'und':
            topic_name = RESULT_TOPIC

        # Compose the message to be sent to pubsub
        message = {
            'text': text,
            'filename': filename,
            'lang': target_lang,
            'src_lang': src_lang
        }

        # Publish message to PubSub
        # Note: the message_data needs to be in bytestring
        # Refer to the documentation: 
        # https://googleapis.dev/python/pubsub/latest/publisher/api/client.html
        message_data = json.dumps(message).encode('utf-8')
        topic_path = publisher_client.topic_path(project_id, topic_name)

        # Publish method returns a future instance
        future = publisher_client.publish(topic_path, data=message_data)
        futures.append(future)

    # We need to call result method to extract the message ID
    # Refer to the documentation: 
    # https://googleapis.dev/python/pubsub/latest/publisher/api/futures.html#google.cloud.pubsub_v1.publisher.futures.Future
    for future in futures:
        future.result()
# [END audio trancription helper function]


# [START transcription process]
def process_audio_file(file, context):
    """
    This function will be triggered when an audio is uploaded to the
    GCS bucket of interest.
    Args:
        file (dict): Metadata of the changed file, provided by the triggering
                                 Cloud Storage event.
        context (google.cloud.functions.Context): Metadata of triggering event.
    Returns:
        None; the output is written to stdout and Stackdriver Logging
    """
    bucket = file.get('bucket')
    name = file.get('name')

    # Call transcription helper function
    transcribe_and_translate_audio(bucket, name)

    print('File {} processed.'.format(file['name']))
# [END transcription process]


