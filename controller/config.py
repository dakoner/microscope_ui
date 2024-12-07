IMAGEZMQ='dektop'
TARGET="dektop"
PORT=5000
MQTT_HOST='dektop'

# Based on .15mm calibration slide, 800x600 image
#PIXEL_SCALE=0.00095547487
# Based on .15mm calibration slide, 1280x720 image
##PIXEL_SCALE=0.00093167701
#PIXEL_SCALE = 0.00119
# Based on .15mm calibration slide, 1440x1080 image from FLIR camera
#PIXEL_SCALE=0.00084745762

# 10X objective to 1280x1024 camera
#PIXEL_SCALE = 1/2062
# 4X objective to 1280x1024 camera
PIXEL_SCALE = 1/833 # pixel / mm
STAGE_X_SIZE=140
STAGE_Y_SIZE=140

# inspection scope with zoom lens, set to minimum zoom, 1280x720 image
#PIXEL_SCALE=.009865
CAMERA='gige'
WIDTH=1280
HEIGHT=1024
FPS=30

FOV_X_PIXELS = WIDTH
FOV_Y_PIXELS = HEIGHT
FOV_X = FOV_X_PIXELS * PIXEL_SCALE
FOV_Y = FOV_Y_PIXELS * PIXEL_SCALE

XY_STEP_SIZE=0.5
XY_FEED=500
Z_STEP_SIZE=0.005
Z_FEED=100

# 161 pix = 0.15mm
