# Imports
import libtcodpy as libtcod ## http://roguecentral.org/doryen/data/libtcod/doc/1.5.1/index2.html
import math ## https://docs.python.org/3/library/math.html
import textwrap ## https://docs.python.org/3/library/textwrap.html
import shelve ## https://docs.python.org/3/library/shelve.html
import os ## https://docs.python.org/3/library/os.html
import shutil ## https://docs.python.org/3/library/shutil.html#shutil.rmtree
import fractions ## https://docs.python.org/3.1/library/fractions.html

# Global Constants 
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 80
MAP_HEIGHT = 43

LIMIT_FPS = 20

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

HEAL_AMOUNT = 4
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

FOV_ALGO = 0 #default FOV algorithm for libtcod
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
LEVEL_SCREEN_WIDTH = 40
CHARACTER_SCREEN_WIDTH = 30

LIGHTNING_RANGE = 5
LIGHTNING_DAMAGE = 20
CONFUSE_RANGE = 8
CONFUSED_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 12
BOLT_RANGE = 5
BOLT_POWER = 7

MAX_MENU_SIZE = 26

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
SAVE_DIRECTORY = CURRENT_DIRECTORY + '\\saves\\'
FONT_FILE = CURRENT_DIRECTORY + '\\arial10x10.png'
MENU_IMAGE = CURRENT_DIRECTORY + '\\menu_background1.png'

# Tile Colours
color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)


"""
CLASSES
"""

class Object:
    #Generic object class, player, monster, item, stairs, etc.
    #Always represented on screen by a character
    def __init__(self, x, y, char, name, color, blocks = False, always_visible = False, fighter = None, ai = None, item = None, burnable = False, equipment = None, trap = None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.always_visible = always_visible
        self.burnable = burnable
        
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self
            
        self.ai = ai
        if self.ai:
            self.ai.owner = self
            
        self.item = item
        if self.item:
            self.item.owner = self
            
        self.equipment = equipment
        if self.equipment:
            self.item = Item()
            self.item.owner = self
            self.equipment.owner = self
            
        self.trap = trap
        if trap:
            self.trap.owner = self
        
    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
        else:
            coin = libtcod.random_get_int(0, 0, 1)
            if coin == 0:
                print
                if not is_blocked(self.x + dx, self.y):
                    self.x += dx
                elif not is_blocked(self.x, self.y + dy):
                    self.y += dy
            elif coin == 1:
                if not is_blocked(self.x, self.y + dy):
                    self.y += dy
                elif not is_blocked(self.x + dx, self.y):
                    self.x += dx
        self.check_poison()
        
    def draw(self):
        #sets colour and draws it where it's at
        if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or (self.always_visible and map[self.x][self.y].explored)):
            libtcod.console_set_default_foreground(console, self.color)
            libtcod.console_put_char(console, self.x, self.y, self.char, libtcod.BKGND_NONE)
        
    def clear(self):
        #erase the character that represents this
        libtcod.console_put_char(console, self.x, self.y, ' ', libtcod.BKGND_NONE)
        
    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        if (target_x - self.x) > 0 and dx == 0:
            self.move(1, dy)
        elif (target_x - self.x) < 0 and dx == 0:
            self.move(-1, dy)
        elif (target_y - self.y) > 0 and dy == 0:
            self.move(dx, 1)
        elif (target_y - self.y) < 0 and dy == 0:
            self.move(dx, -1)
        else:
            self.move(dx, dy)
        
    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
        
    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        
    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)
        
    def burn(self):
        if self.burnable:
            message("The " + self.name + " burns up.", libtcod.red)
            if self.fighter:
                self.fighter.die()
            objects.remove(self)
            self.clear()
            
    def check_poison(self):
        if self.fighter and self.fighter.poisoned:
            self.fighter.take_damage(self.fighter.poison_damage)
            self.fighter.poison_turns -= 1
            if self.fighter.poison_turns <= 0:
                self.fighter.poisoned = False
                self.fighter.poison_damage = 0
   
class Fighter:
    def __init__(self, hp, defense, power, xp, death_function = None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.death_function = death_function
        self.xp = xp
        self.poisoned = False
        self.poison_turns = 0
        self.poison_damage = 0
        
    def power(self):
        bonus = sum(equipment.power_bonus for equipment in get_all_equipped(self.owner))
        return self.base_power + bonus
        
    def defense(self):
        bonus = sum(equipment.defense_bonus for equipment in get_all_equipped(self.owner))
        return self.base_defense + bonus
        
    def max_hp(self):
        bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
        return self.base_max_hp + bonus
        
    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            self.die()

    def die(self):
        function = self.death_function
        if function is not None:
            function(self.owner) 
            #What if it doesn't have one, is this fine? Do we need to close out this with an Else: to a generic death function?
        if self.owner != player:
            player.fighter.xp += self.xp
    
    def attack(self, target):
        damage = self.power() - target.fighter.defense() + libtcod.random_get_int(0, -3, 2)
        
        if damage > 0:
            message(self.owner.name.capitalize() + " attacks " + target.name + " for " + str(damage) + " damage.")
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + " attacks " + target.name + " but nothing happens!")
            
        self.owner.check_poison()
            
    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp():
            self.hp = self.max_hp()
            
    def check_level_up(self):
        level_up_xp = LEVEL_UP_BASE + ((player.level - 1) * LEVEL_UP_FACTOR)
        if player.fighter.xp >= level_up_xp:
            player.level += 1
            player.fighter.xp -= level_up_xp
            message("You get a little better at doing this nonsense! Your level is now " + str(player.level) + "!", libtcod.yellow)
            choice = None
            while choice == None:
                choice = menu("Level up! Choose a stat to raise:\n", ["Constitution (+20HP)", "Strength (+1 attack)", "Agility (+1 Defense)"], LEVEL_SCREEN_WIDTH)
            if choice == 0:
                player.fighter.base_max_hp += 20
                player.fighter.hp += 20
            elif choice == 1:
                player.fighter.base_power += 1
            elif choice == 2:
                player.fighter.base_defense += 1
                
    def get_poisoned(self, turns, strength):
        self.poisoned = True
        self.poison_turns += turns
        self.poison_damage += strength
        
    def spell(self, target):
        if self.owner.ai:
            self.owner.ai.spell(target)

# Monster AI Classes
            
class BasicMonster:
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)
                
class MushroomMonster:
    def __init__(self, poison_length, poison_strength, cooldown, range):
        self.poison_length = poison_length
        self.poison_strength = poison_strength
        self.cooldown_max = cooldown
        self.cooldown = cooldown
        self.range = range
        
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) <= self.range & self.cooldown == self.cooldown_max:
                monster.fighter.spell(player)
                self.cooldown = 0
            else:
                self.cooldown += 1
    
    def spell(self, target):
        if target.fighter:
            message("The giant mushroom quivers and pops, and then shoots out some spores.", libtcod.lime)
            target.fighter.get_poisoned(self.poison_length, self.poison_strength)        

class ConfusedMonster:
    def __init__(self, old_ai, num_turns=CONFUSED_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
        
    def take_turn(self):
        if self.num_turns > 0:
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
            
        else:
            self.owner.ai = self.old_ai
            message("The " + self.owner.name + " is no longer confused!", libtcod.red)

class AnimalMonster:
    def __init__(self):
        self = self
        
    def take_turn(self):
        self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))

class ElementalMonster:
    def __init__(self, type = None):
        if type:
            self.type = type
        else:
            self.type = "Unaspected"
            
    def take_turn(self):
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(player) >= 4:
                monster.move_towards(player.x, player.y)
            elif player.fighter.hp > 0:
                self.spell(player)
            
    def spell(self, target):
        if target.fighter:
            if self.type == "Unaspected":
                message("The bubbling, turgid field of unaspected energy coalesces into a hand, seeming gripping nothing. You feel agony.")
                target.fighter.take_damage(dungeon_level * 2)
            elif self.type == "Fire":
                message("")
            elif self.type == "Water":
                message("")

#Items and Equipment                
        
class Item:
    def __init__(self, use_function = None):
        self.use_function = use_function
    
    def pick_up(self):
        if len(inventory) >= MAX_MENU_SIZE:
            message("Your inventory is full, cannot pick up " + self.owner.name + ".", libtcod.red)
        else:
            inventory.append(self. owner)
            objects.remove(self.owner)
            message("You picked up a " + self.owner.name + "!", libtcod.green)
            
    def use(self):
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return
            
        if self.use_function is None:
            message("The " + self.owner.name + " cannot be used.")
        else:
            if self.use_function() != "cancelled":
                inventory.remove(self.owner)
                
    def drop(self):
        if self.owner.equipment: # dequip dropped equipment
            self.owner.equipment.dequip()
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message("You dropped a(n) " + self.owner.name + ".", libtcod.yellow)
        
class Equipment:
    def __init__(self, slot, power_bonus = 0, defense_bonus = 0, max_hp_bonus = 0):
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
        
        self.slot = slot
        self.is_equipped = False
        
    def toggle_equip(self):
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()
            
    def equip(self):
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()
        self.is_equipped = True
        message("Equipped " + self.owner.name + " to " + self.slot + " .", libtcod.light_green)
        
        
    def dequip(self):
        if not self.is_equipped: 
            message("That isn't even equipped, what are you doing?", libtcod.red)
            return
        self.is_equipped = False
        message("Dequipped " + self.owner.name + " from " + self.slot + ".", libtcod.light_yellow)

class Trap:
    def __init__(self, trap_function = None):
        self.trap_function = trap_function
        
    def trigger(self):
        self.trap_function()
        
    def disarm(self):
        global objects
        objects.remove(self.owner)
        
class Tile:
    # a tile on the map, and its properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        self.explored = False
        
        # by default if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

class Circle:
    def __init__(self):
        self.owner = self
        
    def center(self):
        center_x = (self.owner.x1 + self.owner.x2) / 2
        center_y = (self.owner.y1 + self.owner.y2) / 2
        return (center_x, center_y)
        
class Diamond:
    def __init__(self):
        self.owner = self
        
class Rectangle:
    def __init(self):
        self.owner = self
        
class Room:
    def __init__(self, x, y, w, h, rectangle = None, diamond = None, circle = None):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
        self.type = None
        
        self.rectangle = rectangle
        if self.rectangle:
            self.rectangle.owner = self
            self.type = "Rectangle"
        
        self.diamond = diamond
        if self.diamond:
            self.diamond.owner = self
            self.type = "Diamond"
            
        self.circle = circle
        if self.circle:
            self.circle.owner = self
            self.type = "Circle"
                
    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
    
    def intersect(self, other):
        # true if this rectangle intersects another - potential issue if width is negative? height negative?
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1)
        
    def get_type(self):
        return self.type
      
"""
METHODS
"""
        
def handle_keys():
    global key, stairsup, stairsdown, winnable
    
    # Alt + Enter to fullscreen
    if key.vk == libtcod.KEY_ENTER and (key.lalt or key.ralt):
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        if game_state is not "dead":
            save_game()
        main_menu()
    
    if game_state == 'playing':
        # Movement Keys
        if key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)
        elif key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)
        elif key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)
        elif key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)
        elif key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)
        elif key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)
        elif key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)
        elif key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)
        elif key.vk == libtcod.KEY_KP5:
            player_move_or_attack(0, 0)
            message("You wait.")
        else:
            key_char = chr(key.c)
            
            if key_char == "g": #Get Items
                for object in objects:
                    if object.x == player.x and object.y == player.y and object.item:
                        if object.name == "The Rubber DuckGuffin!":
                            winnable = True
                        object.item.pick_up()
                        break
            elif key_char == "i": # Use items in inventory
                chosen_item = inventory_menu("Select an item with the corresponding key, or any other to cancel.\n")
                if chosen_item is not None:
                    chosen_item.use()
            elif key_char == "d": # Drop items in inventory
                chosen_item = inventory_menu("To drop an item press the corresponding key.\n")
                if chosen_item is not None:
                    chosen_item.drop()
            elif key_char == "c": # Character status
                level_up_xp = LEVEL_UP_BASE + ((player.level - 1) * LEVEL_UP_FACTOR)
                msgbox("Character Information\n\nLevel: " + str(player.level) + "\nExperience: " + str(player.fighter.xp) + "\nExperience to level up: " + str(level_up_xp) + " \n\nMaximum HP: " + str(player.fighter.max_hp()) + "\nAttack: " + str(player.fighter.power()) + "\nDefense: " + str(player.fighter.defense()), CHARACTER_SCREEN_WIDTH)
            elif key_char == "," and key.shift: # < to go up
                if stairsup.x == player.x and stairsup.y == player.y:
                    previous_level()
            elif key_char == "." and key.shift: # > to go down
                if stairsdown.x == player.x and stairsdown.y == player.y:
                    next_level()
                    
            return 'didnt-take-turn'

def place_objects(room):
    global max_monsters, monster_chances
    global max_items, item_chances
    global current_traps, max_traps, trap_chances
    
    num_monsters = libtcod.random_get_int(0, 0, max_monsters)
    
    for i in range(num_monsters):
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
        
        if not is_blocked(x, y):
            choice = random_choice(monster_chances)
            monster = roll_monster_table(choice, x, y)
            objects.append(monster)
        
    
    num_items = libtcod.random_get_int(0, 0, max_items)
    
    for i in range(num_items):
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
        
        if not is_blocked(x, y):
            choice = random_choice(item_chances)
            item = roll_item_table(choice, x, y)
            objects.append(item)
            item.send_to_back()
            
    if current_traps < max_traps:
        remaining_traps = max_traps - current_traps
        num_traps = min(libtcod.random_get_int(0, 0, remaining_traps), libtcod.random_get_int(0, 0, remaining_traps))
        
        
        for i in range(num_traps):
            x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
            y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
            
            if not is_blocked(x, y, True):
                choice = random_choice(trap_chances)
                trap = roll_trap_table(choice, x, y)
                current_traps += 1
                objects.append(trap)
                trap.send_to_back()
                     
def player_move_or_attack(dx, dy):
    global fov_recompute
    
    x = player.x + dx
    y = player.y + dy
    
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y and object != player:
            target = object
            break
        elif object.trap and object.x == x and object.y == y:
            object.trap.trigger()
            if object.name != "pit trap":
                object.trap.disarm()
    
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True

def player_death(player):
    global game_state
    message("You died!")
    game_state = 'dead'
    
    player.char = "%"
    player.color = libtcod.dark_red
    
    make_morgue()
    
def make_map():
    global map, objects, stairsup, stairsdown
    
    compile_trap_table()
    compile_monster_table()
    compile_item_table()
    
    objects = [player]
    
    # fill map with unblocked tiles
    map = [[ Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]
            
    #generate the map
    rooms = []
    num_rooms = 0
    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of bounds
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
        
        d = max(w, h)
        type_roll = libtcod.random_get_int(0, 0, 2)
        if type_roll == 0:
            new_room = Room(x, y, w, h, rectangle = Rectangle())
        elif type_roll == 1 and (x + w) < MAP_WIDTH and (y + w) < MAP_HEIGHT:
            new_room = Room(x, y, w, w, diamond = Diamond()) ## Diamond H is = Width because of how I coded the diamond creator. It only produces exactly even diamonds right now, and this frees up map space.
        elif type_roll == 2 and (x + d) < MAP_WIDTH and (y + d) < MAP_HEIGHT:
            new_room = Room(x, y, d, d, circle = Circle())
        else:
            new_room = Room(x, y, w, h, rectangle = Rectangle())
            
        #check for collisions
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
        
        # carve the new room
        if not failed:
            create_room(new_room)
            (new_x, new_y) = new_room.center()
            """Testing Code - Will message A, B, C, D, etc. in rooms to indicate order created in
            for visualizing the room generation progress"""
            '''room_no = Object(int(new_x), int(new_y), chr(65+num_rooms), "room number", libtcod.white, blocks = False)
            objects.insert(0, room_no)
            print("Room " + chr(65+num_rooms) + " is a " + new_room.get_type())'''
            
            #place the player in the middle of the first room
            if num_rooms == 0:
                ## message("First Room")
                player.x = new_x
                player.y = new_y
                if travel_direction == "down":
                    stairsymbol = "<"
                    stairtext = "stairs up"
                    stairsup = Object(new_x, new_y, stairsymbol, stairtext, libtcod.white, always_visible = True)
                    objects.append(stairsup)
                    stairsup.send_to_back()
                else:
                    stairsymbol = ">"
                    stairtext = "stairs down"
                    stairsdown = Object(new_x, new_y, stairsymbol, stairtext, libtcod.white, always_visible = True)
                    objects.append(stairsdown)
                    stairsdown.send_to_back()
        
            else: #all rooms after #1 connect with tunnels
                (prev_x, prev_y) = rooms[num_rooms - 1].center()
                
                if libtcod.random_get_int(0, 0, 1) == 1:
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
            
            place_objects(new_room)
            rooms.append(new_room)
            num_rooms += 1
    if dungeon_level == 10:
        item_component = Item(use_function = None)
        mcguffin = Object(new_x, new_y, "~", "The Rubber DuckGuffin!", libtcod.gold, always_visible = True, item = item_component)
        objects.append(mcguffin)
        mcguffin.send_to_back()
    else:
        if travel_direction == "up":
            stairsymbol = "<"
            stairtext = "stairs up"
            stairsup = Object(new_x, new_y, stairsymbol, stairtext, libtcod.white, always_visible = True)
            objects.append(stairsup)
            stairsup.send_to_back()
        else:
            stairsymbol = ">"
            stairtext = "stairs down"
            stairsdown = Object(new_x, new_y, stairsymbol, stairtext, libtcod.white, always_visible = True)
            objects.append(stairsdown)
            stairsdown.send_to_back()
    
def render_all():
    global fov_map, fov_recompute
    global color_dark_ground, color_light_ground
    global color_dark_wall, color_light_wall
  
    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = map[x][y].block_sight
                if not visible: 
                    if map[x][y].explored:
                        if wall:
                            libtcod.console_set_char_background(console, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(console, x, y, color_dark_ground, libtcod.BKGND_SET)
                else: 
                    if wall:
                        libtcod.console_set_char_background(console, x, y, color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(console, x, y, color_light_ground, libtcod.BKGND_SET)
                    map[x][y].explored = True ## sets seen tiles to "explored" so they're not in Fog of War
                    
    for object in objects:
        object.draw()     
    player.draw()
          
    # blit the contents of the console to the root
    libtcod.console_blit(console, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
   
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1
    
    render_bar(1, 1, BAR_WIDTH, "HP", player.fighter.hp, player.fighter.max_hp(), libtcod.light_red, libtcod.darker_red)
    
    libtcod.console_set_default_foreground(panel,libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
    libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, "Dungeon level " + str(dungeon_level))
    
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

def create_room(room):
    global map
    # go through tiles in the rectangle (less one at the start and end for walls) and make them passable
    if room.rectangle:
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                map[x][y].blocked = False
                map[x][y].block_sight = False
    elif room.diamond:
        diameter = room.x2 - room.x1
        radius = diameter // 2
        (center_x, center_y) = room.center()
                
        current_y = center_y
        current_x = center_x
        i = 0
        while current_y < center_y + radius:
            current_x = center_x
            while (current_x > center_x - radius + i) and i <= radius:
                map[current_x][current_y].blocked = False
                map[current_x][current_y].block_sight = False
                current_x -= 1
            current_x = center_x
            while (current_x < center_x + radius - i) and i <= radius:
                map[current_x][current_y].blocked = False
                map[current_x][current_y].block_sight = False
                current_x += 1
            i += 1
            current_y += 1
            current_x = center_x + radius - 1
            
        current_y = center_y
        current_x = center_x
        i = 0
        while current_y > center_y - radius:
            current_x = center_x
            while (current_x > center_x - radius + i) and i <= radius:
                map[current_x][current_y].blocked = False
                map[current_x][current_y].block_sight = False
                current_x -= 1
            current_x = center_x
            while (current_x < center_x + radius - i) and i <= radius:
                map[current_x][current_y].blocked = False
                map[current_x][current_y].block_sight = False
                current_x += 1
            i += 1
            current_y -= 1
            current_x = center_x + radius - 1
    elif room.circle:
        (center_x, center_y) = room.circle.center()
        radius = room.x2 - center_x
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if in_range(center_x, center_y, x, y, radius - 1):
                    map[x][y].blocked = False
                    map[x][y].block_sight = False
            
def create_h_tunnel(x1, x2, y):
    global map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
    global map
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

def line (x1, y1, x2 = None, y2 = None, slope = None):
    ## 0,0 -1, 2
    #print("we're in on_line and x1: " + str(x1) + " and x2:" + str(x2) + " and y1: " + str(y1) + " and y2: " + str(y2))
    tiles_on_line = []
    if x2 and y2:
        (rise, run) = get_slope(x1, y1, x2, y2, as_fraction = True)
        #print("we got a rise of " + str(rise) + " and a run of " + str(run) + " from the get_slope function")
        
    if rise == 0: ## ISSUE: using + for i/j, so co-ordinates 1 and 2 have to be properly aligned. No bueno.
        #print("rise is 0!")
        i = 0
        while i < (max(x1, x2) - min (x1, x2)):
            #print(str(min(x1, x2) + i) + " " + str(y1) + " is being added")
            tiles_on_line.append((min(x1, x2) + i, y1))
            i += 1
    elif run == 0:
        #print("run is zero!")
        j = 0
        while j < (max(y1, y2) - min(y1, y2)):
            #print(str(x1) + " " + str(min(y1, y2) + j) + " is being added")
            tiles_on_line.append((x1, min(y1, y2) + j))
            j += 1
    else:
        i = 0
        while i <= rise:
            j = 0
            while j <= run:
                tiles_on_line.append((x1 + i, y1 + j))
                j += 1
            i += 1
    return tiles_on_line       

def targets_on_line(x1, y1, x2 = None, y2 = None, slope = None):
    theLine = line(x1, y1, x2, y2, slope)
    targets_on_line = []
    for xy in theLine:
        for object in objects:
            if object.x == xy[0] and object.y == xy[1]:
                targets_on_line.append(object)
    if targets_on_line == []:
        return None
    return targets_on_line                
    
def get_slope (x1, y1, x2, y2, as_fraction = False):
    rise = y1 - y2
    run = x2 - x1
    if rise == 0 or run == 0:
        return (rise, run)
    slope = rise / run
    if as_fraction:
        return (rise, run)  
    return slope
        
def is_blocked(x, y, stacks = False):
    if map[x][y].blocked:
        return True
    
    if not stacks:
        for object in objects:
            if object.blocks and object.x == x and object.y == y:
                return True
    
    return False
 
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)
    
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
    
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
        
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width // 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name+ ": " + str(value) + "/" + str(maximum))
 
def message(new_msg, color = libtcod.white):
    global game_msgs
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
    
    for line in new_msg_lines:
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
        game_msgs.append( (line, color) )
        
def get_names_under_mouse():
    global mouse
    
    (x, y) = (mouse.cx, mouse.cy)
    
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and not obj.trap and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
        
    names = ", ".join(names)
    return names.capitalize()
    
def menu(header, options, width):
    if len(options) > MAX_MENU_SIZE: raise ValueError("Cannot have a menu with more than 26 options.")
    
    header_height = libtcod.console_get_height_rect(console, 0, 0, width, SCREEN_HEIGHT, header)
    if header == "":
        header_height = 0
    height = len(options) + header_height
    
    window = libtcod.console_new(width, height)
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
    
    y = header_height
    letter_index = ord("a")
    for option_text in options:
        ##print("Iterating through inventory options: " + option_text)
        text = "(" + chr(letter_index) + ") " + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1
        
    x = SCREEN_WIDTH // 2 - width // 2
    y = SCREEN_HEIGHT // 2 - height // 2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    
    libtcod.console_flush()
    
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and (key.lalt or key.ralt):
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
        
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None

def main_menu():
    global game_state, travel_direction
    
    img = libtcod.image_load(MENU_IMAGE)
    
    while not libtcod.console_is_window_closed():
        libtcod.image_blit_2x(img, 0, 0, 0)
        
        libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        libtcod.console_print_ex(0, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 4, libtcod.BKGND_NONE, libtcod.CENTER, "SARCASTIC DUNGEON")
        libtcod.console_print_ex(0, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 2, libtcod.BKGND_NONE, libtcod.CENTER, "By Hikthur")
        
        try:
            if game_state == "fled":
                msgbox("You fled the dungeon, you scaredy cat.", 40)
                game_state = ""
                main_menu()
            elif game_state == "won":
                msgbox("You won! Bathtime is saved! You're the best.", 40)
                game_state = ""
                main_menu()
        except:
            game_state = ""
        
        choice = menu("", ["Play a new game", "Continue last game", "quit"], 24)
        
        if choice == 0:
            new_game()
            play_game()
        if choice == 1:
            try:
                load_game()
            except:
                msgbox("\n No saved game to load.\n", 24)
                continue
            play_game()
        elif choice == 2:
            raise SystemExit("Have fun, be safe!")
    libtcod.console_clear(0)
    
def inventory_menu(header):
    if len(inventory) == 0:
        options = ["Inventory is empty... how sad."]
    else:
        options = []
        for item in inventory:
            text = item.name
            if item.equipment and item.equipment.is_equipped:
                text = text + " (" + item.equipment.slot + ")"
            options.append(text)
        
    index = menu(header, options, INVENTORY_WIDTH)
    
    if index is None or len(inventory) == 0: return None
    return inventory[index].item

def msgbox(text, width = 50):
    menu(text, [], width)
    
def in_range(x, y, x2, y2, range):
    dx = max(x, x2) - min(x, x2)
    dy = max(y, y2) - min(y, y2)
    dist = math.sqrt(dx ** 2 + dy ** 2)
    
    if dist <= range:
        return True
    return False
                
def closest_monster(max_range):
    closest_enemy = None
    closest_dist = max_range + 1
    
    for object in objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
            dist = player.distance_to (object)
            if dist < closest_dist:
                closest_enemy = object
                closest_dist = dist
    return closest_enemy
    
def target_tile(max_range = None):
    global key, mouse
    while True:
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
        render_all()
        
        (x, y) = (mouse.cx, mouse.cy)
        
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)
        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)

def target_monster(max_range = None):
    while True:
        (x, y) = target_tile(max_range)
        if x is None: # player cancelled
            return None
        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj

def new_game():
    global player, inventory, game_msgs, game_state, dungeon_level, travel_direction, winnable, visited_floors
    
    name = ""
    msgbox("Please enter your name, press enter or escape when you're done.")
    key = libtcod.console_wait_for_keypress(True)
    while not key.vk == libtcod.KEY_ENTER and not key.vk == libtcod.KEY_ESCAPE and not key.vk == libtcod.KEY_KPENTER:
        name += chr(key.c)
        print("name is now " + name)
        key = libtcod.console_wait_for_keypress(True)
    if name == "":
        name = "player"
        print("Name was nothing")
    print("name is " + name)
    
    fighter_component = Fighter(hp = 40, defense = 0, power = 2, xp = 0, death_function = player_death)
    player = Object(0, 0, '@', name, libtcod.white, blocks = True, fighter = fighter_component)
    
    player.level = 1
    winnable = False
    
    game_msgs = []
    
    dungeon_level = 1
    visited_floors = []
    visited_floors.append(dungeon_level)
    travel_direction = "down"
    make_map()
    initialize_fov()
    
    game_state = 'playing'
    inventory = []
    
    os.makedirs(SAVE_DIRECTORY + player.name + "\\", exist_ok=True)
    os.makedirs(SAVE_DIRECTORY + "morgue\\", exist_ok=True)
    
    message("Welcome stranger... to your doom. Or something, look we're a bit tired around here, sorry.", libtcod.red)

def save_game():
    file = shelve.open(SAVE_DIRECTORY + player.name + "\\" + 'savegame', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['stairsup_index'] = objects.index(stairsup)
    file['stairsdown_index'] = objects.index(stairsdown)
    file['dungeon_level'] = dungeon_level
    file['travel_direction'] = travel_direction
    file.close()
    
def load_game():
    global map, objects, player, inventory, game_msgs, game_state, stairsdown, stairsup, dungeon_level
    
    file = shelve.open(SAVE_DIRECTORY + player.name + "\\" + 'savegame', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    stairsup = objects[file['stairsup_index']]
    stairsdown = objects[file['stairsdown_index']]
    dungeon_level = file['dungeon_level']
    travel_direction = file['travel_direction']
    file.close()
    
    initialize_fov()
    
def make_morgue():
    file = shelve.open(SAVE_DIRECTORY + "morgue\\" + player.name, 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file.close()
    ## deletes the player's entire save folder when they die - cannot use os. as the functions are too limited.
    shutil.rmtree(SAVE_DIRECTORY + player.name + "\\")

def save_floor():
    global map, objects, stairsup, stairsdown, player
    objects.remove(player)
    file = shelve.open(SAVE_DIRECTORY + player.name + "\\" + str(dungeon_level), 'c')
    file['map'] = map
    file['objects'] = objects
    file['stairsup_index'] = objects.index(stairsup)
    file['stairsdown_index'] = objects.index(stairsdown)
    file.close()
    
def load_floor():
    global map, objects, stairsup, stairsdown, player, travel_direction
    file = shelve.open(SAVE_DIRECTORY + player.name + "\\" + str(dungeon_level), 'r')
    map = file['map']
    objects = file['objects']
    stairsup = objects[file['stairsup_index']]
    stairsdown = objects[file['stairsdown_index']]
    if travel_direction == "up":
        player.x = stairsdown.x
        player.y = stairsdown.y
    elif travel_direction == "down":
        player.x = stairsup.x
        player.y = stairsup.y
    else:
        player.x = stairsup.x
        player.y = stairsup.y
    objects.append(player)
    file.close()
    
def next_level(trap = False):
    global dungeon_level, travel_direction, visited_floors
    
    save_floor()
    
    if not trap:
        message("You head down the stairs. Spooky!", libtcod.light_violet)
        message("You made it down the stairs. Phew, it was hard to remember how to do that.", libtcod.light_violet)
        dungeon_level += 1
    elif trap:
        message("You stand up and brush yourself off. Phew... now where are you?", libtcod.light_violet)
        player.fighter.take_damage(1)
        if dungeon_level == 10:
            distance = 0
        elif dungeon_level == 8 or 9:
            distance = 1
        else:
            distance = libtcod.random_get_int(0, 1, 3)
        dungeon_level += distance
    travel_direction = "down"
    if dungeon_level not in visited_floors:
        visited_floors.append(dungeon_level)
        make_map()
        if trap:
            placed = False
            while not placed:
                player.x = libtcod.random_get_int(0, 0, MAP_WIDTH)
                player.y = libtcod.random_get_int(0, 0, MAP_HEIGHT)
                if not map[player.x][player.y].blocked:
                    placed = True
        else:
            player.fighter.heal(5)
                    
        initialize_fov()
    else:
        load_floor()
        if trap:
            placed = False
            while not placed:
                player.x = libtcod.random_get_int(0, 0, MAP_WIDTH)
                player.y = libtcod.random_get_int(0, 0, MAP_HEIGHT)
                if not map[player.x][player.y].blocked:
                    placed = True
        initialize_fov()

def previous_level():
    global dungeon_level, game_state, travel_direction, winnable, visited_floors
    
    save_floor()
    dungeon_level -= 1
    if dungeon_level <= 0 and winnable:
        game_state = "won"
        save_game()
        make_morgue()
        main_menu()
    elif dungeon_level <= 0:
        game_state = "fled"
        save_game()
        make_morgue()
        main_menu()
    else:
        
        travel_direction = "up"
        if dungeon_level not in visited_floors:
            message("You head up the stairs... but don't recognize anything. Do you have a brain injury?")
            visited_floors.append(dungeon_level)
            make_map()
            initialize_fov()
            player.fighter.heal(5)
        else:
            message("You head up the stairs... Well, I guess you're here now.")
            load_floor()
            initialize_fov()
    
def initialize_fov():
    global fov_recompute, fov_map
    
    fov_recompute = True
    libtcod.console_clear(console)
    
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

def play_game():
    global key, mouse
    
    player_action = None
    
    mouse = libtcod.Mouse()
    key = libtcod.Key()
    
    while not libtcod.console_is_window_closed():

        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
        render_all()
       
        libtcod.console_flush()
        player.fighter.check_level_up()
    
        # replace all characters with a blank space before moving
        for object in objects:
            object.clear()
        
        # handle keypresses and exit if required
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            raise SystemExit("Have fun, be safe!")
        
        # monster turns
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for object in objects:
                if object.ai:
                    object.ai.take_turn()

def initialize_system():
    global console, panel
    
    # Setting font from libtcod, initializing consoles 
    libtcod.console_set_custom_font(FONT_FILE, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'The Sarcastic Dungeon')
    libtcod.sys_set_fps(LIMIT_FPS)
    console = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
    panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
             
def random_choice_index(chances):
    dice = libtcod.random_get_int(0, 1, sum(chances))
    
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w
        
        if dice <= running_sum:
            return choice
        choice += 1

def random_choice(chances_dict):
    chances = chances_dict.values()
    strings = list(chances_dict.keys())
    return strings[random_choice_index(chances)]

def from_dungeon_level(table):
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0

def compile_monster_table(): ## Reflect any changes here in roll_monster_table()
    global max_monsters, monster_chances
    max_monsters = from_dungeon_level([[2, 1], [3, 4], [5, 6]])
    
    monster_chances = {}
    monster_chances['orc'] = 80
    monster_chances['troll'] = from_dungeon_level([[15, 3], [30, 5], [60, 7]])
    monster_chances['giant mushroom'] = from_dungeon_level([[9, 2], [19, 4], [3, 6]])
    monster_chances['bandit'] = from_dungeon_level([[12, 1], [15, 2], [8, 3], [6, 4]])
    monster_chances['skeleton'] = from_dungeon_level([[1, 1], [4, 2], [5, 4], [20, 8]])
    monster_chances['raccoon'] = from_dungeon_level([[20, 1], [15, 2], [10, 3], [2, 4]])
    monster_chances['squirrel'] = from_dungeon_level([[20, 1], [15, 2], [10, 3], [2, 4]])
    monster_chances['elemental'] = from_dungeon_level([[2, 3], [3, 4], [6, 5], [12, 7], [30, 10]])
  
def roll_monster_table(choice, x, y):
    if choice == "orc":
        fighter_component = Fighter(hp = 8, defense = 0, power = 1, xp = 30, death_function = monster_death)
        ai_component = BasicMonster()
        monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks = True, fighter = fighter_component, ai = ai_component)
    elif choice == "troll":
        fighter_component = Fighter(hp = 17, defense = 1, power = 4, xp = 100,  death_function = monster_death)
        ai_component = BasicMonster()
        monster = Object(x, y, 'T', 'troll', libtcod.darker_green, blocks = True, fighter = fighter_component, ai = ai_component)
    elif choice == "giant mushroom":
        fighter_component = Fighter(hp = 5, defense = 6, power = 2, xp = 120, death_function = undead_death)
        ai_component = MushroomMonster(3, 3, 3, 3)
        monster = Object(x, y, 'M', 'giant mushroom', libtcod.lime, blocks = True, fighter = fighter_component, ai = ai_component, burnable = True)
    elif choice == "undead bee":
        fighter_component = Fighter(hp = 5, defense = 0, power = 3, xp = 60, death_function = undead_death)
        ai_component = BasicMonster()
        monster = Object(x, y, 'b', 'undead bee', libtcod.Color(95, 95, 95), blocks = True, fighter = fighter_component, ai = ai_component)
    elif choice == "bandit":
        fighter_component = Fighter(hp = 12, defense = 0, power = 2, xp = 50, death_function = monster_death)
        ai_component = BasicMonster()
        monster = Object(x, y, 'B', 'bandit', libtcod.sepia, blocks = True, fighter = fighter_component, ai = ai_component)
    elif choice == "skeleton":
        fighter_component = Fighter(hp = 6, defense = 1, power = 4, xp = 185, death_function = undead_death)
        ai_component = BasicMonster()
        monster = Object(x, y, 's', 'skeleton', libtcod.Color(95, 95, 95), blocks = True, fighter = fighter_component, ai = ai_component)
    elif choice == "raccoon":
        fighter_component = Fighter(hp = 2, defense = 0, power = 1, xp = 5, death_function = monster_death)
        ai_component = AnimalMonster()
        monster = Object(x, y, 'r', 'raccoon', libtcod.sepia, blocks = True, fighter = fighter_component, ai = ai_component)
    elif choice == "squirrel":
        fighter_component = Fighter(hp = 1, defense = 0, power = 1, xp = 2, death_function = monster_death)
        ai_component = AnimalMonster()
        monster = Object(x, y, 's', 'squirrel', libtcod.sepia, blocks = True, fighter = fighter_component, ai = ai_component)
    elif choice == "elemental":
        fighter_component = Fighter(hp = 26, defense = 4, power = 6, xp = 505, death_function = elemental_death)
        ai_component = ElementalMonster("Unaspected")
        monster = Object(x, y, 'E', 'Unaspected Elemental', libtcod.Color(100, 100, 100), blocks = True, fighter = fighter_component, ai = ai_component)
    return monster

def monster_death(monster):
    message(monster.name.capitalize() + " is dead. Super dead! You gain " + str(monster.fighter.xp) + " experience.", libtcod.orange)
    monster.char = "%"
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = "Remains of " + monster.name
    monster.send_to_back()

def undead_death(monster):
    message(monster.name.capitalize() + " is dead. Again! You gain " + str(monster.fighter.xp) + " experience.", libtcod.orange)
    monster.char = " "
    monster.color = libtcod.red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = ""
    monster.send_to_back()

def elemental_death(monster):
    message(monster.name.capitalize() + " writhes and roils for a moment before exploding into a cataclysmic wave of " + monster.ai.type + " energy.")
    objects.remove(monster)
    for obj in objects:
        if ((obj.x == monster.x - 2 or obj.x == monster.x - 1 or obj.x == monster.x or obj.x == monster.x + 1 or obj.x == monster.x + 2) and (obj.y == monster.y - 2 or obj.y == monster.y - 1 or obj.y == monster.y or obj.y == monster.y + 1 or obj.y == monster.y + 2)) and obj.fighter and obj is not monster:
            obj.fighter.take_damage(max(dungeon_level // 2, 1))
            message(obj.name.capitalize() + " is caught in the explosion")
    message("You gain " + str(monster.fighter.xp) + " experience.", libtcod.orange)
    monster.char = " "
    monster.color = libtcod.red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = ""
    
def compile_item_table(): ## Reflect any changes here in roll_item_table()
    global max_items, item_chances
    max_items = from_dungeon_level([[1, 1], [2, 4], [3, 8]])
    
    item_chances = {}
    item_chances['heal'] = 35
    item_chances['lightning'] = from_dungeon_level([[2, 1], [10, 3], [25, 5]])
    item_chances['fireball'] = from_dungeon_level([[1, 1], [2, 2], [4, 3], [9, 5], [25, 6]])
    item_chances['confuse'] = from_dungeon_level([[5, 1], [10, 2], [15, 3]])
    item_chances['sword'] = from_dungeon_level([[20, 1], [25, 2], [20, 3], [5, 4]])
    item_chances['shield'] = from_dungeon_level([[5, 1], [15, 2], [20, 3]])
    item_chances['bolt'] = from_dungeon_level([[8, 1], [4, 2], [8, 5], [15, 6]])

def roll_item_table(choice, x, y):
    if choice == "heal":
        item_component = Item(use_function = cast_heal)
        item = Object(x, y, "!", "healing potion", libtcod.violet, item = item_component, always_visible = True)
    elif choice == "lightning":
        item_component = Item(use_function = cast_lightning)
        item = Object(x, y, "#", "scroll of lightning bolt", libtcod.light_yellow, item = item_component, burnable = True, always_visible = True)
    elif choice == "fireball":
        item_component = Item(use_function = cast_fireball)
        item = Object(x, y, "#", "scroll of fireball", libtcod.light_yellow, item = item_component, burnable = True, always_visible = True)
    elif choice == "confuse":
        item_component = Item(use_function = cast_confuse)
        item = Object(x, y, "#", "scroll of confuse monster", libtcod.light_yellow, item = item_component, burnable = True, always_visible = True)
    elif choice == "sword":
        equipment_component = Equipment(slot = "right hand", power_bonus = 3)
        item = Object(x, y, "/", "sword", libtcod.sky, equipment=equipment_component)
    elif choice == "shield":
        equipment_component = Equipment(slot = "left hand", defense_bonus = 1)
        item = Object(x, y, "[", "shield", libtcod.darker_orange, equipment = equipment_component)
    elif choice == "bolt":
        item_component = Item(use_function = cast_bolt)
        item = Object(x, y, "#", "scroll of bolt", libtcod.light_yellow, item = item_component, burnable = True, always_visible = True)
    return item

def cast_heal():
    if player.fighter.hp == player.fighter.max_hp():
        message("You are already at full health. Amazing.", libtcod.red)
        return "cancelled"
        
    message("Your wounds are super duper better, man!", libtcod.light_violet)
    player.fighter.poisoned = False
    player.fighter.poison_damage = 0
    player.fighter.poison_turns = 0
    player.fighter.heal(HEAL_AMOUNT * player.level)
    
def cast_lightning():
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:
        message ("No enemy is close enough to strike, and the scroll is boring.", libtcod.red)
        return 'cancelled'
    
    message("A lightning bolt strikes the " + monster.name + " with a loud peel of thunder! The damage is " + str(LIGHTNING_DAMAGE) + " hit points.", libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_bolt(caster = None):
    message("Left-click an enemy to hit it and everything between you and it with a bolt, or right-click to cancel.", libtcod.light_cyan)
    monster = target_monster(BOLT_RANGE)
    #print("A monster was selected")
    if monster is None: return "cancelled"
    if caster == None:
        caster = player
    targets = targets_on_line(caster.x, caster.y, monster.x, monster.y)
    if targets == []:
        message("No targets!")
        return
    for target in targets:
        #print("Iterating through targets")
        if target.fighter and target != player:
            message("The bolt rips through " + monster.name, libtcod.brass)
            target.fighter.take_damage(BOLT_POWER)
    
def cast_confuse():
    message("Left-click an enemy to confuse it, or right-click to cancel.", libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return "cancelled"
        
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster
    message("The " + monster.name + " stumbles a bit and begins to drool.", libtcod.light_green)

def cast_fireball():
    message("Left-click a target tile for the fireball, or right-click to cancel.", libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return "cancelled"
    message ("The fireball explodes, burning everything within " + str(FIREBALL_RADIUS) + " tiles! Wow...", libtcod.orange)
    
    for obj in objects:
        if obj.distance(x, y) <= FIREBALL_RADIUS:
            if obj.burnable:
                obj.burn()
            elif obj.fighter:
                message("The " + obj.name + " gets burned for " + str(FIREBALL_DAMAGE) + " damage", libtcod.orange)
                obj.fighter.take_damage(FIREBALL_DAMAGE)
    
def compile_trap_table(): ## Reflect any changes here in roll_trap_table()
    global max_traps, trap_chances, current_traps
    max_traps = from_dungeon_level([[5, 1], [8, 2], [12, 3], [20, 6]])
    current_traps = 0
    
    trap_chances = {}
    trap_chances['pointless'] = 50
    trap_chances['spike'] = from_dungeon_level([[1, 1], [10, 2], [22, 5]])
    trap_chances['boulder'] = from_dungeon_level([[5, 1], [6, 2], [40, 7]])
    trap_chances['undead bee'] = from_dungeon_level([[2, 3], [6, 5], [12, 7]])
    trap_chances['pit'] = from_dungeon_level([[10, 1], [12, 2], [5, 3], [12, 4], [1, 8], [0, 9]])
    trap_chances['poison'] = from_dungeon_level ([[2, 1], [5, 3]])
    
def roll_trap_table(choice, x, y):
    if choice == "pointless":
        trap_component = Trap(trap_function = pointless_trap)
        trap = Object(x, y, "$", "pointless trap", color_light_ground, trap = trap_component)
    elif choice == "spike":
        trap_component = Trap(trap_function = spike_trap)
        trap = Object(x, y, "$", "spike trap", color_light_ground, trap = trap_component)
    elif choice == "boulder":
        trap_component = Trap(trap_function = boulder_trap)
        trap = Object(x, y, "$", "boulder trap", color_light_ground, trap = trap_component)
    elif choice == "undead bee":
        trap_component = Trap(trap_function = undead_bee_trap)
        trap = Object(x, y, "$", "bee trap", color_light_ground, trap = trap_component)
    elif choice == "pit":
        trap_component = Trap(trap_function = pit_trap)
        trap = Object(x, y, "$", "pit trap", color_light_ground, trap = trap_component)
    elif choice == "poison":
        trap_component = Trap(trap_function = poison_trap)
        trap = Object(x, y, "$", "poison trap", color_light_ground, trap = trap_component)
    return trap

def pointless_trap():
    message_color = libtcod.Color(libtcod.random_get_int(0, 0, 255), libtcod.random_get_int(0, 0, 255), libtcod.random_get_int(0, 0, 255))
    message("Butterflies pour out of the floor, and you feel sad.", message_color)

def spike_trap():
    message("The floor gives way and you fall onto some spikes. Have you considered metal shoes?", libtcod.red)
    player.fighter.take_damage(5)

def boulder_trap():
    message("The ceiling opens up and nothing happens. Then a boulder hits you in the back. Oww.", libtcod.red)
    player.fighter.take_damage(10)

def undead_bee_trap():
    message("Cactarhero sends his regards is scrawled on the floor. What does that mean?")
    monster = roll_monster_table("undead bee", player.x - 1, player.y)
    objects.append(monster)
    monster = roll_monster_table("undead bee", player.x, player.y - 1)
    objects.append(monster)
    monster = roll_monster_table("undead bee", player.x + 1, player.y)
    objects.append(monster)
    monster = roll_monster_table("undead bee", player.x, player.y + 1)
    objects.append(monster)

def pit_trap():
    message("The floor gives way. Wow. Did you seriously fall for this?")
    next_level(trap = True)
   
def poison_trap():
    message("There's a strange smell in the air. Oh, that's you. While you're thinking about this a goblin runs up and poisons you. Rude!", libtcod.lime)
    player.fighter.get_poisoned(3, dungeon_level)
   
def get_equipped_in_slot(slot):
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None

def get_all_equipped(obj):
    if obj == player: ## Chance this to allow monsters to equip items
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []
    
"""
INITIALIZATION & MAIN LOOP
"""

initialize_system()
main_menu()