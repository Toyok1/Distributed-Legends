/*GAME.CPP
 *corpo della classe Game. Qui verra' implementata la partita.
 */

#include "game.h"

const string start_s = "®";
const string end_s = "©";
const string empty_s = "○";
const string busy_s = "●";
Game::Game() : Menu()
{ // costruttore di default
	// i parametri ereditati verranno inizializzati dal costruttore di menu
	// i puntatori degli oggetti da impementare saranno inizializzati a Null
}

Game::Game(int playerAmount, bool mode) : Menu(playerAmount, mode)
{ // constructor with parameters respectively players, map and mode.
	// hereditary parameters are initialized by Menu's constructor

	// Create the map Now
	this->map = new Map(this->getMode());

	// Now create Mazzo -> OK!
	this->cardDeck = new CardDeck();
	this->cardDeck->Mischia();
	// Now create Players List -> OK
	this->player = new Player(); // create the sentinel
	this->createPlayers();			 // now init the players list

	this->initMap();
	// this->parseMap();
	// i puntatori degli oggetti da impementare saranno inizializzati a Null
}

void Game::createPlayers()
{
	string name;
	string age_string;
	int age;
	// Save the tmp pointer
	Player *tmp = NULL;
	Player *p = NULL;
	int playerNumber = this->playerAmount; // save the tmp player number
	cout << "PLAYER INFO" << endl;
	do
	{
		cout << "Name: "; // get the parameters
		getline(cin, name);
		do
		{
			cout << "Age: ";
			getline(cin, age_string);
			age = atoi(age_string.c_str());
			if (age < 1)
			{
				cout << "Age not valid, try again" << endl
						 << "Press any key to continue . . .";
				getchar();
			}
		} while (age < 1);

		tmp = new Player(name, age, (this->map)->init); // instances the new player as next of the current
		p = sortInsert(tmp);
		tmp = NULL;
		playerNumber--;
	} while (playerNumber > 0); // until Players Number is not 0
	p->next = this->player;			// cyclic list to control the turns
	system("clear");
}

Player *Game::sortInsert(Player *p)
{
	Player *curr = this->player;
	Player *prec = curr;
	bool flag = false;

	while (curr != NULL)
	{
		if ((p->getAge() < curr->getAge()) && (!flag))
		{
			flag = true;
			prec->next = p;
			p->next = curr;
		}
		prec = curr;
		curr = curr->next;
	}
	if (!flag)
	{
		prec->next = p;
		return p;
	}
	else
		return (prec);
}

void Game::displayPlayers()
{
	// scan the list and print players
	Player *tmp;
	tmp = this->player->next;
	for (int i = 0; i < this->playerAmount; i++)
	{
		cout << tmp->getName() << "-" << tmp->getAge() << "-" << tmp->position->getName() << "-" << tmp->position->next->getName() << "-";
		cout << tmp->position->next->prev->getName() << endl;
		tmp = tmp->next;
	}
}

void Game::printMap()
{
	for (int i = 0; i < NLENGTH; i++)
	{
		for (int j = 0; j < MLENGTH; j++)
			cout << this->graphicMap[i][j];
		cout << endl;
	}
}

void Game::parseMap()
{
	Box *p = this->map->init;
	int length = this->map->getLength() / 4;
	int i = 0;
	int j = 0;
	bool alt = true; // flag to discriminate the order of insert
	while (p->next != NULL)
	{ // END box will be treated differently (as START BOX have been to)
		// discriminating row lenght
		// first row: Map_lenght/4
		if (alt)
		{
			for (int k = 0; k < length; k++)
			{ // checking if some player is in the box yet
				if (p->next != NULL)
				{
					if (this->isBusy(p))
						this->graphicMap[i][j] = busy_s;
					else
						this->graphicMap[i][j] = empty_s;
					j++;
					p = p->next;
				}
			}
			// if we have element to insert but length is 1 continue one by one
			i++;
			j--;
			this->graphicMap[i][j] = "|"; // PRINTING LINE SEPARATOR.
			i++;
			alt = false;
		} // Left to Right Print
		else
		{
			for (int k = 0; k < length; k++)
			{
				if (p->next != NULL)
				{
					if (this->isBusy(p))
						this->graphicMap[i][j] = busy_s;
					else
						this->graphicMap[i][j] = empty_s;
					j--;
					p = p->next;
				}
			}
			i++;
			j++;
			this->graphicMap[i][j] = "|";
			i++;
			alt = true;
		}
		if (length != 1)
			length--;
	}
	// now we are in the last element
	this->graphicMap[i][j] = end_s;
	i = i + 2;
	this->graphicMap[0][0] = start_s;
	for (j = 0; j < MLENGTH; j++)
	{
		this->graphicMap[i][j] = "#";
	}
}

void Game::initMap()
{
	for (int i = 0; i < NLENGTH; i++)
	{
		for (int j = 0; j < MLENGTH; j++)
			this->graphicMap[i][j] = " ";
	}
}

bool Game::isBusy(Box *b)
{
	Player *tmp = this->player->next; // POINT FIRST PLAYER (NOT CONSIDERING SENTINEL)
	for (int i = 0; i < this->getPlayerAmount(); i++)
	{
		if (tmp->position == b)
			return true;
		tmp = tmp->next;
	}
	return false;
}

void Game::gameStart()
{
	Player *p = this->player->next; // saving the first player of the list. . .
	string winner;
	while (!this->isBusy(this->map->end))
	{ // continue to iterate while a player reach END BOX
		this->parseMap();
		this->printMap();
		this->prntLog(p);

		if (p->getTurn() == 0)
			p->Turn(this->cardDeck);
		else
		{
			cout << p->getName() << " skips the turn";
			getchar();
			system("clear");
			p->setTurn(p->getTurn() - 1);
		}
		// handle the lock/skip a tourn state
		winner = p->getName(); // tieni traccia per stampare il vincitore
		p = p->next;
		if (p->getTurn() == -1)
			p = p->next; // handle the sentinel: it will be skipped
	}
	cout << "BRAVO -" << winner << "- YOU WON!";
	cout << endl
			 << "GAME OVER" << endl
			 << "Press any key to return to the menu . . .";
	getchar(); // handle end game
	system("clear");
}

void Game::prntLog(Player *p)
{
	Player *k;
	k = this->player->next;
	cout << "-------------------------" << endl;
	for (int i = this->playerAmount; i > 0; i--)
	{
		cout << k->getName() << " - " << k->getNBox() << " - " << k->position->getName();
		if (p == k)
			cout << " * ";
		cout << endl;
		k = k->next;
	}
	cout << "-------------------------" << endl;
}
