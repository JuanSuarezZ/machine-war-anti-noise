import pyaudio
import numpy as np
import pygame
import matplotlib.pyplot as plt
from typing import Optional, List
import time

# Constants
CHUNK: int = 1024  # Number of audio samples per frame
FORMAT: int = pyaudio.paInt16  # 16-bit audio format
CHANNELS: int = 1  # Mono audio (for input)
RATE: int = 44100  # Sampling rate (samples per second)
PLOT_INTERVAL: int = 24  # Update the plot every 50 frames
WARNING_SOUND_PATH: str = 'warning.mp3'  # Path to the warning sound file
WARNING_THRESHOLD: float = 50.0  # RMS threshold for triggering the warning sound
WARNING_COOLDOWN: float = 3.0  # Time in seconds to wait before playing the sound again

# Global variable to track the last time the warning sound was played
last_warning_time: float = 0.0

def play_mp3(file_path: str) -> None:
    # Initialize the mixer with 2 channels for stereo output
    pygame.mixer.init(frequency=RATE, channels=2)
    
    # Load the MP3 file and create a Sound object
    sound = pygame.mixer.Sound(file_path)
    
    # Play the sound
    sound.play()

    # Wait until the sound is done playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    warning_playing = False

def calculate_rms(data: bytes) -> Optional[float]:
    try:
        # Convert raw data to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Check if audio_data is empty
        if audio_data.size == 0:
            raise ValueError("Audio data is empty")

        # Calculate the mean of squared audio data
        mean_square = np.mean(np.square(audio_data))
        
        # Ensure mean_square is a valid number
        if np.isnan(mean_square) or np.isinf(mean_square) or mean_square < 0:
            raise ValueError("Mean square value is invalid")

        # Calculate the root mean square (RMS) of the audio data
        rms = np.sqrt(mean_square)
        
        return rms

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def main() -> None:
    global last_warning_time

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Listening... Press Ctrl+C to stop.")

    rms_values: List[Optional[float]] = []
    max_values: List[Optional[float]] = []
    min_values: List[Optional[float]] = []
    
    plt.ion()  # Turn on interactive mode
    fig, ax = plt.subplots()
    line, = ax.plot(rms_values)
    ax.set_ylim(0, 1000)  # Adjust the y-limit based on expected RMS range

    try:
        while True:
            # Read audio data from the stream
            data: bytes = stream.read(CHUNK, exception_on_overflow=False)
            # Calculate the RMS value
            rms: Optional[float] = calculate_rms(data)
            if rms is not None:
                rms_values.append(rms)
                
                # Update max and min lists
                max_values.append(max(rms_values[-PLOT_INTERVAL:], default=0))
                min_values.append(min(rms_values[-PLOT_INTERVAL:], default=0))
                
                # Update the plot
                if len(rms_values) > PLOT_INTERVAL:
                    line.set_ydata(rms_values[-PLOT_INTERVAL:])
                    line.set_xdata(range(len(rms_values[-PLOT_INTERVAL:])))
                    ax.set_ylim(0, max(max_values[-PLOT_INTERVAL:], default=1000) * 1.1)
                    plt.draw()
                    plt.pause(0.01)

                if rms > WARNING_THRESHOLD:
                    current_time = time.time()
                    if current_time - last_warning_time > WARNING_COOLDOWN:
                        play_mp3(WARNING_SOUND_PATH)
                        last_warning_time = current_time
                        print(f"WARNING: RMS Value: {rms:.2f}")

                print(f"RMS Value: {rms:.2f}, Max: {max(rms_values):.2f}, Min: {min(rms_values):.2f}")

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        plt.ioff()
        plt.show()

if __name__ == "__main__":
    main()
