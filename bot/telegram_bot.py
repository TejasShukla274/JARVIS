
                                            #BLOCK 1

from telegram import Update
from telegram.constants import ChatAction #this calls the update library to update
from telegram.ext import Application, CommandHandler, MessageHandler,filters, ContextTypes #these are used to handle messages and etc
from dotenv import load_dotenv #used to read env files in python
import os #helps python interact with the os
from core.command_handler import process_command

                                            #BLOCK 2
load_dotenv() #loads the env file for token

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") #used to get the bot token



                                            #BLOCK 3

async def start_command(update: Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello Tejas JARVIS is now online")
 
 #async def used to define function 
 #start_command is used to start the bot
 # so technically this block deals with the start command and when a person starts it, it replies with Hello.....

                                             
                                            #BLOCK 4


                                            #BLOCK 4

async def handle_message(update: Update,context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text #responsible for questions asked by the user

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING) #shows typing... while jarvis is thinking

    ai_reply = process_command(user_text)

    if len(ai_reply) > 4000: #this makes the bot to give answers in small and consize size with words upto 4000
        
        for i in range(0, len(ai_reply), 4000):
            await update.message.reply_text(ai_reply[i:i+4000])

    else:
        await update.message.reply_text(ai_reply) #telegram sends that answer back to the ai
 #async def used to define function 
 #user_text takes the input of the user
 #await update replies to the user with the text it sent him 
 #f is used to insert variables in a sentece


                                           #BLOCK 5
                            
def run_bot(): # function defined to run the bot 
    app = Application.builder().token(BOT_TOKEN).build() #creates the application for the bot

    app.add_handler(CommandHandler("start",start_command))# says whenever a command start arrives send it to the function start_command
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND , handle_message)) # this takes the other commands than start

    print("JARVIS IS NOW LISTENING......")#confirmation that the code is running
    app.run_polling()#starts sending messages to telegram to check if there are any new messages
  

  #AFTER THIS THIS CODE IS CONNECTED TO main.py
                                    

