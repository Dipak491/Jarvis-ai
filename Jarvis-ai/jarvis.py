import tkinter as tk
from tkinter import scrolledtext, messagebox
import pyttsx3
import datetime
import wikipedia
import webbrowser
import os
import requests
import threading
import speech_recognition as sr
import google.generativeai as genai

# ---------------- CONFIG ----------------
GEMINI_API_KEY = "AIzaSyCeqpvhYvMaW7BRjUmUad705bpFWoOfVcw"
genai.configure(api_key=GEMINI_API_KEY)

# ---------------- VOICE ENGINE ----------------
engine = pyttsx3.init()
voices = engine.getProperty("voices")
if voices:
    engine.setProperty("voice", voices[0].id)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# ---------------- GEMINI CHAT ----------------
def chat_with_gemini(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# ---------------- MAIN JARVIS UI ----------------
class JarvisUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Jarvis AI")
        self.root.geometry("600x500")
        self.root.configure(bg="#222")

        # Chat Area
        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12))
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_area.config(state=tk.DISABLED)

        # Entry & Buttons
        bottom_frame = tk.Frame(root, bg="#222")
        bottom_frame.pack(pady=5)

        self.entry = tk.Entry(bottom_frame, font=("Arial", 14), width=40)
        self.entry.grid(row=0, column=0, padx=5)
        self.entry.bind("<Return>", self.send_message)

        send_btn = tk.Button(bottom_frame, text="Send", command=self.send_message, bg="green", fg="white")
        send_btn.grid(row=0, column=1, padx=5)

        voice_btn = tk.Button(bottom_frame, text="🎤 Speak", command=self.voice_input, bg="blue", fg="white")
        voice_btn.grid(row=0, column=2, padx=5)

    # ---------------- Chat Handling ----------------
    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.entry.delete(0, tk.END)
        self.display_message("You", user_input)
        threading.Thread(target=self.process_input, args=(user_input,)).start()

    def voice_input(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            self.display_message("Jarvis", "Listening...")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=8)
                query = r.recognize_google(audio)
                self.display_message("You", query)
                self.process_input(query)
            except sr.UnknownValueError:
                self.display_message("Jarvis", "Sorry, I couldn't understand.")
                speak("Sorry, I couldn't understand.")
            except sr.RequestError:
                self.display_message("Jarvis", "Speech recognition service error.")
                speak("Speech recognition service error.")

    def display_message(self, sender, message):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def process_input(self, text):
        text = text.lower()

        # Predefined commands
        if "time" in text:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.respond(f"The current time is {now}")
        elif "date" in text:
            today = datetime.date.today().strftime("%B %d, %Y")
            self.respond(f"Today's date is {today}")
        elif "open youtube" in text:
            webbrowser.open("https://youtube.com")
            self.respond("Opening YouTube")
        elif "open google" in text:
            webbrowser.open("https://google.com")
            self.respond("Opening Google")
        elif "wikipedia" in text:
            try:
                topic = text.replace("wikipedia", "").strip()
                summary = wikipedia.summary(topic, sentences=2)
                self.respond(summary)
            except:
                self.respond("Sorry, I couldn't fetch that from Wikipedia.")
        elif "weather" in text:
            self.respond("Please specify a city for weather.")
        else:
            # Gemini AI
            response = chat_with_gemini(text)
            self.respond(response)

    def respond(self, message):
        self.display_message("Jarvis", message)
        speak(message)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisUI(root)
    root.mainloop()
