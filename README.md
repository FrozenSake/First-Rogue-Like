# First-Roguelike

Hi, welcome to this repo for my roguelike. I've been working with the rogue basin tutorial (http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod ) which is based on Python2. I've been manually teaching myself differences as I write it in Python3. This is my first major coding project in over 15 years, and I'm using it to teach myself what's even anything. I have no idea if this is how readme's are used on github, I barely understand git or github, and the main goals here are to produce a "playable roguelike that's also maybe fun" and "to learn a lot." I recently added a new goal: to survive the tedium of balancing and producing the content variety needed for a (even a short) game.

### BUG LOG
- Fireball possibly not hitting multiple burnable targets.

TODO: Figure out if it's even true

- If an elemental kills another with its death explosion, it will die twice, once with no name.

TODO: Ignore.

### RECENTLY FIXED BUGS

- Bolt Scrolls Don't Work

RESOLVE: Bolt scrolls fixed. on_line() fixed, targets_on_line() added.
TODO: Continue to observe to ensure it always works, and there are no failure cases. Only failure case would be player on line and no monster (As far as I can tell)

### V0.2 Patch Notes
- Inventory Size was hardcoded. Now MAX_MENU_SIZE constant in use.
- Poison damage changed from max(new, old) to additive.
- Poison damage now sets to 0 on clearing (see previous note for reason).
- Error message added for unequipping an item that isn't equipped.
- Controls changed to keypad only.
- Compile_Monsters and Compile_Items changed to make_map to reduce calls and optimize performance.
- Current_Traps iterates properly. (I think)
- Messages for going up floors clarified - one for new floor, one for old floor.
- Fixed on_line(), renamed line() returns a list of xy coordinates on a line in form of tuples
- Added targets_on_line() returns a list of objects. Utilizes line()
- RESOLVED BUG: on_line() doesn't work
- Elemental Death iterated through. Introduced infinite loop bug. Fixed infinite loop bug. Elemental death mecahnics work.
- Added new bug: Elementals killing each other on death causes a weird interaction.
- Minor enemy balancing occured.


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