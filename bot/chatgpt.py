import openai
from db.tokens import Token
import random

async def get_chat_gpt_answer(prompt, history):
    tokens = await Token.all()
    token = random.choice(tokens)
    openai.api_key = token["token"]

    prompt_with_history = f"Привіт\n"
    for message in history:
        prompt_with_history += f"You: {message}\nAssistant: "

    response = openai.Completion.create(
        engine = "text-davinci-002",
        prompt = prompt_with_history + "You: " + prompt + "\nAssistant: ",
        max_tokens = 150
    )
    
    if 'choices' in response:
        return response['choices'][0]['text']
    else:
        return None
 
chat_history = {}

async def enter_question(user_id, prompt):
    user_history = chat_history.get(user_id)
   
    if user_history:
        chat_history[user_id].append(prompt)
    else:
        chat_history[user_id] = [prompt]
        
    answer = await get_chat_gpt_answer(prompt, chat_history[user_id])
    return answer