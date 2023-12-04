from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
# Initialize the language model
# Replace 'your_api_key_here' with your actual OpenAI API key
llm = ChatOpenAI(
    openai_api_key="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",
    temperature=0,
    model_name="gpt-4"
)

prompt = PromptTemplate(
    input_variables=["bank"],
    template="Create a bank challan template for {bank}. The template should include fields for the date, payer's name, address, and contact number, beneficiary's name and account number, payment amount in numbers and words, purpose of payment, and options for mode of payment (cash, cheque, demand draft, online transfer) with additional details for cheque/DD number and issuing bank. Include a signature field for the payer, and a dedicated section for official use by the bank, including transaction ID, bank stamp, and official signature. Add a footer section for any special instructions or notes related to the challan.",
)


context = ""
chain = LLMChain(llm=llm, prompt=prompt)


print(chain.run("get the challan"))
