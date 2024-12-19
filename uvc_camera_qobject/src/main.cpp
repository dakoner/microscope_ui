#include <QCoreApplication>
// #include <QtWidgets>
// #include "MainWidget.h"

// int main(int argc, char *argv[])
// {
//     // Creates an instance of QApplication
//     QApplication a(argc, argv);

//     // This is our MainWidget class containing our GUI and functionality
//     MainWidget w;
//     w.show(); // Show main window

//     // run the application and return execs() return value/code
//     return a.exec();
// }

#include "libuvc/libuvc.h"
#include <stdio.h>
#include <unistd.h>
 
#include "uvc_thread.h"

int main(int argc, char *argv[]) {
    QCoreApplication app(argc, argv);
    UVCThread t;
    t.start();
    
    return app.exec();
}