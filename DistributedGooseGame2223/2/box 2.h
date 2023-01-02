/*	BOX.H
 *
 *	DESCRIPTION:
 *		Header file of Box's class.
 */

#include <iostream>
#include <cstdlib>
#include <cstring>
#include <string>
#include "Mazzo.h"

using namespace std;

class Box
{
protected:
	string Name;				// box name
	string Description; // box description
	int Id;							// type of box

public:
	Box *prev; // next and prev are used to handle plaeyer's movement on the map.
	Box *next;
	// constructors
	Box();																				// default constructor
	Box(string name, string description, int id); // constructor with parameters

	// SETTER METHODS
	void setName(string name);
	void setDescription(string description);
	void setId(int id);

	// GETTER METHODS
	string getName();
	string getDescription();
	int getId();

	void display();
};

class Start : public Box
{
public:
	Start();
};

class End : public Box
{
public:
	End();
};

class Draw : public Box
{
public:
	Draw();
};

class Bridge : public Box
{
public:
	Bridge();
};

class Prison : public Box
{
public:
	Prison();
};

class Inn : public Box
{
public:
	Inn();
};

class Labirinth : public Box
{
public:
	Labirinth();
};

class Skull : public Box
{
public:
	Skull();
};
