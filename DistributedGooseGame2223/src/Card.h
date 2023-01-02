#ifndef GOP_CARTE_H
#define GOP_CARTE_H

#include <iostream>
#include <cstdlib>
#include <cstring>

using namespace std;

class Card
{
protected:
    string name;
    string description;
    int id;

public:
    string getName();
    string getDescription();
    int getId();
    void setName(string name);
    void setDescription(string description);
    void setId(int id);
    void message();
};

class Carta_vuota : public Card
{
public:
    Carta_vuota();
};

class Carta_Avanti : public Card
{
public:
    Carta_Avanti();
};

class Carta_Turno : public Card
{
public:
    Carta_Turno();
};

class Carta_Tira_Avanti : public Card
{
public:
    Carta_Tira_Avanti();
};

class Carta_Tira_Indietro : public Card
{
public:
    Carta_Tira_Indietro();
};

class Carta_Start : public Card
{
public:
    Carta_Start();
};
#endif // GOP_CARTE_H
