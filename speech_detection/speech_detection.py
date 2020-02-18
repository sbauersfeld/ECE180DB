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

while True:
    with m as source:
        print("Say something! 'end' will end this session.")
        audio = r.listen(source)

        try:
            command = r.recognize_google(audio)
            print("You said: " + command)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

        if command == "end" or command == "and":
            break