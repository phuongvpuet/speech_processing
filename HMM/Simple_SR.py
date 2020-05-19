import tkinter as tk
from tkinter import Tk, Label, Button, ttk, Frame
from tkinter.font import Font
import pyaudio
import os
import sys
import pickle
import librosa
import numpy as np
import math
from sklearn.cluster import KMeans
import hmmlearn.hmm
import wave
import time

def load_model(path):
    try:
        model_pkl = open(path, "rb")
        models = pickle.load(model_pkl)
    except:
        raise FileNotFoundError("You don't have any models at this path: ", path)
    return models

kmeans = load_model(os.path.join("models", "kmeans.pkl"))
hmms = load_model(os.path.join("models", "models.pkl"))
cnames = {
    "benhvien": "Bệnh Viện",
    "khong": "Không",
    "nguoi": "Người",
    "trong": "Trong",
    "vietnam": "Việt Nam"
}

def predict(path):
    global kmeans
    global hmms
    y, sr = librosa.load(path) # read .wav file
    hop_length = math.floor(sr*0.010) # 10ms hop
    win_length = math.floor(sr*0.025) # 25ms frame
    mfcc = librosa.feature.mfcc(
    y, sr, n_mfcc=12, n_fft=1024,
    hop_length=hop_length, win_length=win_length)
    # energy is 1 x T matrix
    rms = librosa.feature.rms(y=y, frame_length=win_length, hop_length=hop_length)
    # substract mean from mfcc --> normalize mfcc

    # mfcc is 13 x T matrix
    mfcc = mfcc - np.mean(mfcc, axis=1).reshape((-1,1)) 
    mfcc = np.concatenate([mfcc, rms], axis=0)

    # delta feature 1st order and 2nd order
    delta1 = librosa.feature.delta(mfcc, order=1)
    delta2 = librosa.feature.delta(mfcc, order=2)
    # X is 39 x T
    X = np.concatenate([mfcc, delta1, delta2], axis=0) # O^r
    # return T x 39 (transpose of X)
    X = X.T
    print(X.shape)
    X = list([kmeans.predict(v.reshape(1,-1)) for v in X])
    score = -1e6
    classs = ""
    for cname, model in hmms.items():
        model_score = model.score(X, [len(X)])
        if model_score > score:
            score = model_score
            classs = cname
    print("Predict: ", classs)
    predict_class['text'] = "Bạn vừa nói: " + cnames[classs]
    os.remove("hi.wav")




#Pyaudio configure
chunk = 1024
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 1
fs = 44100  # Record at 44100 samples per second
p = pyaudio.PyAudio()  # Create an interface to PortAudio

end = False

def record():
    predict_class['text'] = "Đang thu âm ..."
    buttonRec.pack_forget()
    buttonStop.pack(side='left', padx=3)
    stream = p.open(format=sample_format,
                        channels=channels,
                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True)
    print('Recording')
    frames = []  # Initialize array to store frames
    
    def listen():
            global end
            if not end:
                data = stream.read(chunk)
                frames.append(data)
                window.after(1, listen)
            else:
                #predict(frames)
                wf = wave.open("hi.wav", 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(fs)
                wf.writeframes(b''.join(frames))
                wf.close()
                stream.stop_stream()
                predict("hi.wav")
                end = False
    listen()

def stop():
    predict_class['text'] = "Đang xử lý ..."
    global end 
    buttonStop.pack_forget()
    buttonRec.pack(side='left', padx=3)
    print('Finished recording')
    end = True

#Create window
window = Tk()
screen_width = window.winfo_screenwidth()
screen_heihgt = window.winfo_screenheight()
window.title("Testing HMM models")
window.geometry(f"400x300+{screen_width//2 - 400}+{screen_heihgt//2 - 250}")
window.resizable(0, 0)
window.configure(background='white')
# Define font
font = Font(family='Helvetica')
font_predict = Font(family='Helvetica', size=20)
#Add label
header = Label(bg='white', text="Mô hình HMM nhận diện 5 từ:\nBệnh viện - Không - Người - Trong - Việt Nam", wraplength=400)
header['font'] = font
header.pack(pady=10)

predict_class = Label(bg='white')
predict_class['font'] = font_predict
predict_class.pack(pady=30)
# create bottom frame to hold button
bottomframe = Frame(window)
bottomframe.pack(side='bottom', pady=3)

# Record button
buttonRec = Button(bottomframe, text="Record", width=40, height=2, 
                                relief='solid', fg='white', bg="#24b24e", cursor='hand2', command=record)
buttonRec['font'] = font
buttonRec.pack(side='left', padx=3)

#Stop button
buttonStop = Button(bottomframe, text="Stop", width=40, height=2, 
                                    relief='solid', fg='white', bg="#a51e1a", cursor='hand2', command=stop)#24b24e
buttonStop['font'] = font


window.mainloop()