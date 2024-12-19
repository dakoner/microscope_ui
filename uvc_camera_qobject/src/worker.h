#ifndef _WORKER_H
#define _WORKER_H

#include <QtCore/qobject.h>
#include <QtCore/qbytearray.h>
#include <QtCore/qthread.h>
#include <QtGui/qevent.h>

class EventPrivate;
class Event : public QEvent
{
public:
    enum
    {
        EventType1 = User + 1
    };

    explicit Event(QEvent::Type);
    Event(QEvent::Type, const QByteArray &);

    void setData(const QByteArray &);
    QByteArray data() const;

protected:
    EventPrivate *d;
};

class WorkerPrivate;
/* A worker class to manage one-call and permanent tasks using QThread object */
class Worker : public QObject
{
    Q_OBJECT

public:
    Worker(QThread *);
    ~Worker();

protected slots:
    virtual void init();

protected:
    bool event(QEvent *) override;

protected:
    WorkerPrivate *d;

signals:
    /* this signals is used for one call type worker */
    void finished(bool success);
};

#endif // !_WORKER_H