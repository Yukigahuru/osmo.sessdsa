#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

import random
import math

from consts import Consts
from cell import Cell

from sample.easy_ai1 import Player as Player1
from sample.easy_ai0 import Player as Player0

class World():
    def __init__(self):
        # Variables and setup
        self.cells = [] # Array of cells
        self.result = None
        # Init
        self.new_game()
        self.player0 = Player0()
        self.player1 = Player1()

    # Methods
    def new_game(self):
        self.cells = []
        # Define the players first
        self.cells.append(Cell([Consts["WORLD_X"] / 4, Consts["WORLD_Y"] / 2], [0, 0], 30, isplayer = True))
        self.cells.append(Cell([Consts["WORLD_X"] / 4 * 3, Consts["WORLD_Y"] / 2], [0, 0], 30, isplayer = True))
        # Generate a bunch of random cells
        for i in range(Consts["CELLS_COUNT"]):
            if i < 4:
                rad = 3 + (random.random() * 3) # Small cells
            elif i < 6:
                rad = 20 + (random.random() * 8) # Big cells
            else:
                rad = 4 + (random.random() * 18) # Everything else
            ang = random.random() * 2 * math.pi
            x = Consts["WORLD_X"] * random.random()
            y = Consts["WORLD_Y"] * random.random()
            cell = Cell([x, y], [(random.random() - 0.5) * 0.35, (random.random() - 0.5) * 0.35], rad)
            self.cells.append(cell)

    def save_game(self):
        pass

    def game_over(self, loser):
        self.result = True
        print("Player {} dead".format(loser))

    def eject(self, player, theta):
        if player.dead:
            return
        # Reduce force in proportion to area
        fx = math.sin(theta)
        fy = math.cos(theta)
        # Push player
        new_veloc_x = player.veloc[0] + Consts["DELTA_VELOC"] * fx * (1 - Consts["EJECT_MASS_RATIO"])
        new_veloc_y = player.veloc[1] + Consts["DELTA_VELOC"] * fy * (1 - Consts["EJECT_MASS_RATIO"])
        player.veloc[0] -= Consts["DELTA_VELOC"] * fx * Consts["EJECT_MASS_RATIO"]
        player.veloc[1] -= Consts["DELTA_VELOC"] * fy * Consts["EJECT_MASS_RATIO"]
        # Shoot off the expended mass in opposite direction
        newrad = player.radius * Consts["EJECT_MASS_RATIO"] ** 0.5
        # Lose some mass (shall we say, Consts["EJECT_MASS_RATIO"]?)
        player.radius *= (1 - Consts["EJECT_MASS_RATIO"]) ** 0.5
        new_pos_x = player.pos[0] + fx * (player.radius + newrad)
        new_pos_y = player.pos[1] + fy * (player.radius + newrad)
        newcell = Cell([new_pos_x, new_pos_y], [new_veloc_x, new_veloc_y], newrad)
        newcell.stay_in_bounds()
        newcell.limit_speed()
        self.cells.append(newcell)

    def absorb(self, collision):
        # Calculate total momentum and mass
        mass = sum(self.cells[ele].area() for ele in collision)
        px = sum(self.cells[ele].area() * self.cells[ele].veloc[0] for ele in collision)
        py = sum(self.cells[ele].area() * self.cells[ele].veloc[1] for ele in collision)
        # Determine the biggest cell
        collision.sort(key = lambda ele: self.cells[ele].radius)
        biggest = collision.pop()
        self.cells[biggest].radius = (mass / math.pi) ** 0.5
        self.cells[biggest].veloc[0] = px / mass
        self.cells[biggest].veloc[1] = py / mass
        for ele in collision:
            self.cells[ele].dead = True
            # If we just killed the player, Game over
            if self.cells[ele].isplayer:
                self.game_over(ele)

    def update(self, frame_delta):
        # Save
        self.save_game()
        # New frame
        for cell in self.cells:
            if not cell.dead:
                cell.move(frame_delta)
        # Detect collisions
        collisions = []
        for i in range(len(self.cells)):
            if self.cells[i].dead:
                continue
            for j in range(i + 1, len(self.cells)):
                if not self.cells[j].dead and self.cells[i].collide(self.cells[j]):
                    if self.cells[i].collide_group == None == self.cells[j].collide_group:
                        self.cells[i].collide_group = self.cells[j].collide_group = len(collisions)
                        collisions.append([i, j])
                    elif self.cells[i].collide_group != None == self.cells[j].collide_group:
                        collisions[self.cells[i].collide_group].append(j)
                        self.cells[j].collide_group = self.cells[i].collide_group
                    elif self.cells[i].collide_group == None != self.cells[j].collide_group:
                        collisions[self.cells[j].collide_group].append(i)
                        self.cells[i].collide_group = self.cells[j].collide_group
                    elif self.cells[i].collide_group != self.cells[j].collide_group:
                        collisions[self.cells[i].collide_group] += collisions[self.cells[j].collide_group]
                        for ele in collisions[self.cells[j].collide_group]:
                            self.cells[ele].collide_group = self.cells[i].collide_group
                        collisions[self.cells[j].collide_group] = []
        # Run absorbs
        for collision in collisions:
            if collision != []:
                self.absorb(collision)
        # Eject!
        theta0 = self.player0.strategy(0, self.cells.copy())
        theta1 = self.player1.strategy(1, self.cells.copy())
        if theta0:
            self.eject(self.cells[0], theta0)
        if theta1:
            self.eject(self.cells[1], theta1)
