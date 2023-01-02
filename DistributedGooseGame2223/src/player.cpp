/*
 * Description: Implements the player class
 */

#include "player.h"

// Default constructor-> only for sentinel element
Player::Player()
{
	this->next = NULL;
	this->setName("");
	this->setAge(0);
	this->setTurn(-1);
	this->position = NULL;
	this->setNBox(1);
}

// Constructor with parameters
Player::Player(string name, int age, Box *p)
{
	this->next = NULL;
	this->setName(name);
	this->setAge(age);
	this->setTurn(0);
	this->position = p; // set her the start cell
	this->setNBox(1);
}

// Setters
void Player::setName(string name)
{
	this->name = name;
}

void Player::setAge(int age)
{
	this->age = age;
}

void Player::setTurn(int turn)
{
	this->turn = turn;
}

void Player::setNBox(int nBox)
{
	this->nBox = nBox;
}

void Player::setDice(int dice)
{
	this->dice = dice;
}
// implents here the set cell method

// Getters
string Player::getName()
{
	return this->name;
}

int Player::getAge()
{
	return this->age;
}

int Player::getTurn()
{
	return this->turn;
}

int Player::getNBox()
{
	return this->nBox;
}

int Player::getDice()
{
	return this->dice;
}
// implements here the get cell method

void Player::Turn(CardDeck *m)
{
	cout << "It is the turn of: " << this->getName() << endl;
	cout << "Press enter to start. . .";
	getchar();
	this->setDice(this->throwDice());
	// incrementi nbox e spostamento puntatore a mappa del pg
	this->move(this->getDice(), false);
	cout << "WOW! You rolled a " << this->getDice() << endl;
	this->action(m);
	cout << "END OF TURN OF " << this->getName() << " PRESS ENTER!";
	getchar();
	system("clear");
}

int Player::throwDice()
{
	int x;
	x = rand() % 6 + 1;
	return (x + rand() % 6 + 1);
}

void Player::move(int x, bool v)
{ // if v is 0, move straight, else move backward
	// takes a player and moves its pointer to the apopropriate box one at the time
	// updates the position and nBox parameters
	for (x; x > 0; x--)
	{
		if ((this->position->getId() != 1) && (!v))
		{
			// muovi avanti solo se non sei in casella finale e v non è true
			this->position = this->position->next;
			this->setNBox(this->getNBox() + 1);
		}
		else if (this->position->prev != NULL)
		{ // sei andato oltre end box. torna indietro, solo se, Manage the back movement if we are in start
			this->position = this->position->prev;
			this->setNBox(this->getNBox() - 1);
			v = true;
		}
		// gestire limite di move back a start
	}
}

// now implements the action method for each subclass
void Player::action(CardDeck *cardDeck)
{
	Box *curr = this->position; // saving position before action
	Card card;
	this->position->display();
	switch (this->position->getId())
	{
	case 3: // Draw Box
		// cout <<m->getSegnalino();getchar();
		card = cardDeck->Pesca();
		card.message();
		this->handleCard(card, cardDeck);
		break;
	case 4: // Bridge Box
		// Call movement to the player
		this->move(this->getDice(), false);
		break;
	case 5: // Prison Box
		this->setTurn(3);
		break;
	case 6: // Inn Box
		this->setTurn(1);
		break;
	case 7: // Labirinth Box+
		this->move(this->getDice(), true);
		break;
	case 8: // Skull Box
		this->move(this->getNBox() - 1, true);
		break;
	default:
		break;
	}
	cout << "Press any key to continue . . .";
	getchar();
	if (curr != this->position)
		this->action(cardDeck); // iterate the action only if on a different box
}

void Player::handleCard(Card card, CardDeck *cardDeck)
{
	string s = "";
	switch (card.getId())
	{
	case 0: // empty card
		break;
	case 1:									// move card
		this->move(1, false); // move straight of 1 box
		break;
	case 2:							// Blocked Card
		this->setTurn(1); // block for 1 turn
		break;
	case 3: // Throw straight
		cout << "Press enter to roll the dice . . .";
		getchar();
		this->setDice(this->throwDice());
		cout << "WOW! You rolled a " << this->getDice() << endl;
		this->move(this->getDice(), false); // throw dice and move straight
		break;
	case 4: // throw back
		cout << "Press enter to roll the dice . . .";
		getchar();
		this->setDice(this->throwDice());
		cout << "WOW! You rolled a " << this->getDice() << endl;
		this->move(this->getDice(), true); // throw dice and move backward
		break;
	case 5: // back to start a player
		Player *app = this->next;
		if (app->getAge() == 0)
			app = app->next;										 // skipping the sentinel
		if (app->getTurn() == 0)							 // moving player only if is unblocked
			app->move(app->getNBox() - 1, true); // next player goes to start box
		else
			cout << app->getName() << " is in prison, and cannot move";
		break;
	}
}
