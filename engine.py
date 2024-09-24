import os
import re

from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

import utils
from utils import Utils


class WhipsMMAEngine:
    def __init__(self, s3, bucket_name, model="tiny", compute_type='int8'):
        self.model_size = model
        self.device = "cpu" if compute_type == 'int8' else "cuda"  # cuda for gpu | cpu
        self.compute_type = compute_type  # float16, int8_float16 for gpu | int8 for cpu
        self.s3 = s3
        self.bucket_name = bucket_name

    def generate_srt_file(self, filename):
        Utils.log_info(f'Generating srt file for {filename}')
        model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        audio_file = os.path.join("files", filename)
        segments, info = model.transcribe(audio_file, beam_size=5)

        with open(os.path.join('files', f"{filename}.srt"), 'w') as output_file:
            for segment in segments:
                output_file.write("%.2fs -> %.2fs %s\n" % (segment.start, segment.end, segment.text))

    def generate_rttm_file(self, filename):
        Utils.log_info(f'Generating rttm file for {filename}')
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token="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")
        audio_file = os.path.join("files", filename)
        diarization = pipeline(audio_file)
        with open(os.path.join('files', f"{filename}.rttm"), 'w') as output_file:
            diarization.write_rttm(output_file)

    @staticmethod
    def seconds_to_hms(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02}:{minutes:02}:{secs:06.3f}".replace('.', ',')

    @staticmethod
    def delete_files(filename):
        os.remove(os.path.join('files', f"{filename}.srt"))
        os.remove(os.path.join('files', f"{filename}.rttm"))
        os.remove(os.path.join('files', f"{filename}.conversation.txt"))
        with open(os.path.join('logs', 'log.txt'), 'w'):
            pass

    def generate_conversation_file(self, filename):
        self.generate_srt_file(filename)
        self.generate_rttm_file(filename)

        Utils.log_info(f'Generating conversation file for {filename}')
        # Read srt file
        with open(os.path.join('files', f"{filename}.srt"), 'r') as srt_file:
            srt_lines = srt_file.readlines()

        # Read rttm file
        with open(os.path.join('files', f"{filename}.rttm"), 'r') as rttm_file:
            rttm_lines = rttm_file.readlines()

        # Parse conv1.srt file
        srt_data = []
        for line in srt_lines:
            match = re.match(r'(\d+\.\d+)s -> (\d+\.\d+)s\s+(.*)', line.strip())
            if match:
                start_time = float(match.group(1))
                end_time = float(match.group(2))
                text = match.group(3)
                srt_data.append((start_time, end_time, text))

        # Parse conv1.rttm file
        rttm_data = []
        for line in rttm_lines:
            parts = line.strip().split()
            start_time = float(parts[3])
            duration = float(parts[4])
            speaker = parts[7]
            rttm_data.append((start_time, duration, speaker))

        # Merge data
        merged_data = []
        last_speaker = "SPEAKER_UNKNOWN"
        for srt_start, srt_end, text in srt_data:
            assigned = False
            for rttm_start, rttm_duration, speaker in rttm_data:
                rttm_end = rttm_start + rttm_duration
                if rttm_start <= srt_start < rttm_end or rttm_start < srt_end <= rttm_end:
                    merged_data.append((srt_start, speaker, text))
                    last_speaker = speaker
                    assigned = True
                    break
            if not assigned:
                merged_data.append((srt_start, last_speaker, text))

        # Sort merged data by start time
        merged_data.sort(key=lambda x: x[0])
        # Write to output file
        conversation_file = os.path.join('files', f"{filename}.conversation.txt")
        with open(conversation_file, 'w') as output_file:
            for start_time, speaker, text in merged_data:
                hms_time = WhipsMMAEngine.seconds_to_hms(start_time)
                output_file.write(f"{hms_time} {speaker} {text}\n")

        with open(conversation_file, 'rb') as final:
            self.s3.upload_fileobj(final, self.bucket_name, f"{filename}.conversation.txt")

        Utils.log_info(f'PROCESSED {filename}')
        self.delete_files(filename)

