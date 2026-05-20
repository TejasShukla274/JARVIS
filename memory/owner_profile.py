#this file stores all permanent information about the owner Tejas
#jarvis can directly read from here without asking gemini


OWNER_DATA = {
    "name": "Tejas",
    "birthday": "5 August",
    "city": "Ayodhya",
    "assistant_name": "JARVIS",
    "favorite_site": "youtube",
    "creator": "Tejas Shukla",
    "aadhar": "448701414076",    
    "pan_number": "TGPPS0704F",
    "class10": "23107189,93.833",
    "class12": "23607918,87.4",

#passwords
    "irctc":"Tejas@Shukla@",
    "mySql":"Aiwa@1002",
    "Linux":"Tejas@555"

}




def get_owner_info(key):   #this function returns requested information from dictionary
    return OWNER_DATA.get(key, "Information not found")