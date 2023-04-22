import numpy as np
from math import sqrt
from PyQt5 import QtGui, QtCore, QtWidgets


class Board(QtWidgets.QFrame):
    SPEED = 80
    HEIGHTINBLOCKS = 10
    WIDTHINBLOCKS = 10

    def __init__(self, parent):
        super(Board, self).__init__(parent)

        self.enemies = np.array([], dtype=UFO)

        self.wizards = np.array([], dtype=Wizard)
        self.archers = np.array([], dtype=Archer)
        self.wizardsAttacks = np.zeros((10, 2, 2), dtype=int)   # for fireballs trajectories
        self.archersAttacks = np.zeros((10, 2, 2), dtype=int)   # for bows trajectories

        self.delay = 0  # counter of delay for towers fire and spawn of units

        self.land_tiles = np.array([], dtype=Landscape)
        self.roads = np.array([], dtype=Road)
        self.decor = np.array([], dtype=EnvironmentalTiles)

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self.timer = QtCore.QBasicTimer()

        self.castleHP = 1000
        self.castlePosition = np.array([100, 100], dtype=int)

        self.board_generation()

    def board_generation(self):
        for x in range(0, self.WIDTHINBLOCKS, 1):
            for y in range(0, self.HEIGHTINBLOCKS, 1):
                self.land_tiles = np.append(self.land_tiles, Landscape(np.array([x, y]), "spring", False))

    def enemy_spawn(self):
        pass

    @staticmethod
    def trajectory(coord):
        coord[1] += 2  # x = x; y += 2
        return coord

    def start(self):
        self.timer.start(Board.SPEED, self)

    def shelling(self):
        archer_num = 0  # index of archer tower
        for archer in self.archers:
            for enemy in self.enemies:
                if archer.in_range(enemy.position):
                    self.archersAttacks[archer_num] = [enemy.position, archer.position]
                    enemy.take_damage(archer.make_damage)
                    break
            archer_num += 1

        wizard_num = 0  # index of wizard tower
        for wizard in self.wizards:
            for enemy in self.enemies:
                if wizard.in_range(enemy.position):
                    self.wizardsAttacks[wizard_num] = [enemy.position, wizard.position]
                    enemy.take_damage(wizard.make_damage)
                    break
            wizard_num += 1

    def timerEvent(self, a0: QtCore.QTimerEvent) -> None:
        if a0.timerId() == self.timer.timerId():
            for enemy in self.enemies:
                enemy.move(self.trajectory(enemy.position))

            if self.delay % 5 == 0:
                self.shelling()

            if self.delay % 6 == 0:
                self.archersAttacks = np.zeros_like(self.archersAttacks)
                self.wizardsAttacks = np.zeros_like(self.wizardsAttacks)

            self.delay += 1

    def tile_width(self):
        return self.frameGeometry().width() / self.WIDTHINBLOCKS

    def tile_height(self):
        return self.frameGeometry().height() / self.HEIGHTINBLOCKS

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:

        painter = QtGui.QPainter(self)

        rect = self.contentsRect()

        board_top = rect.bottom() - self.frameGeometry().height()

        for enemy in self.enemies:
            coord = enemy.position
            self.draw_rect(painter, rect.left() + coord[0] * self.tile_width(),
                           board_top + coord[1] * self.tile_height(), enemy.skin)

        for archer in self.archers:
            coord = archer.position
            self.draw_rect(painter, rect.left() + coord[0] * self.tile_width(),
                           board_top + coord[1] * self.tile_height(), archer.skin)

        for wizard in self.wizards:
            coord = wizard.position
            self.draw_rect(painter, rect.left() + coord[0] * self.tile_width(),
                           board_top + coord[1] * self.tile_height(), wizard.skin)

        for land in self.land_tiles:
            coord = land.position
            self.draw_rect(painter, rect.left() + coord[0] * self.tile_width(),
                           board_top + coord[1] * self.tile_height(), land.skin)

        if self.delay % 5 == 0:  # if it's fire iteration
            for archer_line in self.archersAttacks:
                painter.drawLine(archer_line[0][0], archer_line[0][1], archer_line[1][0], archer_line[1][1])
            for wizard_line in self.wizardsAttacks:
                painter.drawLine(wizard_line[0][0], wizard_line[0][1], wizard_line[1][0], wizard_line[1][1])

    def draw_rect(self, painter, x, y, image):
        rect = QtCore.QRect(int(x), int(y), int(self.tile_width()), int(self.tile_height()))
        painter.drawImage(rect, image)


class Unit:
    def __init__(self, coord, level, skins, direction):
        self.position = coord
        self.level = level
        self.direction = direction  # direct one for UFOs and reverse (from castle) for warriors
        self.HP = 100
        self.skin = skins[level]

        self.velocity = level  # 1, 2, 3 pixel/iteration
        self.force = 20 * level  # 20, 40, 60 damage (for units and castle)

    def move(self, coord):
        self.position = coord

    def take_damage(self, value):
        self.HP -= value
        if self.HP <= 0:
            self.HP = 0

    def is_alive(self) -> bool:
        if self.HP == 0:
            return False
        else:
            return True

    def make_damage(self) -> int:
        return self.force


class Warrior(Unit):
    def __init__(self, coord, level):
        skins = [QtGui.QImage("Sprites/Towers/Barrack/warrior_level_1.png"),
                 QtGui.QImage("Sprites/Towers/Barrack/warrior_level_2.png"),
                 QtGui.QImage("Sprites/Towers/Barrack/warrior_level_3.png")]
        super().__init__(coord, level, skins, "inverse")


class UFO(Unit):
    def __init__(self, coord, level):
        skins = [QtGui.QImage("Sprites/UFO/UFO(1).png"),
                 QtGui.QImage("Sprites/UFO/UFO(2).png"),
                 QtGui.QImage("Sprites/UFO/UFO(3).png"),
                 QtGui.QImage("Sprites/UFO/UFO(4).png"),
                 QtGui.QImage("Sprites/UFO/UFO(5).png"),
                 QtGui.QImage("Sprites/UFO/UFO(6).png"),
                 QtGui.QImage("Sprites/UFO/UFO(7).png")]
        super().__init__(coord, level, skins, "direct")


class Tower:
    def __init__(self, coord, level, skins):    # skins is array of QImage
        self.position = coord
        self.level = level
        self.skins = skins
        self.skin = skins[level]
        self.range = 10 * level  # 10, 20, 30 pixels
        self.force = 20 * level  # 20, 40, 60 damage
        self.upgrade_cost = level * 50  # 50, 100, 150 coins

    def change_picture(self):  # change picture in order to level
        self.skin = self.skins[self.level]

    def level_up(self):
        self.level += 1
        self.range = 10 * self.level  # 10, 20, 30 pixels
        self.force = 20 * self.level  # 20, 40, 60 damage
        self.upgrade_cost = self.level * 50  # 50, 100, 150 coins
        self.change_picture()

    def in_range(self, coord) -> bool:  # return true if a particular unit in the tower's range
        dx = self.position[0] - coord[0]
        dy = self.position[1] - coord[1]
        distance = sqrt(dx ** 2 + dy ** 2)
        if distance <= self.range:
            return True
        else:
            return False

    def make_damage(self) -> int:
        return self.force

    def upgrade_cost(self) -> int:  # return upgrade cost
        return self.upgrade_cost


class Archer(Tower):
    def __init__(self, coord, level):
        skins = [QtGui.QImage("Sprites/Towers/Barrack/archer_level_1.png"),
                 QtGui.QImage("Sprites/Towers/Barrack/archer_level_2.png"),
                 QtGui.QImage("Sprites/Towers/Barrack/archer_level_3.png")]
        super().__init__(coord, level, skins)


class Wizard(Tower):
    def __init__(self, coord, level):
        skins = [QtGui.QImage("Sprites/Towers/Barrack/wizard_level_1.png"),
                 QtGui.QImage("Sprites/Towers/Barrack/wizard_level_2.png"),
                 QtGui.QImage("Sprites/Towers/Barrack/wizard_level_3.png")]
        super().__init__(coord, level, skins)


class Tile:
    def __init__(self, coord, skin):
        self.position = coord
        self.skin = skin


class Road(Tile):
    def __init__(self, coord, biome, tile_type):    # np.array(x, y) coord, str biome : {"spring", "winter", "desert"},
                                                    # str tile_type : {"left", "right", "right_top_crossroad",
                                                    # "right_bottom_crossroad", "left_top_crossroad",
                                                    # "left_bottom_crossroad",  "bottom_twist", "top_twist",
                                                    # "right_twist", "left_twist"}
        biome = biome.Title()
        skin = QtGui.QImage("Sprites/Road tiles/" + biome + "/" + tile_type + ".png")

        super().__init__(coord, skin)
        self.type = tile_type   # maybe will be needed


class Landscape(Tile):
    def __init__(self, coord, biome, tower_place):  # np.array(x, y) coord, str biome = {"spring", "winter", "desert"},
                                                    # bool tower_place
        desert_biome = [QtGui.QImage("Sprites/Landscape tiles/sand.png"),
                        QtGui.QImage("Sprites/Landscape tiles/buildingPlaceSand.png")]
        spring_biome = [QtGui.QImage("Sprites/Landscape tiles/grass.png"),
                        QtGui.QImage("Sprites/Landscape tiles/buildingPlaceGrass.png")]
        winter_biome = [QtGui.QImage("Sprites/Landscape tiles/snow.png"),
                        QtGui.QImage("Sprites/Landscape tiles/buildingPlaceSnow.png")]

        skin = QtGui.QImage()

        if biome == "desert":
            if tower_place:
                skin = desert_biome[1]
            else:
                skin = desert_biome[0]
        elif biome == "spring":
            if tower_place:
                skin = spring_biome[1]
            else:
                skin = spring_biome[0]
        elif biome == "winter":
            if tower_place:
                skin = winter_biome[1]
            else:
                skin = winter_biome[0]

        super().__init__(coord, skin)
        self.tower_place = tower_place


class EnvironmentalTiles(Tile):
    def __init__(self, coord, biome, tile_type):    # np.array(x, y) coord, str biome = {"spring", "winter", "desert"},
                                                    # int tile_type
        skin = QtGui.QImage("Sprites/Environment tiles/crystal(1).png")
        super().__init__(coord, skin)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.board = Board(self)
        self.setCentralWidget(self.board)
        self.setGeometry(100, 100, 1500, 1000)
        self.board.start()

        self.show()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MainWindow()
    MainWindow.show()
    sys.exit(app.exec_())
