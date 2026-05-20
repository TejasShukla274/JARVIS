from memory.chat_memory import save_user_data  #imports the function that saves permanent user data into memory.json


def remember_user_facts(user_message): #this function checks whether the user said something personal worth remembering

    text = user_message.lower() #converts the message into lowercase so comparison becomes easy

    if "my name is" in text: #if user tells his name
        name = user_message.split("my name is")[-1].strip() #extracts only the name part after "my name is"
        save_user_data("name", name) #saves it in memory.json with key = name

    elif "i like" in text: #if user says something he likes
        like = user_message.split("i like")[-1].strip() #extracts the liked thing
        save_user_data("likes", like) #stores it permanently

    elif "my favourite car is" in text: #if user reveals favourite car
        car = user_message.split("my favourite car is")[-1].strip() #extracts car name
        save_user_data("favorite_car", car) #stores it in memory

    elif "i study in" in text: #if user tells where he studies
        college = user_message.split("i study in")[-1].strip() #extracts college/institute name
        save_user_data("college", college) #stores it permanently