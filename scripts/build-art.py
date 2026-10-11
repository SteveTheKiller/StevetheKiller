"""Render the profile's transparent collage artwork from the licensed brand fonts.

Example:
  python scripts/build-art.py --fonts "../code/Killer Branding/fonts" \
    --repos ../code --smiley path/to/smiley-03-ransom-face.png \
    --site-smiley path/to/smiley-01-slit-smile.png --output ./art-preview

Requires Pillow. Font files remain in the licensed branding library; only rendered
artwork is distributed by this repository. Output dimensions match the README assets.
The smiley inputs are PNG renderings of the site's named SVG files.
"""
import argparse
from pathlib import Path
import io
import math
import os

from PIL import Image, ImageDraw, ImageFont

S = 3
BONE = '#EDE6D3'
GREEN = '#0F380F'


def canvas(w, h):
    return Image.new('RGBA', (w * S, h * S))


def polygon(image, points, color):
    ImageDraw.Draw(image).polygon([(round(x*S), round(y*S)) for x,y in points], fill=color)


def ellipse(image, bounds, color, width=0):
    box = tuple(round(v*S) for v in bounds)
    d = ImageDraw.Draw(image)
    if width:
        d.ellipse(box, outline=color, width=round(width*S))
    else:
        d.ellipse(box, fill=color)


def place(image, layer, x, y, angle=0):
    if angle:
        old = layer.size
        layer = layer.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        x -= (layer.width-old[0])/(2*S)
        y -= (layer.height-old[1])/(2*S)
    image.alpha_composite(layer, (round(x*S), round(y*S)))


def text(fonts, words, face, height, color, max_width=None):
    path = str(fonts / face)
    probe = ImageFont.truetype(path, 200*S)
    cap = probe.getbbox('H')[3] - probe.getbbox('H')[1]
    font = ImageFont.truetype(path, round(200*S * height*S/cap))
    b = font.getbbox(words)
    ink = Image.new('RGBA', (b[2]-b[0]+4*S, b[3]-b[1]+4*S))
    ImageDraw.Draw(ink).text((2*S-b[0], 2*S-b[1]), words, font=font, fill=color)
    ink = ink.crop(ink.getbbox())
    if max_width and ink.width > max_width*S:
        factor = max_width*S/ink.width
        ink = ink.resize((round(ink.width*factor),round(ink.height*factor)),Image.Resampling.LANCZOS)
    return ink


def button_label(image, label, x, center_y, points):
    top_left, top_right, bottom_right, bottom_left = points
    top_slope = (top_right[1]-top_left[1])/(top_right[0]-top_left[0])
    bottom_slope = (bottom_right[1]-bottom_left[1])/(bottom_right[0]-bottom_left[0])
    angle = -math.degrees(math.atan((top_slope+bottom_slope)/2))
    place(image,label,x,center_y-label.height/(2*S),angle)


def paper(fonts, words, face, w, h, cap, bg, fg, shape):
    layer = canvas(w,h)
    polygon(layer, [(x*w,y*h) for x,y in shape],bg)
    ink = text(fonts,words,face,cap,fg,w-36)
    layer.alpha_composite(ink,((w*S-ink.width)//2,(h*S-ink.height)//2))
    return layer


def tape(image,x,y,w=92,h=24,angle=4):
    layer = canvas(w,h)
    polygon(layer,[(0,1),(w,0),(w-1,h),(1,h-1)],(220,210,170,200))
    polygon(layer,[(0,1),(w,0),(w,h/2),(0,h*.6)],(237,230,211,65))
    place(image,layer,x,y,angle)


def ring(image,x,y,diam,color,width=12,dashed=False):
    if not dashed:
        ellipse(image,(x,y,x+diam,y+diam),color,width)
        return
    d=ImageDraw.Draw(image)
    for a in range(0,360,36):
        d.arc(tuple(round(v*S) for v in (x,y,x+diam,y+diam)),a,a+25,fill=color,width=width*S)


def plus(image,x,y,size,color,angle):
    layer=canvas(size,size)
    polygon(layer,[(size*.35,0),(size*.65,0),(size*.65,size*.35),(size,size*.35),(size,size*.65),(size*.65,size*.65),(size*.65,size),(size*.35,size),(size*.35,size*.65),(0,size*.65),(0,size*.35),(size*.35,size*.35)],color)
    place(image,layer,x,y,angle)


def triangle(image,x,y,size,color,angle):
    layer=canvas(size,size)
    polygon(layer,[(size/2,0),(size,size),(0,size)],color)
    place(image,layer,x,y,angle)


def halftone(image,x,y,size,color):
    step=max(10,round(size/7))
    for a in range(0,size,step):
        for b in range(0,size,step):
            if (a-size/2)**2+(b-size/2)**2 < (size/2-3)**2:
                ellipse(image,(x+a,y+b,x+a+step*.8,y+b+step*.8),color)


def wave(image,x,y,w,color):
    points=[(round((x+t*w/100)*S),round((y+10*math.sin(t*math.pi/25))*S)) for t in range(101)]
    ImageDraw.Draw(image).line(points,fill=color,width=9*S,joint='curve')


def icon(path,height):
    with Image.open(path) as src:
        src=src.convert('RGBA')
        src=src.crop(src.getbbox())
        return src.resize((round(src.width*height*S/src.height),height*S),Image.Resampling.LANCZOS)


def save(image,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    final=image.resize((image.width//S,image.height//S),Image.Resampling.LANCZOS)
    stream=io.BytesIO()
    final.save(stream,format='PNG',optimize=True)
    if path.exists():
        path.read_bytes()
    temporary=path.with_suffix('.pending.png')
    temporary.write_bytes(stream.getvalue())
    os.replace(temporary,path)
    print(path.name,final.size,final.mode)


def header(fonts,smiley,out):
    image=canvas(2000,600)
    ring(image,56,48,140,'#e0a030',16)
    triangle(image,272,66,88,'#2f9e8f',14)
    plus(image,209,241,70,BONE,-12)
    ring(image,240,420,128,'#e76f51',13,True)
    halftone(image,384,476,112,'#3f8efc')
    wave(image,78,540,104,'#7bc950')
    layer=canvas(110,132)
    for a in range(-132,110,30):
        polygon(layer,[(a,0),(a+15,0),(a+147,132),(a+132,132)],'#8e5ba8')
    place(image,layer,65,349,8)
    layer=canvas(114,30)
    polygon(layer,[(0,0),(114,0),(114,30),(0,30)],BONE)
    place(image,layer,40,236,-24)
    ellipse(image,(320,188,344,212),BONE)
    ring(image,1797,44,151,BONE,15,True)
    halftone(image,1632,28,128,'#e63946')
    ellipse(image,(1596,191,1620,215),'#7bc950')
    layer=canvas(124,24)
    polygon(layer,[(0,0),(124,0),(124,24),(0,24)],'#3f8efc')
    place(image,layer,1830,213,16)
    wave(image,1686,320,103,'#e63946')
    triangle(image,1669,404,98,'#8e5ba8',-20)
    ring(image,1844,351,108,'#2f9e8f',16)
    plus(image,1584,525,57,'#e0a030',10)
    layer=canvas(58,58)
    polygon(layer,[(0,0),(58,0),(58,58),(0,58)],'#e76f51')
    place(image,layer,1860,513,-22)

    # The existing paper angles, colors, and positions form the profile lockup.
    layer=canvas(304,302)
    polygon(layer,[(0,0),(304,0),(302,302),(1,301)],BONE)
    layer.alpha_composite(icon(smiley,250),(27*S,26*S))
    place(image,layer,370,70,6)
    tape(image,436,51,138,30,14)
    shape=[(0,.05),(1,0),(.94,1),(.06,.94)]
    layer=paper(fonts,'STEVE','Lacquer-Regular.ttf',416,110,74,'#E8DFC8',GREEN,shape)
    place(image,layer,678,155,3)
    tape(image,837,151,92,24,7)
    layer=paper(fonts,'THE','Punktype.ttf',144,79,46,'#d9c96f',GREEN,[(.04,0),(1,.06),(.96,.96),(0,1)])
    place(image,layer,1075,156,-6)
    tape(image,1099,144,94,23,-9)
    layer=paper(fonts,'KILLER','Punktype.ttf',380,87,60,'#B01E1E',BONE,[(0,0),(.95,.04),(1,1),(.04,.95)])
    place(image,layer,1200,191,4)
    tape(image,1341,175,92,24,1)

    for words,x,y,w,color,angle in [('Technician',526,437,278,'#1a4a6a',3),('Tool Builder',838,456,312,'#277c70',-3),('MSP Veteran',1185,438,290,'#b55721',2)]:
        layer=paper(fonts,words,'KillerSans-Regular.ttf',w,64,34,color,BONE,shape)
        place(image,layer,x,y,angle)
        tape(image,x+w/2-43,y-12,86,24,angle+2)
    save(image,out/'header.png')


def notes(fonts,repos,smiley,out):
    rows=[
        ('killernotes','#793bab',BONE,'KillerNotes/notes-landing/kn-icon.png',[(78,39),(525,51),(505,119),(90,101)],180,310),
        ('killertools','#27cbbb',GREEN,'Killer Branding/og/killertools-icon.png',[(77,53),(521,38),(505,106),(92,114)],180,310),
        ('killendar','#b82b2b',BONE,'Killendar/killendar-landing/brand/kd-icon.png',[(97,39),(505,53),(486,121),(108,101)],197,273),
        ('killerpdf','#20c75c',GREEN,'KillerPDF-1.8/pdf-landing/kp-icon.png',[(97,54),(502,37),(486,106),(113,115)],201,280),
        ('killerscan','#ff9400',GREEN,'KillerScan/scan-landing/ks-icon.png',[(88,42),(514,51),(495,118),(99,103)],188,300),
        ('killershell','#2864c3',BONE,'KillerShell/shell-landing/brand/ksh-icon.png',[(76,57),(521,35),(505,104),(91,117)],177,305),
        ('killerbench','#EAD900',GREEN,'KillerBench/bench-landing/app-icon.png',[(80,42),(523,54),(507,119),(93,104)],182,310),
        ('thekiller',GREEN,BONE,smiley,[(83,57),(521,33),(505,104),(97,118)],184,310),
    ]
    for i,(name,bg,fg,source,points,tx,tw) in enumerate(rows):
        image=canvas(600,160)
        if i==0:
            ellipse(image,(56,20,72,36),'#7bc950'); plus(image,17,88,38,'#e0a030',-12); ring(image,538,14,55,'#e76f51',11,True)
        elif i==1:
            halftone(image,4,6,56,'#e63946'); wave(image,527,111,48,'#8e5ba8')
        elif i==2:
            triangle(image,27,97,38,'#3f8efc',16); ring(image,537,16,47,'#2f9e8f',10); plus(image,544,111,33,'#e0a030',-20)
        elif i==3:
            ring(image,13,73,58,'#e0a030',11,True); plus(image,555,20,34,'#e63946',10)
        elif i==4:
            wave(image,19,43,49,'#7bc950'); halftone(image,533,86,54,'#3f8efc')
        elif i==5:
            ring(image,17,85,45,'#e76f51',10); ellipse(image,(68,16,84,32),'#e0a030'); triangle(image,545,28,40,'#8e5ba8',-20)
        elif i==6:
            triangle(image,20,83,40,'#2f9e8f',12); halftone(image,535,17,48,'#e63946')
        else:
            ring(image,15,28,52,'#e0a030',10,True); plus(image,547,99,35,'#8e5ba8',-16)
        polygon(image,points,bg)
        badge=icon(repos/source,58)
        image.alpha_composite(badge,(round((points[0][0]+27)*S),44*S))
        label=text(fonts,name+'.net','KillerSans-Regular.ttf',35,fg,tw)
        button_label(image,label,tx,78,points)
        tape(image,254,30,92,24,3 if i%2 else 1)
        save(image,out/('note-'+name+'.png'))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fonts',required=True,type=Path)
    p.add_argument('--repos',required=True,type=Path)
    p.add_argument('--smiley',required=True,type=Path)
    p.add_argument('--site-smiley',required=True,type=Path,help='PNG rendering of smiley-01-slit-smile.svg')
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    if not args.smiley.exists():
        p.error('--smiley must point to the PNG rendering of the site smiley')
    header(args.fonts,args.smiley,args.output)
    notes(args.fonts,args.repos,args.site_smiley,args.output)
