#ifndef _UVC_THREAD_H
#define _UVC_THREAD_H

#include <QtCore/qobject.h>
#include "libuvc/libuvc.h"
#include "MainWidget.h"

class UVCQObject:public QObject
{
    Q_OBJECT
public:
    UVCQObject();
    void run(MainWidget *mw);
    void stop();
protected:

    uvc_error init();

private:
    uvc_context_t *ctx;
    uvc_device_t *dev;
    uvc_device_handle_t *devh;
    uvc_stream_ctrl_t ctrl;
    uvc_error_t res;
    
signals:
    void valueChanged(int newValue);
};

#endif // !_UVC_THREAD_H