import os
from io import BytesIO
import argparse

from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums, types
from pydub import AudioSegment

SIZE = 55000  # 55 sec
BUFFER = 5000  # 5 sec

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
config_args = {
    'enable_automatic_punctuation': True,
    'language_code': "th-TH",
    'encoding': enums.RecognitionConfig.AudioEncoding.MP3,
    'sample_rate_hertz': 44100
}


def transcribe_from_folder(path2folder):
    """
    transcribe each mp3 file in folder and save their transcriptions in the same folder as txt file
    :param path2folder: folder containing mp3 files
    :type path2folder: string
    :return:
    :rtype:
    """
    for fname in os.listdir(path2folder):
        if fname[-3:].lower() == "mp3":
            print("\nstart processing {}".format(fname))
            transcribe_from_file(
                os.path.join(path2folder, fname),
                os.path.join(path2folder, fname[:-3] + "txt"),
            )
            print("finish processing {}\n".format(fname))


def transcribe_from_file(path2mp3, path2transcription):
    """
    transcribe an mp3 file and save its transcription in the same folder as txt file
    if the mp3 is longer than 1 min, split it to overlapping segments
    :param path2mp3: path to mp3
    :type path2mp3: string
    :param path2transcription: path to save the transcription
    :type path2transcription: string
    :return:
    :rtype:
    """

    if os.path.exists(path2transcription):
        os.remove(path2transcription)

    sound = AudioSegment.from_mp3(path2mp3)
    length = len(sound)
    start = 0

    while start < length:
        header = "starting : {:d} s, ending {:d} s, total {:d} s".format(
            start // 1000,
            min((start + SIZE), length) // 1000,
            length // 1000
        )
        print("\tprocessing segment " + header)
        section = sound[start:start + SIZE]
        out = BytesIO()
        section.export(out, format="mp3")
        audio_byte = out.read()
        transcription = gcp_transcribe(audio_byte)
        with open(path2transcription, "a") as f:
            f.write("\n" + header + "\n" + transcription + "\n")

        start = start + SIZE - BUFFER


def gcp_transcribe(audio_byte):
    """

    :param audio_byte: mp3 bytes
    :type audio_byte: bytes
    :return: transcription
    :rtype: string
    """
    config = types.RecognitionConfig(**config_args)
    audio = types.RecognitionAudio(content=audio_byte)
    client = speech_v1p1beta1.SpeechClient()
    response = client.recognize(config, audio)
    transcription = ' '.join([result.alternatives[0].transcript for result in response.results])
    return transcription


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transcribe a folder containing mp3 and save their transcriptions'
                                                 'in the same folder as txt file')
    parser.add_argument('folder', help='absolute path to folder containing mp3')
    args = parser.parse_args()

    # "/Users/pataveemeemeng/Downloads/lydia"
    transcribe_from_folder(args.folder)
