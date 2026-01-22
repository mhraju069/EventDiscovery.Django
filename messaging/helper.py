def get_chat_name(user1,user2):
    name1 = user1.email.split('@')[0]
    name2 = user2.email.split('@')[0]
    return f"{name1} and {name2}"