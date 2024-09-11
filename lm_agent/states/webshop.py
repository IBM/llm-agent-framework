# Standard
from typing import Any, Callable, Dict
import json

# Third Party
from bs4 import BeautifulSoup
from bs4.element import Comment
import requests

# Local
from lm_agent.base.registry import register_state_handler
from lm_agent.base.state_handler import BaseStateHandler, StateHandlerConfig


@register_state_handler("webshop_observation")
class WebshopObservationHandler(BaseStateHandler):
    def __init__(self, config: StateHandlerConfig, *args: Any, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.env = WebshopEnv()
        self._retrieved_items = []
        self.idx = f"fixed_{config.webshop_idx}"
        observation, reward, done, asins, buttons = self.env.step(self.idx, "reset")
        self.input_text = observation
        self.observed_reward = reward
        self.trajectory = []

    def adjust_prompt_args(self, prompt_kwargs: Dict):
        prompt_kwargs[
            "tool_descriptions"
        ] = "(1) search: a tool you can use to search for products. You can ONLY use this from the WebShop page"
        prompt_kwargs[
            "tool_descriptions"
        ] += '\n(2) click: a tool you can use to click on a website button. The buttons will be marked with brackets "[" and "]", e.g., "[Next >]". To click a button, select it as an Action Input'
        return prompt_kwargs

    def __call__(self, monitor, *args: Any, **kwds: Any) -> str:
        # Hack hack
        history = monitor.history
        action_name, action_input = history[-2][1], history[-1][1]
        action = f"{action_name}[{action_input}]"

        self.trajectory = [(state.name, resp) for state, resp in history]

        observation, reward, done, asins, buttons = self.env.step(self.idx, action)
        observation = observation.strip()
        self.observed_reward = reward
        assert not done

        return observation


@register_state_handler("webshop_summarize")
class WebshopSummarizationHandler(BaseStateHandler):
    def __init__(self, config: StateHandlerConfig, *args: Any, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.env = WebshopEnv()
        self._retrieved_items = []
        self.idx = f"fixed_{config.webshop_idx}"
        observation, reward, done, asins, buttons = self.env.step(self.idx, "reset")
        self.input_text = observation
        self.observed_reward = reward
        self.trajectory = []
        self.summarizer = ToolSetSummarizeHandler(config)
        self.llm_scorer = LlmScoringTool(config)

    def adjust_prompt_args(self, prompt_kwargs: Dict):
        prompt_kwargs[
            "tool_descriptions"
        ] = "(1) search: a tool you can use to search for products. You can ONLY use this from the WebShop page"
        prompt_kwargs[
            "tool_descriptions"
        ] += '\n(2) click: a tool you can use to click on a website button. The buttons will be marked with brackets "[" and "]", e.g., "[Next >]". To click a button, select it as an Action Input'
        return prompt_kwargs

    def __call__(self, monitor, *args: Any, **kwds: Any) -> str:
        def is_meta_line(line):
            return ("[" in line and "]" in line) or any(
                [line.startswith(x) for x in ["Page "]]
            )

        # Hack hack
        history = [(state.name, resp) for state, resp in monitor.history]
        init_text = history[0][-1].split("Instruction: ")[-1].strip()

        self.trajectory = history + []

        observations = []
        orig_observations = []
        while len(history) >= 2:
            # print(json.dumps(history, indent=4))
            # input('--')
            state_label = history[-2][0]
            if "action" == state_label:
                action_input = history.pop()[1]
                action_name = history.pop()[1]
                action = f"{action_name}[{action_input}]"

                observation, reward, done, asins, buttons = self.env.step(
                    self.idx, action
                )
                # print(observation)
                observation = observation.strip()
                new_observation_lines = []

                to_summarize = [
                    line.strip()
                    for line in observation.split("\n")
                    if not is_meta_line(line)
                ]
                summarized_lines = self.summarizer.summarize(to_summarize, init_text)
                summary_map = dict(zip(to_summarize, summarized_lines))

                for line in observation.split("\n"):
                    if line:
                        if is_meta_line(line):
                            # summarize only non-buttons
                            summarized_line = line.strip()
                        else:
                            summarized_line = summary_map[line.strip()].strip()
                            if not summarized_line:
                                summarized_line = line.strip()
                        new_observation_lines.append(summarized_line)
                new_observation = "\n".join(new_observation_lines)
                observations.append(new_observation)
                orig_observations.append(observation)

                # print(json.dumps(observation.split('\n'), indent=4))
                # print('##')
                # print(json.dumps(new_observation_lines, indent=4))
                # input('%%')

                self.observed_reward = reward
                assert not done
            else:
                history = []

        obs_str = "\n".join(observations)
        resp_str = "\n".join(orig_observations)

        if obs_str.strip() == resp_str.strip():
            return obs_str

        gen_output = (
            monitor.input_text
            + monitor.get_generated_response()
            + f"\n{monitor.get_current_state().text} "
        )

        obs_sc = self.llm_scorer(gen_output, obs_str)
        summ_sc = self.llm_scorer(gen_output, resp_str)

        return resp_str if summ_sc > obs_sc else obs_str


WEBSHOP_URL = "http://127.0.0.1:3000"
ACTION_TO_TEMPLATE = {
    "Description": "description_page.html",
    "Features": "features_page.html",
    "Reviews": "review_page.html",
    "Attributes": "attributes_page.html",
}
MAX_PRO_OB = 8


def clean_str(p):
    return p.encode().decode("unicode-escape").encode("latin1").decode("utf-8")


def tag_visible(element):
    ignore = {"style", "script", "head", "title", "meta", "[document]"}
    return element.parent.name not in ignore and not isinstance(element, Comment)


def webshop_text(
    session,
    page_type,
    query_string="",
    page_num=1,
    asin="",
    options={},
    subpage="",
    **kwargs,
):
    if page_type == "init":
        url = f"{WEBSHOP_URL}/{session}"
    if page_type == "search":
        url = f"{WEBSHOP_URL}/search_results/{session}/" f"{query_string}/{page_num}"
    elif page_type == "item":
        url = (
            f"{WEBSHOP_URL}/item_page/{session}/"
            f"{asin}/{query_string}/{page_num}/{options}"
        )
    elif page_type == "item_sub":
        url = (
            f"{WEBSHOP_URL}/item_sub_page/{session}/"
            f"{asin}/{query_string}/{page_num}/{subpage}/{options}"
        )
    elif page_type == "end":
        url = f"{WEBSHOP_URL}/done/{session}/" f"{asin}/{options}"
    # print(url)
    html = requests.get(url).text
    html_obj = BeautifulSoup(html, "html.parser")
    texts = html_obj.findAll(text=True)
    visible_texts = list(filter(tag_visible, texts))
    # visible_texts = [str(text).strip().strip('\\n') for text in visible_texts]
    # if page_type == 'end': import pdb; pdb.set_trace()

    observation = ""
    option_type = ""
    options = {}
    asins = []
    cnt = 0
    prod_cnt = 0
    just_prod = 0
    clickable = []
    for t in visible_texts:
        if t == "\n":
            continue
        if t.replace("\n", "").replace("\\n", "").replace(" ", "") == "":
            continue
        # if t.startswith('Instruction:') and page_type != 'init': continue
        # print(t.parent.name, t)
        if t.parent.name == "button":  # button
            processed_t = f"\n[{t}] "
            clickable.append(t)
        elif t.parent.name == "label":  # options
            if f"'{t}'" in url:
                processed_t = f"[[{t}]]"
                # observation = f'You have clicked {t}.\n' + observation
            else:
                processed_t = f"[{t}]"
            options[str(t)] = option_type
            # options[option_type] = options.get(option_type, []) + [str(t)]
        elif t.parent.get("class") == ["product-link"]:  # product asins
            processed_t = f"\n[{t}] "
            if prod_cnt >= MAX_PRO_OB:
                processed_t = ""
            prod_cnt += 1
            asins.append(str(t))
            just_prod = 0
        else:  # regular, unclickable text
            processed_t = "\n" + str(t) + " "
            if cnt < 2 and page_type != "init":
                processed_t = ""
            if just_prod <= 2 and prod_cnt > MAX_PRO_OB:
                processed_t = ""
            option_type = str(t)
            cnt += 1
        just_prod += 1
        observation += processed_t
    info = {}
    if options:
        info["option_types"] = options
    if asins:
        info["asins"] = asins
    if "Your score (min 0.0, max 1.0)" in visible_texts:
        idx = visible_texts.index("Your score (min 0.0, max 1.0)")
        info["reward"] = float(visible_texts[idx + 1])
        observation = "Your score (min 0.0, max 1.0): " + (visible_texts[idx + 1])
    clickable.extend(asins)
    # merging option buttons
    clickable.extend(options)
    return clean_str(observation), info, clickable


class WebshopEnv:
    def __init__(self):
        self.sessions = {}

    def step(self, session, action):
        done = False
        observation_ = None
        if action == "reset":
            self.sessions[session] = {"session": session, "page_type": "init"}
        elif action.startswith("search"):
            assert self.sessions[session]["page_type"] == "init"
            query = action[7:-1]
            self.sessions[session] = {
                "session": session,
                "page_type": "search",
                "query_string": query,
                "page_num": 1,
            }
        elif action.startswith("click"):
            button = action[6:-1]
            while button.startswith("["):
                button = button[1:]
            while button.endswith("]"):
                button = button[:-1]
            if button == "Buy Now":
                assert self.sessions[session]["page_type"] == "item"
                self.sessions[session]["page_type"] = "end"
                done = True
            elif button == "Back to Search":
                assert self.sessions[session]["page_type"] in [
                    "search",
                    "item_sub",
                    "item",
                ]
                self.sessions[session] = {"session": session, "page_type": "init"}
            elif button == "Next >":
                assert False  # ad hoc page limitation
            elif button == "< Prev":
                assert self.sessions[session]["page_type"] in [
                    "search",
                    "item_sub",
                    "item",
                ]
                if self.sessions[session]["page_type"] == "search":
                    assert False
                elif self.sessions[session]["page_type"] == "item_sub":
                    self.sessions[session]["page_type"] = "item"
                elif self.sessions[session]["page_type"] == "item":
                    self.sessions[session]["page_type"] = "search"
                    self.sessions[session]["options"] = {}
            elif button in ACTION_TO_TEMPLATE:
                assert self.sessions[session]["page_type"] == "item"
                self.sessions[session]["page_type"] = "item_sub"
                self.sessions[session]["subpage"] = button
            else:
                if self.sessions[session]["page_type"] == "search":
                    assert button in self.sessions[session].get(
                        "asins", []
                    ), f'Button [{button}] must be in [{", ".join(self.sessions[session].get("asins", []))}]'  # must be asins
                    self.sessions[session]["page_type"] = "item"
                    self.sessions[session]["asin"] = button
                elif self.sessions[session]["page_type"] == "item":
                    assert "option_types" in self.sessions[session]
                    assert button in self.sessions[session]["option_types"], (
                        button,
                        self.sessions[session]["option_types"],
                    )  # must be options
                    option_type = self.sessions[session]["option_types"][button]
                    if not "options" in self.sessions[session]:
                        self.sessions[session]["options"] = {}
                    self.sessions[session]["options"][option_type] = button
                    observation_ = f"You have clicked {button}."
        else:
            assert False
        observation, info, clickable = webshop_text(**self.sessions[session])
        if observation_:
            observation = observation_
        self.sessions[session].update(info)
        reward = info.get("reward", 0.0)
        asins = info.get("asins", [])
        return observation, reward, done, asins, clickable
