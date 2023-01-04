
#include "CardDeck.h"

CardDeck::CardDeck()
{ // generates an ordered deck of cards.

    for (int i = 0; i < 10; i++)
    {
        CartaMazzoEasy[i] = new Carta_vuota();
    }
    for (int i = 10; i < 20; i++)
    {
        CartaMazzoEasy[i] = new Carta_Avanti();
    }
    for (int i = 20; i < 25; i++)
    {
        CartaMazzoEasy[i] = new Carta_Turno();
    }
    for (int i = 25; i < 30; i++)
    {
        CartaMazzoEasy[i] = new Carta_Tira_Avanti();
    }

    for (int i = 30; i < 35; i++)
    {
        CartaMazzoEasy[i] = new Carta_Tira_Indietro();
    }
    for (int i = 35; i < 40; i++)
    {
        CartaMazzoEasy[i] = new Carta_Start();
    }
}

void CardDeck::setSegnalino(int i)
{
    this->segnalino = i;
}

int CardDeck::getSegnalino()
{
    return this->segnalino;
}

void CardDeck::Mischia()
{
    int i;
    i = 40;
    Card *tmp;
    for (int p = 0; p < 40; p++)
    {          //"shuffling" algorithm, generates a random integes that dictates the position
        int k; // will be swapped with the last element of the list, which will then increment because it was already swapped.
        k = rand() % i;
        tmp = this->CartaMazzoEasy[k];
        this->CartaMazzoEasy[k] = this->CartaMazzoEasy[i - 1];
        this->CartaMazzoEasy[i] = tmp;
        i--; // decrement last position index
    }
    this->setSegnalino(0);
}

Card CardDeck::Pesca()
{
    // segnalino ++;
    // contatore che tiene conto della carta pescata e della prossima carta da pescare
    if (segnalino <= 39)
        return *CartaMazzoEasy[segnalino++];
    else
    {
        this->Mischia();
        this->setSegnalino(0);
        return *CartaMazzoEasy[segnalino++];
    }
}

void CardDeck::stampa()
{
    int k = 1; // testing function, DELETE!!!
    for (auto &i : CartaMazzoEasy)
    {
        cout << i->getName() << " - " << k << " - " << i->getDescription() << endl;
        k++;
    }
}