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
        # 'rtsp_flags': 'prefer_tcp',
        # 'stimeout': '10000000',
    }
    try:
        with av.open(stream_url, options=options, timeout=10) as c:
            vs = c.streams.video[0]
            # vs.thread_type = "AUTO"
            vs.codec_context.skip_frame = 'NONKEY'
            for frame in c.decode(vs):
                frame.to_image().save(img_path, quality=85)
                return True
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print('[E]', stream_url, repr(e))
        pass

    return False


def capture_image(stream_url, img_path, prefer_ffmpeg=False):
    if prefer_ffmpeg:
        return capture_image_av(stream_url, img_path)
    try:
        return capture_image_cv2(stream_url, img_path)
    except ImportError:
        return capture_image_av(stream_url, img_path)
