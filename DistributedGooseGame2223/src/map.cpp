/*
 *  Description:	Implementation of of Map class
 */

#include "map.h"

Map::Map(bool mode)
{
	this->init = new Start();
	generateMap(mode); // generate the map(Random)
}

void Map::setLength(int length)
{
	this->length = length;
}

int Map::getLength()
{
	return this->length;
}

void Map::setAvg(int avg)
{
	this->avg = avg;
}

int Map::getAvg()
{
	return this->avg;
}

void Map::setNEmpty(int nEmpty)
{
	this->nEmpty = nEmpty;
}

int Map::getNEmpty()
{
	return this->nEmpty;
}

int Map::testRand()
{
	int a;
	a = rand() % 100 + 1;
	return a;
}

void Map::generateMap(bool mode)
{
	Box *p; // create end box as next of init
	this->end = new End();
	this->init->next = this->end;
	this->end->prev = this->init; // link data structures
	// calculations of number of boxes and empty boxes (using mode parameter)
	this->setLength(this->calcNBox(mode));
	this->setAvg(this->HowEmpty(mode));
	this->setNEmpty(this->getAvg() * this->getLength() / 100);
	int empty = this->getNEmpty();
	p = this->init;
	// now generate the middle boxes and connects them into the map
	for (int i = this->getLength(); i > 2; i--)
	{
		if (empty == i - 2)
		{
			Box *s;
			p = this->init;
			for (i; i > 2; i--)
			{
				s = p->next;
				p->next = new Box();
				p->next->next = s;
				s->prev = p->next;
				p->next->prev = p;
				p = p->next;
				empty--;
			}
		}
		else
		{
			Box *tmp = genBox(); // generate the box
			if (tmp->getId() == 2)
			{
				if (empty != 0)
					empty--;
				else
				{ // this provide to not insert more empty boxes then Nempty calculated before
					while (tmp->getId() == 2)
						tmp = genBox();
				}
			}
			p->next = tmp;
			tmp->prev = p;
			tmp->next = this->end;
			this->end->prev = tmp;
			p = p->next;
		}
	}
}

int Map::calcNBox(bool mode)
{
	if (!mode)
	{ // easy mode -> map length between 40-63
		return (rand() % 24 + 40);
	}
	else // hard mode -> map length between 64-90
		return (rand() % 27 + 64);
}

int Map::HowEmpty(bool mode)
{
	if (!mode)
	{ // easy Empty box perc range between 51 and 65%
		return (rand() % 15 + 51);
	}
	else // hard Empty box perc range between 35 and 50%
		return (rand() % 16 + 35);
}

Box *Map::genBox()
{
	Box *box;
	int event;
	int i = rand() % 100 + 1; // estraction of the number for the probability cases
	if (i <= this->getAvg())
	{
		box = new Box();
	}
	else
	{
		event = rand() % 6 + 3;
		switch (event)
		{
		case 3:
			box = new Draw();
			break;
		case 4:
			box = new Bridge();
			break;
		case 5:
			box = new Prison();
			break;
		case 6:
			box = new Inn();
			break;
		case 7:
			box = new Labirinth();
			break;
		case 8:
			box = new Skull();
			break;
		default:
			cout << "An unexpected error has occurred" << endl
					 << "Press a key to continue . . .";
			getchar();
			break;
		}
	}
	return box;
}
