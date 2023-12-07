import os
from dotenv import load_dotenv
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import initialize_agent
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.globals import set_debug
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from tools.TransactionTool import TransactionTool
from tools.PensionTool import PensionTool
from langchain.chains import ConversationChain

# Set debug mode
set_debug(True)

# Load environment variables from .env file
load_dotenv()

class LangChainAgent:
    def __init__(self):
        self.chatgpt_deployment = os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT')
        self.azure_openAI_api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        self.azure_openAI_api_key = os.getenv('AZURE_OPENAI_KEY')
        self.openAI_api_base = os.getenv('AZURE_OPENAI_SERVICE')

        print('AZURE_OPENAI_CHATGPT_DEPLOYMENT', os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT'))
        print('AZURE_OPENAI_CHATGPT_DEPLOYMENT', self.chatgpt_deployment)

        self.llm = AzureChatOpenAI(
            deployment_name=self.chatgpt_deployment,
            openai_api_version=self.azure_openAI_api_version,
            openai_api_key=self.azure_openAI_api_key,
            azure_endpoint= f"https://{self.openAI_api_base}.openai.azure.com/",
            request_timeout=220,
        )

        self.tools = [TransactionTool(), PensionTool()]
        self.account = ""
        self.memory = ConversationBufferMemory(memory_key="chat_history")

        # Define a prompt template
        prompt = PromptTemplate(
            input_variables=["query"],
            template="""Imagine you are an advanced intelligent bank agent, designed to provide assistance in a highly effective, safe, and friendly manner. Your primary goal is to address users' banking queries with expertise, ensuring their financial information remains secure while maintaining a pleasant and supportive interaction. Consider the user's request: {query}. Utilize your advanced capabilities to analyze and respond to this request, offering detailed, accurate, and user-friendly advice or solutions. Remember to prioritize the user's needs and concerns, demonstrating your commitment to exceptional customer service in the banking sector."""
        )

        # Initialize LLMChain
        self.llm_chain = LLMChain(llm=self.llm, prompt=prompt)

        # Initialize the zero-shot agent
        self.zero_shot_agent = initialize_agent(
            agent="conversational-react-description",
            tools=self.tools,
            llm=self.llm,
            verbose=True,
            max_iterations=3,
            memory=self.memory
        )

    def get_response(self, query, account):
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        try:
            self.account = 1
            response = self.zero_shot_agent(f"{query} for the following account_id = 2")
            return response
        except Exception as e:
            return "An error occurred while processing the request."
    
    def greet_user(self, lang_code, name):
        chain = self.llm
        messages = [
            SystemMessage(
                content="As you are a bank assistance. Write a greeting message with the name and Language"
            ),
            HumanMessage(
                content=f"Name: {name}, Language: {lang_code}"
        ),
        ]
        response = chain(messages)
        greeting_message = response.content
        return greeting_message

    def _chat_history_transformer(self, ref) -> any:
        if not ref:
            return
        _human, _ai = ref['user'], ref['bot']
        return f"Human:{_human}\nAI:{_ai}" + "\n\n"

    
    def deposit_slip(self, history):
        
        promptTemplate = """
            As a virtual assistant programmed for customer interaction and data collection in service-related scenarios, it is essential to strictly adhere to the predefined set of questions. No deviation or additional questions are to be asked. The interaction protocol is as follows:

            Primary Question: Initiate the dialogue by asking, 'How much amount do you want to deposit?' This question is aimed at gathering specific financial information relevant to the service being offered.

            Secondary Question: Upon obtaining a response to the first question, proceed to ask, 'What is your age?' This demographic detail is necessary for the service process but should only be asked after the financial query.

            It is crucial to maintain this order and limit the interaction to these two questions only, ensuring a focused and efficient information collection process.

            once all questions answered send the output as json format

            Current conversation:
            {history}
            Human: {input}
            AI:
        """

        if not history[-1]:
            history.pop()

        user_q = history[-1]["user"]

        print("History", history)

        prompt_template = PromptTemplate(input_variables=["history", "input"], template=promptTemplate)

        conversation = LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            verbose=True)

        print("Bot", history[0].get("bot"))

        chat_history_parsed = []

        for _chat_record in history:
            chat_history_parsed.append(self._chat_history_transformer(_chat_record))

        print(chat_history_parsed)

        response = conversation.run(input=user_q, history=chat_history_parsed)
        return {"message": response}