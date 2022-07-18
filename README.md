# Multiplayer-Jeopardy


# CMPT 371 Summer 2022

## Project

```
This project is to be done in groups of 5 students!
```
In this project, your group will build an online multiplayer game. The game itself is up to you, though a
suggested game called Deny and Conquer is described later below.

**Game Requirements:**

- The game shall be a client-server program. Each player is a client connecting to the server from a
    remote machine/device.
- The server can be started by any player. All players (including the player who started the session)
    connect to that server as clients.
- There must be at least one shared object in the game which requires “locking” of that object for
    concurrency; i.e., only one player at a time can use that object. In the Deny and Conquer game below,
    each white box is a shared object.

**Technical Rules:**

- You can use any programming language that you like.
- For the frontend, you can use any existing graphics or GUI library or framework. Make your life easy
    for the frontend as much as possible. Don’t overdo the GUI. A simple and functional GUI is enough.
- For the backend (client and server system), you cannot use any existing gaming, client-server,
    messaging, remote calling, or other middleware or frameworks. Everything must be written from
    scratch. You must use sockets programming and send application-layer messages directly.

**Deliverables:**

1. A working demo, to be presented in person to the TAs at the end of the course (schedule TBD).
2. A project report, due August 1 4 in Canvas, which includes:
    a. Description of the game and your design, including your application-layer messaging scheme.
    b. A list of group members and their % contribution to the project.
    c. Commented source code of the client and the server. Alternatively you can include a link to
       Github or other repositories, though the code still has to be commented.

**Marking Scheme:**

Working Demo 50%
Project report 50%

**Deny and Conquer**
The game board is a square divided into boxes of equal size. The number of boxes shall be 8 × 8. The game
is played by multiple players, each having a pen of different colour. The thickness of the pen is the same
for all players. The objective is to deny your opponents filling the most number of boxes, by taking over
as many boxes as you can. To take over a box, you must colour the box with your pen, and at least 50 % of


the area of the box must be coloured to be considered taken over by you. Otherwise, another player can
try taking over the box. Once a box has been taken over by a given player, then the box turns entirely to
the colour of the player and can no longer be taken over by any other player. At the end of the game; i.e.,
when all boxes have been taken over, whoever has the most number of boxes will win the game. Tie is
also possible. An example is shown in Figure 1.

```
Figure 1. An example gameplay between 4 players in Deny and Conquer.
```
**Game Mechanics:**
To take over a white box, a player must hold the click button down inside that box while scribbling inside
the box. Once the player lets go of the click button, the game should calculate the %area that is coloured.
If it is more than 50% of the area of that box, then the player has taken over that box, and the colour of
the box shall change completely to the colour of the player. No other player can take over that box
anymore. But, if it is less than 50% _,_ the player has not taken over the box, in which case the game
immediately changes the box back to pure white, and the box is up for grabs again!

While a player is scribbling in a box, that box is no longer available to other players. If those other players
click in that box, they should not be able to draw anything in it.


