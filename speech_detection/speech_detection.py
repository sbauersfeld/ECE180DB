import sys
import speech_recognition as sr

def speech_setup(headset_name):
    m = None
    print("Showing available microphones...")
    for i, microphone_name in enumerate(sr.Microphone.list_microphone_names()):
        print(microphone_name)
        if microphone_name == headset_name:
            print("Setting up bluetooth microphone!")
            m = sr.Microphone(device_index=i)
            break

    if m is None:
        print("Using default microphone.")
        m = sr.Microphone()

    return m

def get_speech(microphone, trigger=["end", "and"], energy = 250, pause=0.5):
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    adjust = True
    while True:
        with microphone as source:
            if adjust:
                # r.adjust_for_ambient_noise(source)
                adjust = False
                print(r.energy_threshold)
                print(r.pause_threshold)
            print("Say something! '{}' will end this session.".format(trigger[0]))
            audio = r.listen(source, phrase_time_limit=2)

            try:
                print("detected voice")
                command = r.recognize_google(audio).lower()
                print("You said: " + command)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
                continue
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
                continue

            if command in trigger:
                break

def get_speech2(microphone, adjust=True, energy = 250, pause=0.5):
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause

    with microphone as source:
        if adjust:
            # r.adjust_for_ambient_noise(source)
            print(r.energy_threshold)
            print(r.pause_threshold)
        audio = r.listen(source, phrase_time_limit=2)

    return r, audio

def translate_speech(recognizer, audio):
    try:
        command = recognizer.recognize_google(audio).lower()
        return True, command
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return False, "Could not understand!"
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return False, "No service connection!"

def main():
    name = sys.argv[1] if len(sys.argv) == 2 else "Headset (SoundBuds Slim Hands-F"
    m = speech_setup(name)
    print()
    get_speech(m)

if __name__ == '__main__':
    main()
