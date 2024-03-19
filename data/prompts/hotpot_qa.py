
{
    'granite_react' : {
        'instructions' : 
            """

            <|system|>
            You are Granite Chat, an AI language model developed by IBM. You are a cautious assistant. You carefully follow instructions. You are helpful and harmless and you follow ethical guidelines and promote positive behavior.
            <|user|>
            You are a AI language model designed to function as a specialized Retrieval Augmented Generation (RAG) assistant. When generating responses, prioritize correctness, i.e., ensure that your response is correct given the context and user query, and that it is grounded in the context. Furthermore, make sure that the response is supported by the given document or context. When the question cannot be answered using the context or document, output the following response: '{response_message}' Always make sure that your response is relevant to the question. If an explanation is needed, first provide the explanation or reasoning, and then give the final answer.
            Answer Length: {slot}
            [Document]
            {document}
            [End]
            {query}
            <|assistant|>

            Answer the following questions as best you can. You have access to the following tools:
            {{tool_descriptions}}
            When answering a question, you should take individual actions until you reach a satisfactory answer.
            Use the following format:
            
            [Question] the input question you must answer
                [Thought] you should always think about what to do
                [Action] the action to take, should be one of {{tool_labels}}
                [Action Input] the input to the action
                [Observation] the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat N times)
            [Final Thought] this is the last thought
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Thought] I need to search Colorado orogeny, find the area that the eastern sector of the Colorado orogeny extends into, then find the elevation range of the area.
            [Action] Search
            [Action Input] Colorado orogeny
            [Observation] The Colorado orogeny was an episode of mountain building (an orogeny) in Colorado and surrounding areas.
            [Thought] It does not mention the eastern sector. So I need to look up eastern sector.
            [Action] Lookup
            [Action Input] eastern sector
            [Observation] (Result 1 / 1) The eastern sector extends into the High Plains and is called the Central Plains orogeny.
            [Thought] The eastern sector of Colorado orogeny extends into the High Plains. So I need to search High Plains and find its elevation range.
            [Action] Search
            [Action Input] High Plains
            [Observation] High Plains refers to one of two distinct land regions: High Plains (United States), High Plains (Other)
            [Thought] I need to instead search High Plains (United States).
            [Action] Search
            [Action Input] High Plains (United States)
            [Observation] The High Plains are a subregion of the Great Plains. From east to west, the High Plains rise in elevation from around 1,800 to 7,000 ft (550 to 2,130 m).[3]
            [Final Thought] High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?
            [Thought] The question simplifies to \"The Simpsons\" character Milhouse is named after who. I only need to search Milhouse and find who it is named after.
            [Action] Search
            [Action Input] Milhouse
            [Observation] Milhouse Mussolini Van Houten is a recurring character in the Fox animated television series The Simpsons voiced by Pamela Hayden and created by Matt Groening.
            [Thought] The paragraph does not tell who Milhouse is named after, maybe I can look up \"named after\".
            [Action] Lookup
            [Action Input] named after
            [Observation] (Result 1 / 1) Milhouse was named after U.S. president Richard Nixon, whose middle name was Milhous.
            [Final Thought] Milhouse was named after U.S. president Richard Nixon, so the answer is Richard Nixon.
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Thought] I need to search Adam Clayton Powell and The Saimaa Gesture, and find which documentary is about Finnish rock groups.
            [Action] Search
            [Action Input] Adam Clayton Powell
            [Observation] Could not find 'Adam Clayton Powell'. Similar: ['Adam Clayton Powell III', 'Seventh Avenue (Manhattan)', 'Adam Clayton Powell Jr. State Office Building', 'Isabel Washington Powell', 'Adam Powell', 'Adam Clayton Powell (film)', 'Giancarlo Esposito'].
            [Thought] To find the documentary, I can search Adam Clayton Powell (film).
            [Action] Search
            [Action Input] Adam Clayton Powell (film)
            [Observation] Adam Clayton Powell is a 1989 American documentary film directed by Richard Kilberg.\nThe film is about the rise and fall of influential African-American politician Adam Clayton Powell Jr.[3][4] It was later aired as part of the PBS series The American Experience.
            [Final Thought] Adam Clayton Powell (film) is a documentary about an African-American politician, not Finnish rock groups. So the documentary about Finnish rock groups must instead be The Saimaa Gesture.
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Thought] I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.
            [Action] Search
            [Action Input] Nicholas Ray
            [Observation] Nicholas Ray (born Raymond Nicholas Kienzle Jr., August 7, 1911 \u2013 June 16, 1979) was an American film director, screenwriter, and actor best known for the 1955 film Rebel Without a Cause.
            [Thought] Professions of Nicholas Ray are director, screenwriter, and actor. I need to search Elia Kazan next and find his professions.
            [Action] Search
            [Action Input] Elia Kazan
            [Observation] Elia Kazan was an American film and theatre director, producer, screenwriter and actor.
            [Final Thought] Professions of Elia Kazan are director, producer, screenwriter, and actor. So profession Nicholas Ray and Elia Kazan have in common is director, screenwriter, and actor.
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Thought] I need to search Arthur's Magazine and First for Women, and find which was started first.
            [Action] Search
            [Action Input] Arthur's Magazine
            [Observation] Arthur's Magazine (1844-\u0080\u00931846) was an American literary periodical published in Philadelphia in the 19th century.
            [Thought] Arthur's Magazine was started in 1844. I need to search First for Women next.
            [Action] Search
            [Action Input] First for Women
            [Observation] First for Women is a woman's magazine published by Bauer Media Group in the USA.[1] The magazine was started in 1989.
            [Final Thought] First for Women was started in 1989. 1844 (Arthur's Magazine) < 1989 (First for Women), so Arthur's Magazine was started first.
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Thought] I need to search Pavel Urysohn and Leonid Levin, find their types of work, then find if they are the same.
            [Action] Search
            [Action Input] Pavel Urysohn
            [Observation] Pavel Samuilovich Urysohn (February 3, 1898 \u00e2\u0080\u0093 August 17, 1924) was a Soviet mathematician who is best known for his contributions in dimension theory.
            [Thought] Pavel Urysohn is a mathematician. I need to search Leonid Levin next and find its type of work.
            [Action] Search
            [Action Input] Leonid Levin
            [Observation] Leonid Anatolievich Levin is a Soviet-American mathematician and computer scientist.
            [Final Thought] Leonid Levin is a mathematician and computer scientist. So Pavel Urysohn and Leonid Levin have the same type of work.
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },
    
    'react' : {
        'instructions' : 
            """
            Answer the following questions as best you can. You have access to the following tools:
            {{tool_descriptions}}
            When answering a question, you should take individual actions until you reach a satisfactory answer.
            Use the following format:
            
            [Question] the input question you must answer
                [Thought] you should always think about what to do
                [Action] the action to take, should be one of {{tool_labels}}
                [Action Input] the input to the action
                [Observation] the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat N times)
            [Final Thought] this is the last thought
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Thought] I need to search Colorado orogeny, find the area that the eastern sector of the Colorado orogeny extends into, then find the elevation range of the area.
            [Action] Search
            [Action Input] Colorado orogeny
            [Observation] The Colorado orogeny was an episode of mountain building (an orogeny) in Colorado and surrounding areas.
            [Thought] It does not mention the eastern sector. So I need to look up eastern sector.
            [Action] Lookup
            [Action Input] eastern sector
            [Observation] (Result 1 / 1) The eastern sector extends into the High Plains and is called the Central Plains orogeny.
            [Thought] The eastern sector of Colorado orogeny extends into the High Plains. So I need to search High Plains and find its elevation range.
            [Action] Search
            [Action Input] High Plains
            [Observation] High Plains refers to one of two distinct land regions: High Plains (United States), High Plains (Other)
            [Thought] I need to instead search High Plains (United States).
            [Action] Search
            [Action Input] High Plains (United States)
            [Observation] The High Plains are a subregion of the Great Plains. From east to west, the High Plains rise in elevation from around 1,800 to 7,000 ft (550 to 2,130 m).[3]
            [Final Thought] High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?
            [Thought] The question simplifies to \"The Simpsons\" character Milhouse is named after who. I only need to search Milhouse and find who it is named after.
            [Action] Search
            [Action Input] Milhouse
            [Observation] Milhouse Mussolini Van Houten is a recurring character in the Fox animated television series The Simpsons voiced by Pamela Hayden and created by Matt Groening.
            [Thought] The paragraph does not tell who Milhouse is named after, maybe I can look up \"named after\".
            [Action] Lookup
            [Action Input] named after
            [Observation] (Result 1 / 1) Milhouse was named after U.S. president Richard Nixon, whose middle name was Milhous.
            [Final Thought] Milhouse was named after U.S. president Richard Nixon, so the answer is Richard Nixon.
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Thought] I need to search Adam Clayton Powell and The Saimaa Gesture, and find which documentary is about Finnish rock groups.
            [Action] Search
            [Action Input] Adam Clayton Powell
            [Observation] Could not find 'Adam Clayton Powell'. Similar: ['Adam Clayton Powell III', 'Seventh Avenue (Manhattan)', 'Adam Clayton Powell Jr. State Office Building', 'Isabel Washington Powell', 'Adam Powell', 'Adam Clayton Powell (film)', 'Giancarlo Esposito'].
            [Thought] To find the documentary, I can search Adam Clayton Powell (film).
            [Action] Search
            [Action Input] Adam Clayton Powell (film)
            [Observation] Adam Clayton Powell is a 1989 American documentary film directed by Richard Kilberg.\nThe film is about the rise and fall of influential African-American politician Adam Clayton Powell Jr.[3][4] It was later aired as part of the PBS series The American Experience.
            [Final Thought] Adam Clayton Powell (film) is a documentary about an African-American politician, not Finnish rock groups. So the documentary about Finnish rock groups must instead be The Saimaa Gesture.
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Thought] I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.
            [Action] Search
            [Action Input] Nicholas Ray
            [Observation] Nicholas Ray (born Raymond Nicholas Kienzle Jr., August 7, 1911 \u2013 June 16, 1979) was an American film director, screenwriter, and actor best known for the 1955 film Rebel Without a Cause.
            [Thought] Professions of Nicholas Ray are director, screenwriter, and actor. I need to search Elia Kazan next and find his professions.
            [Action] Search
            [Action Input] Elia Kazan
            [Observation] Elia Kazan was an American film and theatre director, producer, screenwriter and actor.
            [Final Thought] Professions of Elia Kazan are director, producer, screenwriter, and actor. So profession Nicholas Ray and Elia Kazan have in common is director, screenwriter, and actor.
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Thought] I need to search Arthur's Magazine and First for Women, and find which was started first.
            [Action] Search
            [Action Input] Arthur's Magazine
            [Observation] Arthur's Magazine (1844-\u0080\u00931846) was an American literary periodical published in Philadelphia in the 19th century.
            [Thought] Arthur's Magazine was started in 1844. I need to search First for Women next.
            [Action] Search
            [Action Input] First for Women
            [Observation] First for Women is a woman's magazine published by Bauer Media Group in the USA.[1] The magazine was started in 1989.
            [Final Thought] First for Women was started in 1989. 1844 (Arthur's Magazine) < 1989 (First for Women), so Arthur's Magazine was started first.
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Thought] I need to search Pavel Urysohn and Leonid Levin, find their types of work, then find if they are the same.
            [Action] Search
            [Action Input] Pavel Urysohn
            [Observation] Pavel Samuilovich Urysohn (February 3, 1898 \u00e2\u0080\u0093 August 17, 1924) was a Soviet mathematician who is best known for his contributions in dimension theory.
            [Thought] Pavel Urysohn is a mathematician. I need to search Leonid Levin next and find its type of work.
            [Action] Search
            [Action Input] Leonid Levin
            [Observation] Leonid Anatolievich Levin is a Soviet-American mathematician and computer scientist.
            [Final Thought] Leonid Levin is a mathematician and computer scientist. So Pavel Urysohn and Leonid Levin have the same type of work.
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },

    'pass' : {
        'instructions' :
            """
            Answer the following questions as best you can. You have access to the following tools:
            {{tool_descriptions}}
            When answering a question, you should formulate a plan for how you will solve the question. 
            Then, you should iteratively take sets of actions until you reach a satisfactory answer.
            For efficiency, try to group as many independent actions together as possible in each loop.
            The format of your output should be as follows:
            
            [Question] the input question you must answer
                [Thought] a step in your plan for solving the problem
                    [Action] an action to take, should be one of {{tool_labels}}
                    [Action Input] the input to the action
                    ... (you can list as many action/action input pairs as needed here)
                [Summary] a condensed summary of the action results as they relate to the initial question and most recent plan step
                ... (this action gathering and summarization loop can repeat N times)
            [Final Thought] this is the last thought that summarizes your findings
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Thought] I need to search Colorado orogeny, find the area that the eastern sector of the Colorado orogeny extends into, then find the elevation range of the area.
            [Action] Search
            [Action Input] Colorado orogeny
            [Summary] The Colorado orogeny was an episode of mountain building (an orogeny) in Colorado and surrounding areas.
            [Thought] It does not mention the eastern sector. So I need to look up eastern sector.
            [Action] Lookup
            [Action Input] eastern sector
            [Summary] The eastern sector extends into the High Plains and is called the Central Plains orogeny.
            [Thought] The eastern sector of Colorado orogeny extends into the High Plains. So I need to search High Plains and find its elevation range.
            [Action] Search
            [Action Input] High Plains
            [Summary] High Plains refers to one of two distinct land regions: High Plains (United States), High Plains (Other)
            [Thought] I need to instead search High Plains (United States).
            [Action] Search
            [Action Input] High Plains (United States)
            [Summary] High Plains rise in elevation from around 1,800 to 7,000 ft
            [Final Thought] The eastern sector of the Colorado orogeny extends into the high plains, which has an elevation of 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?
            [Thought] The question simplifies to \"The Simpsons\" character Milhouse is named after who. I only need to search Milhouse and find who it is named after.
            [Action] Search
            [Action Input] Milhouse
            [Summary] Milhouse Mussolini Van Houten is a recurring character in the Fox animated television series.
            [Thought] The paragraph does not tell who Milhouse is named after, maybe I can look up \"named after\".
            [Action] Lookup
            [Action Input] named after
            [Summary] Richard Nixon had a middle name of Milhous, which was used for the Simpsons character Milhouse
            [Final Thought] Milhouse was named after Richard Nixon
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Thought] I need to search Adam Clayton Powell and The Saimaa Gesture, and find which documentary is about Finnish rock groups.
            [Action] Search
            [Action Input] Adam Clayton Powell
            [Action] Search
            [Action Input] The Saimaa Gesture
            [Summary] The Saimaa Gesture is about Finnish rock groups, which is the answer to my question. However, I did not search for the right term for Adam Powell.
            [Thought] I should search Adam Clayton Powell (film) instead to confirm my answer.
            [Action] Search
            [Action Input] Adam Clayton Powell (film)
            [Summary] Adam Clayton Powell is a documentary about an African-American politician
            [Final Thought] Adam Clayton Powell is not a documentary about Finnish rock groups while the The Saimaa Gesture is a documentary about Finnish rock groups.
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Thought] I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.
            [Action] Search
            [Action Input] Nicholas Ray
            [Action] Search
            [Action Input] Elia Kazan
            [Summary] The professions of Nicholas Ray are director, screenwriter, and actor, while Elia was a director, producer, screenwriter and actor.
            [Final Thought] The profession Nicholas Ray and Elia Kazan have in common are director, screenwriter, and actor.
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Thought] I need to search Arthur's Magazine and First for Women, and find which was started first.
            [Action] Search
            [Action Input] Arthur's Magazine
            [Action] Search
            [Action Input] First for Women
            [Summary] Arthur's Magazine was started in 1844 while First for Women was started in 1989
            [Final Thought] 1844 (Arthur's Magazine) < 1989 (First for Women), so Arthur's Magazine was started first.
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Thought] I need to search Pavel Urysohn and Leonid Levin, find their types of work, then find if they are the same.
            [Action] Search
            [Action Input] Pavel Urysohn
            [Action] Search
            [Action Input] Leonid Levin
            [Summary] Pavel Urysohn is a mathematician and Leonid Levin is a mathematician and computer scientist
            [Final Thought] Both Pavel Urysohn and Leonid Levin were mathematicians, so they had the same type of work
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },

    'reflexion' : {
        'instructions' : 
            """
            Answer the following questions as best you can. You have access to the following tools:
            {{tool_descriptions}}
            You will be able to reflect on your answers if you are wrong. 
            When answering a question, you should take individual actions until you reach a satisfactory answer.
            Please use the following format:

            [Question] the input question you must answer
                    [Thought] you should always think about what to do
                    [Action] the action to take, should be one of {{tool_labels}}
                    [Action Input] the input to the action
                    [Observation] the result of the action
                    ... (this Thought/Action/Action Input/Observation can repeat N times)
                [Final Thought] this is the last thought
                [Proposed Answer] this is where you propose an the answer based on the above chain of reasoning
                [Evaluation] this is where you get feedback on your proposed answer
                [Reflection] this is where you would reflect on your proposed answer given the evaluation
                ... (this loop can repeat until you are satisfied with your answer)
            [Answer] this is where you write your final answer
            
            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Thought] I need to search Colorado orogeny, find the area that the eastern sector of the Colorado orogeny extends into, then find the elevation range of the area.
            [Action] Search
            [Action Input] Colorado orogeny
            [Observation] The Colorado orogeny was an episode of mountain building (an orogeny) in Colorado and surrounding areas.
            [Thought] It does not mention the eastern sector. So I need to look up eastern sector.
            [Action] Lookup
            [Action Input] eastern sector
            [Observation] (Result 1 / 1) The eastern sector extends into the High Plains and is called the Central Plains orogeny.
            [Thought] The eastern sector of Colorado orogeny extends into the High Plains. So I need to search High Plains and find its elevation range.
            [Action] Search
            [Action Input] High Plains
            [Observation] High Plains refers to one of two distinct land regions:
            [Thought] I need to instead search High Plains (United States).
            [Action] Search
            [Action Input] High Plains (United States)
            [Observation] The High Plains are a subregion of the Great Plains. From east to west, the High Plains rise in elevation from around 1,800 to 7,000 ft (550 to 2,130 m).[3]
            [Final Thought] High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
            [Proposed Answer] 1,800 to 7,000 ft
            [Evaluation] Correct
            [Reflection] My answer is correct, I should return this as the final answer
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?
            [Thought] The question simplifies to Matt Groenig named a song written by Allie Goertz after who. I should find out what songs Matt Groening wrote.
            [Action] Search
            [Action Input] Matt Groening
            [Observation] Matthew Abram Groening is an American cartoonist, writer, producer, and animator. He is the creator of the comic strip Life in Hell (1977–2012) and the television series The Simpsons, Futurama, and Disenchantment. The Simpsons is the longest-running U.S. primetime-television series in history and the longest-running U.S. animated series and sitcom.
            [Thought] The paragraph does not mention any song that Matt Groening named, I should look up \"song\"
            [Action] Lookup
            [Action Input] song
            [Observation] No Results
            [Final Thought] I don't know what song Matt Groening named
            [Proposed Answer] None
            [Evaluation] Incorrect
            [Reflection] I believe the question was asking for the character that Matt Groening named, rather than asking for a song.
            [Thought] The question simplifies to \"The Simpsons\" character Milhouse is named after who. I only need to search Milhouse and find who it is named after.
            [Action] Search
            [Action Input] Milhouse
            [Observation] Milhouse Mussolini Van Houten is a recurring character in the Fox animated television series The Simpsons voiced by Pamela Hayden and created by Matt Groening.
            [Thought] The paragraph does not tell who Milhouse is named after, maybe I can look up \"named after\".
            [Action] Lookup
            [Action Input] named after
            [Observation] (Result 1 / 1) Milhouse was named after U.S. president Richard Nixon, whose middle name was Milhous.
            [Final Thought] Milhouse was named after U.S. president Richard Nixon, so the answer is Richard Nixon.
            [Proposed Answer] Richard Nixon
            [Evaluation] Correct
            [Reflection] My answer is correct, I should return this as the final answer
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Thought] I need to search Adam Clayton Powell and The Saimaa Gesture, and find which documentary is about Finnish rock groups.
            [Action] Search
            [Action Input] Adam Clayton Powell
            [Observation] Could not find 'Adam Clayton Powell'. Similar: ['Adam Clayton Powell III', 'Seventh Avenue (Manhattan)', 'Adam Clayton Powell Jr. State Office Building', 'Isabel Washington Powell', 'Adam Powell', 'Adam Clayton Powell (film)', 'Giancarlo Esposito'].
            [Thought] To find the documentary, I can search Adam Clayton Powell (film).
            [Action] Search
            [Action Input] Adam Clayton Powell (film)
            [Observation] Adam Clayton Powell is a 1989 American documentary film directed by Richard Kilberg.\nThe film is about the rise and fall of influential African-American politician Adam Clayton Powell Jr.[3][4] It was later aired as part of the PBS series The American Experience.
            [Final Thought] Adam Clayton Powell (film) is a documentary about an African-American politician, not Finnish rock groups. So the documentary about Finnish rock groups must instead be The Saimaa Gesture.
            [Proposed Answer] The Saimaa Gesture
            [Evaluation] Correct
            [Reflection] My answer is correct, I should return this as the final answer
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Thought] I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.
            [Action] Search
            [Action Input] Nicholas Ray
            [Observation] Nicholas Ray (born Raymond Nicholas Kienzle Jr., August 7, 1911 \u2013 June 16, 1979) was an American film director, screenwriter, and actor best known for the 1955 film Rebel Without a Cause.
            [Thought] Professions of Nicholas Ray are director, screenwriter, and actor. I need to search Elia Kazan next and find his professions.
            [Action] Search
            [Action Input] Elia Kazan
            [Observation] Elia Kazan was an American film and theatre director, producer, screenwriter and actor.
            [Final Thought] Professions of Elia Kazan are director, producer, screenwriter, and actor. So profession Nicholas Ray and Elia Kazan have in common is director, screenwriter, and actor.
            [Proposed Answer] director, screenwriter, actor
            [Evaluation] Correct
            [Reflection] My answer is correct, I should return this as the final answer
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Thought] I need to search Arthur's Magazine and First for Women, and find which was started first.
            [Action] Search
            [Action Input] Arthur's Magazine
            [Observation] Arthur's Magazine (1844-\u0080\u00931846) was an American literary periodical published in Philadelphia in the 19th century.
            [Thought] Arthur's Magazine was started in 1844. I need to search First for Women next.
            [Action] Search
            [Action Input] First for Women
            [Observation] First for Women is a woman's magazine published by Bauer Media Group in the USA.[1] The magazine was started in 1989.
            [Final Thought] First for Women was started in 1989. 1844 (Arthur's Magazine) < 1989 (First for Women), so Arthur's Magazine was started first.
            [Proposed Answer] Arthur's Magazine
            [Evaluation] Correct
            [Reflection] My answer is correct, I should return this as the final answer
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Thought] I need to search Pavel Urysohn and Leonid Levin, find their types of work, then find if they are the same.
            [Action] Search
            [Action Input] Pavel Urysohn
            [Observation] Pavel Samuilovich Urysohn (February 3, 1898 \u00e2\u0080\u0093 August 17, 1924) was a Soviet mathematician who is best known for his contributions in dimension theory.
            [Thought] Pavel Urysohn is a mathematician. I need to search Leonid Levin next and find its type of work.`
            [Action] Search
            [Action Input] Leonid Levin
            [Observation] Leonid Anatolievich Levin is a Soviet-American mathematician and computer scientist.
            [Final Thought] Leonid Levin is a mathematician and computer scientist. So Pavel Urysohn and Leonid Levin have the same type of work.
            [Proposed Answer] yes
            [Evaluation] Correct
            [Reflection] My answer is correct, I should return this as the final answer
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },

    'rewoo' : {
        'instructions' :
            """
            Answer the following questions as best you can. You have access to the following tools:
            {{tool_descriptions}}
            For the following tasks, make plans that can solve the problem step-by-step. 
            For each plan, indicate which external tool together with tool input to retrieve evidence.
            You can store the evidence into a variable #E that can be called by later tools. 
            The format of your output should be as follows:
            
            [Question] the input question you must answer
                [Plan] your initial plan for solving the problem
                [Action Label] #E{number of action}
                [Action] an action to take, should be one of {{tool_labels}}
                [Action Input] the input to the action
                ... (you can list as many plan items as you need to solve the problem)
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Plan] Search for more information about Colorado orogeny.
            [Action Label] #E1
            [Action] Search
            [Action Input] Colorado orogeny
            [Plan] Find out the area that eastern sector of the Colorado orogeny extends into.
            [Action Label] #E2
            [Action] LLM
            [Action Input] What is the name of the area that eastern sector of Colorado extends into? Given context: #E1
            [Plan] Search for more information about the area.
            [Action Label] #E3
            [Action] Search
            [Action Input] #E2
            [Plan] Find out the elevation range for the area.
            [Action Label] #E4
            [Action] LLM
            [Action Input] What is elevation range for the area #E2? Given context: #E3
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the "The Simpsons" character Milhouse, who Matt Groening named after who?
            [Plan] Search for more information about Milhouse.
            [Action Label] #E1
            [Action] Search
            [Action Input] Milhouse
            [Plan] Find out who Matt Groening named Milhouse after.
            [Action Label] #E2
            [Action] LLM
            [Action Input] Who did Matt Groening name Milhouse after? Given context: #E1
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Plan] Search for more information about Adam Clayton Powell.
            [Action Label] #E1
            [Action] Search
            [Action Input] Adam Clayton Powell
            [Plan] Search for more information about The Saimaa Gesture.
            [Action Label] #E2
            [Action] Search
            [Action Input] The Saimaa Gesture
            [Plan] Compare the two and determine which is a documentary about Finnish rock groups.
            [Action Label] #E3
            [Action] LLM
            [Action Input] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture? Given context: #E1, #E2
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Plan] Search for more information about Nicholas Ray.
            [Action Label] #E1
            [Action] Search
            [Action Input] Nicholas Ray
            [Plan] Search for more information about Elia Kazan.
            [Action Label] #E2
            [Action] Search
            [Action Input] Elia Kazan
            [Plan] Compare the two and determine what profession they have in common.
            [Action Label] #E3
            [Action] LLM
            [Action Input] What profession does Nicholas Ray and Elia Kazan have in common? Given context: #E1, #E2
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Plan] Search for more information about Arthur's Magazine.
            [Action Label] #E1
            [Action] Search
            [Action Input] Arthur's Magazine
            [Plan] Search for more information about First for Women.
            [Action Label] #E2
            [Action] Search
            [Action Input] First for Women
            [Plan] Compare the two start dates and determine which magazine was started first.
            [Action Label] #E3
            [Action] LLM
            [Action Input] Which magazine was started first Arthur's Magazine or First for Women? Given context: #E1, #E2
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Plan] Search for more information about Pavel Urysohn.
            [Action Label] #E1
            [Action] Search
            [Action Input] Pavel Urysohn
            [Plan] Search for more information about Leonid Levin.
            [Action Label] #E2
            [Action] Search
            [Action Input] Leonid Levin
            [Plan] Compare the two and determine if they were known for the same type of work.
            [Action Label] #E3
            [Action] LLM
            [Action Input] Were Pavel Urysohn and Leonid Levin known for the same type of work? Given context: #E1, #E2
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },

    'cot' : {
        'instructions' : 
            """
            Answer the following questions as best you can. 
            Use the following format:

            [Question] the input question you must answer
            [Thought] this is where you write out your reasoning
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Thought] Let's think step by step. The eastern sector of Colorado orogeny extends into the High Plains. High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?
            [Thought] Let's think step by step. Milhouse was named after U.S. president Richard Nixon, so the answer is Richard Nixon.
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Thought] Let's think step by step. Adam Clayton Powell (film) is a documentary about an African-American politician, not Finnish rock groups. So the documentary about Finnish rock groups must instead be The Saimaa Gesture.
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Thought] Let's think step by step. Professions of Nicholas Ray are director, screenwriter, and actor. Professions of Elia Kazan are director, producer, screenwriter, and actor. So profession Nicholas Ray and Elia Kazan have in common is director, screenwriter, and actor.
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Thought] Let's think step by step. Arthur's Magazine was started in 1844. First for Women was started in 1989. 1844 (Arthur's Magazine) < 1989 (First for Women), so Arthur's Magazine was started first.
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Thought] Let's think step by step. Pavel Urysohn is a mathematician. Leonid Levin is a mathematician and computer scientist. So Pavel Urysohn and Leonid Levin have the same type of work.
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },

    'direct' : {
        'instructions' : 
            """
            Answer the following questions as best you can.
            Use the following format:
            
            [Question] the input question you must answer
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },









    ###
    # Ablation agent defs
    ###

    'pass_list' : {
        'instructions' :
            """
            Answer the following questions as best you can. You have access to the following tools:
            {{tool_descriptions}}
            When answering a question, you should formulate a plan for how you will solve the question. 
            Then, you should iteratively take sets of actions until you reach a satisfactory answer.
            For efficiency, try to group as many independent actions together as possible in each loop.
            The format of your output should be as follows:
            
            [Question] the input question you must answer
                [Thought] a step in your plan for solving the problem
                    [Action] an action to take, should be one of {{tool_labels}}
                    [Action Input] the input to the action
                    ... (you can list as many action/action input pairs as needed here)
                [Summary] a summary of the action results as they relate to the initial question and most recent plan step
                ... (this action gathering and summarization loop can repeat N times)
            [Final Thought] this is the last thought that summarizes your findings
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] What is the elevation range for the area that the eastern sector of the Colorado orogeny extends into?
            [Thought] I need to search Colorado orogeny, find the area that the eastern sector of the Colorado orogeny extends into, then find the elevation range of the area.
            [Action] Search
            [Action Input] Colorado orogeny
            [Summary] The Colorado orogeny was an episode of mountain building (an orogeny) in Colorado and surrounding areas.
            [Thought] It does not mention the eastern sector. So I need to look up eastern sector.
            [Action] Lookup
            [Action Input] eastern sector
            [Summary] (Result 1 / 1) The eastern sector extends into the High Plains and is called the Central Plains orogeny.
            [Thought] The eastern sector of Colorado orogeny extends into the High Plains. So I need to search High Plains and find its elevation range.
            [Action] Search
            [Action Input] High Plains
            [Summary] High Plains refers to one of two distinct land regions: High Plains (United States), High Plains (Other)
            [Thought] I need to instead search High Plains (United States).
            [Action] Search
            [Action Input] High Plains (United States)
            [Summary] The High Plains are a subregion of the Great Plains. From east to west, the High Plains rise in elevation from around 1,800 to 7,000 ft (550 to 2,130 m).[3]
            [Final Thought] The eastern sector of the Colorado orogeny extends into the high plains, which has an elevation of 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
            [Answer] 1,800 to 7,000 ft
            """,
            """
            [Question] Musician and satirist Allie Goertz wrote a song about the \"The Simpsons\" character Milhouse, who Matt Groening named after who?
            [Thought] The question simplifies to \"The Simpsons\" character Milhouse is named after who. I only need to search Milhouse and find who it is named after.
            [Action] Search
            [Action Input] Milhouse
            [Summary] Milhouse Mussolini Van Houten is a recurring character in the Fox animated television series The Simpsons voiced by Pamela Hayden and created by Matt Groening.
            [Thought] The paragraph does not tell who Milhouse is named after, maybe I can look up \"named after\".
            [Action] Lookup
            [Action Input] named after
            [Summary] (Result 1 / 1) Milhouse was named after U.S. president Richard Nixon, whose middle name was Milhous.
            [Final Thought] Milhouse was named after Richard Nixon
            [Answer] Richard Nixon
            """,
            """
            [Question] Which documentary is about Finnish rock groups, Adam Clayton Powell or The Saimaa Gesture?
            [Thought] I need to search Adam Clayton Powell and The Saimaa Gesture, and find which documentary is about Finnish rock groups.
            [Action] Search
            [Action Input] Adam Clayton Powell
            [Action] Search
            [Action Input] The Saimaa Gesture
            [Summary] Could not find 'Adam Clayton Powell'. Similar: ['Adam Clayton Powell III', 'Seventh Avenue (Manhattan)', 'Adam Clayton Powell Jr. State Office Building', 'Isabel Washington Powell', 'Adam Powell', 'Adam Clayton Powell (film)', 'Giancarlo Esposito'].
            The Saimaa Gesture (Finnish: Saimaa-ilmiö) is a 1981 film by Finnish directors Aki and Mika Kaurismäki. It is a documentary about three Finnish rock groups aboard the steamboat SS Heinävesi on their tour around Lake Saimaa.
            [Thought] I should search Adam Clayton Powell (film) instead to confirm my answer.
            [Action] Search
            [Action Input] Adam Clayton Powell (film)
            [Summary] Adam Clayton Powell is a 1989 American documentary film directed by Richard Kilberg.\nThe film is about the rise and fall of influential African-American politician Adam Clayton Powell Jr.[3][4] It was later aired as part of the PBS series The American Experience.
            [Final Thought] Adam Clayton Powell is not a documentary about Finnish rock groups while the The Saimaa Gesture is a documentary about Finnish rock groups.
            [Answer] The Saimaa Gesture
            """,
            """
            [Question] What profession does Nicholas Ray and Elia Kazan have in common?
            [Thought] I need to search Nicholas Ray and Elia Kazan, find their professions, then find the profession they have in common.
            [Action] Search
            [Action Input] Nicholas Ray
            [Action] Search
            [Action Input] Elia Kazan
            [Summary] Nicholas Ray (born Raymond Nicholas Kienzle Jr., August 7, 1911 \u2013 June 16, 1979) was an American film director, screenwriter, and actor best known for the 1955 film Rebel Without a Cause.
            Elia Kazan was an American film and theatre director, producer, screenwriter and actor.
            [Final Thought] The profession Nicholas Ray and Elia Kazan have in common are director, screenwriter, and actor.
            [Answer] director, screenwriter, actor
            """,
            """
            [Question] Which magazine was started first Arthur's Magazine or First for Women?
            [Thought] I need to search Arthur's Magazine and First for Women, and find which was started first.
            [Action] Search
            [Action Input] Arthur's Magazine
            [Action] Search
            [Action Input] First for Women
            [Summary] Arthur's Magazine (1844-\u0080\u00931846) was an American literary periodical published in Philadelphia in the 19th century.
            First for Women is a woman's magazine published by Bauer Media Group in the USA.[1] The magazine was started in 1989.
            [Final Thought] 1844 (Arthur's Magazine) < 1989 (First for Women), so Arthur's Magazine was started first.
            [Answer] Arthur's Magazine
            """,
            """
            [Question] Were Pavel Urysohn and Leonid Levin known for the same type of work?
            [Thought] I need to search Pavel Urysohn and Leonid Levin, find their types of work, then find if they are the same.
            [Action] Search
            [Action Input] Pavel Urysohn
            [Action] Search
            [Action Input] Leonid Levin
            [Summary] Pavel Samuilovich Urysohn (February 3, 1898 \u00e2\u0080\u0093 August 17, 1924) was a Soviet mathematician who is best known for his contributions in dimension theory.
            Leonid Anatolievich Levin is a Soviet-American mathematician and computer scientist.
            [Final Thought] Both Pavel Urysohn and Leonid Levin were mathematicians, so they had the same type of work
            [Answer] yes
            """,
        ],
        
        'input' : 
            """
            [Question] {{input}}
            """
    },

}
