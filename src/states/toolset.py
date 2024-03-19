import copy
from typing import Any, Dict

from ..tools.tool_handler import Tool
from ..constrained_decoding import DecodingMonitor
from ..config import Config
from .tool import ToolStateHandler
from ..tools.llm import LlmGenerationTool, LlmScoringTool
from .state_handler import *

class ToolSetHandler(ToolStateHandler): pass

class ToolSetSummarizeHandler(ToolSetHandler):

    name: str = 'summarize'

    _PREFIX = 'You will be given a list of statements, a context, and a goal you are trying to solve. Your task is to summarize the list of statements as they relate to the provided goal while keeping the context in mind as best you can. The format of your output should be as follows:'
    _FORMAT = 'Statements: A list of N statements to summarize\nContext: the context to keep in mind for the summary\nGoal: the goal to focus on\nSummary: the list of statements summarized'
    _GEN_EXAMPLES = [
        "Here are a few examples.", 
        "Statements: 1. The Colorado orogeny was an episode of mountain building (an orogeny) in Colorado and surrounding areas. This took place from 1780 to 1650 million years ago (Mya), during the Paleoproterozoic (Statherian Period).\nContext: What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?\nGoal: I need to search Colorado orogeny, find the area that the eastern sector of the Colorado orogeny extends into, then find the elevation range of the area.\nSummary: The Colorado orogeny was an episode of mountain building in the Colorado area.",
        "Statements: 1. Milhouse Mussolini Van Houten is a recurring character in the Fox animated television series The Simpsons voiced by Pamela Hayden and created by Matt Groening.\nContext: Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?\nGoal: The question simplifies to \"The Simpsons\" character Milhouse is named after who. I only need to search Milhouse and find who it is named after.\nSummary: The paragraph does not tell who Milhouse is named after",
        "Statements: 1. Could not find 'Adam Clayton Powell'. Similar: ['Adam Clayton Powell III', 'Seventh Avenue (Manhattan)', 'Adam Powell', 'Adam Clayton Powell (film)', 'Giancarlo Esposito']\n2. The Saimaa Gesture (Finnish: Saimaa-ilmiö) is a 1981 film by Finnish directors Aki and Mika Kaurismäki. It is a documentary about three Finnish rock groups aboard the steamboat SS Heinävesi on their tour around Lake Saimaa.\nContext: Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?\nGoal: I need to search Adam Clayton Powell and The Saimaa Gesture, and find which documentary is about Finnish rock groups.\nSummary: The Saimaa Gesture is about Finnish rock groups. However, I did not search for the right term for Adam Powell. I should instead search for 'Adam Clayton Powell (film)'",
        "Statements: 1. Nicholas Ray (born Raymond Nicholas Kienzle Jr., August 7, 1911 \u2013 June 16, 1979) was an American film director, screenwriter, and actor best known for the 1955 film Rebel Without a Cause.\n2. Elia Kazan was an American film and theatre director, producer, screenwriter and actor.\nContext: What profession does Nicholas Ray and Elia Kazan have in common?\nGoal: I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.\nSummary: The professions of Nicholas Ray are director, screenwriter, and actor, while Elia was a director, producer, screenwriter and actor.",
        "Statements: 1. Arthur's Magazine (1844-\u0080\u00931846) was an American literary periodical published in Philadelphia in the 19th century.\n2. First for Women is a woman's magazine published by Bauer Media Group in the USA.[1] The magazine was started in 1989.\nContext: Which magazine was started first Arthur's Magazine or First for Women?\nGoal: I need to search Arthur's Magazine and First for Women, and find which was started first.\nSummary: Arthur's Magazine was started in 1844 while First for Women was started in 1989",
    ]    
    _SUFFIX = 'Now begin to solve the task or problem. Respond with a concise summary.'

    def __init__(self, config : Config):
        super().__init__(config)
        config = copy.deepcopy(self.config)
        config.tool_model = self.config.model
        self.llm_solver = LlmGenerationTool(config)
        self.llm_scorer = LlmScoringTool(config)

    def __call__(self, monitor : DecodingMonitor, *args: Any, **kwds: Any) -> str:
        history = monitor.history
        i = len(history) - 1
        while history[i][0].name != PLAN_SN: i -= 1
        rel_history = history[i+1:]

        question_text = history[0][1]
        plan_text = history[i][1]

        obs_lst = [(act_name, act_input) for (_, act_name), (_, act_input) in zip(filter(lambda x : x[0].name == ACT_SN, rel_history), filter(lambda x : x[0].name == ACT_INP_SN, rel_history))]

        obs_str = []
        for action_name, action_input in obs_lst:
            obs = self._get_observation(action_name, action_input)
            obs_str.append(obs)

        obs_str = '\n'.join(obs_str)

        llm_text = f'Statements: {obs_str}\nContext: {question_text}\nGoal: {plan_text}\nSummary:'

        prompt = []
        prompt.append(self._PREFIX)
        prompt.append(self._FORMAT)
        prompt.append('\n\n'.join(self._GEN_EXAMPLES))
        prompt.append(self._SUFFIX)
        prompt.append('{{' + self.llm_solver.INP_VAR + '}}')
        prompt = '\n\n'.join(prompt)

        resp = self.llm_solver(llm_text, prompt=prompt)

        gen_output = monitor.input_text + monitor.get_generated_response() + f'\n{monitor.get_current_state().text} '

        obs_sc = self.llm_scorer(gen_output, obs_str)
        summ_sc = self.llm_scorer(gen_output, resp)

        return resp if summ_sc > obs_sc else obs_str


class ToolSetListHandler(ToolSetHandler):

    name: str = 'list-results'

    def __init__(self, config : Config):
        super().__init__(config)

    def __call__(self, monitor : DecodingMonitor, *args: Any, **kwds: Any) -> str:
        history = monitor.history
        i = len(history) - 1
        while history[i][0].name != PLAN_SN: i -= 1
        rel_history = history[i+1:]

        obs_lst = [(act_name, act_input) for (_, act_name), (_, act_input) in zip(filter(lambda x : x[0].name == ACT_SN, rel_history), filter(lambda x : x[0].name == ACT_INP_SN, rel_history))]

        obs_str = []
        for action_name, action_input in obs_lst:
            obs = self._get_observation(action_name, action_input)
            obs_str.append(obs)
        
        obs_str = '\n'.join(obs_str)

        return obs_str
