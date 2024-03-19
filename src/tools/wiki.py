from typing import Any
import wikipedia, requests, re

from ..config import Config
from .tool_handler import Tool

class WikipediaSearchTool(Tool):

    name: str = 'Search'
    description: str = 'which searches the exact entity on Wikipedia and returns the first paragraph if it exists. If not, it will return some similar entities to search.'

    def __init__(self, config : Config):
        super().__init__(config)
        self._context = None

    def __call__(self, action_input : str, *args: Any, attempts=3, **kwds: Any) -> Any:

        def _strip(string):
            if string.startswith('"'):
                return _strip(string[1:])
            elif string.endswith('"'):
                return _strip(string[:-1])
            return string

        try:
            action_input = _strip(action_input)
            self._context = wikipedia.summary(action_input, auto_suggest=False)
            text = self._context.replace('\n', ' ')
            response = ' '.join([s.strip() + '.' for s in text.split('. ') if s.strip()][:2])
        except wikipedia.DisambiguationError as e:
            response = f'Could not find \'{action_input}\'. Similar: [\'' + '\', \''.join(e.options[:5]) + '\']'
        except wikipedia.PageError as e:
            search_results = wikipedia.search(action_input)
            if search_results: response = f'Could not find \'{action_input}\'. Similar: [\'' + '\', \''.join(search_results[:5]) + '\']'
            else: response = f'Could not find \'{action_input}\'. No similar options can be found!'
        except KeyError as e:
            response = f'Could not find \'{action_input}\'. No similar options can be found!'
        except wikipedia.exceptions.WikipediaException as e:
            if 'Search is currently too busy' in str(e):
                return self(action_input, attempts=attempts - 1, *args, **kwds) if attempts > 0 else 'Search is currently too busy!'
        except requests.exceptions.JSONDecodeError as e:
            return self(re.escape(action_input), attempts=attempts - 1, *args, **kwds) if attempts > 0 else 'JSON decoding error!'

        return response


class WikipediaLookupTool(Tool):

    name: str = 'Lookup'
    description: str = 'which returns the next sentence containing keyword in the current passage.'

    def __init__(self, config : Config):
        super().__init__(config)
        self._context = ''
        self._keyword = ''
        self._lookup_count = 0
        self._lookup_list = []

    def __call__(self, action_input : str, *args: Any, **kwds: Any) -> Any:
        if action_input != self._keyword:
            self._keyword = action_input
            self._lookup_count = 0
            self._construct_lookup_list()
        else:
            self._lookup_count += 1

        if self._lookup_count >= len(self._lookup_list): 
            return 'No more results.' if self._context else f'Cannot use {self.__class__.name} without using {WikipediaSearchTool.name} first!'
        else:
            response = f'(Result {self._lookup_count + 1} / {len(self._lookup_list)}) {self._lookup_list[self._lookup_count]}'
        return response
    
    def update_state(self, action_tool: Tool):
        if type(action_tool) == WikipediaSearchTool:
            self._context = action_tool._context
            self._lookup_count = 0

    def _construct_lookup_list(self):
        # find all paragraphs
        if self._context is None:
            self._lookup_list = []
        else:
            paragraphs = [p.strip() for p in self._context.split("\n") if p.strip()]
            sentences = [sentence.strip() for paragraph in paragraphs for sentence in paragraph.split('. ')]
            self._lookup_list = [sentence for sentence in sentences if sentence.strip() and self._keyword in sentence]
