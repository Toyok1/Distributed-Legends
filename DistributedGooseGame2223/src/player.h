/*
 * Description: Header file of class Player
 */

#include <iostream>
#include <cstdlib>
#include <cstring>
#include "box.h"
#include "CardDeck.h"

using namespace std;

class Player
{
private:
	string name;
	int age;
	int turn;
	int nBox;
	int dice; // save the last dice throw
public:
	Player *next;	 // gestore lista giocatori
	Box *position; // current position on map
	// Constructors
	Player();
	Player(string name, int age, Box *p);

	// setters methods
	void setNBox(int nBox);
	void setName(string name);
	void setAge(int age);
	void setTurn(int turn);
	void setDice(int dice);
	// declare here the set for cells

	// Getters methods
	int getNBox();
	string getName();
	int getAge();
	int getTurn();
	int getDice();
	// Declare here the get for cells

	// Game Methods
	int throwDice();					// throw the dice
	void Turn(CardDeck *m);		// manage the turn of the current player
	void move(int x, bool v); // manage the player movement
	void action(CardDeck *m);
	void handleCard(Card c, CardDeck *m);
};
