# Distributed-Legends
## Introduction

GRPCombat is a distributed videogame built using gRPC [@grpc], an open
source framework for remote procedure calls that was originally built by
Google. The premise is simple: a group of 3 heroes (chosen from 3
playable classes: knight, priest or mage) have all assembled to defeat
the big bad monster but he is not going down so easy and their battle
shall be legendary.\
The player hosting the gaming session plays as the monster and the
people connecting to the game are the heroes. The heroes collaborate to
defeat the common threat and the monster tries to defeat all of the
heroes to assure their world dominance.

## Technologies used

### Middleware - gRPC

The middleware we used is the Python version of gRPC and it handles
communication between any number of clients (in our case between 2 and
4) and a central server that is run on the machine of the user that
plays as the monster. The basic functioning is this: we defined a series
of messages and functions that use them in a file with a .proto
extension that, when compiled, turn into a package that can be imported
in our Python files where we actually implement the functions we defined
previously. In particular, we defined and used two main types of
functions, normal service methods which take a message as the input and
return a message as the output and stream service methods which act
almost like a message queue where, once a client connects to the stream,
it receives every message in the associated list. We were inspired to
create a videogame based on the combat styles of Pokémon or Final
Fantasy by this last type of function because it resembles a
correspondence chess match, where all the messages are available to both
parties like a stack of letters.\
This framework has a few quirks like the fact that the server can never
start a communication, it can only respond to a message sent by a user.
Managing a shared-state videogame under these constraints was
challenging but we managed to share our player list by combining the
simple act of pinging the server frequently to ensure that the client is
still connected (ping) with the response containing the list of players
with all of their values updated to the last change (pong). This
implementation lets every client know how many players are in the game
and their usernames, health and block values and more.

### UX-UI - tkinter

The interface is built using tkinter because it's complete and
easy to set up while offering a large amount of room for customization.
The main elements are the top portion, where on top of a background we
can see the icons for our heroes and the monster. Every player can see
their health and block values as well as those of all the others. The
bottom part of the window is split into two sides: the controls section
and the text box. The controls are 4 buttons that let the player decide
what to do on their turn, while the text box shows messages related to
the actions performed by the players during the game; for example, after
a hero attacks the monster, on the text box of everyone a message like
*"User \[USERNAME1\] attacked \[USERNAME2\] for \[VALUE\] points!\"*.

## Main features

The application features a shared list of players, built using a custom
class called Player that contains all of the information needed to
identify a player like its username, its unique id, and the values for
health and block, to name a few. The client handles events by using
listener functions (called \_\_listen_for\_ and the thing they listen
for like actions or turn endings) that are connected to stream functions
so that when an even gets put into its respective list it is broadcasted
to all clients and they handle it accordingly. For example when one
player ends its turn every client receives the message containing the
next turn's player and they check to see if it is their turn before
unlocking all buttons thus letting the user play that turn. The actions
a player can take in a turn are: attacking, healing, blocking and ending
the turn. After a player has performed any of the first three actions he
can only end their turn but that button is always active in case the
player wants, for some reason, to skip their turn. Whenever one of these
actions (one per turn) is performed, an Action message is generated
using the player who sends the action, the "victim\" of it, the amount
and the type, for example in a turn a player decides to attack the
monster so he uses the appropriate action and automatically a value gets
randomly chosen and the action is sent to every client so that they can
properly adjust the labels for health and eventually block. Every class
is better than the others numerically when it comes to a certain action:
the knight can use their shied to better block for his allies, the
priest is specialized in healing incantations and the mage uses their
fire magic to deal the most damage to the monster who, in their own
regards is special because they do better in battle the more enemies
they have.\
Like any videogame if your character reaches 0 HP it dies and it cannot
be revived. If a hero dies, his allies have to continue fighting without
him but if the monster dies the game finishes then and there with the
heroes' victory. The same happens with disconnections to the server
either accidental or voluntary.


## Future Developments

As of today, the application is fully functional, and it meets our
purposes of development. But, there is always room for improvement, so
we discussed on how this project could be polished up.

-   Using a better framework for the GUI: searching on the internet, we
    found a lot of interesting alternatives to tkinter such as pygames,
    gtk, qt, and python for unity. Using another framework could make
    the experience better, adding for example item transparency,
    animations, fullscreen support, touchscreen support, etc.

-   Adding in-game items to enrich the game loop depth.

-   Adding a soundtrack and sound effects to the game to better create
    immersion for the player.

-   Adding a game server list to join into a game.

-   Creating a builded version for macOs, Windows and Linux OSs.

