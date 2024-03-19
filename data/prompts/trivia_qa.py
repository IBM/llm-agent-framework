{
    'react' : { 

        'instructions' :
            """
            Answer the following questions as best you can. You have access to the following tools:
            {{tool_descriptions}}
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
            # """
            # [Question] What is the name of the river on which Bakewell stands?
            # [Thought] I need to search Bakewell and find out its location.
            # [Action] Search
            # [Action Input] Bakewell
            # [Observation] Bakewell is a market town and civil parish in the Derbyshire Dales district of Derbyshire, England, known for Bakewell pudding. It lies on the River Wye, 13 miles (21 km) south-west of Sheffield. At the 2011 census, the population of the civil parish was 3,949. It was estimated at 3,695 in 2019. The town is close to the tourist attractions of Chatsworth House and Haddon Hall.
            # [Final Thought] Now I know that Bakewell lies on the River Wye
            # [Answer] River Wye
            # """,
            """
            [Question] Which Asian capital city is known as Krung Thep to its inhabitants and stands on the Chao Phraya River?
            [Thought] I need to search for more information about Krung Thep
            [Action] Search 
            [Action Input] Krung Thep
            [Observation] Bangkok, officially known in Thai as Krung Thep Maha Nakhon and colloquially as Krung Thep, is the capital and most populous city of Thailand. The city occupies 1,568.7 square kilometres (605.7 sq mi) in the Chao Phraya River delta in central Thailand and has an estimated population of 10.539 million as of 2020, 15.3 per cent of the country's population.
            [Thought] Now I should search for more information about Chao Phraya River
            [Action] Search
            [Action Input] Chao Phraya River
            [Observation] The Chao Phraya ( or ; Thai: แม่น้ำเจ้าพระยา, RTGS: Maenam Chao Phraya, pronounced [mɛ̂ːnáːm tɕâːw pʰráʔ.jāː]  or [tɕâːw pʰrā.jāː]) is the major river in Thailand, with its low alluvial plain forming the centre of the country. It flows through Bangkok and then into the Gulf of Thailand.
            [Final Thought] The name of the city is Bangkok
            [Answer] Bangkok
            """
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
            [Question] Which Asian capital city is known as Krung Thep to its inhabitants and stands on the Chao Phraya River?
            [Thought] I need to search for more information about Krung Thep and the Chao Phraya River
            [Action] Search
            [Action Input] Krung Thep
            [Action] Search
            [Action Input] Chao Phraya River
            [Summary] Bangkok is the capital city of Thailand and is known as Krung Thep to its inhabitants. It stands on the Chao Phraya River.
            [Final Thought] The name of the city is Bangkok
            [Answer] Bangkok
            """
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
            # """
            # [Question] Which Asian capital city is known as Krung Thep to its inhabitants and stands on the Chao Phraya River?
            # [Plan] Search for more information about Krung Thep
            # [Action Label] #E1 
            # [Action] Search
            # [Action Input] Krung Thep
            # [Plan] Search for more information about Chao Phraya River
            # [Action Label] #E2 
            # [Action] Search
            # [Action Input] Chao Phraya River
            # [Plan] Find out the name of the river on which Bakewell stands.
            # [Action Label] #E3 
            # [Action] LLM
            # [Action Input] What is the name of the river on which Bakewell stands? Given context: #E1 and #E2
            # [Answer] Bangkok
            # """,
            """
            [Question] Which Asian capital city is known as Krung Thep to its inhabitants and stands on the Chao Phraya River?
            [Plan] Search for more information about Krung Thep
            [Action Label] #E1 
            [Action] Search
            [Action Input] Krung Thep
            [Plan] Search for more information about Chao Phraya River
            [Action Label] #E2 
            [Action] Search
            [Action Input] Chao Phraya River
            [Action] LLM
            [Action Input] What is the name of the capital city that goes by Krung Thep and stands on the Chao Phraya River? Given context: #E1 and #E2
            [Answer] Bangkok
            """

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
            [Question] What is the name of the river on which Bakewell stands?
            [Thought] The location of Bakewell is Derbyshire, England. The River Wye flows through the town.
            [Answer] River Wye
            """
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
            [Question] What is the name of the river on which Bakewell stands?
            [Answer] River Wye
            """
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
            [Question] Which Asian capital city is known as Krung Thep to its inhabitants and stands on the Chao Phraya River?
            [Thought] I need to search for more information about Krung Thep and the Chao Phraya River
            [Action] Search
            [Action Input] Krung Thep
            [Action] Search
            [Action Input] Chao Phraya River
            [Summary] Bangkok, officially known in Thai as Krung Thep Maha Nakhon and colloquially as Krung Thep, is the capital and most populous city of Thailand. The city occupies 1,568.7 square kilometres (605.7 sq mi) in the Chao Phraya River delta in central Thailand and has an estimated population of 10.539 million as of 2020, 15.3 per cent of the country's population.
            The Chao Phraya ( or ; Thai: แม่น้ำเจ้าพระยา, RTGS: Maenam Chao Phraya, pronounced [mɛ̂ːnáːm tɕâːw pʰráʔ.jāː]  or [tɕâːw pʰrā.jāː]) is the major river in Thailand, with its low alluvial plain forming the centre of the country. It flows through Bangkok and then into the Gulf of Thailand.
            [Final Thought] The name of the city is Bangkok
            [Answer] Bangkok
            """
        ],

        'input' : 
            """
            [Question] {{input}}
            """
    },

}