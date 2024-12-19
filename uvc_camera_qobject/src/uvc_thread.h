#ifndef _UVC_THREAD_H
#define _UVC_THREAD_H

#include <QtCore/qthread.h>
#include "libuvc/libuvc.h"

class UVCThread : public QThread {
    public:
    UVCThread();
protected:
 void run();
 uvc_error init();
 static void cb(uvc_frame_t *frame, void *ptr);

 private:
  uvc_context_t *ctx;
  uvc_device_t *dev;
  uvc_device_handle_t *devh;
  uvc_stream_ctrl_t ctrl;
  uvc_error_t res;
};


#endif // !_UVC_THREAD_H