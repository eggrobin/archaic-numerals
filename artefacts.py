import html.parser
import re
from typing import Optional
import urllib.request
from TexSoup import TexSoup
from TexSoup.data import TexNode, BraceGroup, BracketGroup


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

    def __init__(self, *, convert_charrefs: bool = True) -> None:
      self.line_to_id: dict[tuple[str, ...], Optional[str]] = {}
      super().__init__(convert_charrefs=convert_charrefs)

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
           self.line_to_id[tuple(str(deromanize(s)) if re.match(r'^[ivxlcdm]+$', s) else s for s in data.split())] = self.line_id

def get_line_to_id_map(project: str, artefact):
  with urllib.request.urlopen('https://oracc.museum.upenn.edu/' + project + '/' + artefact) as f:
    page = f.read().decode('utf-8')
  parser = Parser()
  parser.feed(page)
  return parser.line_to_id

with open('archaic-numerals.tex', encoding='utf-8') as f:
   source = f.read()

citations : list[TexNode] = []

soup = TexSoup(source, tolerance=1)
for command in ('cite', 'cites'):
  for node in soup.find_all(command):
    if any(isinstance(arg, BraceGroup) and re.match(r'^[PQ][0-9]+$', arg.string) for arg in node.args):
      citations.append(node)

location_arg = None

substitutions = []

for citation in citations:
  for arg in citation.args:
    if isinstance(arg, BracketGroup):
      if not r'\href' in arg.string:
        location_arg = arg
    if isinstance(arg, BraceGroup):
      if location_arg and re.match(r'^[PQ][0-9]+$', arg.string):
        artefact = arg.string
        if artefact == 'P222399':
          artefact = 'Q001056'
        location_sources = location_arg.string.split(';')
        locations = []
        for location in location_sources:
          parts = tuple('o' if part == r'\obverse' else
                        'r' if part == r'\reverse' else
                        part.split('--')[0] for part in location.split('~'))
          if not locations or len(parts) >= len(locations[-1]):
            locations.append(parts)
          else:
            locations.append(locations[-1][:-len(parts)]+parts)
        print(arg.string, locations, location_arg)
        print(locations)
        for project in 'etcsri', 'dccmt', 'dcclt', 'epsd2':
          line_to_id = get_line_to_id_map(project, artefact)
          for i, location in enumerate(locations):
            if location in line_to_id:
              location_sources[i] = r'\href{http://oracc.org/' + project + '/' + line_to_id[location] + '}{' + location_sources[i] + '}'
            else:
              break
          else:
            break
        substitutions.append((location_arg, ';'.join(location_sources)))
        print(location_arg.string, '->', ';'.join(location_sources), ' at ', location_arg.position)
      location_arg = None

substitutions = sorted(substitutions, key=lambda s: -s[0].position)

for arg, replacement in substitutions:
  if source[arg.position+1:arg.position+len(arg.string)] != arg.string:
    raise ValueError(source[arg.position:arg.position+len(arg.string)], arg.string)
  source = source[:arg.position+1] + replacement + source[arg.position+1 + len(arg.string):]

with open('archaic-numerals.tex', 'w', encoding='utf-8') as f:
   f.write(source)