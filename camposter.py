#!/usr/bin/env python3
from configparser import ConfigParser
import io
from PIL.ImageFont import ImageFont
from fire import Fire
import requests
import re
from PIL import Image, ImageDraw, ImageFont

from lib.files import DATA_DIR, LOCAL_DIR
from lib.utils import encode_ip

CFG_PATH = LOCAL_DIR / '.camposter.ini'
FONT_PATH = DATA_DIR / 'fonts' / 'opensans.ttf'
IP_RE = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')


def main(stream_url, image_path, location):
    print(stream_url, image_path, location)

    cfg = ConfigParser()
    cfg.read(str(CFG_PATH))
    token, chat_id = cfg['tg']['token'], cfg['tg']['chat_id']
    password, water = cfg['enc']['password'], cfg['enc']['water']
    ip = IP_RE.findall(stream_url)[0]
    water = '%s %s' % (encode_ip(ip, password), water)

    url = 'https://api.telegram.org/bot%s/sendphoto' % token

    data = dict(
        chat_id=chat_id,
        caption='```%s```' % stream_url,
        parse_mode='Markdown'
    )

    px = 16
    py = 2

    with open(image_path, 'rb') as f:
        img: Image = Image.open(f)
        w, h = img.size

        text = ' '.join(location)
        print(w, h)
        font_size = min(16, int(16 * h / 640))
        font = ImageFont.truetype(str(FONT_PATH), font_size)
        draw = ImageDraw.Draw(img, 'RGBA')
        _, text_height = draw.textsize('Wg', font)
        water_width, _ = draw.textsize(water, font)

        text_y = h - py - text_height

        draw.rectangle((0, text_y - py, w, h), fill=(0, 0, 0, 160))

        draw.text((px, text_y), text, fill='yellow', font=font)
        draw.text((w - px - water_width, text_y), water,
                  fill=(255, 255, 255, 128), font=font)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        response = requests.post(url, data=data, files={'photo': img_byte_arr})

    print(response.json())


if __name__ == "__main__":
    Fire(main)
