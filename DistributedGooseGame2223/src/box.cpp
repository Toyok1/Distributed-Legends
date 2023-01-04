/*	BOX.CPP
 *	DESCRIPTION:
 *		Implementation of Box's class.
 */

#include "box.h"

// constructors
Box::Box()
{
	setName(" ");
	setDescription(" ");
	setId(2);
	this->prev = NULL;
	this->next = NULL;
} // default constructor

Box::Box(string name, string description, int id)
{ // costruttore con parametri
	setName(name);
	setDescription(description);
	setId(id);
	this->prev = NULL;
	this->next = NULL;
}
// SETTER METHODS
void Box::setName(string name) { this->name = name; }
void Box::setDescription(string description) { this->description = description; }
void Box::setId(int id) { this->id = id; }

// GETTER METHODS
string Box::getName() { return this->name; }
string Box::getDescription() { return this->description; }
int Box::getId() { return this->id; }

// Display box's info
void Box::display()
{
	cout << this->getName() << " - " << this->getDescription() << endl;
}

// Now defining the constructor of subclasses
Start::Start() : Box("Start", "Starting Square", 0) {}
End::End() : Box("End", "You Won!", 1) {}
Draw::Draw() : Box("Pesca", "Draw a Card", 3) {}
Bridge::Bridge() : Box("Bridge", "You're lucky, double your result ;)", 4) {}
Prison::Prison() : Box("Prison", "You landed in jail, skip your next three turns :(", 5) {}
Inn::Inn() : Box("Inn", "You stop to get a beer in a streetside inn, skip one turn", 6) {}
Labirinth::Labirinth() : Box("Labirinth", "You're lost in the labirinth, go back the amount of squares you rolled.", 7) {}
Skull::Skull() : Box("Skull", "How scary, a SKULL! You pass out and wake up at the start", 8) {}