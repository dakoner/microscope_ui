#include "uvc_qobject.h"
#include <QtGui/qimage.h>
#include <QtGui/qpixmap.h>

void cb(uvc_frame *frame, void *ptr)
{
    uvc_frame_t *bgr;
    uvc_error_t ret;
    

    /* We'll convert the image from YUV/JPEG to BGR, so allocate space */
    bgr = uvc_allocate_frame(frame->width * frame->height * 3);
    if (!bgr)
    {
        printf("unable to allocate bgr frame!\n");
        return;
    }

    printf("callback! frame_format = %d, width = %d, height = %d, length = %lu, ptr = %p\n",
           frame->frame_format, frame->width, frame->height, frame->data_bytes, ptr);
    if (frame->frame_format == UVC_FRAME_FORMAT_H264)
    {
        /* use `ffplay H264_FILE` to play */
        /* fp = fopen(H264_FILE, "a");
         * fwrite(frame->data, 1, frame->data_bytes, fp);
         * fclose(fp); */
    }
    else if (frame->frame_format == UVC_COLOR_FORMAT_MJPEG)
    {
        /* sprintf(filename, "%d%s", jpeg_count++, MJPEG_FILE);
         * fp = fopen(filename, "w");
         * fwrite(frame->data, 1, frame->data_bytes, fp);
         * fclose(fp); */
    }
    else if (frame->frame_format == UVC_COLOR_FORMAT_YUYV)
    {
        /* Do the BGR conversion */
        ret = uvc_any2bgr(frame, bgr);
        if (ret)
        {
            uvc_perror(ret, "uvc_any2bgr");
            uvc_free_frame(bgr);
            return;
        }
        QImage i((uchar *)bgr->data, frame->width, frame->height, QImage::Format::Format_RGB888);
        QPixmap p = QPixmap::fromImage(i);
        //printf("Emit\n");
        MainWidget *q = (MainWidget*)ptr;
        q->test(p);
    }
}
// Finish massaging this into a working qobject and make the mainwidget get events from it

void UVCQObject::run(MainWidget *mw)
{
    printf("Run\n");
    res = uvc_start_streaming(devh, &ctrl, cb, mw, 0);

    if (res < 0)
    {
        uvc_perror(res, "start_streaming"); /* unable to start stream */
    }
    else
    {
        puts("Streaming...");

        /* enable auto exposure - see uvc_set_ae_mode documentation */
        puts("Enabling auto exposure ...");
        const uint8_t UVC_AUTO_EXPOSURE_MODE_AUTO = 2;
        res = uvc_set_ae_mode(devh, UVC_AUTO_EXPOSURE_MODE_AUTO);
        if (res == UVC_SUCCESS)
        {
            puts(" ... enabled auto exposure");
        }
        else if (res == UVC_ERROR_PIPE)
        {
            /* this error indicates that the camera does not support the full AE mode;
             * try again, using aperture priority mode (fixed aperture, variable exposure time) */
            puts(" ... full AE not supported, trying aperture priority mode");
            const uint8_t UVC_AUTO_EXPOSURE_MODE_APERTURE_PRIORITY = 8;
            res = uvc_set_ae_mode(devh, UVC_AUTO_EXPOSURE_MODE_APERTURE_PRIORITY);
            if (res < 0)
            {
                uvc_perror(res, " ... uvc_set_ae_mode failed to enable aperture priority mode");
            }
            else
            {
                puts(" ... enabled aperture priority auto exposure mode");
            }
        }
        else
        {
            uvc_perror(res, " ... uvc_set_ae_mode failed to enable auto exposure mode");
        }
    }
}

void UVCQObject::stop()
{

    /* End the stream. Blocks until last callback is serviced */
    uvc_stop_streaming(devh);
    puts("Done streaming.");

    /* Release our handle on the device */
    uvc_close(devh);
    puts("Device closed");

    /* Release the device descriptor */
    uvc_unref_device(dev);

    /* Close the UVC context. This closes and cleans up any existing device handles,
     * and it closes the libusb context if one was not provided. */
    uvc_exit(ctx);
    puts("UVC exited");
}

UVCQObject::UVCQObject()
{
    uvc_error res = init();
    if (res)
        throw("Failed to setup UVC thread");
}

uvc_error UVCQObject::init()
{
    uvc_error res;

    res = uvc_init(&ctx, NULL);

    if (res < 0)
    {
        uvc_perror(res, "uvc_init");
        return res;
    }

    puts("UVC initialized");

    res = uvc_find_device(
        ctx, &dev,
        0, 0, NULL); /* filter devices: vendor_id, product_id, "serial_num" */

    if (res < 0)
    {
        uvc_perror(res, "uvc_find_device"); /* no devices found */
        return res;
    }
    else
    {
        puts("Device found");

        /* Try to open the device: requires exclusive access */
        res = uvc_open(dev, &devh);

        if (res < 0)
        {
            uvc_perror(res, "uvc_open"); /* unable to open device */
            return res;
        }
        else
        {
            puts("Device opened");
            uvc_print_diag(devh, stderr);

            const uvc_format_desc_t *format_desc = uvc_get_format_descs(devh);
            enum uvc_frame_format frame_format;
            int width = 640;
            int height = 480;
            int fps = 30;
                const uvc_frame_desc_t *frame_desc;
            while (format_desc != NULL)
            {
                frame_desc = format_desc->frame_descs;
                switch (format_desc->bDescriptorSubtype)
                {
                case UVC_VS_FORMAT_MJPEG:
                    frame_format = UVC_COLOR_FORMAT_MJPEG;
                    break;
                case UVC_VS_FORMAT_FRAME_BASED:
                    frame_format = UVC_FRAME_FORMAT_H264;
                    break;
                default:
                    frame_format = UVC_FRAME_FORMAT_YUYV;
                    break;
                }
                if (frame_format == UVC_FRAME_FORMAT_YUYV)
                    break;

                format_desc = format_desc->next;
            }

            if (frame_desc)
            {
                width = frame_desc->wWidth;
                height = frame_desc->wHeight;
                fps = 10000000 / frame_desc->dwDefaultFrameInterval;
            }

            printf("\nFirst format: (%4s) %dx%d %dfps\n", format_desc->fourccFormat, width, height, fps);

            /* Try to negotiate first stream profile */
            res = uvc_get_stream_ctrl_format_size(
                devh, &ctrl, /* result stored in ctrl */
                frame_format,
                width, height, fps /* width, height, fps */
            );

            /* Print out the result */
            uvc_print_stream_ctrl(&ctrl, stderr);
        }
    }
    return UVC_SUCCESS;
}

//     if (res < 0)
//     {
//         uvc_perror(res, "get_mode"); /* device doesn't provide a matching stream */
//     }
//     else
//     {
//         /* Start the video stream. The library will call user function cb:
//          *   cb(frame, (void *) 12345)
//          */
