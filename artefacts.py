import html.parser
from typing import Optional
import urllib.request

with urllib.request.urlopen('https://oracc.museum.upenn.edu/etcsri/Q001056') as f:
  page = f.read().decode('utf-8')

line_to_id : dict[tuple[str, ...], Optional[str]] = {}

def deromanize(s: str) -> int:
  numerals = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}
  total = 0
  last_value = None
  for c in s.lower():
     value = numerals[c]
     if last_value and value > last_value:
       total += value - last_value
       last_value = None
     else:
       if last_value:
         total += last_value
       last_value = value
  if last_value:
    total += last_value
  return total

class Parser(html.parser.HTMLParser):
    line_id : Optional[str] = None
    xlabel_start : Optional[str] = None
    def handle_starttag(self, tag : str, attrs : list[tuple[str, Optional[str]]]):
        attributes = dict(attrs)
        if 'class' in attributes and attributes['class']:
          classes = attributes['class'].split()
        else:
           return
        if (tag == 'tr' and 'l' in classes and 'id' in attributes):
          self.line_id = attributes['id']
        if 'xlabel' in classes:
           self.xlabel_start = tag

    def handle_endtag(self, tag : str):
        if tag == self.xlabel_start:
           self.xlabel_start = None
        if tag == 'tr':
           self.line_id = None

    def handle_data(self, data : str):
        if self.xlabel_start:
           line_to_id[tuple(data.split())] = self.line_id

parser = Parser()
parser.feed(page)

for line, id in line_to_id.items():
   print(line[0], [deromanize(i) if i.isalpha() else i for i in line[1:]], '\t', id)