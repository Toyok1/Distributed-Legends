// Created by Andrea D'Arpa

#include "Carte.h"

using namespace std;


//there'll be 6 types of cards that will be initialized in Main calling the constructor.

void Carte::messaggio(){
    cout<< Name << ": "<< Description << endl;
}
void Carte::setName(string Nome){
    this->Name = Nome;
};
void Carte::setDescription(string Descrizione){
    Description = Descrizione;
};
void Carte::setId(int id){
    this->Id=id;
};
string Carte::getName(){
    return Name;
};
string Carte::getDescription(){
    return Description;
};
int Carte::getId(){
    return Id;
};


Carta_vuota::Carta_vuota(){
    setId(0);
    setName("Empty Card");
    setDescription("Tough luck :(");
}



Carta_Avanti::Carta_Avanti(){
    setName("FULL THROTTLE!");
    setDescription("Forward one square");
    setId(1);
}

Carta_Turno::Carta_Turno(){
    setName("Stopped!");
    setDescription("Whoopsie, you're stuck for one turn...");
    setId(2);
}

Carta_Tira_Avanti::Carta_Tira_Avanti(){
    setName("Roll Again!");
    setDescription("and go forward");
    setId(3);
}


Carta_Tira_Indietro::Carta_Tira_Indietro(){
    setName("Roll Again, BUT!");
    setDescription("go backwards!");
    setId(4);
}

Carta_Start::Carta_Start() {//porta un giocatore al punto di partenza
        setName("The pitcher goes so often to the well");
          setDescription("that the next player goes back to the starting square!");
          setId(5);
      }
