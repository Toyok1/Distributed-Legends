
#include <iostream>
#include <cstdlib>
#include <cstring>
#include "box 2.h"
#include "Mazzo 2.h"

using namespace std;

class Player{
	private:
		string name;
		int age;
		int turn;
		int nBox;
		int d;			//save the last dice throw		
	public:
		Player *next;		//player list handler
		Box *position;		//current position on map
		//Constructors
		Player();
		Player(string n, int a, Box *p);

		//setters methods
		void setNBox(int x);
		void setName(string n);
		void setAge(int n);
		void setTurn(int n);
		void setDice(int n);
		//declare here the set for cells
	
		//Getters methods
		int getNBox();
		string getName();
		int getAge();
		int getTurn();
		int getDice();
		//Declare here the get for cells

		//Game Methods
		int dice();		//throw the dice
		void Turn(Mazzo *m);		//manage the turn of the current player
		void move(int x, bool v);	//manage the player movement
		void action(Mazzo *m);
		void handleCard(Carte c, Mazzo *m);
};


