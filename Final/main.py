import PIL
from PIL import Image,ImageTk
import cv2
import threading
import time
import pyaudio
from queue import Queue
import numpy as np
from pydub import AudioSegment
import matplotlib.mlab as mlab
from tkinter import Tk, Label, Button, filedialog, Frame
import os
import sys
import wave
from scipy.io.wavfile import read

from keras.models import model_from_json
from keras.models import load_model
from tkinter.font import Font
from SpeakerIdentifier import get_model
from extract_features import extract_features

print('\n'*2)
"""
First, Load Realtime model for word trigger detection
"""
print("Load realtime word trigger model")
# load json and create model
json_file = open('models/model_num.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)

# load weights into new model
model.load_weights("models/model_num.h5")
print("--Done--")
print('\n'*2)

"""
Load identify speaker model
"""
print("Load identity speaker models")
model_path = "Models/"
identify_models = get_model(model_path)
print("--Done--")

def get_spectrogram(data):
    nfft = 200 # Length of each window segment
    fs = 8000 # Sampling frequencies
    noverlap = 120 # Overlap between windows
    nchannels = data.ndim
    if nchannels == 1:
        pxx, _, _ = mlab.specgram(data, nfft, fs, noverlap = noverlap)
    elif nchannels == 2:
        pxx, _, _ = mlab.specgram(data[:,0], nfft, fs, noverlap = noverlap)
    return pxx

def has_new_trigger(predictions, threshold=0.75):
    chunk_size = int(len(predictions) * 0.5 / 10)
    max_prob = np.max(predictions[-chunk_size:])
    #print("Max prob", max_prob)
    if max_prob > threshold:
        return True
    return False

q = Queue()

chunk_duration = 0.5 # Each read length in seconds from mic.
fs = 44100 # sampling rate for mic
#chunk_samples = int(fs * chunk_duration) # Each read length in number of samples.

# Each model input data duration in seconds, need to be an integer numbers of chunk_duration
feed_duration = 10
feed_samples = int(fs * feed_duration)

silence_threshold = 100

# Data buffer for the input wavform
data = np.zeros(feed_samples, dtype='int16')
rec_data = []
def callback(in_data, frame_count, time_info, status):
    global data, silence_threshold, q  
    data0 = np.frombuffer(in_data, dtype='int16')
    if np.abs(data0).mean() < silence_threshold:
        #print('-')
        return (in_data, pyaudio.paContinue)
    else:
        #print('.')
        pass
    data = np.concatenate((data,data0))   
    if len(data) > 441000:
        data = data[-441000:]
        # Process data async by sending a queue.
        q.put(data)
    return (in_data, pyaudio.paContinue)


def get_audio_input_stream(callback, rate=44100, chunk_samples=22050):
    stream = pyaudio.PyAudio().open(
        format=pyaudio.paInt16,
        channels=1,
        rate=rate,
        input=True,
        frames_per_buffer=chunk_samples,
        input_device_index=0,
        stream_callback=callback)
    return stream


# Queue to communiate between the audio callback and main thread
stream = get_audio_input_stream(callback)
stream.start_stream()

def record():
    global rec_data, stream
    rec_data = []
    print("record")
    buttonRec.pack_forget()
    buttonStop.pack()
    def callback2(in_data, frame_count, time_info, status):
        global rec_data
        #print("data: ", len(rec_data))
        data0 = np.frombuffer(in_data, dtype='int16')
        rec_data.append(data0)
        return (in_data, pyaudio.paContinue)
    stream = get_audio_input_stream(callback=callback2, rate=44100, chunk_samples=1024)
    stream.start_stream()

def stop():
    global stream, rec_data
    print(len(rec_data))
    stream.stop_stream()
    stream.close()
    wf = wave.open("rec.wav", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    wf.setframerate(44100)
    wf.writeframes(b''.join(rec_data))
    wf.close()
    sr, audio = read("rec.wav")
    vector = extract_features(audio, sr)
    if vector.shape != (0,):
        print(vector.shape)
        log_likelihood = {}
        m = {}
        for speaker, model in identify_models.items():
            gmm = model
            scores = np.array(gmm.score(vector))
            log_likelihood[speaker] = round(scores.sum(), 3)
            m[speaker] = scores

        max_log_likelihood = max(log_likelihood.values())
        keys, values = list(log_likelihood.keys()), list(log_likelihood.values())
        winner = keys[values.index(max_log_likelihood)]
    # if winner == "f0003":
    #     winner = "Phuong"
    text['text'] = "Hello " + winner + ", wait a second!"
    root.after(1000, lambda: os.startfile(os.path.join(os.getcwd(), "albums")))
    root.after(2000, show_album)
    # else:
    #     text['text'] = "You are not Phuong!"
    buttonStop.pack_forget()
    buttonRec.pack()
    pass

def show_album():
    global stream
    album['text'] = "Close"
    if show_album_frame.winfo_ismapped():
        show_album_frame.place_forget()
        album['text'] = "Albums"
        stream = get_audio_input_stream(callback)
        stream.start_stream()
    else:
        text['text'] = "Who are you?"
        show_album_frame.place(x=350, y=200)
        stream.stop_stream()
        stream.close()
    #os.startfile(os.path.join(os.getcwd(), "albums"))

width, height = 800, 600
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)


root = Tk()
root.wm_protocol("WM_DELETE_WINDOW", quit)
root.title("Camera")
# Define font
font = Font(family='Helvetica', weight="bold")
title_font = Font(family='Helvetica', size=46, weight="bold")

lmain = Label(root)
lmain.pack()

album = Button(text="Albums", width=10, height=5, command=show_album, bg="yellow")
album['font'] = font
album.place(x=750, y=380)

title = Label(text="", width=800, height=20)
title['font'] = title_font

show_album_frame = Frame(root)

text = Label(show_album_frame, text="Who are you?")
text['font'] = font
text.pack(pady=50)

buttonRec = Button(show_album_frame, text="Record", width=20, height=2, relief='solid', fg='white', bg="#24b24e", command=record)
buttonRec['font'] = font
buttonRec.pack()

#Stop button
buttonStop = Button(show_album_frame, text="Stop", width=20, height=2, relief='solid', fg='white', bg="#a51e1a", command=stop)#24b24e
buttonStop['font'] = font


def show_frame(event):
    while True:
        _, frame = cap.read()
        frame = cv2.flip(frame, 1)

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)
        lmain.configure(image=image)
        lmain.image = image
        if event.isSet():
            timestr = time.strftime("%Y%m%d_%H%M%S")
            label = f"albums/IMG_{timestr}.jpg"
            cv2.imwrite(label, frame)
            print("Captured", label)
            title.place(x=0, y=0)
            root.after(300, lambda : title.place_forget())
            event.clear()

def process(event):
    global q
    while True:
        data = q.get()
        spectrum = get_spectrogram(data)
        preds = model.predict(np.expand_dims(spectrum.swapaxes(0, 1), axis=0)).reshape(-1)
        #preds = detect_triggerword_spectrum(spectrum)
        if has_new_trigger(preds):
            event.set()
            tmp = q.get()
            tmp = q.get()

event = threading.Event()
thread = threading.Thread(target=show_frame, args=(event,), daemon=True)
thread.start()
thread2 = threading.Thread(target=process, args=(event,), daemon=True)
thread2.start()

def quit():
    stream.stop_stream()
    stream.close()
    root.quit()
print("Run App")
root.mainloop()