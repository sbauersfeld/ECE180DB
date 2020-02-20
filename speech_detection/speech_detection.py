import speech_recognition as sr

m = None
print("Showing available microphones...")
for i, microphone_name in enumerate(sr.Microphone.list_microphone_names()):
    print(microphone_name)
    if microphone_name == "Headset (SoundBuds Slim Hands-F":
        print("Setting up bluetooth microphone!")
        m = sr.Microphone(device_index=i)
        break

if m is None:
    print("Using default microphone.")
    m = sr.Microphone()

print()
r = sr.Recognizer()
r.energy_threshold = 300
r.pause_threshold = 0.5
adjust = True
while True:
    with m as source:
        if adjust:
            # r.adjust_for_ambient_noise(source)
            adjust = False
            print(r.energy_threshold)
            print(r.pause_threshold)
        print("Say something! 'end' will end this session.")
        audio = r.listen(source, phrase_time_limit=2)

        try:
            print("detected voice")
            command = r.recognize_google(audio)
            print("You said: " + command)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            continue
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))
            continue

        if command == "end" or command == "and":
            break