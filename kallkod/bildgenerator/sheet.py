"""contact sheet of renders on the app tile background"""
import sys, pathlib
from PIL import Image, ImageDraw
def sheet(paths, out, cols=3, w=800, bg=(227,232,228), labels=None):
    ims=[Image.open(p).convert("RGBA") for p in paths]
    h=int(w*ims[0].size[1]/ims[0].size[0]); rows=(len(ims)+cols-1)//cols
    S=Image.new("RGB",(cols*w,rows*(h+18)),bg); dr=ImageDraw.Draw(S)
    for i,im in enumerate(ims):
        im=im.resize((w,h),Image.LANCZOS); t=Image.new("RGBA",im.size,bg+(255,)); t.alpha_composite(im)
        x=(i%cols)*w; y=(i//cols)*(h+18); S.paste(t.convert("RGB"),(x,y)); dr.text((x+6,y+h+3),(labels or [pathlib.Path(p).stem for p in paths])[i],fill=(40,40,40))
    S.save(out)
if __name__=="__main__":
    sheet(sys.argv[2:],sys.argv[1])
