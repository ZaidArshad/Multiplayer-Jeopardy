# Key value for every token
TKN = "token"

# Client that sent this message has closed
CLIENT_CLOSED = "client_closed"

# Server message to inform recently connected client of establishment
CLIENT_CONNECTED = "client_connected"

# Informs client of the result of their answer
ANSWER_RESPONSE = "answer_response"

# Message with categories
SERVER_CATEGORY = "category_sent"

# Client message confirming the CLIENT_CONNECTED message
PLAYER_JOIN = "player_join"

# Has list of all the players and their info, frequently sent for UI updates
PLAYER_UPDATE = "player_update"

# Used in PLAYER_UPDATE as message of individual players, incudes score, name, number
PLAYER_INFO = "player_info"

# Indicates a player's answer to the current prompt 
PLAYER_ANSWER = "player_answer"

# Indicates a player's "buzz-in" to be given the right to answer the current prompt 
PLAYER_BUZZ = "player_buzz"

# Includes the row/col of the clicked button to chose a value/category
PLAYER_QUESTION_SELECT = "player_question_select"

# Has the question prompt, row, col and answer
SERVER_QUESTION_SELECT = "server_question_select"

# Unused
TIMEOUT = "timeout"
PLAYER_TURN = "player_turn"
LINE_EDIT_UPDATE = "line_edit_update"
BUZZ_TIME_OVER = "buzz_time_over"