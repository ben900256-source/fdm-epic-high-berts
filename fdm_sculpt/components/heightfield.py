"""Original seeded scalar terrain fields, sampled without Blender or imported maps.

Uses the same class of technique as BaseForge: continuous multi-scale noise and
warped waves sampled onto a surface. No BaseForge code or generated assets.
"""
import hashlib
import math


def smooth(t):
    t = max(0., min(1., t))
    return t*t*t*(t*(t*6-15)+10)


def noise_function(seed):
    cache = {}

    def lattice(i,j):
        key = i,j
        if key not in cache:
            raw = hashlib.blake2s(f'{seed}:{i}:{j}'.encode(),digest_size=4).digest()
            cache[key] = int.from_bytes(raw,'little')/4294967295
        return cache[key]

    def noise(x,y):
        i,j = math.floor(x),math.floor(y)
        u,v = smooth(x-i),smooth(y-j)
        lower = lattice(i,j)*(1-u)+lattice(i+1,j)*u
        upper = lattice(i,j+1)*(1-u)+lattice(i+1,j+1)*u
        return lower*(1-v)+upper*v
    return noise


def field_function(style,scale,density,seed):
    noise = noise_function(seed)

    def layered(x,y):
        value,weight,total = 0.,1.,0.
        for octave in range(5):
            value += weight*noise(x,y)
            total += weight
            x,y = 1.67*x-1.11*y+19.3,1.11*x+1.67*y-7.8
            weight *= .47
        return value/total

    def field(x,y):
        x,y = x/scale*math.sqrt(density),y/scale*math.sqrt(density)
        ground = layered(x,y)
        if style=='soil':
            return ground
        if style=='sand':
            warp = 1.8*(noise(x*.32+6,y*.32-9)-.5)
            phase = 2*math.pi*(.82*x+.57*y)+warp
            ripple = (.5+.5*math.cos(phase))**1.7
            return .08+.78*ripple*(.75+.25*noise(x*.4,y*.4))+.08*ground
        if style=='rocky':
            ridge = 1-abs(2*layered(x*.7,y*.7)-1)
            return .1+.9*ridge**2.8
        if style=='meadow':
            clumps = smooth((noise(x*1.3,y*1.3)-.3)/.4)
            blades = (.5+.5*math.sin(11*x+2*noise(x,y)))**5
            return .24*ground+.65*clumps*blades
        raise ValueError('unknown heightfield style')
    return field


def sample_surface(*,width,length,style,feature_scale,relief_height,density,seed,boots,spacing=.065):
    if type(spacing) not in (int,float) or not math.isfinite(spacing) or spacing<=0:
        raise ValueError('sample spacing must be finite and positive')
    step = min(spacing,feature_scale/(18*math.sqrt(density)))
    nx,ny = max(1,math.ceil(width/step)),max(1,math.ceil(length/step))
    if (nx+1)*(ny+1)>500000:
        raise ValueError('heightfield exceeds 500000 samples')
    field = field_function(style,feature_scale,density,seed)
    heights = []
    pad = math.hypot(width/nx,length/ny)
    for j in range(ny+1):
        y = -length/2+length*j/ny
        row = []
        for i in range(nx+1):
            x = -width/2+width*i/nx
            height = relief_height*field(x,y)
            influence = 1.
            for x0,y0,x1,y1 in boots:
                distance = math.hypot(max(x0-x,0,x-x1),max(y0-y,0,y-y1))
                influence = min(influence,smooth((distance-pad)/.3))
            height = min(height,.012)+(max(0,height-.012))*influence
            row.append(round(height,7))
        heights.append(row)
    return dict(width=width,length=length,bottom=-.15,heights=heights)


def validate_grid(grid):
    for key in ('width','length'):
        value=grid[key]
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
            raise ValueError('invalid heightfield footprint')
    rows=grid['heights']
    bottom=grid['bottom']
    if type(bottom) not in (int,float) or not math.isfinite(bottom):
        raise ValueError('invalid heightfield bottom')
    if len(rows)<2 or len(rows[0])<2 or len(rows)*len(rows[0])>500000:
        raise ValueError('invalid heightfield grid dimensions')
    for row in rows:
        if len(row)!=len(rows[0]) or any(type(h) not in (int,float) or not math.isfinite(h) or h<=bottom for h in row):
            raise ValueError('invalid heightfield height')


def grid_mesh(grid):
    """Deterministic closed shell; top, bottom and walls share boundary vertices."""
    validate_grid(grid)
    rows=grid['heights']; nx,ny=len(rows[0])-1,len(rows)-1
    vertices=[(-grid['width']/2+grid['width']*i/nx,
               -grid['length']/2+grid['length']*j/ny,rows[j][i])
              for j in range(ny+1) for i in range(nx+1)]
    n=len(vertices)
    vertices += [(x,y,grid['bottom']) for x,y,z in vertices]
    top=[]; bottom=[]
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;b=a+1;c=a+nx+1;d=c+1
            top.extend([(a,b,d),(a,d,c)])
            bottom.extend([(n+a,n+d,n+b),(n+a,n+c,n+d)])
    rim = (list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+
           [ny*(nx+1)+i for i in range(nx-1,-1,-1)]+
           [j*(nx+1) for j in range(ny-1,0,-1)])
    walls=[]
    for a,b in zip(rim,rim[1:]+rim[:1]):
        walls.extend([(a,n+a,n+b),(a,n+b,b)])
    return vertices,top+bottom+walls,len(top)
