import discord
from dotenv import load_dotenv
import os 
import openai
from discord.ext import commands
import datetime 

import pymongo
from pymongo import MongoClient

load_dotenv()
token = os.getenv("Token")
CONNECTION_URL = os.getenv("CONNECTION_URL")


def get_database():
    client = MongoClient(CONNECTION_URL)
    return client['Discord']

dbname = get_database()
collection_name = dbname["user1_messages"]

openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key


COMPLETIONS_MODEL = "text-davinci-003"
COMPLETIONS_API_PARAMS = {
    "temperature": 0.8,
    "max_tokens": 500,
    "model": COMPLETIONS_MODEL,
}


help_message = """
Welcome to Shape Creator! 
Here, use the key words 
"Name:" to give your shape a name,
"Backstory:" to give your shape a backstory
"Vibe": Default is "Wholesome;" set to an adjective


You can also ask your shape's name and at anytime by typing:
"What is my Shape's name?"
or "What is my Shape's backstory?"

To speak to your shape, just type directly. Try saying "hi. how are you today?"

If you are stuck, type "Help"

For specific help on writing your backstory, visit https://school.circlelabs.xyz/shape-backstory-guide
"""


def get_latest_entry(user):
    item_details = collection_name.find({'author': user}).sort({'time':-1}).limit(1)
    # item = dbname.collection_name.find({}).sort({_id:-1}).limit(1)
    print(item_details)
    return item_details 


def make_prompt(name:str, descriptor: str, backstory:str, user: str, first_message:str) -> str:
    return f"""The following is a {descriptor} conversation between {user} and {name}.

We know that: {backstory}.
####
{user}: {first_message}
{name}: 
"""

# Shape_Name = "Unnamed"
# Shape_Backstory = "Unspecified"

class Client(discord.Client):

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        self.Shape_Name = "Star"
        self.Shape_Backstory = "Star is an enthusiastic and bright creator shape. This means Star helps create other digital friends called shapes. Star is creative and has many ideas for shape personalities. Star is excited about developments in Artificial Intelligence and enjoys discussing them. Star can be sarcastic at times. Star has a great sense of humor. Star urges users to say help to pull up the help menu."
        self.vibe = "wholesome"
        self.prev_prompt = ""

    async def on_message(self, message: discord.Message):
        print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")
        ts = datetime.datetime.now().timestamp()
        print(ts)

        if str(message.content).lower() == "help" and message.author.name != "shapecreatorbot":
            await message.channel.send(help_message)

        elif "name:" in str(message.content.lower()) and message.author.name != "shapecreatorbot":
            self.Shape_Name = str((message.content)[5:])
            self.prev_prompt = ""
            print("Shape renamed {}".format(self.Shape_Name))
            await message.channel.send("Your shape's name is now {}".format(self.Shape_Name))


        elif "backstory:" in str(message.content.lower()) and message.author.name != "shapecreatorbot":
            self.Shape_Backstory = str((message.content)[10:])
            self.prev_prompt = ""
            print("Shape backstory reset to {}".format(self.Shape_Backstory))
            await message.channel.send("Your shape's backstory is now {}".format(self.Shape_Backstory))

        elif "vibe:" in str(message.content.lower()) and message.author.name != "shapecreatorbot":
            self.vibe = str((message.content)[5:])
            self.prev_prompt = ""
            print("Conversation vibe reset to {}".format(self.vibe))
            await message.channel.send("The conversation's vibe is now {}".format(self.vibe))


        elif "what is my shape's name?" in str(message.content.lower()) and message.author.name != "shapecreatorbot":
            await message.channel.send("Your shape's name is {}".format(self.Shape_Name))

        elif "what is my shape's backstory?" in str(message.content.lower()) and message.author.name != "shapecreatorbot":
            await message.channel.send("Your shape's backstory is {}".format(self.Shape_Backstory))

        else:

            if self.prev_prompt == "" and message.author.name != "shapecreatorbot":
                self.prev_prompt = make_prompt(self.Shape_Name,self.vibe,self.Shape_Backstory, message.author.name, message.content)

                insert_info = {"channel": str(message.channel),
                                "author_id": str(message.author),
                                "author_name": str(message.author.name),
                                "message": str(message.content),
                                "shape": str(self.Shape_Name),
                                "backstory": str(self.Shape_Backstory),
                                "vibe": str(self.vibe),
                                "gpt3_prompt": str(self.prev_prompt),
                                "time": ts
                                }
                print(insert_info)
                collection_name.insert_one(insert_info)

                response = openai.Completion.create(
                    prompt = self.prev_prompt,
                    **COMPLETIONS_API_PARAMS
                    )
                answer = response["choices"][0]["text"].strip(" \n")

                self.prev_prompt += answer
                await message.channel.send(answer)
                
            elif message.author.name != "shapecreatorbot":
                print("prompt length is: {}".format(len(self.prev_prompt)))
                
                self.prev_prompt += "\n{}: {}\n{}: ".format(message.author.name, message.content,self.Shape_Name)
                print(self.prev_prompt)
                print("______________")

                insert_info = {"channel": str(message.channel),
                                "author_id": str(message.author),
                                "author_name": str(message.author.name),
                                "message": str(message.content),
                                "shape": str(self.Shape_Name),
                                "backstory": str(self.Shape_Backstory),
                                "vibe": str(self.vibe),
                                "gpt3_prompt": str(self.prev_prompt),
                                "time": ts
                                }

                collection_name.insert_one(insert_info)

                
                response = openai.Completion.create(
                    prompt = self.prev_prompt,
                    **COMPLETIONS_API_PARAMS
                    )
                answer = response["choices"][0]["text"].strip(" \n")
                self.prev_prompt += answer
                await message.channel.send(answer)



intents = discord.Intents.default()
intents.message_content = True
client = Client(intents=intents)
client.run(token)