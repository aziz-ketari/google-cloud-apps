import os
import json

from pydub import AudioSegment
from google.cloud import storage

storage_client = storage.Client()

# SET VARIABLES
project_id = os.environ['GCP_PROJECT']
DEST_BUCKET = 'tmp_wav_audio'
dst_bucket = storage_client.get_bucket(DEST_BUCKET)

def mp3_to_wav(gcs_filename, local_tmp_dir):
    """
    This function is a helper function that will convert the audio file to the 
    encoded version as needed. Support mp3 files.
    Args:
        bucket: str - Name of the source bucket of audio files
        audio_filename: str - title of the audio blob 
    Returns:
        None; the output is written to stdout and Stackdriver Logging
    """
    print(local_tmp_dir)
    print('Encoding {} file into wav format'.format(gcs_filename))
    sound = AudioSegment.from_mp3(local_tmp_dir)
    return sound.export(local_tmp_dir, format="wav")



def encode_audio_file(file,context):
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
    dst_gcs_uri = name.split('.')[0] + '.wav'
    #data = file.get('data')

    # Download the mp3 file to a local tmp directory
    tmp_destination_uri = '/tmp/'+name
    src_bucket = storage_client.get_bucket(bucket)
    audio_blob = src_bucket.get_blob(name)
    audio_blob.download_to_filename(tmp_destination_uri)
    print('{} was successfully downloaded.'.format(name))

    # Call transcription helper function
    mp3_to_wav(name, tmp_destination_uri)
    print('File {} encoded.'.format(file['name']))

    # Upload wav file from tmp directort to gcs
    encoded_blob = dst_bucket.blob(dst_gcs_uri)
    encoded_blob.upload_from_filename(filename=tmp_destination_uri)
    print('{} was successfully converted then uploaded \
        here {}.'.format(name, dst_gcs_uri))
 
    


