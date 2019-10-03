import apraw
import praw
import asyncio
import re
import sys
import math
import os
import re
import json
from datetime import datetime
from math import sqrt, pow
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def get_difference(rgb1, rgb2):
    rgb1 = sRGBColor(rgb1[0], rgb1[1], rgb1[2])
    rgb2 = sRGBColor(rgb2[0], rgb2[1], rgb2[2])

    lab1 = convert_color(rgb1, LabColor)
    lab2 = convert_color(rgb2, LabColor)

    delta = delta_e_cie2000(lab1, lab2)

    return delta


def perfect_sqr(n):
    nextN = math.floor(math.sqrt(n)) + 1
    return nextN * nextN


def largest_prime_factor(n):
    i = 2
    while i * i <= n:
        if n % i:
            i += 1
        else:
            n //= i
    return n


def save_grid(rgbs, filename="image.png", block_size=200):
    gridy = int(perfect_sqr(len(rgbs)) ** 0.5)

    if gridy ** 2 != len(rgbs):
        gridy = largest_prime_factor(len(rgbs))

    gridy = 15

    grid = list()
    row = list()
    count = 0
    for i in range(0, len(rgbs)):
        c = rgbs[i]
        row.append(c)
        count += 1
        if count % gridy == 0 or i == len(rgbs) - 1:
            grid.append(row)
            row = list()

    image = Image.new("RGBA", (len(grid[0]) * block_size, len(grid) * block_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font_size = int(block_size / 10)
    font = ImageFont.truetype("Roboto.ttf", font_size)

    for i in range(0, len(grid)):
        row = grid[i]
        yrange = list(range(i * block_size, i * block_size + block_size))
        for j in range(0, len(row)):
            rgb = hex_to_rgb(row[j]["hex"])
            xrange = list(range(j * block_size, j * block_size + block_size))

            for x in xrange:
                for y in yrange:
                    image.putpixel((x, y), rgb)

            # h = "#%02x%02x%02x" % rgb
            padding = int(block_size / 20)

            diff_to_white = get_difference(rgb, WHITE)

            font_color = WHITE if diff_to_white > 40 else BLACK

            text = "/u/{}\n{}".format(row[j]["c_author"], row[j]["hex"]) if "c_author" in row[j] else row[j]["hex"]
            draw.text((j * block_size + padding, i * block_size + padding), text, font_color, font=font)

    image.save(filename)

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

AUTHOR = "XelaaleX1234"
COLOR = "#41e8e2"
COLOR_RGB = hex_to_rgb(COLOR)

def process_comments():
    file = open("comments.json")
    cs = json.loads(file.read())
    ids = [c["c_id"] for c in cs if "c_id" in c]
    file.close()

    reddit = praw.Reddit("D6B")
    s = reddit.submission("db8k9e")
    s.comments.replace_more(limit=None)
    i = 0
    nc = 0
    ic = 0
    for c in s.comments.list():
        i += 1
        if c.id in ids or c.author.name.lower() == s.author.name.lower():
            continue
        nc += 1
        h = ""
        for r in re.findall("(#?[a-fA-F0-9]{3,6})", c.body):
            if r.startswith("#"):
                h = r
            elif h == "":
                h = "#" + r

        if len(h) == 7:
            r = hex_to_rgb(h)
            cs.append({
                "c_id": c.id,
                "c_author": c.author.name,
                "c_body": c.body,
                "hex": h,
                "diff": get_difference(r, COLOR_RGB)
            })
            ic += 1
        else:
            print("No color in comment by /u/{} found. Would you like to manually enter one?".format(c.author))
            us = input(c.body + " ")
            if "y" in us:
                h = input("What color? ")
                r = hex_to_rgb(h)
                cs.append({
                    "c_id": c.id,
                    "c_author": str(c.author),
                    "c_body": c.body,
                    "hex": h,
                    "diff": get_difference(r, COLOR_RGB)
                })
                ic += 1
            else:
                cs.append({
                    "c_id": c.id,
                    "c_author": str(c.author),
                    "c_body": c.body
                })

    with open("comments.json", "w+") as f:
        f.write(json.dumps(cs, indent=4))

    print("Total comments:", i)

    cc = 0
    for c in cs:
        if "hex" in c:
            cc += 1
    print("Total comments with color:", cc)

    print("New comments:", nc)
    print("New comments with color:", ic)

    cs = [c for c in cs if "hex" in c]
    cs = sorted(cs, key=lambda c: c["diff"])
    cs.insert(0, {"c_author": AUTHOR, "hex": COLOR, "diff": 0})

    print("")
    print("Saving image...")
    save_grid(cs, "guesses.png")
    print("Done saving image!")

def generate_color_card(color=COLOR, author=AUTHOR, filename="color.png", block_size=1000):
    save_grid([{"hex": color, "c_author": author}], filename, block_size)

time_started = datetime.now()
process_comments()
print("Processing comments & saving image:", datetime.now() - time_started)
generate_color_card()
# generate_color_card("#5d2573", "SantasChristmasWish", "Kallie.png")
