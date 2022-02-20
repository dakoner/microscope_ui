import cv2

cap = cv2.VideoCapture('outpy.mkv')

width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
out = cv2.VideoWriter('outpy-out.mkv',cv2.VideoWriter_fourcc(*'XVID'), 24, (width, height))

index = 0

frameCache = {}

while True:
    print("index:", index)
    if index not in frameCache:
        print("read frame", index)
        _, img = cap.read()
        frameCache[index] = img
    else:
        print("cache hit", index)
        img = frameCache[index]

    cv2.imshow('frame',img)
    k = cv2.waitKey(0) & 0xFF
    if k == ord('q'):
        break
    elif k == ord('d'):
        index += 1
        continue
    elif k == ord('b'):
        if index > 0:
            print("decrement index")
            index -= 1
            cap.set(cv2.CAP_PROP_POS_FRAMES,index)
    else:
        index += 1
        out.write(img)

cap.release()
cv2.destroyAllWindows()