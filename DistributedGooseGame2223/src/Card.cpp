#include "Card.h"

using namespace std;

// there'll be 6 type of cards that will be initialized in Main calling the constructor.

void Card::message()
{
    cout << name << ": " << description << endl;
}
void Card::setName(string name)
{
    this->name = name;
};
void Card::setDescription(string description)
{
    this->description = description;
};
void Card::setId(int id)
{
    this->id = id;
};
string Card::getName()
{
    return name;
};
string Card::getDescription()
{
    return description;
};
int Card::getId()
{
    return id;
};

Carta_vuota::Carta_vuota()
{
    setId(0);
    setName("Empty Card");
    setDescription("Tough luck :(");
}

Carta_Avanti::Carta_Avanti()
{
    setName("FULL THROTTLE!");
    setDescription("Forward one square");
    setId(1);
}

Carta_Turno::Carta_Turno()
{
    setName("Stopped!");
    setDescription("Whoopsie, you're stuck for one turn...");
    setId(2);
}

Carta_Tira_Avanti::Carta_Tira_Avanti()
{
    setName("Roll Again!");
    setDescription("and go forward");
    setId(3);
}

Carta_Tira_Indietro::Carta_Tira_Indietro()
{
    setName("Roll Again, BUT!");
    setDescription("go backwards!");
    setId(4);
}

Carta_Start::Carta_Start()
{ // porta un giocatore al punto di partenza
    setName("The pitcher goes so often to the well");
    setDescription("that the next player goes back to the starting square!");
    setId(5);
}
