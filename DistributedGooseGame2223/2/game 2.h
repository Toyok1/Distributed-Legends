/*GAME.H		
*/

#include "menu 2.h"
#include "Mazzo 2.h"
#include "map 2.h"
const int MLENGTH =25;
const int NLENGTH=15;
using namespace std;


class Game:public Menu{
protected:
	//parameters about player number are inherited from the Menu class
	string graphicMap[NLENGTH][MLENGTH];	

public:
	Map *map;
	Mazzo *mazzo;
	Player *player;
//constructors:
	Game();								//default constructor  
	Game(int p, bool mo);		//constructor with parameters respectively players, map and mode.
	
	//Method that creates a list of player (knowing player's number)
	void createPlayers();
	Player* sortInsert(Player *p);
	void displayPlayers();
	void parseMap();	//parse the list and update the graphc map
	void printMap();
	void initMap();		//initialize the matrix with empty strings
	bool isBusy(Box *b);
	void gameStart();
	void prntLog(Player *p);
};
