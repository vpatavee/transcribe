import argparse
import os
from io import BytesIO

from google.cloud import speech_v1p1beta1
from pydub import AudioSegment

SIZE = 40000  # 55 sec
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
        if fname.split(".")[-1].lower() in {"flac", "mp3", "wav"}:
            print("\nstart processing {}".format(fname))
            transcribe_from_file(
                os.path.join(path2folder, fname),
                os.path.join(path2folder, "".join(fname.split(".")[:-1]) + ".txt"),
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
        header = "starting {} ending {} total {}".format(
            second_to_min(start // 1000),
            second_to_min(min((start + SIZE), length) // 1000),
            second_to_min(length // 1000)
        )
        print("\tprocessing segment " + header)
        section = sound[start:start + SIZE]
        out = BytesIO()
        section.export(out, format="flac")
        audio_byte = out.read()
        transcription = gcp_transcribe(audio_byte, sound.frame_rate)
        with open(path2transcription, "a") as f:
            f.write("\n" + header + "\n" + transcription + "\n")

        start = start + SIZE - BUFFER


def second_to_min(s):
    """

    :param s:
    :type s:
    :return: hh:mm:ss
    :rtype: string
    """

    h = s // 3600
    rem = s - h * 3600
    m = rem // 60
    s = s - h * 3600 - m * 60

    return "{:02d}:{:02d}:{:02d}".format(h, m, s)


def gcp_transcribe(audio_byte, sample_rate_hertz=44000):
    """

    :param audio_byte: mp3 bytes
    :type audio_byte: bytes
    :param sample_rate_hertz: sample_rate_hertz
    :type sample_rate_hertz: int
    :return: transcription
    :rtype: string
    """

    # example how to use RecognitionMetadata
    context = speech_v1p1beta1.SpeechContext(
        phrases=[
            "ไวรัส",
            "virus",
            "covid",
            "โคโรน่าไวรัส",
            "ไวรัส",
            "วัคซีน",
            "โควิด",
            "coronavirus",
            "โคโรน่าไวรัส",
            "Vaccine",
            "วัคซีน",
            "Blueprint",
            "บลูปริ้น",
            "blueprint"
            "3 แนวทาง",
            "AstraZeneca",
            "SCG",
            "Oxford",
            "พ.ร.บ.จัดซื้อจัดจ้าง",
            "วิจัยในประเทศ",
            "ทีมไทยแลนด์",
            "Team Thailand",
            "สวทช.",
            "การให้ทุน",
            "ความพร้อม",
            "ถ่ายทอดเทคโนโลยี"
        ],
        boost=20
    )

    metadata = speech_v1p1beta1.RecognitionMetadata(
        interaction_type=speech_v1p1beta1.RecognitionMetadata.InteractionType.PHONE_CALL,
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
        sample_rate_hertz=sample_rate_hertz,
        language_code="th-TH",
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
    if response.results:
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
