#ifndef GOP_MAZZO_H
#define GOP_MAZZO_H

#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <ctime>
#include "Card.h"

class CardDeck
{
private:
    Card *CartaMazzoEasy[40]; // array of pointers to cards that are part of the deck
    int segnalino;            // counter for the card to draw
public:
    CardDeck(); // default constructor

    // getters & setters
    void setSegnalino(int i);
    int getSegnalino();

    // deck handling functions

    /* Mischia --> Generate a random integer (1-n), swap between card n and card k,
                  if they match, a new random number is generated, n is decremented at each iteration */
    void Mischia();
    Card Pesca(); // returns the first card of the deck
    void stampa();
};
#endif // GOP_MAZZO_H