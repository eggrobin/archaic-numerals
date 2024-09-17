import math

from PIL import ImageFont

font = ImageFont.truetype("Archaic-Cuneiform-Numerals.ttf", size=16)
names : dict[int, str] = {}
with open("dUnicodeData.txt") as f:
  for line in f.readlines():
    cp, name = line.split(';')[:2]
    names[int(cp, base=16)]=name

def width(cp: int) -> float:
  return font.getlength(chr(cp))

def height(cp: int) -> int:
  box = font.getbbox(chr(cp))
  return box[3]-box[1]

by_height = {}
by_width = {}

for cp in names.keys():
  if height(cp) not in by_height or ('ONE' in names[cp] and 'ONE' not in names[by_height[height(cp)]]):
    by_height[height(cp)] = cp
  if width(cp) not in by_width or ('ONE' in names[cp] and 'ONE' not in names[by_width[width(cp)]]):
    by_width[width(cp)] = cp

for h in reversed(sorted(by_height.keys())):
  print("U+%04X" % by_height[h], "h=%02d" % height(by_height[h]), names[by_height[h]])

for w in reversed(sorted(by_width.keys())):
  print("U+%04X" % by_width[w], "w=%02d" % width(by_width[w]), names[by_width[w]])

maxwidth = width(0x1257A)
maxheight = height(0x12644)

ranges_by_size : dict[int, list[tuple[int, int]]] = {}

for cp in names.keys():
  w = width(cp)
  h = height(cp)
  if w > maxwidth or h > maxheight:
    size = math.floor(min(maxwidth/w, maxheight/h)*16)
    print(size, "U+%04X" % cp, names[cp])
    if size not in ranges_by_size:
      ranges_by_size[size] = [(cp, cp)]
    else:
      first, last = ranges_by_size[size][-1]
      if last == cp - 1:
        ranges_by_size[size][-1] = (first, cp)
      else:
        ranges_by_size[size].append((cp, cp))

for size in sorted(ranges_by_size.keys()):
  line = f"Archaic Cuneiform Numerals,{size} /X=0000-10FFFF"
  for range in ranges_by_size[size]:
    line += f" /I={range[0]:04X}-{range[1]:04X}"
  print(line)