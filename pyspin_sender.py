
# if __name__ == '__main__':
#    from simple_pyspin import Camera
#    cam = Camera()
#    cam.init()
#    sender = imagezmq.ImageSender("tcp://*:{}".format(port), REQ_REP=False)
#    cam.start()
#    while True:
#        img = cam.get_array()
#        # Convert to 3 dimensions
#        img = img[..., np.newaxis]
#        # Repeat inner element to turn 8-bit grayscale into 8-bit RGB.
       
#        img = np.repeat(img, repeats=3, axis=2)
#        jpg_buffer = simplejpeg.encode_jpeg(img, quality=55, colorspace='RGB')
#        sender.send_jpg("inspectionscope", jpg_buffer)
