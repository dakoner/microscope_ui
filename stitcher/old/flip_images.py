import sys
import glob
import json
import cv2

def main():
    #g = glob.glob(sys/argv[1] + "/*.jpg")
    #g.sort()
    #prefix = g[-1]
    #d=json.load(open(f"{prefix}/scan_config.json"))
    import glob
    g = glob.glob("photo/*")
    prefix = sorted(g, key=lambda x: float(x.split("/")[1]))[-1]
    g = glob.glob(prefix + "/*jpg")
    print(g)
    for item in g:
        print(item)
        d=cv2.imread(item)
        d = cv2.flip(d, 0)
        cv2.imwrite(item, d)

if __name__ == '__main__':
    main()