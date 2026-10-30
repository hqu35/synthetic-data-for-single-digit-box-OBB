"""Deterministic camera processing executed inside Blender, using bundled NumPy.

Only radiometry and subpixel blur change; crop, dimensions and coordinates are identity.
"""
import struct
import zlib
from pathlib import Path
import numpy as np


def read_png(path):
    data=Path(path).read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Not a PNG')
    offset=8;compressed=bytearray()
    while offset<len(data):
        length=struct.unpack('>I',data[offset:offset+4])[0]
        kind=data[offset+4:offset+8];body=data[offset+8:offset+8+length];offset+=12+length
        if kind==b'IHDR':width,height,depth,color,_,_,interlace=struct.unpack('>IIBBBBB',body)
        if kind==b'IDAT':compressed.extend(body)
    if depth!=8 or color!=2 or interlace!=0:raise ValueError('Camera processing expects noninterlaced 8-bit RGB PNG')
    raw=zlib.decompress(compressed);stride=width*3;previous=bytearray(stride);rows=[]
    for y in range(height):
        f=raw[y*(stride+1)];row=bytearray(raw[y*(stride+1)+1:(y+1)*(stride+1)])
        for x in range(stride):
            left=row[x-3] if x>=3 else 0;up=previous[x];ul=previous[x-3] if x>=3 else 0
            if f==1:predictor=left
            elif f==2:predictor=up
            elif f==3:predictor=(left+up)//2
            elif f==4:
                p=left+up-ul;dist=[abs(p-left),abs(p-up),abs(p-ul)];predictor=[left,up,ul][dist.index(min(dist))]
            elif f==0:predictor=0
            else:raise ValueError('Unknown PNG filter')
            row[x]=(row[x]+predictor)&255
        rows.append(bytes(row));previous=row
    return np.frombuffer(b''.join(rows),dtype=np.uint8).reshape(height,width,3).copy()


def write_png(path,rgb):
    height,width,_=rgb.shape
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\x00'+row.tobytes() for row in rgb)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+
                           chunk(b'sRGB',b'\x00')+chunk(b'IDAT',zlib.compress(rows,6))+chunk(b'IEND',b''))


def process_image(raw_path,final_path,params):
    encoded=read_png(raw_path).astype(np.float64)/255
    rgb=np.where(encoded<=.04045,encoded/12.92,((encoded+.055)/1.055)**2.4)
    gains=np.array(params['camera_white_balance'])*np.array(params['postprocess_color_cast'])
    rgb=rgb*gains*(2**params['camera_exposure'])
    rgb=(rgb-.18)*params['contrast']+.18
    sigma=params['blur_sigma_px']
    if sigma>0:
        radius=max(1,int(np.ceil(sigma*3)));x=np.arange(-radius,radius+1)
        kernel=np.exp(-.5*(x/sigma)**2);kernel/=kernel.sum()
        for axis in (0,1):
            pads=[(0,0)]*3;pads[axis]=(radius,radius)
            padded=np.pad(rgb,pads,mode='edge');out=np.zeros_like(rgb)
            for i,weight in enumerate(kernel):
                selection=[slice(None)]*3;selection[axis]=slice(i,i+rgb.shape[axis])
                out+=padded[tuple(selection)]*weight
            rgb=out
    if params['sensor_noise_std']:
        rng=np.random.default_rng(params['noise_seed'])
        rgb+=rng.normal(0,params['sensor_noise_std'],rgb.shape)
    clipped=float(np.mean((rgb<0)|(rgb>1)))
    rgb=np.clip(rgb,0,1)
    srgb=np.where(rgb<=.0031308,rgb*12.92,1.055*rgb**(1/2.4)-.055)
    write_png(final_path,np.rint(srgb*255).astype(np.uint8))
    params['clipped_channel_fraction']=clipped
    params['final_dimensions']=[int(rgb.shape[1]),int(rgb.shape[0])]
    if clipped>.03:raise ValueError('Camera appearance clips more than 3% of RGB channels')
