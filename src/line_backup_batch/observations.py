"""Typed perception boundaries. Artifact validity alone never certifies live pixels."""
import datetime as dt
import math
import re
import struct
import time
from line_backup_acceptance.project_binding import ProjectReader,dates,integer,sha
from .schema import require

def artifact(reader,ref):
    require(isinstance(ref,dict) and set(ref)=={'path','bytes','sha256'},'INVALID_ARTIFACT')
    require(ref['path'].startswith('harness-development/') and integer(ref['bytes'],1),'UNSAFE_ARTIFACT')
    raw,_=reader.read(ref['path'],'ARTIFACT_UNAVAILABLE')
    require(len(raw)==ref['bytes'] and sha(raw)==ref['sha256'],'ARTIFACT_DRIFT')
    return raw

def image_size(raw):
    if raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw)>=24:return struct.unpack('>II',raw[16:24])
    require(raw.startswith(b'\xff\xd8'),'UNSUPPORTED_FRAME')
    i=2
    while i+4<=len(raw):
        require(raw[i]==255,'INVALID_JPEG_FRAME')
        marker=raw[i+1];i+=2
        if marker==255:i-=1;continue
        if marker in (0xD8,0xD9) or 0xD0<=marker<=0xD7:continue
        size=int.from_bytes(raw[i:i+2],'big');require(size>=2 and i+size<=len(raw),'INVALID_JPEG_FRAME')
        if marker in (0xC0,0xC1,0xC2):return int.from_bytes(raw[i+5:i+7],'big'),int.from_bytes(raw[i+3:i+5],'big')
        i+=size
    require(False,'INVALID_FRAME_DIMENSIONS')

def fp(value):
    require(isinstance(value,dict) and set(value)=={'start_date','end_date','expected_images'},'ALBUM_IDENTITY')
    dates(value['start_date'],value['end_date'],'ALBUM_IDENTITY')
    require(integer(value['expected_images'],1),'ALBUM_COUNT')
    return value

def rect(value,width,height):
    require(isinstance(value,list) and len(value)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in value),'INVALID_BOUNDS')
    x,y,w,h=value;require(w>0 and h>0 and x>=0 and y>=0 and x+w<=width and y+h<=height,'BOUNDS_OUTSIDE_FRAME')
    return value

def inside(inner,outer,margin=0):
    x,y,w,h=inner;a,b,c,d=outer
    return x>=a+margin and y>=b+margin and x+w<=a+c-margin and y+h<=b+d-margin

def point(value,bounds,uncertainty):
    require(isinstance(value,list) and len(value)==2 and all(type(v) in (int,float) and math.isfinite(v) for v in value),'INVALID_POINT')
    require(inside([*value,0,0],bounds,uncertainty),'UNSAFE_POINT')
    return value

def frame(reader,record,cfg,*,session,now=None,max_age=5):
    required={'frame','frame_id','session_id','group_key','surface','captured_at','provider','layout_key',
        'window_id','pid','width','height','mapping','cards','boundary','editable_focus','occlusion'}
    require(isinstance(record,dict) and set(record)==required,'INVALID_OBSERVATION')
    require(record['session_id']==session and record['group_key']==cfg['group_key'],'CONTEXT_MISMATCH')
    require(record['provider']=='HOSTED_CUA' and record['surface'] in ('ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER'),'SURFACE_MISMATCH')
    require(record['occlusion']=='CLEAR' and record['editable_focus'] in ('NONE','LOW_GHOST'),'INPUT_SAFETY_UNKNOWN')
    require(integer(record['pid'],1) and integer(record['window_id'],1) and isinstance(record['layout_key'],str) and record['layout_key'],'WINDOW_IDENTITY')
    instant=dt.datetime.fromisoformat(record['captured_at'].replace('Z','+00:00'))
    require(instant.tzinfo is not None,'INVALID_CAPTURE_TIME')
    age=(dt.datetime.now(dt.timezone.utc) if now is None else now)-instant
    require(0<=age.total_seconds()<=max_age,'STALE_OBSERVATION')
    raw=artifact(reader,record['frame']);require(record['frame_id']==sha(raw),'FRAME_ID_MISMATCH')
    size=image_size(raw);require(size==(record['width'],record['height']),'FRAME_DIMENSIONS_MISMATCH')
    mapping=record['mapping']
    require(isinstance(mapping,dict) and set(mapping)=={'space','uncertainty','evidence','frame_id','layout_key'},'MAPPING_UNKNOWN')
    require(mapping['space']=='CUA_CAPTURE_PIXELS' and mapping['frame_id']==record['frame_id'] and mapping['layout_key']==record['layout_key'],'MAPPING_MISMATCH')
    require(type(mapping['uncertainty']) in (int,float) and math.isfinite(mapping['uncertainty']) and mapping['uncertainty']>=0,'MAPPING_UNKNOWN')
    artifact(reader,mapping['evidence'])
    seen=set();by_dates=set()
    require(isinstance(record['cards'],list),'INVALID_CARDS')
    for card in record['cards']:
        require(set(card)=={'fingerprint','title','metadata_bounds','card_bounds','fully_visible','safe_metadata_bounds','neighbor_bounds'},'INVALID_CARD')
        ident=fp(card['fingerprint']);key=tuple(ident.values());datekey=(ident['start_date'],ident['end_date'])
        require(key not in seen and datekey not in by_dates,'AMBIGUOUS_ALBUM_IDENTITY');seen.add(key);by_dates.add(datekey)
        require(card['title']==ident['start_date'].replace('-','/')+'～'+ident['end_date'][5:].replace('-','/'),'NON_DATE_TITLE')
        rect(card['metadata_bounds'],*size)
        if card['fully_visible'] is True:
            rect(card['card_bounds'],*size);rect(card['safe_metadata_bounds'],*size)
            require(inside(card['metadata_bounds'],card['card_bounds']) and inside(card['safe_metadata_bounds'],card['metadata_bounds'],mapping['uncertainty']),
                'CARD_METADATA_CROSS_PAIR')
            for neighbor in card['neighbor_bounds']:
                rect(neighbor,*size)
                a,b,c,d=card['safe_metadata_bounds'];x,y,w,h=neighbor
                require(a+c+mapping['uncertainty']<=x or x+w+mapping['uncertainty']<=a or b+d+mapping['uncertainty']<=y or y+h+mapping['uncertainty']<=b,
                    'NEIGHBOR_TARGET_OVERLAP')
        else:require(card['fully_visible'] is False,'CARD_VISIBILITY_UNKNOWN')
    return record

def card_target(reader,record,cfg,target,session,*,now=None):
    frame(reader,record,cfg,session=session,now=now)
    require(record['surface']=='ALBUMS','SURFACE_MISMATCH')
    cards=[c for c in record['cards'] if c['fingerprint']==target]
    require(len(cards)==1 and cards[0]['fully_visible'] is True,'CARD_NOT_FULLY_VISIBLE')
    b=cards[0]['safe_metadata_bounds'];p=[b[0]+b[2]/2,b[1]+b[3]/2]
    return point(p,b,record['mapping']['uncertainty'])

def catalog(reader,records,cfg,session,*,now=None):
    require(isinstance(records,list) and records,'EMPTY_CATALOG')
    identities=[];prior=None;context=None;seen_dates={}
    for i,record in enumerate(records):
        frame(reader,record,cfg,session=session,now=now,max_age=600)
        require(record['surface']=='ALBUMS' and record['cards'],'CATALOG_SURFACE')
        current=(record['session_id'],record['group_key'],record['pid'],record['window_id'],record['layout_key'])
        require(context is None or context==current,'COLLECTION_IDENTITY_DRIFT');context=current
        keys=[tuple(c['fingerprint'].values()) for c in record['cards']]
        if prior is not None:
            require(keys!=prior,'NO_COLLECTION_PROGRESS')
            require(any(prior[-k:]==keys[:k] for k in range(1,min(len(prior),len(keys))+1)),
                'COLLECTION_COVERAGE_GAP')
        for c in record['cards']:
            identity=c['fingerprint'];datekey=(identity['start_date'],identity['end_date'])
            if identity in identities:
                require(prior is not None and tuple(identity.values()) in prior,'REAPPEARED_AMBIGUOUS_IDENTITY')
            require(datekey not in seen_dates or seen_dates[datekey]==identity,'ALBUM_COUNT_DRIFT')
            seen_dates[datekey]=identity
            if identity not in identities:identities.append(identity)
        boundary=record['boundary']
        require(isinstance(boundary,dict) and set(boundary)=={'top','bottom','evidence'},'BOUNDARY_UNKNOWN')
        require(type(boundary['top']) is bool and type(boundary['bottom']) is bool,'BOUNDARY_UNKNOWN')
        artifact(reader,boundary['evidence'])
        if i==0:require(boundary['top'],'TOP_NOT_PROVEN')
        if i==len(records)-1:require(boundary['bottom'],'BOTTOM_NOT_PROVEN')
        prior=keys
    return identities
