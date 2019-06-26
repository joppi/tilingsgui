import math, pyglet, sys
from permuta import Perm
from permuta.misc import DIR_NONE, DIR_NORTH, DIR_SOUTH, DIR_WEST, DIR_EAST
from tilings import Tiling, Obstruction, Requirement, GriddedPerm
from tilescopethree.strategies.inferral_strategies.row_and_column_separation import row_and_column_separation as real_row_and_col_sep
from tilescopethree.strategies.inferral_strategies.obstruction_transitivity import obstruction_transitivity as real_obs_trans
from tilescopethree.strategies.inferral_strategies.subobstruction_inferral import empty_cell_inferral as real_empty_cell_inferral
from tilescopethree.strategies.equivalence_strategies.point_placements import place_point_of_requirement

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
SHADING = True
PRETTY_POINTS = True

window = pyglet.window.Window(height=SCREEN_HEIGHT,
                              width=SCREEN_WIDTH)


def fill_background(color):
    cols = [x/255.0 for x in color]
    cols.append(1)
    pyglet.gl.glClearColor(*cols)
    window.clear()

def draw_circle(pos, r, color=[0,0,0]):
    N = 30
    x,y = pos
    verts = [x, y]
    cols = color*(N+2)
    for i in range(N+1):
        ang = 2*math.pi*i/N
        verts.append(x+math.cos(ang)*r)
        verts.append(y+math.sin(ang)*r)
    pyglet.graphics.draw(N+2,
                         pyglet.gl.GL_TRIANGLE_FAN,
                         ('v2f', verts),
                         ('c3B', cols))

def draw_line_segment(p1, p2, color=[0,0,0]):
    N = 2
    x1,y1 = p1
    x2,y2 = p2
    verts = [x1, y1, x2, y2]
    cols = color*N
    pyglet.graphics.draw(N,
                         pyglet.gl.GL_LINE_STRIP,
                         ('v2f', verts),
                         ('c3B', cols))

def draw_segment_array(locs, color=[0,0,0]):
    verts = []
    N = len(locs)
    cols = color*N
    for i in range(N):
        verts.append(locs[i][0])
        verts.append(locs[i][1])
    pyglet.graphics.draw(N,
                         pyglet.gl.GL_LINE_STRIP,
                         ('v2f', verts),
                         ('c3B', cols))

def draw_filled_rectangle(loc, sz, color=[0,0,0]):
    x,y = loc
    w,h = sz
    N = 4
    verts = [x,y,x,y+h,x+w,y,x+w,y+h]
    cols = color * N
    pyglet.graphics.draw(N,
                         pyglet.gl.GL_TRIANGLE_STRIP,
                         ('v2f', verts),
                         ('c3B', cols))

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
        locs.append((locx, locy))
    return locs

def draw_gridded_perm(locs, radius, color, lines=False):
    for i in range(len(locs)):
        draw_circle(locs[i], radius, color)
        if lines and len(locs) > 1:
            draw_segment_array(locs, color)

def distsq(v, w):
    return (w[0]-v[0])**2 + (w[1]-v[1])**2

class TilingDrawing(object):
    def __init__(self, tiling, x, y, w, h):
        self.tiling = tiling
        tw, th = self.tiling.dimensions
        self.obstruction_locs = [gridded_perm_initial_locations(gp, (tw, th), (SCREEN_WIDTH//tw, SCREEN_HEIGHT//th)) for gp in self.tiling.obstructions]
        self.requirement_locs = [[gridded_perm_initial_locations(gp, (tw, th), (SCREEN_WIDTH//tw, SCREEN_HEIGHT//th)) for gp in reqlist] for reqlist in self.tiling.requirements]
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def cell_to_rect(self, c):
        cx, cy = c
        tw, th = self.tiling.dimensions
        cw, ch = self.w/tw, self.h/th
        return ((self.x+cx*cw, self.y+cy*ch), (cw, ch))

    def draw_shaded_cells(self):
        SHADING_COLOR = (127,127,127)
        for c in self.tiling.empty_cells:
            draw_filled_rectangle(*self.cell_to_rect(c), SHADING_COLOR)

    def draw_point_cells(self):
        POINT_COLOR = (0,0,0)
        RAD = 10
        for c in self.tiling.point_cells:
            pos,sz = self.cell_to_rect(c)
            x,y = pos
            w,h = sz
            draw_circle((x+w/2, y+h/2), RAD, POINT_COLOR)

    def draw(self):
        GRID_COLOR = (0,0,0)
        OBS_COLOR = (255,0,0)
        REQ_COLOR = (0,0,255)
        HIGHLIGHTED_COLOR = (0,255,0)
        RAD = 5
        THICK = 3
        tw, th = self.tiling.dimensions
        hover_index = None
        #hover_index = self.get_point_req_index(pygame.mouse.get_pos())
        if SHADING:
            self.draw_shaded_cells()
        if PRETTY_POINTS:
            self.draw_point_cells()
        for i in range(tw):
            x = self.x + self.w*i/tw
            draw_line_segment((x, self.y+self.h), (x, self.y), GRID_COLOR)
        for i in range(th):
            y = self.y + self.h*i/th
            draw_line_segment((self.x, y), (self.x+self.w, y), GRID_COLOR)
        for i,loc in enumerate(self.obstruction_locs):
            if SHADING and self.tiling.obstructions[i].is_point_obstr():
                continue
            if PRETTY_POINTS and any(p in self.tiling.point_cells for p in self.tiling.obstructions[i].pos):
                continue
            draw_gridded_perm(loc, RAD, OBS_COLOR, True)
        for i,reqlist in enumerate(self.requirement_locs):
            if PRETTY_POINTS and any(p in self.tiling.point_cells for req in self.tiling.requirements[i]
                                                                  for p in req.pos):
                continue
            col = HIGHLIGHTED_COLOR if hover_index != None and i == hover_index[0]else REQ_COLOR
            for loc in reqlist:
                draw_gridded_perm(loc, RAD, col, True)

    def get_cell(self, mpos):
        tw,th = self.tiling.dimensions
        cw,ch = self.w/tw, self.h/th
        mx,my = mpos[0]-self.x, mpos[1]-self.y
        cx,cy = int(mx/cw),int(my/ch)
        return (cx, cy)

    def get_point_obs_index(self, mpos):
        mx,my = mpos[0]-self.x, mpos[1]-self.y
        for j,loc in enumerate(self.obstruction_locs):
            for k,v in enumerate(loc):
                if distsq((mx,my), v) <= 100:
                    return (j,k)

    def get_point_req_index(self, mpos):
        mx,my = mpos[0]-self.x, mpos[1]-self.y
        for i,reqlist in enumerate(self.requirement_locs):
            for j,loc in enumerate(reqlist):
                for k,v in enumerate(loc):
                    if distsq((mx,my), v) <= 100:
                        return (i,j,k)


def cell_insertion(t, x, y, button, modifiers):
    cx,cy = t.get_cell((x,y))
    if button == pyglet.window.mouse.LEFT:
        return t.tiling.add_single_cell_requirement(Perm((0,)), (cx, cy))
    elif button == pyglet.window.mouse.RIGHT:
        return t.tiling.add_single_cell_obstruction(Perm((0,)), (cx, cy))



def place_point(t, x, y, button, modifiers, force_dir=DIR_NONE):
    if button == pyglet.window.mouse.LEFT:
        ind = t.get_point_req_index((x,y))
        if ind != None:
            return place_point_of_requirement(t.tiling, ind[0], ind[2], force_dir)

def factor(t, x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        facs,maps = t.tiling.find_factors(regions=True)
        c = t.get_cell((x,y))
        for i in range(len(facs)):
            if c in maps[i]:
                return facs[i]

def place_point_south(t, x, y, button, modifiers):
    return place_point(t, x, y, button, modifiers, DIR_SOUTH)
def place_point_north(t, x, y, button, modifiers):
    return place_point(t, x, y, button, modifiers, DIR_NORTH)
def place_point_west(t, x, y, button, modifiers):
    return place_point(t, x, y, button, modifiers, DIR_WEST)
def place_point_east(t, x, y, button, modifiers):
    return place_point(t, x, y, button, modifiers, DIR_EAST)

def row_and_col_separation(t, x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        x = real_row_and_col_sep(t.tiling)
        if x:
            return x.comb_classes[0]

def obstruction_transitivity(t, x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        x = real_obs_trans(t.tiling)
        if x:
            return x.comb_classes[0]


#def empty_cell_inferral(t):
#    lb,mb,rb = pygame.mouse.get_pressed()
#    if lb or mb or rb:
#        x = real_empty_cell_inferral(t.tiling)
#        if x and x.comb_classes[0] != t.tiling:
#            return x.comb_classes[0]

tiling_drawing = None

strats = [cell_insertion,
          place_point_north,
          place_point_south,
          place_point_west,
          place_point_east,
          factor,
          row_and_col_separation,
          obstruction_transitivity]
cur_strat = 0
stack = []

window.set_caption("Tilings GUI - strat: {}".format(strats[cur_strat].__name__))

@window.event
def on_mouse_press(x, y, button, modifiers):
    global tiling_drawing
    try:
        new_tiling = strats[cur_strat](tiling_drawing, x, y, button, modifiers)
        if new_tiling != None:
            tiling_drawing = TilingDrawing(new_tiling, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            stack.append(tiling_drawing)
    except Exception as e:
        raise e

@window.event
def on_key_press(symbol, modifiers):
    global cur_strat, tiling_drawing
    if symbol == pyglet.window.key.LEFT:
        cur_strat -= 1
        cur_strat %= len(strats)
        window.set_caption("Tilings GUI - strat: {}".format(strats[cur_strat].__name__))

    if symbol == pyglet.window.key.RIGHT:
        cur_strat += 1
        cur_strat %= len(strats)
        window.set_caption("Tilings GUI - strat: {}".format(strats[cur_strat].__name__))

    if symbol == pyglet.window.key.BACKSPACE:
        if len(stack) > 1:
            stack.pop()
            tiling_drawing = stack[-1]

def draw():
    if any(len(obs) == 0 for obs in tiling_drawing.tiling.obstructions):
        fill_background([127,127,127])
    else:
        fill_background([255,255,255])
        tiling_drawing.draw()

def update(time):
    pass

def main():
    global tiling_drawing
    start_tiling = Tiling.from_string(sys.argv[1])
    tiling_drawing = TilingDrawing(start_tiling, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    stack.append(tiling_drawing)

    @window.event
    def on_draw():
        draw()
        
    pyglet.clock.schedule_interval(update, 1/120.0)
    pyglet.app.run()

if __name__ == "__main__":
    main()