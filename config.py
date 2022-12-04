IMAGEZMQ='microcontroller'
TARGET="microcontroller"
PORT=5000
MQTT_HOST='microcontroller'
# Based on .15mm calibration slide, 800x600 image
#PIXEL_SCALE=0.00095547487
# Based on .15mm calibration slide, 1280x720 image
#PIXEL_SCALE=0.00093167701
# Based on .15mm calibration slide, 1440x1080 image from FLIR camera
PIXEL_SCALE=0.00084745762
    
WIDTH=1440
HEIGHT=1080
FPS=30

FOV_X_PIXELS = WIDTH * 0.9
FOV_Y_PIXELS = HEIGHT * 0.9
FOV_X = FOV_X_PIXELS * PIXEL_SCALE
FOV_Y = FOV_Y_PIXELS * PIXEL_SCALE


XY_STEP_SIZE=0.1
XY_FEED=200

Z_STEP_SIZE=0.01
Z_FEED=25

# 161 pix = 0.15mm
