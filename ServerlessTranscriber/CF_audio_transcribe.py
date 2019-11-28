import json
import os
import wave

from google.cloud import pubsub_v1
from google.cloud import translate
from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums
from google.cloud import storage

storage_client = storage.Client()
speech_client = speech_v1p1beta1.SpeechClient()
translate_client = translate.Client()
publisher_client = pubsub_v1.PublisherClient()


# SET VARIABLES
project_id = os.environ['GCP_PROJECT']
RESULT_TOPIC = "audio-to-text-results"
TRANSLATE_TOPIC = "audio-to-text-translation"
TO_LANG = ["en", "fr", "es", "ar", "ru", "hi"]


def transcribe_and_translate_audio(bucket, filename, sample_rate_hertz, audio_channels):
    """
    This funciton is a helper function that will call the 
    required APIs in due time. It will make a call to Speech-to-text
    and subsequently publish messages to a Pub/Sub topic.
    Args:
        bucket: str - Name of the source bucket of audio files
        filename: str - title of the audio blob 
        sample_rate_hertz: int -
        audio_channels: int -
    Returns:
        None; the output is written to stdout and Stackdriver Logging
    """   
    print('Transcribing text from this raw audio file: {}'.format(filename))

    futures = []

    # audio_uri 
    audio = {"uri": 'gs://{}/{}'.format(bucket, filename)}

    if audio_channels != 1:
        # When set to true, each audio channel will be recognized separately.
        # The recognition result will contain a channel_tag field to state which
        # channel that result belongs to
        enable_separate_recognition_per_channel = True
    else:
        enable_separate_recognition_per_channel = False

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
    if audio_file_fomat == 'flac':
        encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
        config = {
            "audio_channel_count": audio_channels,
            "enable_separate_recognition_per_channel": enable_separate_recognition_per_channel,
            "sample_rate_hertz": sample_rate_hertz,
            "language_code": language_code,
            "alternative_language_codes": alternative_language_codes
        }
    else:
        encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
        config = {
            "audio_channel_count": audio_channels,
            "enable_separate_recognition_per_channel": enable_separate_recognition_per_channel,
            "sample_rate_hertz": sample_rate_hertz,
            "language_code": language_code,
            "alternative_language_codes": alternative_language_codes,
            "encoding": encoding,
        }

    operation = speech_client.long_running_recognize(config, audio)

    print("Waiting for operation to complete...")
    response = operation.result()
    all_text = ""
    # Extract results from the transcription
    for result in response.results:
        detected_language = result.language_code
        print("Detected language: {}".format(detected_language))
        # First alternative is the most probable result
        alternative = result.alternatives[0]
        text = alternative.transcript + " "
        print("Transcript: {}".format(text))
        all_text += text 

    print('All transcribed lyrics here:              {}'.format(all_text))
    # Send the transcribed text to be translated
    print('Translating  text from this raw audio file: {}'.format(filename))
    detect_language_response = translate_client.detect_language(all_text)
    src_lang = detect_language_response['language']
    # print('Detected language {} for text {}.'.format(src_lang, text))

    # Publish a message to pubsub to translate for each language of interest
    for target_lang in TO_LANG:
        topic_name = TRANSLATE_TOPIC

        # Take care of the case when the audio language is 
        # part of the list of languages of interest
        if src_lang == target_lang or src_lang == 'und':
            topic_name = RESULT_TOPIC

        # Compose the message to be sent to pubsub
        message = {
            'text': all_text,
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
    bucket_name = file.get('bucket')
    audio_name = file.get('name')

    # Speech API needs a few parameters that we need to extract from
    # the header im the wav file. So we need to download it and extract them
    bucket = storage_client.get_bucket(bucket_name)
    audio_blob = bucket.get_blob(audio_name)
    tmp_dst_filename = '/tmp/{}'.format(audio_name)
    audio_blob.download_to_filename(tmp_dst_filename)

    with wave.open(tmp_dst_filename,'rb') as wave_file:
        sample_rate = wave_file.getframerate()
        nbr_channels = wave_file.getnchannels()

    print('Audio sample rate is: {}'.format(sample_rate))
    print('Audio file has {} channels'.format(nbr_channels))

    # Call transcription helper function
    transcribe_and_translate_audio(bucket_name, audio_name, 
        sample_rate, nbr_channels)

    print('File {} processed.'.format(file['name']))