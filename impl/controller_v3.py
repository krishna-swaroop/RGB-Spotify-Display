import os, inspect, sys, math, time, configparser, argparse
from PIL import Image

from apps_v2 import spotify_player
from modules import spotify_module
from mfrc522 import SimpleMFRC522
import threading

# def read_rfid(RFIDReader, app_list):
#     while True:
#         try:
#             id,text = RFIDReader.read()
#             if id is not None:
#                 print("ID: %s\nText: %s" % (id,text))
#                 # if (id == (songs[''][0])):
#                 if (id == 907276392724):
#                     # modules['spotify'].start_playback(uris=['spotify:track:45vW6Apg3QwawKzBi03rgD'])
#                     currentsong = app_list.spotify_module.getCurrentPlayback()
#                     print(currentsong)
#                 else:
#                     print("No Song attached to this Tag")
#         except Exception as e:
#             print("Error:",e)
#         time.sleep(1)


def main():
    canvas_width = 64
    canvas_height = 64

    # get arguments
    parser = argparse.ArgumentParser(
                    prog = 'RpiSpotifyMatrixDisplay',
                    description = 'Displays album art of currently playing song on an LED matrix')

    parser.add_argument('-f', '--fullscreen', action='store_true', help='Always display album art in fullscreen')
    parser.add_argument('-e', '--emulated', action='store_true', help='Run in a matrix emulator')
    args = parser.parse_args()

    is_emulated = args.emulated
    is_full_screen_always = args.fullscreen

    # switch matrix library import if emulated
    if is_emulated:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
    else:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions

    # get config
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    sys.path.append(currentdir+"/rpi-rgb-led-matrix/bindings/python")

    config = configparser.ConfigParser()
    parsed_configs = config.read('../config.ini')

    if len(parsed_configs) == 0:
        print("no config file found")
        sys.exit()

    RFIDReader = SimpleMFRC522()
    # connect to Spotify and create display image
    modules = { 'spotify' : spotify_module.SpotifyModule(config) }
    app_list = [ spotify_player.SpotifyScreen(config, modules, is_full_screen_always, RFIDReader)]

    # setup matrix
    options = RGBMatrixOptions()
    options.hardware_mapping = config.get('Matrix', 'hardware_mapping', fallback='regular')
    options.rows = canvas_width
    options.cols = canvas_height
    options.brightness = 100 if is_emulated else config.getint('Matrix', 'brightness', fallback=100)
    options.gpio_slowdown = config.getint('Matrix', 'gpio_slowdown', fallback=1)
    options.limit_refresh_rate_hz = config.getint('Matrix', 'limit_refresh_rate_hz', fallback=0)
    options.drop_privileges = False
    matrix = RGBMatrix(options = options)

    shutdown_delay = config.getint('Matrix', 'shutdown_delay', fallback=600)
    black_screen = Image.new("RGB", (canvas_width, canvas_height), (0,0,0))
    last_active_time = math.floor(time.time())

    

    # rfid_thread = threading.Thread(target=read_rfid, args=(RFIDReader, app_list[0]))
    # rfid_thread.daemon = True
    # rfid_thread.start()

    #generate image
    while(True):
        frame, is_playing = app_list[0].generate()
        current_time = math.floor(time.time())

        if frame is not None:
            if is_playing:
                last_active_time = math.floor(time.time())
            elif current_time - last_active_time >= shutdown_delay:
                frame = black_screen
        else:
            frame = black_screen

        matrix.SetImage(frame)
        # try:
        #     id, text = RFIDReader.read()
        #     print("ID: %s\nText: %s" % (id,text))
        # except:
        #     print('No RFID Reader Detected')
        
        time.sleep(0.08)
    # import selectors
    # # import sys

    # selector = selectors.DefaultSelector()
    # selector.register(sys.stdin, selectors.EVENT_READ)

    # while True:
    #     frame, is_playing = app_list[0].generate()
    #     current_time = math.floor(time.time())

    #     if frame is not None:
    #         if is_playing:
    #             last_active_time = math.floor(time.time())
    #         elif current_time - last_active_time >= shutdown_delay:
    #             frame = black_screen
    #     else:
    #         frame = black_screen

    #     matrix.SetImage(frame)

    #     # Check if there's input available
    #     events = selector.select(timeout=0)
    #     for key, mask in events:
    #         if key.fileobj == sys.stdin:
    #             # Input is available
    #             user_input = input("Enter something: \n")
    #             # Process the input if needed
    #             print(user_input)

    #     time.sleep(0.08)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted with Ctrl-C')
        sys.exit(0)
