from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np
import queue
import threading

samplerate = 16000  
block_dur = 0.5
chunk_dur = 2
channels = 2

frames_per_block = int(samplerate * block_dur)
frames_per_chunk = int(samplerate * chunk_dur)