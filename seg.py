import os

from google.cloud import speech_v1p1beta1
from google.cloud.speech_v1p1beta1 import enums, types
from pydub import AudioSegment

SIZE = 55000  # 50 sec
BUFFER = 5000  # 5 sec

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
config_args = {
    'enable_automatic_punctuation': True,
    'language_code': "th-TH",
    'encoding': enums.RecognitionConfig.AudioEncoding.MP3,
    'sample_rate_hertz': 44100
}


def gcp(fdir):
    fname = os.path.split(fdir)[-1]
    fname_prefix = fname.rsplit(".", 1)[0]
    fname_suffix = fname.rsplit(".", 1)[1]
    dir_ = list(os.path.split(fdir)[:-1]) + [fname_prefix]
    os.mkdir(os.path.join(*dir_))

    sound = AudioSegment.from_mp3(fdir)
    length = len(sound)
    start = 0

    while start < length:
        print("processing {:d} - {:d} of {:d}".format(start, start + SIZE, length))
        section = sound[start:start + SIZE]
        fname_section = "{}.{:09d}.{}".format(fname_prefix, start, fname_suffix)
        fdir_section = os.path.join(*(list(dir_) + [fname_section]))
        section.export(fdir_section, format="mp3")

        transcription = transcribe(fdir_section)
        header = "starting : {:d} s, ending {:d} s, total {:d} s".format(start // 1000, (start + SIZE) // 1000,
                                                                         length // 1000)

        with open(os.path.join(*(dir_[:-1] + [fname_prefix + ".txt"])), "a") as f:
            f.write("\n" + header + "\n" + transcription + "\n")

        start = start + SIZE - BUFFER


def transcribe(fdir_section):
    with open(fdir_section, "rb") as f:
        audio_byte = f.read()

    config = types.RecognitionConfig(**config_args)
    audio = types.RecognitionAudio(content=audio_byte)
    client = speech_v1p1beta1.SpeechClient()
    response = client.recognize(config, audio)
    transcription = ' '.join([result.alternatives[0].transcript for result in response.results])
    return transcription


if __name__ == '__main__':

    for fname in os.listdir("/Users/pataveemeemeng/Downloads/lydia"):
        if fname[-3:] == "mp3":
            gcp(os.path.join("/Users/pataveemeemeng/Downloads/lydia", fname))
