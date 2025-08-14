import os
import tkinter as tk
from tkinter import scrolledtext
import threading
import datetime
import webbrowser
import wikipedia
import requests
import pyttsx3
import speech_recognition as sr
import google.generativeai as genai

# ---- Online AI (OpenAI) ----
# pip install openai==1.*
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# --------------- CONFIG ----------------
genai.configure(api_key="AIzaSyCeqpvhYvMaW7BRjUmUad705bpFWoOfVcw")

MODEL_NAME = "gpt-4o-mini"  # fast + smart; you can change to "gpt-4o"
#OPENAI_API_KEY = os.getenv("AIzaSyCeqpvhYvMaW7BRjUmUad705bpFWoOfVcw")  # set via env var
WEATHER_API_KEY = "7b5ec6a728ff865f6524386d81f98eba"  # put your key here
# ---------------------------------------


class JarvisUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS • Voice Assistant")
        self.root.geometry("900x620")
        self.root.configure(bg="#0b1220")
        self.root.minsize(860, 600)

        # TTS engine (offline, fast & reliable)
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)

        # Speech recognizer
        self.recognizer = sr.Recognizer()
        self.listening = False

        # Chat memory for LLM context
        self.chat_history = [
            {"role": "system",
             "content": (
                 "You are Jarvis, a concise, helpful voice assistant for Dipak. "
                 "When asked to open, launch or search, reply briefly and be action-oriented. "
                 "Keep responses under 80 words unless asked for details."
             )}
        ]

        # Build UI
        self._build_ui()

        # Welcome
        self._say_and_show("Jarvis", self._welcome_text())

    # ---------------- UI ----------------
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#0b1220")
        header.pack(fill=tk.X, pady=(10, 0))

        title = tk.Label(
            header,
            text="J A R V I S",
            font=("Verdana", 22, "bold"),
            fg="#66d9ff",
            bg="#0b1220"
        )
        title.pack(side=tk.LEFT, padx=16)

        self.status_dot = tk.Canvas(header, width=16, height=16, bg="#0b1220", highlightthickness=0)
        self.status_dot.pack(side=tk.RIGHT, padx=(0, 8))
        self._set_status_dot("#f0506e")  # idle/red

        self.status_label = tk.Label(header, text="Ready", fg="#9fb4d0", bg="#0b1220", font=("Consolas", 11))
        self.status_label.pack(side=tk.RIGHT, padx=6)

        # Chat area
        self.chat_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, width=100, height=24,
            font=("Segoe UI", 12), bg="#10182b", fg="#e6eefc", insertbackground="#e6eefc"
        )
        self.chat_area.pack(padx=16, pady=12, fill=tk.BOTH, expand=True)
        self.chat_area.config(state=tk.DISABLED)

        # Bottom controls
        controls = tk.Frame(self.root, bg="#0b1220")
        controls.pack(fill=tk.X, padx=16, pady=(0, 14))

        self.entry = tk.Entry(
            controls, font=("Segoe UI", 12), bg="#10182b", fg="#e6eefc",
            insertbackground="#e6eefc", relief=tk.FLAT
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))
        self.entry.bind("<Return>", self._on_send)

        self.mic_btn = tk.Button(
            controls, text="🎤  Mic", font=("Segoe UI", 11, "bold"),
            bg="#1e293b", fg="#a0e9ff", activebackground="#1b2536", activeforeground="#a0e9ff",
            relief=tk.FLAT, padx=16, pady=8, command=self._toggle_listen
        )
        self.mic_btn.pack(side=tk.LEFT, padx=(0, 8))

        send_btn = tk.Button(
            controls, text="Send", font=("Segoe UI", 11, "bold"),
            bg="#2563eb", fg="white", activebackground="#1d4ed8", relief=tk.FLAT,
            padx=18, pady=8, command=self._on_send
        )
        send_btn.pack(side=tk.LEFT, padx=(0, 8))

        clear_btn = tk.Button(
            controls, text="Clear", font=("Segoe UI", 11),
            bg="#334155", fg="#e6eefc", activebackground="#293548", relief=tk.FLAT,
            padx=14, pady=8, command=self._clear_chat
        )
        clear_btn.pack(side=tk.LEFT)

    def _set_status(self, text):
        self.status_label.config(text=text)

    def _set_status_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(2, 2, 14, 14, fill=color, outline=color)

    def _append_chat(self, who, msg):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"{who}: {msg}\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _say(self, text):
        def run():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

    def _say_and_show(self, who, msg):
        self._append_chat(who, msg)
        if who == "Jarvis":
            self._say(msg)

    # ------------- Logic -------------
    def _welcome_text(self):
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            g = "Good morning"
        elif 12 <= hour < 18:
            g = "Good afternoon"
        else:
            g = "Good evening"
        return f"{g}! I’m online. Tap the mic and speak, or type a command."

    def _on_send(self, event=None):
        query = self.entry.get().strip()
        if not query:
            return
        self.entry.delete(0, tk.END)
        self._append_chat("You", query)
        self._route_command(query)

    def _toggle_listen(self):
        if self.listening:
            self.listening = False
            self._set_status("Ready")
            self._set_status_dot("#f0506e")
            self.mic_btn.config(text="🎤  Mic")
            return

        self.listening = True
        self._set_status("Listening…")
        self._set_status_dot("#22c55e")
        self.mic_btn.config(text="■  Stop")

        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        while self.listening:
            try:
                with sr.Microphone() as source:
                    # Calibrate to ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=7)
                self._set_status("Recognizing…")
                text = self.recognizer.recognize_google(audio, language="en-IN")
                self._append_chat("You (mic)", text)
                self._route_command(text)
                self._set_status("Listening…")
            except sr.WaitTimeoutError:
                self._set_status("…")
            except sr.UnknownValueError:
                self._set_status("Didn't catch that")
            except sr.RequestError as e:
                self._set_status(f"STT error: {e}")
                break
            except Exception as e:
                self._set_status(f"Mic error: {e}")
                break

        self.listening = False
        self._set_status("Ready")
        self._set_status_dot("#f0506e")
        self.mic_btn.config(text="🎤  Mic")

    # Command router: handle quick local actions, else ask the online AI
    def _route_command(self, query_raw: str):
        query = query_raw.lower().strip()
        self._set_status("Processing…")

        # Quick intents
        if "open youtube" in query:
            self._action_open("https://youtube.com", "Opening YouTube.")
        elif "open google" in query:
            self._action_open("https://google.com", "Opening Google.")
        elif query.startswith("search "):
            term = query.replace("search", "", 1).strip()
            self._action_open(f"https://www.google.com/search?q={term}", f"Searching for {term}.")
        elif "time" in query:
            now = datetime.datetime.now().strftime("%I:%M %p")
            self._say_and_show("Jarvis", f"The time is {now}.")
        elif "date" in query:
            today = datetime.datetime.now().strftime("%B %d, %Y")
            self._say_and_show("Jarvis", f"Today is {today}.")
        elif "wikipedia" in query:
            topic = query.replace("wikipedia", "").strip() or "Python (programming language)"
            threading.Thread(target=self._do_wikipedia, args=(topic,), daemon=True).start()
        elif "weather" in query:
            city = (query.replace("weather", "").replace("in", "").strip()) or "Pune"
            threading.Thread(target=self._do_weather, args=(city,), daemon=True).start()
        elif "play music" in query or "play song" in query:
            self._do_music()
        elif query.startswith("open "):
            app = query.replace("open", "", 1).strip()
            self._open_app(app)
        elif any(g in query for g in ["exit", "quit", "goodbye", "close app"]):
            self._say_and_show("Jarvis", "Goodbye!")
            self.root.after(800, self.root.destroy)
        else:
            # Ask online AI
            threading.Thread(target=self._ask_ai, args=(query_raw,), daemon=True).start()

    # ---- Local actions ----
    def _action_open(self, url, message):
        try:
            webbrowser.open(url)
            self._say_and_show("Jarvis", message)
        finally:
            self._set_status("Ready")

    def _do_wikipedia(self, topic):
        try:
            summary = wikipedia.summary(topic, sentences=2, auto_suggest=True, redirect=True)
            self._say_and_show("Jarvis", summary)
        except Exception:
            self._say_and_show("Jarvis", "Sorry, I couldn't fetch that from Wikipedia.")
        self._set_status("Ready")

    def _do_weather(self, city):
        if not WEATHER_API_KEY or WEATHER_API_KEY.startswith("YOUR_"):
            self._say_and_show("Jarvis", "Weather is not set up. Add your OpenWeatherMap API key.")
            self._set_status("Ready")
            return
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={WEATHER_API_KEY}"
            data = requests.get(url, timeout=10).json()
            if str(data.get("cod")) != "404":
                main = data["main"]
                weather = data["weather"][0]["description"].capitalize()
                temp = int(round(main["temp"]))
                hum = main["humidity"]
                self._say_and_show("Jarvis", f"{city.title()}: {temp}°C, {weather}. Humidity {hum}%.")
            else:
                self._say_and_show("Jarvis", "City not found.")
        except Exception:
            self._say_and_show("Jarvis", "Sorry, I couldn't get the weather.")
        self._set_status("Ready")

    def _do_music(self):
        # Change path if you like
        music_dir = os.path.expanduser("~/Music")
        try:
            files = [f for f in os.listdir(music_dir) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
            if files:
                path = os.path.join(music_dir, files[0])
                if os.name == "nt":
                    os.startfile(path)  # Windows
                elif os.name == "posix":
                    import subprocess
                    subprocess.Popen(["xdg-open", path])
                self._say_and_show("Jarvis", f"Playing {files[0]}")
            else:
                self._say_and_show("Jarvis", "No music files found in your Music folder.")
        except Exception:
            self._say_and_show("Jarvis", "Couldn't play music.")
        self._set_status("Ready")

    def _open_app(self, app_name):
        try:
            name = app_name.lower()
            if "chrome" in name:
                self._launch(r"C:\Program Files\Google\Chrome\Application\chrome.exe", "Google Chrome")
            elif "code" in name or "visual studio" in name:
                self._launch(r"C:\Users\Dipak\AppData\Local\Programs\Microsoft VS Code\Code.exe", "Visual Studio Code")
            elif "word" in name:
                self._launch(r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE", "Microsoft Word")
            elif "excel" in name:
                self._launch(r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE", "Microsoft Excel")
            elif "notepad" in name:
                self._launch("notepad.exe", "Notepad")
            else:
                self._say_and_show("Jarvis", f"I don't know how to open {app_name}.")
        except Exception:
            self._say_and_show("Jarvis", f"Sorry, I couldn't open {app_name}.")
        self._set_status("Ready")

    def _launch(self, path, pretty):
        try:
            os.startfile(path)
            self._say_and_show("Jarvis", f"Opening {pretty}.")
        except Exception:
            self._say_and_show("Jarvis", f"Couldn't find {pretty} at: {path}")

    # ---- Online AI via OpenAI ----
    def _ask_ai(self, user_text: str):
        if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
            self._say_and_show("Jarvis", "Online AI not configured. Set OPENAI_API_KEY to enable.")
            self._set_status("Ready")
            return
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            self.chat_history.append({"role": "user", "content": user_text})
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=self.chat_history,
                temperature=0.5,
                max_tokens=400
            )
            answer = (resp.choices[0].message.content or "").strip()
            if not answer:
                answer = "I'm here."
            self.chat_history.append({"role": "assistant", "content": answer})
            self._say_and_show("Jarvis", answer)
        except Exception as e:
            self._say_and_show("Jarvis", f"AI error: {e}")
        self._set_status("Ready")

    # Utilities
    def _clear_chat(self):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state=tk.DISABLED)
        self._say_and_show("Jarvis", "Cleared.")
        self._set_status("Ready")


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisUI(root)
    root.mainloop()
