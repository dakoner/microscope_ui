#include <QApplication>
#include "MainWidget.h"
#include "libuvc/libuvc.h"
#include "uvc_thread.h"
#include <stdio.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    // Creates an instance of QApplication
    QApplication a(argc, argv);
    UVCQObject uvc_qobject;
    uvc_qobject.run();

    // This is our MainWidget class containing our GUI and functionality
    MainWidget w;
    w.show(); // Show main window

    // run the application and return execs() return value/code
    return a.exec();
}
