import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import struct
import pygame  # Necesario para reproducir archivos MP3
import time

# Inicializar PyAudio
p = pyaudio.PyAudio()

# Inicializar pygame para reproducir sonido
pygame.mixer.init()

# Listar dispositivos de audio
print("Dispositivos de audio disponibles:")
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print(f"{i}: {dev['name']} (Input Channels: {dev['maxInputChannels']}, Output Channels: {dev['maxOutputChannels']})")

# Seleccionar el micrófono
input_device_index = int(input("Selecciona el dispositivo de entrada (micrófono) por índice: "))

# Seleccionar la salida de audio
output_device_index = int(input("Selecciona el dispositivo de salida (bocinas) por índice: "))

# Configuración de audio
CHUNK = 4096  # Aumentar el tamaño del buffer
FORMAT = pyaudio.paInt16  # Formato de audio (16 bits por muestra)
CHANNELS = 1  # Número de canales
RATE = 22050  # Reducir la frecuencia de muestreo (samples per second)
GAIN = 2.0  # Factor de ganancia (ajustable)
THRESHOLD_DB = 50  # Umbral de decibeles para reproducir el MP3

# Abrir flujo de entrada (micrófono)
stream_input = p.open(format=FORMAT,
                      channels=CHANNELS,
                      rate=RATE,
                      input=True,
                      input_device_index=input_device_index,
                      frames_per_buffer=CHUNK)

# Abrir flujo de salida (bocinas)
stream_output = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       output=True,
                       output_device_index=output_device_index,
                       frames_per_buffer=CHUNK)

# Configurar la gráfica
plt.ion()  # Habilitar modo interactivo
fig, ax = plt.subplots()
x = np.arange(0, CHUNK)  # Eje X para las muestras de audio
line, = ax.plot(x, np.random.rand(CHUNK), '-')
ax.set_ylim(-32768, 32767)  # Rango de valores para int16
ax.set_xlim(0, CHUNK)
plt.show()

# Archivo MP3 a reproducir
mp3_file = "alert.mp3"  # Reemplaza con la ruta a tu archivo MP3

print("Escuchando y reproduciendo...")

try:
    while True:
        try:
            # Leer datos de audio del micrófono
            data = stream_input.read(CHUNK, exception_on_overflow=False)
        except IOError:
            print("Overflow occurred")
            continue

        # Convertir los datos a enteros
        data_int = struct.unpack(str(CHUNK) + 'h', data)
        # Aplicar ganancia (amplificación)
        data_int = np.array(data_int) * GAIN
        # Evitar que los valores excedan el rango permitido para int16
        data_int = np.clip(data_int, -32768, 32767)
        data_int = data_int.astype(np.int16)
        
        # Calcular RMS (Root Mean Square)
        rms = np.sqrt(np.mean(data_int**2))
        # Calcular dB
        dB = 20 * np.log10(rms)

        # Si los dB superan el umbral, reproducir MP3
        if dB > THRESHOLD_DB:
            print(f"Sonido detectado: {dB:.2f} dB, reproduciendo {mp3_file}")
            pygame.mixer.music.load(mp3_file)
            pygame.mixer.music.play()
            time.sleep(1)  # Esperar un segundo antes de continuar

        # Actualizar la gráfica
        line.set_ydata(data_int)
        fig.canvas.draw()
        fig.canvas.flush_events()
        
        # Convertir los datos de nuevo a binario y reproducir
        stream_output.write(data_int.tobytes())

except KeyboardInterrupt:
    print("Terminando...")

# Cerrar los flujos y PyAudio
stream_input.stop_stream()
stream_input.close()
stream_output.stop_stream()
stream_output.close()

p.terminate()
