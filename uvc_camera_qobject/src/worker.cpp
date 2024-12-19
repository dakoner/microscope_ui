/*
* This is a simple, safe and best-practice way to demonstrate how to use threads in Qt5.
* Copyright (C) 2019 Iman Ahmadvand
*
* This is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* It is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*/

#include "worker.h"

class EventPrivate {
public:
    QByteArray data;
};

Event::Event(QEvent::Type t):QEvent(t), d(new EventPrivate) {
    setAccepted(false);
}

Event::Event(QEvent::Type t, const QByteArray& __data) : Event(t) {
    setData(__data);
}

void Event::setData(const QByteArray& __data) {
    d->data = __data;
}

QByteArray Event::data() const {
    return d->data;
}



class WorkerPrivate {
public:
    WorkerPrivate() {

    }
};

Worker::Worker(QThread* thread) :QObject(nullptr), d(new WorkerPrivate) {

    moveToThread(thread);

    QObject::connect(thread, &QThread::started, this, &Worker::init);
    QObject::connect(this, &Worker::finished, thread, &QThread::quit);
    QObject::connect(thread, &QThread::finished, thread, &QThread::deleteLater);
    QObject::connect(thread, &QThread::finished, this, &Worker::deleteLater);
}

Worker::~Worker() {
    /* do clean up if needed */
}

void Worker::init() {
    /* this will called once for construction and initializing purpose */
}

bool Worker::event(QEvent* e) {
    /* event handler */
    if (e->type() == QEvent::Type(Event::EventType1)) {
        /* do some work with event's data and emit signals if needed */
        auto ev = static_cast<Event*>(e);
        ev->accept();
        printf("TA-DA\n");
    }
    return QObject::event(e);
}