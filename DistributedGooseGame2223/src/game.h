/*GAME.H
 *header della classe Game. Qui verra' implementata la partita.
 */

#include "menu.h"
#include "CardDeck.h"
#include "map.h"
const int MLENGTH = 25;
const int NLENGTH = 15;
using namespace std;

class Game : public Menu
{
protected:
	// i parametri di numero giocatori sono ereditati dalla classe madre Menu
	string graphicMap[NLENGTH][MLENGTH];

public:
	Map *map;
	CardDeck *cardDeck;
	Player *player;
	// constructors:
	Game();														 // Default constructor
	Game(int playerAmount, bool mode); // constructor with parameters respectively players, map and mode.

	// da implementare set e get degli oggetti da implementare

	// Method that creates a list of player (knowing player's number)
	void createPlayers();
	Player *sortInsert(Player *player);
	void displayPlayers();
	void parseMap(); // parse the list and update the graphc map
	void printMap();
	void initMap(); // initialize the matrix with empty strings
	bool isBusy(Box *box);
	void gameStart();
	void prntLog(Player *player);
};
