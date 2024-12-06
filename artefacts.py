import html.parser
import re
from typing import Literal, Optional
import urllib.request
import sys

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
           line_number = tuple(str(deromanize(s)) if re.match(r'^[ivxlcdm]+$', s) else s for s in data.split())
           if artefact == 'P010586' and line_number[0] not in ('o', 'r'):
             line_number = ('o', *line_number)
           self.line_to_id[line_number] = self.line_id or None

def get_line_to_id_map(project: str, artefact: str):
  with urllib.request.urlopen('https://oracc.museum.upenn.edu/' + project + '/' + artefact) as f:
    page = f.read().decode('utf-8')
  parser = Parser()
  parser.feed(page)
  return parser.line_to_id

with open(f'{sys.argv[1]}.tex', encoding='utf-8') as f:
   source = f.read()

class Argument:
  position: int
  string: str
  brackets:  Literal['[]', '{}']

  def __init__(self, position : int, string : str, brackets : Literal['[]', '{}']):
    self.position = position
    self.string = string
    self.brackets = brackets

  def __repr__(self):
    return f"Argument({self.position}, {repr(self.string)})"

citations : list[list[Argument]] = []

for match in re.finditer(r'\\cites?(?=[\[{])', source):
  i = match.end()
  depth = 0
  start = i
  args : list[Argument] = []
  while i < len(source):
    c = source[i]
    if c in ('[', '{'):
      depth += 1
      i += 1
    elif c in (']', '}'):
      depth -= 1
      if depth == 0:
        args.append(Argument(start, source[start+1:i], '[]' if c == ']' else '{}'))
        start = i+1
      i += 1
    elif depth == 0:
      break
    elif c == '\\':
      i += 2
    else:
      i += 1
  else:
    raise SyntaxError("File ended while parsing \\cite" + str(args))
  citations.append(args)

location_arg = None

substitutions : list[tuple[Argument, str]] = []

for citation in citations:
  for arg in citation:
    if arg.brackets == '[]':
      if not r'\href' in arg.string:
        location_arg = arg
    if arg.brackets == '{}':
      if location_arg and re.match(r'^[PQ][0-9]+$', arg.string):
        artefact = arg.string
        if artefact == 'P222399':
          artefact = 'Q001056'
        location_sources = [s.strip() for s in location_arg.string.split(';')]
        locations : list[tuple[str, ...]] = []
        for location in location_sources:
          parts = tuple('o' if part == r'\obverse' else
                        'r' if part == r'\reverse' else
                        part.split('--')[0].replace('′',"'")
                        for part in location.split('~')
                        if part not in (r"\psq", r"\psqq"))
          if not locations or len(parts) >= len(locations[-1]):
            locations.append(parts)
          else:
            locations.append(locations[-1][:-len(parts)] + parts)
        print(arg.string, locations, location_arg)
        print(locations)
        for project in 'etcsri', 'dccmt', 'dcclt', 'epsd2':
          line_to_id = get_line_to_id_map(project, artefact)
          for i, location in enumerate(locations):
            if 'href' in location_sources[i]:
              raise NameError(location_arg, artefact)
            if location not in line_to_id:
              break
            id = line_to_id[location]
            if not id:
              break
            location_sources[i] = r'\href{http://oracc.org/' + project + '/' + id + '}{' + location_sources[i] + '}'
          else:
            break
        substitutions.append((location_arg, ';'.join(location_sources)))
        print(location_arg.string, '->', ';'.join(location_sources), ' at ', location_arg.position)
      location_arg = None

substitutions = sorted(substitutions, key=lambda s: -s[0].position)

for arg, replacement in substitutions:
  if source[arg.position+1:arg.position+1+len(arg.string)] != arg.string:
    raise ValueError(source[arg.position+1:arg.position+1+len(arg.string)], arg.string)
  source = source[:arg.position+1] + replacement + source[arg.position+1 + len(arg.string):]

with open(f'{sys.argv[1]}.tex', 'w', encoding='utf-8') as f:
   f.write(source)