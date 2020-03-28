from tkinter import Tk, Label, Button, Text, filedialog, Menu, Frame
import sys
from tkinter.font import Font
import tkinter as tk
from tkinter import ttk
import pyaudio
import wave
import os
import re 



def split_text(text):
    pattern1 = re.compile(r"[.]\n+|\n")
    pattern2 = re.compile(r"[.]+\s|\n")
    #OPen text
    with open(text, "r", encoding='utf-8') as f:
        texts = f.read()

    #Tach thanh tung doan nho 
    blocks = re.split(pattern1, texts)

    #Tach cac cau trong doan nho
    result = []
    for block in blocks:
        result += re.split(pattern2, block)
    result = [res for res in result if res != '']
    #Print ket qua
    return result

# Open a text file and display it
def openFile():
    label_count['text'] = '0'
    save_label['text'] = f"Saved {label_count['text']}.wav"
    save_label.pack_forget()
    file_name = filedialog.askopenfilename(initialdir = "./text",
                                                title = "Select file",
                                                filetypes = (("text files","*.txt"),("all files","*.*")))
    if file_name:
        text = split_text(file_name)
        total_sens['text'] = str(len(text))
        text_label['text'] = '@@'.join(text)
        lines = [str(i) + ".wav\n" + t for i, t in enumerate(text)]
        if not os.path.isdir(file_name[:-3]): os.mkdir(file_name[:-3])
        save_folder['text'] = file_name[:-3]
        with open(file_name[:-3]+"/Description.txt", "w", encoding='utf-8') as f:
            f.write('\n'.join(lines))
        sentence['text'] = label_count['text'] + ".wav ---> " + text_label['text'].split('@@')[int(label_count['text'])]


# Exit function
def onExit():
    p.terminate()
    sys.exit()

#pyaudio configure
chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second
p = pyaudio.PyAudio()  # Create an interface to PortAudio

end = False
def record():
    if label_count['text'] != total_sens['text'] and label_count['text'] != '-1':
        save_label.pack_forget()
        buttonRec.pack_forget()
        buttonPre.pack_forget()
        buttonNext.pack_forget()
        buttonPre.pack(side='left', padx=3)
        buttonStop.pack(side='left', padx=3)
        buttonNext.pack(side='left', padx=3)
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
                stream.stop_stream()
                filename = save_folder['text'] + "/" + label_count['text']
                wf = wave.open(filename+".wav", 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(fs)
                wf.writeframes(b''.join(frames))
                wf.close()
                end = False
        listen()
def next_sen():
    save_label.pack_forget()
    if label_count['text'] != total_sens['text']:
        label_count['text'] = str(int(label_count['text']) + 1)
        save_label['text'] = f"Saved {label_count['text']}.wav"
    if label_count['text'] == total_sens['text']:
        sentence['text'] = "This is the end!"
    else:
        sentence['text'] = label_count['text'] + ".wav ---> " + text_label['text'].split('@@')[int(label_count['text'])]

def pre_sen():
    save_label.pack_forget()
    if label_count['text'] != '-1':
        label_count['text'] = str(int(label_count['text']) - 1)
        save_label['text'] = f"Saved {label_count['text']}.wav"
    if label_count['text'] == '-1':
        sentence['text'] = "This is the begining!"
    else:
        sentence['text'] = label_count['text'] + ".wav ---> " + text_label['text'].split('@@')[int(label_count['text'])]

def stop():
    save_label.pack()
    print(save_label['text'])
    buttonStop.pack_forget()
    buttonPre.pack_forget()
    buttonNext.pack_forget()
    buttonPre.pack(side='left', padx=3)
    buttonRec.pack(side='left', padx=3)
    buttonNext.pack(side='left', padx=3)
    
    global end

    # Stop and close the stream 
    print('Finished recording')
    end = True
#Create window
window = Tk()
screen_width = window.winfo_screenwidth()
screen_heihgt = window.winfo_screenheight()
window.title("Recorder Speech Processing")
window.geometry(f"800x300+{screen_width//2 - 400}+{screen_heihgt//2 - 250}")
window.resizable(0, 0)
window.configure(background='white')
# Define font
font = Font(family='Helvetica')
#Add menuBar
menuBar = Menu(window)
window.config(menu=menuBar)
fileMenu = Menu(menuBar)
fileMenu.add_command(label="Open File", command=openFile)
fileMenu.add_command(label="Exit", command=onExit)
menuBar.add_cascade(label="Options", menu=fileMenu)
#Add a label to count sentence
label_count = Label(text='0')
total_sens = Label(text='0')
save_folder = Label()
text_label = Label()
save_label = Label(window, text=f"Saved {label_count['text']}.wav")

sentence = Label(bg='white', wraplength=780, anchor='w', justify='left', height=12)
sentence['font'] = font
sentence.pack(side='top')

# create bottom frame to hold button
bottomframe = Frame(window)
bottomframe.pack(side='bottom', pady=3)

# Pre button
buttonPre = Button(bottomframe, text="Previous", width=20, height=2, 
                                relief='solid', fg='black', bg="yellow", command=pre_sen)
buttonPre['font'] = font
buttonPre.pack(side='left', padx=3)

# Record button
buttonRec = Button(bottomframe, text="Record", width=20, height=2, 
                                relief='solid', fg='white', bg="#24b24e", command=record)
buttonRec['font'] = font
buttonRec.pack(side='left', padx=3)

#Stop button
buttonStop = Button(bottomframe, text="Stop", width=20, height=2, 
                                    relief='solid', fg='white', bg="#a51e1a", command=stop)#24b24e
buttonStop['font'] = font

# Next button
buttonNext = Button(bottomframe, text="Next", width=20, height=2, 
                                relief='solid', fg='black', bg="yellow", command=next_sen)
buttonNext['font'] = font
buttonNext.pack(side='left', padx=3)



window.mainloop()