# Distributed-Legends
## Introduction
  
The distributed game developed with gRPC is a turn-based game where players compete to become the ultimate champion. Players can perform actions such as attacking, blocking or healing, by sending messages via gRPC technology. Thanks to the efficient and reliable communication provided by gRPC, the game offers a smooth and uninterrupted gaming experience for all players. Furthermore, the modular and flexible design of the game allows for the addition of new features to continuously improve the gaming experience.

## Technologies used

### Middleware - gRPC

The middleware we used is the Python version of gRPC and it handles the communication between any number of clients (in our case between 2 and 4) and a central service that runs on the cloud to manage all game lobbies. The basic operation is this: we have defined a series of messages and functions that we use in a file with the .proto extension which, once compiled, is transformed into a package that can be imported into our Python files where we actually implement the functions that we defined earlier. In particular, we have defined and used two main types of functions, the normal service methods which take a message as input and return a message as output and the stream service methods which show almost like a message queue where once a client connects to stream , receives all messages in associated list. We were inspired to make a video game based on the fighting styles of Pokémon or Final Fantasy (early versions) by the latter kind of feature because it resembles a correspondence chess game, where all messages are available to both sides as one pile of letters. \\
To manage the state of the game, each player has the list of players and with a Ping-Pong logic using the messages defined with gRPC, it updates who is connected and who is not. These connections between peers are also used to send player actions each turn.

### UX-UI - tkinter

The interface is built using tkinter because it's complete and easy to set up while offering a large amount of room for customization. The main elements are the top portion, where on top of a background we can see the icons for our heroes and the monster. Every player can see their health and block values as well as those of all the others. The bottom part of the window is split into two sides: the controls section and the text box. The controls are 4 buttons that let the player decide what to do on their turn, while the text box shows messages related to the actions performed by the players during the game; for example, after a hero attacks the monster, on the text box of everyone a message like "User USERNAME1 attacked USERNAME2 for VALUE points".

## Main features

The application features a shared list of players, built using a custom class called Player that contains all of the information needed to identify a player like its username, its unique id, and the values for health and block, to name a few. Every peer handles events by using listener functions (called \_\_listen\_for\_ and the thing they listen for like actions or turn endings) that are connected to stream functions so that when an even gets put into its respective list it is broadcasted to all other peers and they handle it accordingly. For example when one player ends its turn every peer receives the message containing the next turn's player and they check to see if it is their turn before unlocking all buttons thus letting the user play that turn. The actions a player can take in a turn are: attacking, healing, blocking and ending the turn. After a player has performed any of the first three actions he can only end their turn but that button is always active in case the player wants, for some reason, to skip their turn. Whenever one of these actions (one per turn) is performed, an Action message is generated using the player who sends the action, the ''victim" of it, the amount and the type, for example in a turn a player decides to attack the monster so he uses the appropriate action and automatically a value gets randomly chosen and the action is sent to every peer so that they can properly adjust the labels for health and eventually block.

## Start Game - Instructions

On a cloud machine or in your local pc run the lobby Auth service run:
````
cd build
bash LobbyAuthService.sh
````
To play instead you have to start the game with the following command:
````
cd build
bash DistributedLegends.sh
````
To end the game:
````
cd build
bash killer_distributed_legends.sh
````
And to terminate the service:
````
cd build
bash killer_lobby_service.sh
````
It's time to play, have fun!


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
  