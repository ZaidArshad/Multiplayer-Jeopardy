# Description of key : datatype of value

# Player number assigned by server : int
PLAYER_NUM = "player_num"

# Player named submitted by client : str
PLAYER_NAME = "player_name"

# Player score modified by server : int
PLAYER_SCORE = "player_score"

# Player num that sent the message : int
SELF_PLAYER_NUM = "self_player_num"

# List of players with their PLAYER_INFO : list[dict] 
PLAYER_LIST = "player_list"

# Status of given token : bool
STATUS = "status"

# Who sent the message (CLIENT, SERVER, BROADCAST) : str
SEND_TYPE = "send_type"

# Client answer to a question : str
ANSWER = "answer"

# Row of current question : int
ROW = "row"

# Column of current question : int
COL = "col"

# List of categories sent by server : list[str]
CATEGORIES = "category"

# Name of category : str
CATEGORY = "category"

# Answer to clue : str
QUESTION = "question"

# The player number to choose the next value/category : int
CURRENT_PLAYER_TURN = "current_player_turn"

# Wager for final jeopardy (UNUSED)
WAGER_VALUE = "wager_value"