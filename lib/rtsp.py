def capture_image_cv2(stream_url, img_path):
    from cv2 import VideoCapture, imwrite
    vcap = VideoCapture(stream_url)
    if vcap.isOpened():
        ret, frame = vcap.read()
        vcap.release()
        if ret:
            imwrite(img_path, frame)
            return True
    return False


def capture_image_av(stream_url, img_path):
    import av
    options = {
        'rtsp_transport': 'tcp',
        'rtsp_flags': 'prefer_tcp',
        'stimeout': '60000000',
    }
    try:
        with av.open(stream_url, options=options, timeout=20) as c:
            vs = c.streams.video[0]
            if vs.profile is not None and vs.codec_context.format and vs.start_time is not None:
                vs.thread_type = "AUTO"
                for frame in c.decode(video=0):
                    frame.to_image().save(img_path)
                    return True

    except Exception as e:
        # print('[E]', stream_url, repr(e))
        pass

    return False


def capture_image(stream_url, img_path, prefer_ffmpeg=False):
    if prefer_ffmpeg:
        return capture_image_av(stream_url, img_path)
    try:
        return capture_image_cv2(stream_url, img_path)
    except ImportError:
        return capture_image_av(stream_url, img_path)
