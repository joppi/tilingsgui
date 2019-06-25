import pygame, sys
from permuta import Perm
from permuta.misc import DIR_NONE, DIR_NORTH, DIR_SOUTH, DIR_WEST, DIR_EAST
from tilings import Tiling, Obstruction, Requirement, GriddedPerm
from tilescopethree.strategies.inferral_strategies.row_and_column_separation import row_and_column_separation as real_row_and_col_sep
from tilescopethree.strategies.equivalence_strategies.point_placements import place_point_of_requirement
from pygame.locals import *
from pygame import draw

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000

def gridded_perm_initial_locations(gp, gridsz, cellsz):
    colcount = [0]*gridsz[0]
    rowcount = [0]*gridsz[1]
    col = [[] for i in range(gridsz[0])]
    row = [[] for i in range(gridsz[1])]
    locs = []
    for ind in range(len(gp)):
        cx,cy = gp.pos[ind]
        colcount[cx]+=1
        rowcount[cy]+=1
        col[cx].append(ind)
        row[cy].append(gp.patt[ind])
    for r in row:
        r.sort()
    for ind in range(len(gp)):
        val = gp.patt[ind]
        cx,cy = gp.pos[ind]
        locx = cx*cellsz[0] + cellsz[0]*(col[cx].index(ind)+1)//(colcount[cx]+1)
        locy = cy*cellsz[1] + cellsz[1]*(row[cy].index(val)+1)//(rowcount[cy]+1)
        locs.append([locx, locy])
    return locs

def draw_gridded_perm(Surface, locs, color, radius, lines=False):
    for i in range(len(locs)):
        draw.circle(Surface, color, locs[i], radius)
        if lines and len(locs) > 1:
            draw.lines(Surface, color, False, locs, radius//2)

def distsq(v, w):
    return (w[0]-v[0])**2 + (w[1]-v[1])**2

class TilingDrawing(object):
    def __init__(self, tiling, rect):
        self.tiling = tiling
        tw, th = self.tiling.dimensions
        self.obstruction_locs = [gridded_perm_initial_locations(gp, (tw, th), (SCREEN_WIDTH//tw, SCREEN_HEIGHT//th)) for gp in self.tiling.obstructions]
        self.requirement_locs = [[gridded_perm_initial_locations(gp, (tw, th), (SCREEN_WIDTH//tw, SCREEN_HEIGHT//th)) for gp in reqlist] for reqlist in self.tiling.requirements]
        self.rect = rect

    def draw(self, Surface):
        GRID_COLOR = (0,0,0)
        OBS_COLOR = (255,0,0)
        REQ_COLOR = (0,0,255)
        HIGHLIGHTED_COLOR = (0,255,0)
        RAD = 5
        THICK = 3
        tw, th = self.tiling.dimensions
        for i in range(tw):
            x = self.rect.left + self.rect.width*i//tw
            draw.line(Surface, GRID_COLOR, (x, self.rect.bottom), (x, self.rect.top), THICK)
        for i in range(th):
            y = self.rect.top + self.rect.height*i//th
            draw.line(Surface, GRID_COLOR, (self.rect.left, y), (self.rect.right, y), THICK)
        for loc in self.obstruction_locs:
            draw_gridded_perm(Surface, loc, OBS_COLOR, RAD, True)
        for reqlist in self.requirement_locs:
            for loc in reqlist:
                draw_gridded_perm(Surface, loc, REQ_COLOR, RAD, True)

    def get_cell(self, mpos):
        tw,th = self.tiling.dimensions
        cw,ch = self.rect.width//tw, self.rect.height//th
        mx,my = mpos[0]-self.rect.left, mpos[1]-self.rect.top
        my = self.rect.height-my
        cx,cy = mx//cw,my//ch
        return (cx, cy)

    def get_point_obs_index(self, mpos):
        mx,my = mpos[0]-self.rect.left, mpos[1]-self.rect.top
        my = self.rect.height-my
        for j,loc in enumerate(self.obstruction_locs):
            for k,v in enumerate(loc):
                if distsq((mx,my), v) <= 100:
                    return (j,k)

    def get_point_req_index(self, mpos):
        mx,my = mpos[0]-self.rect.left, mpos[1]-self.rect.top
        my = self.rect.height-my
        for i,reqlist in enumerate(self.requirement_locs):
            for j,loc in enumerate(reqlist):
                for k,v in enumerate(loc):
                    if distsq((mx,my), v) <= 100:
                        print("MOUSE: ", mx, my)
                        print("REQ:   ", v[0], v[1])
                        print(distsq((mx, my), v))
                        return (i,j,k)

#def draw_gridded_perm(Surface, gp, color, pos, gridsz, cellsz, radius, lines=False):
#    locs = gridded_perm_initial_locations(gp, gridsz, cellsz)
#    for i in range(len(gp)):
#        draw.circle(Surface, color, locs[i], radius)
#        if lines and len(gp) > 1:
#            draw.lines(Surface, color, False, locs, radius//2)

def draw_tiling(Surface, tiling, rect):
    BLACK = (0,0,0)
    RED = (255,0,0)
    GREEN = (0,0,255)
    RAD = 10
    THICK = 5
    tw, th = tiling.dimensions
    for i in range(tw):
        x = rect.left + rect.width*i//tw
        draw.line(Surface, BLACK, (x, rect.bottom), (x, rect.top), THICK)
    for i in range(th):
        y = rect.top + rect.height*i//th
        draw.line(Surface, BLACK, (rect.left, y), (rect.right, y), THICK)
    for obs in tiling.obstructions:
        draw_gridded_perm(Surface, obs, RED, (rect.left, rect.top), (tw, th), (rect.width//tw, rect.height//th), RAD, True)
    for reqlist in tiling.requirements:
        for req in reqlist:
            draw_gridded_perm(Surface, req, GREEN, (rect.left, rect.top), (tw, th), (rect.width//tw, rect.height//th), RAD, True)

def cell_insertion(t):
    cx,cy = t.get_cell(pygame.mouse.get_pos())
    lb,mb,rb = pygame.mouse.get_pressed()
    if lb and not mb and not rb:
        return t.tiling.add_single_cell_requirement(Perm((0,)), (cx, cy))
    elif not lb and not mb and rb:
        return t.tiling.add_single_cell_obstruction(Perm((0,)), (cx, cy))


def row_and_col_separation(t):
    lb,mb,rb = pygame.mouse.get_pressed()
    if lb and not mb and not rb:
        x = real_row_and_col_sep(t.tiling)
        if x:
            return x.comb_classes[0]

def place_point(t, force_dir=DIR_NONE):
    lb,mb,rb = pygame.mouse.get_pressed()
    if lb and not mb and not rb:
        ind = t.get_point_req_index(pygame.mouse.get_pos())
        if ind == None:
            return
        return place_point_of_requirement(t.tiling, ind[0], ind[2], force_dir)

def factor(t):
    facs,maps = t.tiling.find_factors(regions=True)
    c = t.get_cell(pygame.mouse.get_pos())
    for i in range(len(facs)):
        if c in maps[i]:
            return facs[i]

def place_point_south(t):
    return place_point(t, DIR_SOUTH)
def place_point_north(t):
    return place_point(t, DIR_NORTH)
def place_point_west(t):
    return place_point(t, DIR_WEST)
def place_point_east(t):
    return place_point(t, DIR_EAST)


def main():
    #Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Tilings GUI')

    #Create The Backgound
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((255, 255, 255))
    
    """
    #Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 36)
        text = font.render("Time for binary arithmetic", 1, (240, 10, 10))
        textpos = text.get_rect(centerx=background.get_width()/2)
        background.blit(text, textpos)
    """

    #Tiling
    t = Tiling.from_string(sys.argv[1])
    trect = Rect(0, 0, background.get_width(), background.get_height())
    
    #Strats
    stck = [TilingDrawing(t,trect)]
    empty_stack = [t.is_empty()]
    t = stck[0]
    strats = [cell_insertion, 
              row_and_col_separation,
              place_point_north,
              place_point_south,
              place_point_east,
              place_point_west,
              factor]
    cur_strat = 0
    
    #Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()
    

    #Prepare Game Objects
    clock = pygame.time.Clock()
    going = True
    while going:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                going = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                going = False
            elif event.type == KEYDOWN and event.key == K_LEFT:
                cur_strat -= 1
            elif event.type == KEYDOWN and event.key == K_RIGHT:
                cur_strat += 1
            elif event.type == KEYDOWN and event.key == K_BACKSPACE:
                if len(stck) > 1:
                    stck.pop()
                    empty_stack.pop()
                    t = stck[-1]
            elif event.type == KEYDOWN and event.key == K_SPACE:
                mpos = pygame.mouse.get_pos()
                print(t.get_cell(mpos))
                print(t.get_point_obs_index(mpos))
                print(t.get_point_req_index(mpos))
            elif event.type == MOUSEBUTTONDOWN:
                try:
                    stck.append(TilingDrawing(strats[cur_strat](t), trect))
                    empty_stack.append(stck[-1].tiling.is_empty())
                except Exception as e:
                    print(e)
                t = stck[-1]
            elif event.type == MOUSEBUTTONUP:
                pass

        cur_strat = cur_strat % len(strats)
        pygame.display.set_caption('Tilings GUI - empty: ' + str(empty_stack[-1]) + " - strat: " + strats[cur_strat].__name__)
        background.fill((255, 255, 255))
        t.draw(background)
        flipped = pygame.transform.flip(background, False, True)
        screen.blit(flipped, (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()