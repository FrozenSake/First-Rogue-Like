# First-Roguelike

Hi, welcome to this repo for my roguelike. I've been working with the rogue basin tutorial (http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod ) which is based on Python2. I've been manually teaching myself differences as I write it in Python3. This is my first major coding project in over 15 years, and I'm using it to teach myself what's even anything. I have no idea if this is how readme's are used on github, I barely understand git or github, and the main goals here are to produce a "playable roguelike that's also maybe fun" and "to learn a lot." I recently added a new goal: to survive the tedium of balancing and producing the content variety needed for a (even a short) game.

### BUG LOG
- Fireball possibly not hitting multiple burnable targets.

TODO: Figure out if it's even true

- Bolt Scrolls don't appear to work

ERROR: Bolt Scrolls don't work

CAUSE: on_line() function does not appear to work

### TODO
- More varied AI
- More monsters
- More items
- More types of things!
- Loading old saves (instead of just the active one)

    Method: Perhaps something like a list of all "alive" players, that can be iterated to make a menu?
	
        How do we save the array and load it safely?
		
    Alternative:
	
        Can we crawl folders in the save folder and use their names, excluding Morgue?
		

### COMPLETED TASKS:
- Dungeon Generator - Rectangle rooms and straight hallways
- Field of View
- Fog of War
- General graphics, rendering, etc.
- Monster spawning
- Combat
- GUI
- Inventory and Items
- Win condition!
- Traps
- Pit traps random location
- Saving and Loading of floors


### MAJOR LEARNING POINTS:
- Integer division in Python 3 - / vs //
- Composition versus Inheritance
- Brittle data structures / data structure introduction
- OS commands