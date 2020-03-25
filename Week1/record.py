from tkinter import Tk, Label, Button, Text, filedialog, Menu, Frame
import sys
from tkinter.font import Font
import tkinter as tk
from tkinter import ttk
import pyaudio
import wave
from functools import partial

#pyaudio configure
chunk = 1024  # Record in chunks of 1024 samples
sample_format = pyaudio.paInt16  # 16 bits per sample
channels = 2
fs = 44100  # Record at 44100 samples per second
p = pyaudio.PyAudio()  # Create an interface to PortAudio

end = False
def record():
    buttonRec.pack_forget()
    buttonStop.pack(side='left')
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
            # Save the recorded data as a WAV file
            filename = filedialog.asksaveasfilename(initialdir = ".",
                                                    title = "Select file",
                                                    filetypes = (("wave files","*.wav"),("all files","*.*")))
            if filename:
                wf = wave.open(filename+".wav", 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(fs)
                wf.writeframes(b''.join(frames))
                wf.close()
            end = False
    listen()
    

def stop():
    buttonStop.pack_forget()
    buttonRec.pack(side='left')
    global end
    # Stop and close the stream 
    print('Finished recording')
    end = True
    
    

#Create window
window = Tk()
screen_width = window.winfo_screenwidth()
screen_heihgt = window.winfo_screenheight()
window.title("Recorder Speech Processing")
window.geometry(f"600x500+{screen_width//2 - 300}+{screen_heihgt//2 -300}")
window.resizable(0, 0)
window.iconbitmap(r"record.ico")
window.configure(background='white')
# Define font
font = Font(family='Helvetica')

# Exit function
def onExit():
    p.terminate()
    sys.exit()

# Open a text file and display it
def openFile():
    file_name = filedialog.askopenfilename(initialdir = ".",
                                                title = "Select file",
                                                filetypes = (("text files","*.txt"),("all files","*.*")))
    if file_name:
        with open(file_name, "r", encoding='utf-8') as f:
            text = f.read()
            label.configure(text=text, anchor='nw')

#Add menuBar
menuBar = Menu(window)
window.config(menu=menuBar)
fileMenu = Menu(menuBar)
fileMenu.add_command(label="Open File", command=openFile)
fileMenu.add_command(label="Exit", command=onExit)
menuBar.add_cascade(label="Options", menu=fileMenu)


#SCrollbar class --> To reuse
class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, height=400)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.scrollable_frame.bind('<Enter>', self._bound_to_mousewheel)
        self.scrollable_frame.bind('<Leave>', self._unbound_to_mousewheel)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units") 
    
# create scrollable Frame
frame = ScrollableFrame(window)
#add label to frame
label = Label(frame.scrollable_frame, text="Chọn file cần ghi âm!\nOptions -> Open File", 
                                        bg='white', wraplength=580,
                                        anchor='w', justify='left')
label['font'] = font
label.pack(side='top')
frame.pack(fill="both", pady=5, padx=1)

# create bottom frame to hold button
bottomframe = Frame(window)
bottomframe.pack(side='bottom', pady=5)
# Record button
buttonRec = Button(bottomframe, text="Record", width=15, height=4, 
                                relief='solid', fg='white', bg="#24b24e", command=record)
buttonRec['font'] = font
buttonRec.pack(side='left')

#Stop button
buttonStop = Button(bottomframe, text="Stop", width=15, height=4, 
                                    relief='solid', fg='white', bg="#a51e1a", command=stop)#24b24e
buttonStop['font'] = font


#Mainloop
window.mainloop()