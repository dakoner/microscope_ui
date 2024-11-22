import numpy as np
import ffmpeg
from PIL import Image

results = np.load("movie.npy")
process = (
    ffmpeg.input(
        "pipe:", format="rawvideo", pix_fmt="rgb24", s="{}x{}".format(1280, 1024)
    )
    .output(
        "movie.mp4", pix_fmt="yuv420p", vcodec="libx264", r=100
    )  # , preset="ultrafast", crf=50)
    .overwrite_output()
    .run_async(pipe_stdin=True)
)

for i, frame in enumerate(results):
    # im = Image.fromarray(frame)
    # im.save(f"test.{i}.png")
    process.stdin.write(frame.astype(np.uint8).tobytes())
process.stdin.close()
process.wait()
