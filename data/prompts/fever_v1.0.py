{
    'react' : { 

        'instructions' :
            """
            Determine if there is an observation that SUPPORTS or REFUTES a Claim, or if there is NOT ENOUGH INFORMATION. You have access to the following tools:
            {{tool_descriptions}}
            Use the following format:
            
            [Question] the input question you must answer
                [Thought] you should always think about what to do
                [Action] the action to take, should be one of {{tool_labels}}
                [Action Input] the input to the action
                [Observation] the result of the action
                ... (this Thought/Action/Action Input/Observation can repeat N times)
            [Final Thought] this is the last thought
            [Answer] this is where you write your final answer, it should be one of [SUPPORTS, REFUTES, NOT ENOUGH INFORMATION]

            Here are some examples.
            """,
        
        'examples' : [
            """
            [Question] Nikolaj Coster-Waldau worked with the Fox Broadcasting Company.
            [Thought] I need to search Nikolaj Coster-Waldau and find if he has worked with the Fox Broadcasting Company.
            [Action] Search
            [Action Input] Nikolaj Coster-Waldau
            [Observation] Nikolaj William Coster-Waldau (born 27 July 1970) is a Danish actor and producer. He graduated from the Danish National School of Performing Arts in Copenhagen in 1993,[1] and had his breakthrough role in Denmark with the film Nightwatch (1994). He played Jaime Lannister in the HBO fantasy drama series Game of Thrones, for which he received two Primetime Emmy Award nominations for Outstanding Supporting Actor in a Drama Series.. Coster-Waldau has appeared in numerous films in his native Denmark and Scandinavia, including Headhunters (2011) and A Thousand Times Good Night (2013). In the U.S, his debut film role was in the war film Black Hawk Down (2001), playing Medal of Honor recipient Gary Gordon.[2] He then played a detective in the short-lived Fox television series New Amsterdam (2008), and appeared in the 2009 Fox television film Virtuality, originally intended as a pilot.
            [Final Thought] Because he \"appeared in the 2009 Fox television film Virtuality\", he should have worked with the Fox Broadcasting Company.
            [Answer] SUPPORTS
            """,
            """
            [Question] Stranger Things is set in Bloomington, Indiana.
            [Thought] I should search for Stranger Things, and see if it is set in Bloomington, Indiana.
            [Action] Search
            [Action Input] Stranger Things
            [Observation] Stranger Things is an American science fiction horror drama television series created by the Duffer Brothers. Set in the 1980s, primarily in the fictional town of Hawkins, Indiana, the series centers on a number of mysteries and supernatural events occurring around the town and their impact on an ensemble of child and adult characters.
            [Final Thought] The observation says that it is set in a \"fictional town of Hawkins, Indiana\", so it is not set in Bloomington.
            [Answer] REFUTES
            """,
            """
            [Question] Beautiful reached number two on the Billboard Hot 100 in 2003.?
            [Thought] I need to search the song Beautiful and find if it reached number two on the Billboard Hot 100 in 2003.
            [Action] Search
            [Action Input] Beautiful
            [Observation] Could not find [Beautiful]. Similar: ['Beautiful', 'Beautiful, Beautiful', 'A Beautiful Mind (film)', 'Beautiful (Christina Aguilera song)', 'Life Is Beautiful'].
            [Thought] From suggestions, I should search \"Beautiful (Christina Aguilera song)\" to find the song.
            [Action] Search
            [Action Input] Beautiful (Christina Aguilera song)
            [Observation] \"Beautiful\" is a song recorded by American singer Christina Aguilera for her fourth studio album, Stripped (2002).
            [Thought] It does not mention Billboard, so I need to look up \"Billboard Hot 100\" to find if it reached number two on it in 2003.
            [Action] Lookup
            [Action Input] Billboard Hot 100
            [Observation] (Result 1 / 3) The song peaked at number two on the Billboard Hot 100 in the United States, where it was certified Gold for 500,000 units shipped.
            [Final Thought] It only says the song peaked at number two on the Billboard Hot 100, but not if it was in 2003. I am not sure if this claim is true or not.
            [Answer] NOT ENOUGH INFORMATION
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
            Determine if there is an observation that SUPPORTS or REFUTES a Claim, or if there is NOT ENOUGH INFORMATION. You have access to the following tools:
            {{tool_descriptions}}
            When answering a question, you should formulate a plan for how you will solve the question. 
            Then, you should iteratively take sets of actions until you reach a satisfactory answer.
            For efficiency, try to group as many independent actions together as possible in each loop.
            The format of your output should be as follows:
            
            [Question] the input question you must answer
                [Plan] a step in your plan for solving the problem
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
            [Question] Nikolaj Coster-Waldau worked with the Fox Broadcasting Company.
            [Plan] I need to search Nikolaj Coster-Waldau and find if he has worked with the Fox Broadcasting Company.
            [Action] Search
            [Action Input] Nikolaj Coster-Waldau
            [Summary] Nikolaj William Coster-Waldau (born 27 July 1970) is a Danish actor and producer. He graduated from the Danish National School of Performing Arts in Copenhagen in 1993,[1] and had his breakthrough role in Denmark with the film Nightwatch (1994). He played Jaime Lannister in the HBO fantasy drama series Game of Thrones, for which he received two Primetime Emmy Award nominations for Outstanding Supporting Actor in a Drama Series.. Coster-Waldau has appeared in numerous films in his native Denmark and Scandinavia, including Headhunters (2011) and A Thousand Times Good Night (2013). In the U.S, his debut film role was in the war film Black Hawk Down (2001), playing Medal of Honor recipient Gary Gordon.[2] He then played a detective in the short-lived Fox television series New Amsterdam (2008), and appeared in the 2009 Fox television film Virtuality, originally intended as a pilot.
            [Final Thought] Because he \"appeared in the 2009 Fox television film Virtuality\", he should have worked with the Fox Broadcasting Company.
            [Answer] SUPPORTS
            """,
            """
            [Question] Stranger Things is set in Bloomington, Indiana.
            [Plan] I should search for Stranger Things, and see if it is set in Bloomington, Indiana.
            [Action] Search
            [Action Input] Stranger Things
            [Summary] Stranger Things is an American science fiction horror drama television series created by the Duffer Brothers. Set in the 1980s, primarily in the fictional town of Hawkins, Indiana, the series centers on a number of mysteries and supernatural events occurring around the town and their impact on an ensemble of child and adult characters.
            [Final Thought] The observation says that it is set in a \"fictional town of Hawkins, Indiana\", so it is not set in Bloomington.
            [Answer] REFUTES
            """,
            """
            [Question] Beautiful reached number two on the Billboard Hot 100 in 2003.?
            [Plan] I need to search the song Beautiful and find if it reached number two on the Billboard Hot 100 in 2003.
            [Action] Search
            [Action Input] Beautiful
            [Summary] Could not find [Beautiful]. Similar: ['Beautiful', 'Beautiful, Beautiful', 'A Beautiful Mind (film)', 'Beautiful (Christina Aguilera song)', 'Life Is Beautiful'].
            [Plan] From suggestions, I should search \"Beautiful (Christina Aguilera song)\" to find the song.
            [Action] Search
            [Action Input] Beautiful (Christina Aguilera song)
            [Summary] \"Beautiful\" is a song recorded by American singer Christina Aguilera for her fourth studio album, Stripped (2002).
            [Plan] It does not mention Billboard, so I need to look up \"Billboard Hot 100\" to find if it reached number two on it in 2003.
            [Action] Lookup
            [Action Input] Billboard Hot 100
            [Summary] (Result 1 / 3) The song peaked at number two on the Billboard Hot 100 in the United States, where it was certified Gold for 500,000 units shipped.
            [Final Thought] It only says the song peaked at number two on the Billboard Hot 100, but not if it was in 2003. I am not sure if this claim is true or not.
            [Answer] NOT ENOUGH INFORMATION
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
            Determine if there is an observation that SUPPORTS or REFUTES a Claim, or if there is NOT ENOUGH INFORMATION. You have access to the following tools:
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
            [Question] Nikolaj Coster-Waldau worked with the Fox Broadcasting Company.
            [Plan] I need to search Nikolaj Coster-Waldau and find if he has worked with the Fox Broadcasting Company.
            [Action Label] #E1
            [Action] Search
            [Action Input] Nikolaj Coster-Waldau
            [Action Label] #E2
            [Action] LLM
            [Action Input] Does the context provide an observation that SUPPORTS or REFUTES the claim, or is there NOT ENOUGH INFORMATION. Given context: #E1
            [Answer] SUPPORTS
            """,
            """
            [Question] Stranger Things is set in Bloomington, Indiana.
            [Plan] I should search for Stranger Things, and see if it is set in Bloomington, Indiana.
            [Action Label] #E1
            [Action] Search
            [Action Input] Stranger Things
            [Action Label] #E2
            [Action] LLM
            [Action Input] Does the context provide an observation that SUPPORTS or REFUTES the claim, or is there NOT ENOUGH INFORMATION. Given context: #E1
            [Answer] REFUTES
            """,
            """
            [Question] Beautiful reached number two on the Billboard Hot 100 in 2003.?
            [Plan] I need to search the song Beautiful and find if it reached number two on the Billboard Hot 100 in 2003.
            [Action Label] #E1
            [Action] Search
            [Action Input] Beautiful
            [Action Label] #E2
            [Action] LLM
            [Action Input] Does the context provide an observation that SUPPORTS or REFUTES the claim, or is there NOT ENOUGH INFORMATION. Given context: #E1
            [Answer] NOT ENOUGH INFORMATION
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
            Determine if there is an observation that SUPPORTS or REFUTES a Claim, or if there is NOT ENOUGH INFORMATION.
            Use the following format:
            
            [Question] the input question you must answer
            [Thought] this is where you write out your reasoning
            [Answer] this is where you write your final answer

            Here are some examples.
            """,
        
        'examples' : [
            """
            [Question] Nikolaj Coster-Waldau worked with the Fox Broadcasting Company.
            [Thought] Nikolaj William Coster-Waldau appeared in the 2009 Fox television film Virtuality, so he has worked with the Fox Broadcasting Company.
            [Answer] SUPPORTS
            """,
            """
            [Question] Stranger Things is set in Bloomington, Indiana.
            [Thought] Stranger Things is in the fictional town of Hawkins, Indiana, not in Bloomington, Indiana.
            [Answer] REFUTES
            """,
            """
            [Question] Beautiful reached number two on the Billboard Hot 100 in 2003.?
            [Thought] The song peaked at number two on the Billboard Hot 100 in the United States, but not sure if it was in 2003.
            [Answer] NOT ENOUGH INFORMATION
            """
        ],
        'input' : 
            """
            [Question] {{input}}
            """
    },

}