import argparse
import os
from io import BytesIO

from google.cloud import speech_v1p1beta1
from pydub import AudioSegment

SIZE = 55000  # 55 sec
BUFFER = 5000  # 5 sec

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"


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

    # https://stackoverflow.com/questions/64085443/audio-files-downloaded-from-youtube-dl-are-corrupted
    # Your audio file is probably encoded not as MP3. It is probably AAC (usually having file extension .aac),
    # which is the default format for .mp4 and AVC video codec and youtube.
    # sound = AudioSegment.from_mp3(path2mp3)
    sound = AudioSegment.from_file(path2mp3)
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

    # example how to use RecognitionMetadata
    context = speech_v1p1beta1.SpeechContext(
        phrases=["ไวรัส", "virus", "covid", "โคโรน่าไวรัส", "ไวรัส", "วัคซีน"],
        boost=20
    )

    metadata = speech_v1p1beta1.RecognitionMetadata(
        interaction_type=speech_v1p1beta1.RecognitionMetadata.InteractionType.DISCUSSION,
        microphone_distance=speech_v1p1beta1.RecognitionMetadata.MicrophoneDistance.FARFIELD,
        recording_device_type=speech_v1p1beta1.RecognitionMetadata.RecordingDeviceType.SMARTPHONE
    )

    diarization_config = speech_v1p1beta1.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=2
    )

    config = speech_v1p1beta1.RecognitionConfig(
        encoding=speech_v1p1beta1.RecognitionConfig.AudioEncoding.MP3,
        enable_automatic_punctuation=True,
        sample_rate_hertz=24000,
        language_code="th-TH",
        diarization_config=diarization_config,
        metadata=metadata,
        speech_contexts=[context]
    )

    audio = speech_v1p1beta1.RecognitionAudio(content=audio_byte)
    client = speech_v1p1beta1.SpeechClient()
    response = client.recognize(config=config, audio=audio)
    transcription = ' '.join([result.alternatives[0].transcript for result in response.results])
    # example from official tutorial
    # for i, result in enumerate(response.results):
    #     for alternative in result.alternatives:
    #
    #         print("-" * 20)
    #         print(u"First alternative of result {}".format(i))
    #         print(u"Transcript: {}".format(alternative.transcript))

    # example from official tutorial
    # for i, result in enumerate(response.results):
    #     alternative = result.alternatives[0]
    #     print("-" * 20)
    #     print(u"First alternative of result {}".format(i))
    #     print(u"Transcript: {}".format(alternative.transcript))
    print("transcription", transcription)

    # example for multiple speakers
    for word_info in response.results[-1].alternatives[0].words:
        if word_info.speaker_tag != 1:
            print(
                u"word: '{}', speaker_tag: {}".format(word_info.word, word_info.speaker_tag)
            )
    return transcription


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transcribe a folder containing mp3 and save their transcriptions'
                                                 'in the same folder as txt file')
    parser.add_argument('folder', help='absolute path to folder containing mp3')
    args = parser.parse_args()

    # "/Users/pataveemeemeng/Downloads/lydia"
    transcribe_from_folder(args.folder)
