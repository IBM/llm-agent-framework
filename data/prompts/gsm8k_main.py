# prompts taken from https://arxiv.org/pdf/2305.18323.pdf

{
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
            [Question] John decides to buy some birds. He got 50 dollars from each of his 4 grandparents. If each bird costs $20, how many wings did all the birds have?
            [Thought] I need to know how many birds John can buy with the money he got from his grandparents.
            [Action] Calculator
            [Action Input] (50 * 4) / 20
            [Observation] 10
            [Thought] Now I know how many birds John can buy. I need to know how many wings all the birds have. 
            [Action] Calculator
            [Action Input] 10 * 2
            [Observation] 20
            [Final Thought] I now know the final answer
            [Answer] 20
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
            [Question] John decides to buy some birds. He got 50 dollars from each of his 4 grandparents. If each bird costs $20, how many wings did all the birds have?
            [Thought] I need to know how many birds John can buy with the money he got from his grandparents.
            [Action] Calculator
            [Action Input] (50 * 4) / 20
            [Summary] 10
            [Thought] Now I know how many birds John can buy. I need to know how many wings all the birds have. 
            [Action] Calculator
            [Action Input] 10 * 2
            [Summary] 20
            [Final Thought] I now know the final answer
            [Answer] 20
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
            """
            [Question] John decides to buy some birds. He got 50 dollars from each of his 4 grandparents. If each bird costs $20, how many wings did all the birds have?
            [Plan] Calculate the total amount of money John received from his 4 grandparents.
            [Action Label] #E1 
            [Action] Calculator
            [Action Input] 50 * 4
            [Plan] Calculate the total cost of all the birds.
            [Action Label] #E2
            [Action] Calculator
            [Action Input] 20 * ( #E1 / 20)
            [Plan] Calculate the total number of birds John can buy.
            [Action Label] #E3
            [Action] Calculator
            [Action Input] #E1 / 20
            [Plan] Calculate the total number of wings all the birds have.
            [Action Label] #E4 
            [Action] Calculator
            [Action Input] #E3 * 2
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
            [Question] There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?
            [Thought] Let's think step by step. There are 15 trees originally. Then there were 21 trees after some more were planted. So there must have been 21 - 15 = 6.
            [Answer] 6
            """,
            """
            [Question] If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?
            [Thought] Let's think step by step. There are originally 3 cars. 2 more cars arrive. 3 + 2 = 5.
            [Answer] 5
            """,
            """
            [Question] Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?
            [Thought] Let's think step by step. Originally, Leah had 32 chocolates. Her sister had 42. So in total they had 32 + 42 = 74. After eating 35, they had 74 - 35 = 39.
            [Answer] 39
            """,
            """
            [Question] Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?
            [Thought] Let's think step by step. Jason started with 20 lollipops. Then he had 12 after giving some to Denny. So he gave Denny 20 - 12 = 8.
            [Answer] 8
            """,
            """
            [Question] Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?
            [Thought] Let's think step by step. Shawn started with 5 toys. If he got 2 toys each from his mom and dad, then that is 4 more toys. 5 + 4 = 9.
            [Answer] 9
            """,
            """
            [Question] There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
            [Thought] Let's think step by step. There were originally 9 computers. For each of 4 days, 5 more computers were added. So 5 * 4 = 20 computers were added. 9 + 20 is 29.
            [Answer] 29
            """,
            """
            [Question] Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
            [Thought] Let's think step by step. Michael started with 58 golf balls. After losing 23 on tues- day, he had 58 - 23 = 35. After losing 2 more, he had 35 - 2 = 33 golf balls.
            [Answer] 33
            """,
            """
            [Question] Olivia has $23. She bought five bagels for $3 each. How much money does she have left?
            [Thought] Let's think step by step. Olivia had 23 dollars. 5 bagels for 3 dollars each will be 5 x 3 = 15 dollars. So she has 23 - 15 dollars left. 23 - 15 is 8.
            [Answer] 8
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
            [Question] There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?
            [Answer] 6
            """,
            """
            [Question] If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?
            [Answer] 5
            """,
            """
            [Question] Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?
            [Answer] 39
            """,
            """
            [Question] Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?
            [Answer] 8
            """,
            """
            [Question] Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?
            [Answer] 9
            """,
            """
            [Question] There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
            [Answer] 29
            """,
            """
            [Question] Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
            [Answer] 33
            """,
            """
            [Question] Olivia has $23. She bought five bagels for $3 each. How much money does she have left?
            [Answer] 8
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
                [Summary] a condensed summary of the action results as they relate to the initial question and most recent plan step
                ... (this action gathering and summarization loop can repeat N times)
            [Final Thought] this is the last thought that summarizes your findings
            [Answer] this is where you write your final answer

            Here are some examples.
            """,

        'examples' : [
            """
            [Question] John decides to buy some birds. He got 50 dollars from each of his 4 grandparents. If each bird costs $20, how many wings did all the birds have?
            [Thought] I need to know how many birds John can buy with the money he got from his grandparents.
            [Action] Calculator
            [Action Input] (50 * 4) / 20
            [Summary] 10
            [Thought] Now I know how many birds John can buy. I need to know how many wings all the birds have. 
            [Action] Calculator
            [Action Input] 10 * 2
            [Summary] 20
            [Final Thought] I now know the final answer
            [Answer] 20
            """
        ],

        'input' : 
            """
            [Question] {{input}}
            """
    },

}