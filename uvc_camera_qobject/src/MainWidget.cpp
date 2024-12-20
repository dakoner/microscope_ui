#include <QtWidgets>
#include "MainWidget.h"
#include "uvc_qobject.h"


// Constructor for main widget
MainWidget::MainWidget(QWidget *parent) :
    QWidget(parent)
{
   button_ = new QPushButton(tr("Push Me!"));
   label_ = new QLabel();

   QGridLayout *mainLayout = new QGridLayout;
   mainLayout->addWidget(button_,0,0);
   mainLayout->addWidget(label_,1,0);
   setLayout(mainLayout);
   setWindowTitle(tr("Connecting buttons to processes.."));
   UVCQObject uvc_qobject;
   // QObject::connect(&uvc_qobject, &UVCQObject::valueChanged,
   //                  this, &MainWidget::cb);
   // setProperty("name", "foo");
   uvc_qobject.run(this);
}

void MainWidget::cb(int i) {
   printf("Blah %d\n", i);
}

void MainWidget::test(QPixmap p) {
   QSize s = p.size();
   printf("p: %d %d\n", s.width(), s.height());
   label_->setPixmap(p);
}

// Destructor
MainWidget::~MainWidget()
{
   delete button_;
   delete label_;
}