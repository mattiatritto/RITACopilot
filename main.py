# Standard library imports
import json
import time
import os
import wave

# Third-party imports
import azure.cognitiveservices.speech as speechsdk
import openai
from openai import AzureOpenAI
import pyaudio
from dotenv import load_dotenv

# Application-specific imports
from google_api import (get_geolocation, search_nearby_places, fetch_directions)
from kuksa_seat_control import setup_driver_seat

# Profiles mapped by name
profiles = {
    'Dario': [550, 550, 250],
    'Vito': [520, 30, 15],
    'Antonio': [530, 650, 250],
    'Mattia': [350, 450, 150]
}

# Function to process welcome command
def process_welcome_command(content):
    for name, profile in profiles.items():
        welcome_command_key = f'welcome command {name}'
        if welcome_command_key in content and content[welcome_command_key]:
            welcome_message = f"Welcome {name}, I've set up your profile. I'm ready to start. Where are we going today?"
            setup_driver_seat(profile)
            return welcome_message
    return "I don't know you. You want create a new profile?."

def retrieve_profile_info(content):
    for name, profile in profiles.items():
        profile_command_key = f'profile command {name}'
        if profile_command_key in content and content[profile_command_key]:
            profile_message = f"Hey {name}, you're setup are: Position {profile[0]}, Tilt {profile[1]}, and Height {profile[2]}"
            return profile_message
        else:
            return "I don't know you. Please use the FaceID to set up the profile."

def record_audio(filename="my_recording.wav", duration=5, sample_rate=44100,
                 chunk_size=1024, audio_format=pyaudio.paInt16,
                 channels=1):
    """
    Record audio from the microphone and save it as a WAV file.

    Parameters:
    - filename: Name of the file where the recording will be saved.
    - duration: Recording duration in seconds.
    - sample_rate: Sampling rate in Hz.
    - chunk_size: Number of audio frames per buffer.
    - audio_format: Format of the audio (default is pyaudio.paInt16).
    - channels: Number of audio channels.
    """
    try:
        p = pyaudio.PyAudio()  # Create a PyAudio session

        # Open stream
        stream = p.open(format=audio_format,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk_size)

        print(f"Recording for {duration} seconds.")
        frames = []

        # Record data for the set duration
        for _ in range(int(sample_rate / chunk_size * duration)):
            frames.append(stream.read(chunk_size))

        print(f"Recording saved as {filename}.")
    finally:
        # Ensure proper resource cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()

    # Save the recorded data as a WAV file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(audio_format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

def speech_to_text():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_WHISPER_KEY"),
        api_version = "2023-09-01-preview",
        azure_endpoint = os.getenv("AZURE_OPENAI_WHISPER_ENDPOINT")
        )
    model_name = "whisper"
    audio_language = "en"
    audio_test_file = "./my_recording.wav"

    result = client.audio.transcriptions.create(
        file=open(audio_test_file, "rb"),
        model = model_name,
        language = audio_language,
    )

    print(result.text)
    return result.text

def chat_with_gpt(user_message):
    delimiter = "####"
    system_message = f"""
        You are RITA Copilot, a Road Information and Travel Assistant. \
        Your role encompasses a wide array of support functions to assist the driver in \
        ensuring both the vehicle's optimal performance and a pleasant journey. \

        Your capabilities include, but are not limited to, providing real-time traffic updates, \
        suggesting optimal routes, locating nearby services such as fuel stations, restaurants, \
        and parking lots, offering mechanical advice, and facilitating emergency assistance when needed. \
        Additionally, you can engage in light entertainment, such as playing music, podcasts, \
        or audiobooks, to enhance the driving experience. \

        Interaction with the user will be through queries delimited with \
        {delimiter} characters.

        You are tasked with classifying each query into specific categories, including \
        welcome commands (personalized greetings), \
        set up new profile (new profile settings), 
        seat settings (Seat Position, the Seat Tilt and Seat Height)\
        route commands (navigation and traffic updates), \
        service location commands (finding nearby facilities), \
        vehicle support commands (maintenance tips and troubleshooting), \
        profile information commands (give my setting information), \
        emergency assistance commands, and entertainment commands. \

        Identify and categorize queries into welcome command Dario, \
        welcome command Vito, welcome command Antonio, welcome command Mattia, route command, service location command, \
        vehicle support command, new profile, emergency assistance command, profile command Dario, profile command Vito, profile command Antonio, \
        profile command Mattia, or entertainment command, as applicable. \

        Provide your output in JSON format with the \
        keys corresponding to the identified category of the query.
        """

    client = openai.OpenAI(
        api_key=os.getenv("OPEN_AI_KEY"),
        base_url="https://llms.azurewebsites.net"
    )

    completion = client.chat.completions.create(
        model="gpt-4",
        temperature = 0.1,
        messages = [
            {'role': 'system',
             'content': system_message},
            {'role': 'user',
             'content': f"{delimiter}{user_message}{delimiter}"},
        ]
    )

    print(json.loads(completion.choices[0].message.content))

    try:
        content = json.loads(completion.choices[0].message.content)

        if 'welcome command' in str(content):
            welcome_message = process_welcome_command(content)
            print(welcome_message)
            return welcome_message

        elif 'new profile' in content and content['new profile']:
            print("Ops, for security purpose I can't setup a new profile. Turning off the car.")
            return "Ops, for security purpose I can't setup a new profile. Turning off the car."

        elif 'route command' in content and content['route command']:
            route_message = "Okay, we're ready to go"
            print(route_message)
            return route_message

        elif 'profile command' in str(content):
            profile_message = retrieve_profile_info(content)
            print(profile_message)
            return profile_message

        elif 'service location command' in content and content['service location command']:
            print("Searching for location nearby ...")
            query = client.chat.completions.create(
                model="gpt-4",
                temperature=0.1,
                messages=[
                    {'role': 'system',
                     'content': f"Given the following question, output my point of interest \
                                Q: Where is the nearest grocery store? \
                                A: grocery store \
                                Q: {content['service location command']} \
                                A: "},
                    {'role': 'user',
                     'content': f"{delimiter}{user_message}{delimiter}"},
                ]
            )
            place_to_search = query.choices[0].message.content
            position = get_geolocation()
            place = search_nearby_places(os.getenv("GOOGLE_MAPS_API"), position['location']['lat'], position['location']['lng'],
                                 radius=1000, place_type=place_to_search)
            direction = fetch_directions(os.getenv("GOOGLE_MAPS_API"), position['location']['lat'], position['location']['lng'],
                             place[0]['geometry']['location']['lat'], place[0]['geometry']['location']['lng'])
            print((f"The nearest {place_to_search} is {place[0]['name']}. "
                    f"It takes {direction['routes'][0]['legs'][0]['duration']['text']} to get there."))
            return (f"The nearest {place_to_search} is {place[0]['name']}. "
                    f"It takes {direction['routes'][0]['legs'][0]['duration']['text']} to get there.")

        else:
            free_completion = client.chat.completions.create(
                model="gpt-4",
                temperature=0.1,
                messages=[
                    {'role': 'system',
                     'content': "You are RITA Copilot, a Road Information and Travel Assistant. \
                                 Your role encompasses a wide array of support functions to assist \
                                 the driver in ensuring both the vehicle's optimal performance and a pleasant journey."},
                    {'role': 'user',
                     'content': f"{delimiter}{user_message}{delimiter}"},
                ]
            )
            print(free_completion.choices[0].message.content)
            return free_completion.choices[0].message.content
    except (IndexError, KeyError, json.JSONDecodeError) as e:
        print(f"Error processing the command: {e}")
        # To-Do
        # Handle the error appropriately

def text_to_speech(text):
    """
    Converts the given text to speech using Azure's Text to Speech service.

    Parameters:
    - text: The text to be converted to speech.
    """
    # Retrieve environment variables
    speech_key = os.getenv('AZURE_OPENAI_TTS_KEY')
    speech_region = os.getenv('SPEECH_REGION')

    if not (speech_key and speech_region):
        print("Azure Speech key or region is missing.")
        return

    # Configure speech service
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

    # Set the voice name
    speech_config.speech_synthesis_voice_name = 'en-US-AvaNeural'

    # Initialize synthesizer
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Perform text-to-speech
    result = speech_synthesizer.speak_text_async(text).get()

    # Check the result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized for text successfully.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                print(f"Error details: {cancellation_details.error_details}")

if __name__ == '__main__':
    load_dotenv()
    try:
        while True:
            print("Press Ctrl+C to exit.")
            record_audio()
            command = speech_to_text()
            response = chat_with_gpt(command)
            text_to_speech(response)
            time.sleep(1)  # Sleep to avoid rapid-fire actions
    except KeyboardInterrupt:
        print("Exiting...")