"""Typed perception boundaries. Artifact validity alone never certifies live pixels."""
import datetime as dt
import itertools
import math
import os
from pathlib import Path
import re
import stat
import struct
import time
from line_backup_acceptance.project_binding import ProjectReader,dates,integer,sha,strict_json
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

def _support(reader,ref,record,cfg,*,now,max_age):
    raw=artifact(reader,ref);sidecar=strict_json(raw,'INVALID_SCK_SUPPORT')
    required={'version','provider','fixture','frame_id','session_id','pid','window_id','layout_key','captured_at',
        'sck_frame','ocr','native_binding','uncertainty_px','safe_margin_px','interactive_intersection_px'}
    require(isinstance(sidecar,dict) and set(sidecar)==required and sidecar['version']==1,'INVALID_SCK_SUPPORT')
    is_fixture=sidecar['fixture'] is True and sidecar['provider']=='FIXTURE_ONLY'
    fixture_root=Path(reader.root).is_relative_to(Path(__file__).resolve().parents[2]/'harness-development') and '/fixtures/' in reader.root
    require(is_fixture if fixture_root else sidecar['fixture'] is False and sidecar['provider']=='SCREEN_CAPTURE_KIT','SCK_PROVIDER_MISMATCH')
    for key in ('frame_id','session_id','pid','window_id','layout_key'):
        require(sidecar[key]==record[key],'SCK_BINDING_MISMATCH')
    support_time=dt.datetime.fromisoformat(sidecar['captured_at'].replace('Z','+00:00'))
    cua_time=dt.datetime.fromisoformat(record['captured_at'].replace('Z','+00:00'))
    require(support_time.tzinfo is not None and cua_time.tzinfo is not None
        and abs((support_time-cua_time).total_seconds())<=5,'SCK_CAPTURE_TIME_MISMATCH')
    age=(dt.datetime.now(dt.timezone.utc) if now is None else now)-support_time
    require(age.total_seconds()>=0 and (max_age is None or age.total_seconds()<=max_age),'STALE_SCK_SUPPORT')
    sck_raw=artifact(reader,sidecar['sck_frame']);sck_size=image_size(sck_raw)
    ocr=strict_json(artifact(reader,sidecar['ocr']),'INVALID_SCK_OCR')
    require(isinstance(ocr,dict) and set(ocr)=={'version','cua_frame_id','sck_frame_sha256','cua','sck'}
        and ocr['version']==1 and ocr['cua_frame_id']==record['frame_id']
        and ocr['sck_frame_sha256']==sha(sck_raw),'SCK_OCR_BINDING_MISMATCH')
    binding=sidecar['native_binding']
    bind_keys={'bundle_id','pid','window_id','display_id','cua_capture_bounds_points','sck_window_bounds_points',
        'display_bounds_points','cua_size_px','sck_size_px'}
    require(isinstance(binding,dict) and set(binding)==bind_keys and binding['bundle_id']==cfg['app_identifier']
        and binding['pid']==record['pid'] and binding['window_id']==record['window_id']
        and integer(binding['display_id'],1) and binding['cua_size_px']==[record['width'],record['height']]
        and binding['sck_size_px']==list(sck_size),'SCK_NATIVE_BINDING_MISMATCH')
    cua_bounds=binding['cua_capture_bounds_points'];window_bounds=binding['sck_window_bounds_points'];display=binding['display_bounds_points']
    for bounds in (cua_bounds,window_bounds,display):
        require(isinstance(bounds,list) and len(bounds)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in bounds)
            and bounds[2]>0 and bounds[3]>0,'SCK_NATIVE_BOUNDS')
    require(max(abs(cua_bounds[i]-window_bounds[i]) for i in range(4))<=1,'SCK_WINDOW_BOUNDS_DRIFT')
    dw,dh=display[2],display[3];sw,sh=sck_size
    scale_x=(cua_bounds[2]/record['width'])*(sw/dw);scale_y=(cua_bounds[3]/record['height'])*(sh/dh)
    offset_x=(cua_bounds[0]-display[0])*(sw/dw);offset_y=(cua_bounds[1]-display[1])*(sh/dh)
    cua_items=ocr['cua'];sck_items=ocr['sck']
    require(isinstance(cua_items,list) and isinstance(sck_items,list),'SCK_OCR_BINDING_MISMATCH')
    def index_items(items,width,height):
        indexed={}
        for item in items:
            require(isinstance(item,dict) and set(item)=={'text','confidence','candidate_count','bounds'}
                and isinstance(item['text'],str) and item['text'].strip()
                and type(item['confidence']) in (int,float) and 0<=item['confidence']<=1
                and integer(item['candidate_count'],1),'SCK_OCR_ITEM')
            box=rect(item['bounds'],width,height)
            indexed.setdefault(item['text'],[]).append((box[0]+box[2]/2,box[1]+box[3]/2))
        return indexed
    left=index_items(cua_items,record['width'],record['height']);right=index_items(sck_items,*sck_size)
    anchors=[]
    for text in sorted(set(left)&set(right)):
        if len(left[text])==len(right[text])==1:
            x,y=left[text][0];u,v=right[text][0]
            predicted=(scale_x*x+offset_x,scale_y*y+offset_y)
            residual=math.hypot(predicted[0]-u,predicted[1]-v)
            anchors.append((text,x,y,residual))
    require(len(anchors)>=3,'SCK_ANCHOR_COVERAGE')
    largest_area=0.0
    for a,b,c in itertools.combinations(anchors,3):
        area=abs((b[1]-a[1])*(c[2]-a[2])-(b[2]-a[2])*(c[1]-a[1]))/2
        largest_area=max(largest_area,area)
    require(largest_area/(record['width']*record['height'])>=0.02,'SCK_ANCHOR_DISTRIBUTION')
    require(max(a[3] for a in anchors)<=2,'SCK_TRANSFORM_RESIDUAL')
    uncertainty=sidecar['uncertainty_px'];margin=sidecar['safe_margin_px'];intersection=sidecar['interactive_intersection_px']
    require(type(uncertainty) in (int,float) and uncertainty>=2 and type(margin) in (int,float)
        and margin>=uncertainty+4,'SCK_SAFE_MARGIN')
    require(isinstance(intersection,list) and len(intersection)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in intersection)
        and intersection[2]>=16 and intersection[3]>=16,'SCK_INTERACTIVE_INTERSECTION')
    return dict(sidecar=sidecar,anchors=anchors,transform=[scale_x,0,0,scale_y,offset_x,offset_y],
        max_residual=max(a[3] for a in anchors),sck_size=sck_size)

def _grounding_evidence(reader,ref,record,support):
    """Bind live geometry and retained AX bytes to the exact classifier frame."""
    raw=artifact(reader,ref);envelope=strict_json(raw,'INVALID_GROUNDING_EVIDENCE')
    require(isinstance(envelope,dict) and set(envelope)=={'version','geometry','manifest','classifier'}
        and envelope.get('version')==1,'INVALID_GROUNDING_EVIDENCE')
    geometry_ref=envelope['geometry'];manifest_ref=envelope['manifest'];classifier_ref=envelope['classifier']
    evidence=strict_json(artifact(reader,geometry_ref),'INVALID_GROUNDING_EVIDENCE')
    required={'version','frame_id','session_id','surface','pid','window_id','layout_key','captured_at',
        'cua_capture_bounds_points','surface_bounds_px','ax_state','layout_signature','structure_sha256'}
    require(isinstance(evidence,dict) and set(evidence)==required and evidence['version']==1,
        'INVALID_GROUNDING_EVIDENCE')
    for key in ('frame_id','session_id','surface','pid','window_id','layout_key','captured_at'):
        require(evidence[key]==record[key],'GROUNDING_FRAME_MISMATCH')
    layout=evidence['layout_signature']
    layout_keys={'line_version','language','window_class','frame_width_px','frame_height_px','native_scale','structure_sha256'}
    require(isinstance(layout,dict) and set(layout)==layout_keys
        and all(isinstance(layout[key],str) and layout[key] for key in ('line_version','language','window_class'))
        and layout['frame_width_px']==record['width'] and layout['frame_height_px']==record['height']
        and type(layout['native_scale']) in (int,float) and math.isfinite(layout['native_scale'])
        and layout['native_scale']>0 and evidence['structure_sha256']==layout['structure_sha256'],
        'GROUNDING_LAYOUT_MISMATCH')
    from line_backup_acceptance.common import json_bytes
    require(sha(json_bytes(layout))==record['layout_key'],'GROUNDING_LAYOUT_KEY')
    bounds=evidence['cua_capture_bounds_points']
    require(isinstance(bounds,list) and len(bounds)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in bounds)
        and bounds[2]>0 and bounds[3]>0,'GROUNDING_NATIVE_BOUNDS')
    sidecar=support['sidecar'];binding=sidecar['native_binding']
    require(max(abs(bounds[i]-binding['cua_capture_bounds_points'][i]) for i in range(4))<=1,
        'GROUNDING_NATIVE_BOUNDS')
    surface=evidence['surface_bounds_px']
    require(isinstance(surface,list) and len(surface)==4 and all(type(v) in (int,float) and math.isfinite(v) for v in surface)
        and surface==sidecar['interactive_intersection_px'],'GROUNDING_SURFACE_BOUNDS')
    ax_ref=evidence['ax_state'];ax_raw=artifact(reader,ax_ref)
    require(ax_raw and len(ax_raw)<=16*1024*1024,'GROUNDING_AX_REQUIRED')
    ax=strict_json(ax_raw,'INVALID_GROUNDING_AX')
    ax_keys={'version','frame_id','session_id','pid','window_id','surface','focused_index','elements'}
    require(isinstance(ax,dict) and set(ax)==ax_keys and ax.get('version')==1
        and ax.get('frame_id')==record['frame_id'] and ax.get('session_id')==record['session_id']
        and ax.get('pid')==record['pid'] and ax.get('window_id')==record['window_id']
        and ax.get('surface')==record['surface'] and isinstance(ax.get('elements'),list),'GROUNDING_AX_BINDING')
    for element in ax['elements']:
        require(isinstance(element,dict) and set(element)=={'index','role','subrole','identifier','label','value','bounds_px','parent_index','enabled'}
            and type(element.get('index')) is int and element['index']>=0 and isinstance(element.get('role'),str)
            and isinstance(element.get('subrole'),str) and isinstance(element.get('identifier'),str)
            and isinstance(element.get('enabled'),bool)
            and (element.get('parent_index') is None or type(element.get('parent_index')) is int),
            'GROUNDING_AX_ELEMENT')
        rect(element.get('bounds_px'),record['width'],record['height'])
    manifest=strict_json(artifact(reader,manifest_ref),'INVALID_FRAME_SUPPORT_MANIFEST')
    manifest_keys={'version','producer','projectRoot','output','surface','pairFrameId','sckFrameId','sessionId','pid',
        'windowId','displayId','layoutKey','captureKind','includeMenuBar','sourceRectAbsent','imageWidthPx','imageHeightPx',
        'pointPixelScale','backingScaleFactor','contentRect','displayBounds','surfaceBoundsPx','anchorTexts',
        'maximumAnchorResidualPx','uncertaintyPx','safeMarginPx','interactiveIntersectionPx','geometryEvidence',
        'sckFrame','ocr','support','captureRecord','captureTiming'}
    require(isinstance(manifest,dict) and set(manifest)==manifest_keys and manifest.get('version')==1
        and manifest.get('producer')=='rev28ctl frame-support' and manifest.get('projectRoot')==reader.root
        and manifest.get('surface')==record['surface'] and manifest.get('pairFrameId')==record['frame_id']
        and manifest.get('sessionId')==record['session_id'] and manifest.get('pid')==record['pid']
        and manifest.get('windowId')==record['window_id'] and manifest.get('layoutKey')==record['layout_key']
        and manifest.get('geometryEvidence')==geometry_ref and manifest.get('support')==record['mapping']['sck_support']
        and manifest.get('surfaceBoundsPx')==evidence['surface_bounds_px']
        and manifest.get('includeMenuBar') is True and manifest.get('sourceRectAbsent') is True
        and manifest.get('captureKind')=='fullDisplayFrame','FRAME_SUPPORT_MANIFEST_BINDING')
    timing=manifest.get('captureTiming');capture_record=manifest.get('captureRecord')
    require(isinstance(capture_record,dict) and isinstance(timing,dict)
        and set(timing)=={'requestStartedAtISO8601','requestFinishedAtISO8601',
            'requestStartMonotonicNanoseconds','requestEndMonotonicNanoseconds'}
        and isinstance(timing.get('requestStartedAtISO8601'),str)
        and isinstance(timing.get('requestFinishedAtISO8601'),str)
        and type(timing.get('requestStartMonotonicNanoseconds')) is int
        and type(timing.get('requestEndMonotonicNanoseconds')) is int
        and timing['requestStartMonotonicNanoseconds']>=0
        and timing['requestEndMonotonicNanoseconds']>=timing['requestStartMonotonicNanoseconds']
        and capture_record.get('capturedAtISO8601')==timing['requestStartedAtISO8601']
        and capture_record.get('fullDisplayCaptureTiming')==timing,
        'FRAME_SUPPORT_CAPTURE_TIMING')
    sidecar=support['sidecar'];binding=sidecar['native_binding']
    require(manifest.get('sckFrameId')==sidecar['sck_frame']['sha256']
        and manifest.get('sckFrame')==sidecar['sck_frame'] and manifest.get('ocr')==sidecar['ocr']
        and manifest.get('displayId')==binding['display_id']
        and manifest.get('uncertaintyPx')==sidecar['uncertainty_px']
        and manifest.get('safeMarginPx')==sidecar['safe_margin_px']
        and manifest.get('displayBounds')==binding['display_bounds_points']
        and manifest.get('surfaceBoundsPx')==sidecar['interactive_intersection_px'],
        'FRAME_SUPPORT_WITNESS_BINDING')
    sck_raw=artifact(reader,manifest['sckFrame']);sck_dimensions=image_size(sck_raw)
    def cgrect(value):
        if isinstance(value,list) and len(value)==4:return value
        if isinstance(value,dict) and set(value)=={'x','y','width','height'}:
            return [value['x'],value['y'],value['width'],value['height']]
        if isinstance(value,dict) and set(value)=={'origin','size'}:
            origin=value['origin'];size=value['size']
            if isinstance(origin,dict) and isinstance(size,dict) and set(origin)=={'x','y'} and set(size)=={'width','height'}:
                return [origin['x'],origin['y'],size['width'],size['height']]
        return None
    witness=capture_record.get('fullDisplayWitness')
    display_bounds=manifest.get('displayBounds');content_rect=manifest.get('contentRect')
    require(isinstance(display_bounds,list) and len(display_bounds)==4
        and isinstance(content_rect,list) and len(content_rect)==4
        and all(type(v) in (int,float) and math.isfinite(v) for v in display_bounds+content_rect)
        and display_bounds[2]>0 and display_bounds[3]>0 and content_rect[2]>0 and content_rect[3]>0
        and type(manifest.get('pointPixelScale')) in (int,float) and math.isfinite(manifest['pointPixelScale'])
        and manifest['pointPixelScale']>0 and manifest.get('backingScaleFactor')==manifest.get('pointPixelScale')
        and type(manifest.get('imageWidthPx')) is int and manifest['imageWidthPx']>0
        and type(manifest.get('imageHeightPx')) is int and manifest['imageHeightPx']>0,
        'FRAME_SUPPORT_CAPTURE_WITNESS')
    require(isinstance(witness,dict) and witness.get('displayID')==manifest.get('displayId')
        and cgrect(witness.get('displayBoundsPoints'))==display_bounds
        and cgrect(witness.get('contentRectPoints'))==content_rect,
        'FRAME_SUPPORT_CAPTURE_WITNESS')
    dx,dy,dw,dh=display_bounds;cx,cy,cw,ch=content_rect
    expected_dimensions=(int(math.floor(dw*manifest['pointPixelScale']+0.5)),
        int(math.floor(dh*manifest['pointPixelScale']+0.5)))
    require(sck_dimensions==(manifest.get('imageWidthPx'),manifest.get('imageHeightPx'))
        and sck_dimensions==expected_dimensions
        and capture_record.get('imageWidthPx')==manifest.get('imageWidthPx')
        and capture_record.get('imageHeightPx')==manifest.get('imageHeightPx')
        and capture_record.get('imageSHA256')==manifest.get('sckFrameId')
        and capture_record.get('capturedAtISO8601')==timing['requestStartedAtISO8601']
        and capture_record.get('scale')==manifest.get('pointPixelScale')
        and capture_record.get('backingScaleFactor')==manifest.get('backingScaleFactor')
        and manifest['pointPixelScale']==manifest['backingScaleFactor']
        and witness.get('imageWidthPx')==manifest.get('imageWidthPx')
        and witness.get('imageHeightPx')==manifest.get('imageHeightPx')
        and witness.get('pointPixelScale')==manifest.get('pointPixelScale')
        and witness.get('backingScaleFactor')==manifest.get('backingScaleFactor')
        and witness.get('includeMenuBar') is True and witness.get('sourceRectAbsent') is True
        and cx<=dx and cy<=dy and cx+cw>=dx+dw and cy+ch>=dy+dh,
        'FRAME_SUPPORT_CAPTURE_WITNESS')
    try:
        start=dt.datetime.fromisoformat(timing['requestStartedAtISO8601'].replace('Z','+00:00'))
        finish=dt.datetime.fromisoformat(timing['requestFinishedAtISO8601'].replace('Z','+00:00'))
        cua=dt.datetime.fromisoformat(record['captured_at'].replace('Z','+00:00'))
    except (AttributeError,TypeError,ValueError):
        raise AcceptanceError('FRAME_SUPPORT_CAPTURE_TIMING','capture timing is invalid',4)
    require(timing['requestStartedAtISO8601'].endswith('Z') and timing['requestFinishedAtISO8601'].endswith('Z')
        and start.tzinfo is not None and finish.tzinfo is not None and start>=cua
        and finish>=start and (finish-cua).total_seconds()<=5
        and sidecar.get('captured_at')==timing['requestStartedAtISO8601']
        and abs((finish-start).total_seconds()
            -(timing['requestEndMonotonicNanoseconds']-timing['requestStartMonotonicNanoseconds'])/1_000_000_000)<=0.05,
        'FRAME_SUPPORT_CAPTURE_TIMING')
    ocr=strict_json(artifact(reader,manifest['ocr']),'INVALID_FRAME_SUPPORT_OCR')
    require(isinstance(ocr,dict) and set(ocr)=={'version','cua_frame_id','sck_frame_sha256','cua','sck'}
        and ocr.get('version')==1 and ocr.get('cua_frame_id')==record['frame_id']
        and ocr.get('sck_frame_sha256')==manifest.get('sckFrameId'),'FRAME_SUPPORT_OCR_BINDING')
    classifier=strict_json(artifact(reader,classifier_ref),'INVALID_CLASSIFIER_EVIDENCE')
    ckeys={'version','frame_id','session_id','ax_state_sha256','screenshot_sha256','cards','boundary',
        'structure_sha256','surface_structure','focus_evidence'}
    require(isinstance(classifier,dict) and set(classifier)==ckeys and classifier.get('version')==1
        and classifier.get('frame_id')==record['frame_id'] and classifier.get('session_id')==record['session_id']
        and classifier.get('ax_state_sha256')==sha(ax_raw) and classifier.get('screenshot_sha256')==record['frame_id']
        and classifier.get('structure_sha256')==evidence['structure_sha256']
        and isinstance(classifier.get('surface_structure'),list)
        and isinstance(classifier.get('cards'),list) and len(classifier['cards'])==len(record['cards']),
        'CLASSIFIER_EVIDENCE_BINDING')
    require(sha(json_bytes(classifier['surface_structure']))==classifier['structure_sha256'],'CLASSIFIER_LAYOUT_STRUCTURE')
    focus=strict_json(artifact(reader,classifier['focus_evidence']),'INVALID_CLASSIFIER_FOCUS_EVIDENCE')
    if record['editable_focus']=='NONE':
        require(focus==dict(version=1,frame_id=record['frame_id'],session_id=record['session_id'],kind='NONE',
            focused_index=ax.get('focused_index')),'CLASSIFIER_FOCUS_EVIDENCE')
    elif record['editable_focus']=='HIGH_EDITABLE':
        focused=[e for e in ax['elements'] if e['index']==ax.get('focused_index')]
        require(record['surface']=='FOLDER_CHOOSER' and len(focused)==1 and focused[0]['role']=='text field'
            and focused[0]['subrole']=='PathTextField' and focus==dict(version=1,frame_id=record['frame_id'],
                session_id=record['session_id'],kind='HIGH_EDITABLE',focused_index=focused[0]['index'],
                element_identifier=focused[0]['identifier']),'CLASSIFIER_FOCUS_EVIDENCE')
    else:
        require(False,'CLASSIFIER_FOCUS_EVIDENCE')
    boundary=classifier['boundary']
    require(isinstance(boundary,dict) and set(boundary)=={'top','bottom','evidence'}
        and boundary==record['boundary'],'CLASSIFIER_BOUNDARY_BINDING')
    boundary_proof=strict_json(artifact(reader,boundary['evidence']),'INVALID_CLASSIFIER_BOUNDARY')
    if record['surface']=='ALBUMS':
        require(isinstance(boundary_proof,dict) and set(boundary_proof)=={'version','frame_id','session_id','source',
            'indicator_index','minimum','maximum','value'} and boundary_proof.get('version')==1
            and boundary_proof.get('frame_id')==record['frame_id'] and boundary_proof.get('session_id')==record['session_id']
            and boundary_proof.get('source')=='AX_SCROLLBAR' and type(boundary_proof.get('indicator_index')) is int
            and all(type(boundary_proof.get(key)) in (int,float) and math.isfinite(boundary_proof[key])
                for key in ('minimum','maximum','value'))
            and boundary_proof['maximum']>boundary_proof['minimum']
            and boundary_proof['minimum']<=boundary_proof['value']<=boundary_proof['maximum'],
            'CLASSIFIER_BOUNDARY_EVIDENCE')
        indicator=[e for e in ax['elements'] if e['index']==boundary_proof['indicator_index']]
        require(len(indicator)==1 and indicator[0]['role']=='scroll bar'
            and indicator[0]['value']==boundary_proof['value']
            and boundary['top']==(boundary_proof['value']==boundary_proof['minimum'])
            and boundary['bottom']==(boundary_proof['value']==boundary_proof['maximum']),
            'CLASSIFIER_BOUNDARY_EVIDENCE')
    else:
        require(isinstance(boundary_proof,dict) and set(boundary_proof)=={'version','frame_id','session_id','source'}
            and boundary_proof==dict(version=1,frame_id=record['frame_id'],session_id=record['session_id'],source='NOT_APPLICABLE'),
            'CLASSIFIER_BOUNDARY_EVIDENCE')
    ocr_items=ocr['cua'];elements={e['index']:e for e in ax['elements']}
    for card,witness in zip(record['cards'],classifier['cards']):
        wkeys={'fingerprint','title','card_bounds','metadata_bounds','safe_metadata_bounds','neighbor_bounds',
            'thumbnail_bounds','title_ocr','count_ocr','card_ax_index','thumbnail_ax_index'}
        require(isinstance(witness,dict) and set(witness)==wkeys and witness['fingerprint']==card['fingerprint']
            and witness['title']==card['title'] and witness['card_bounds']==card['card_bounds']
            and witness['metadata_bounds']==card['metadata_bounds'] and witness['safe_metadata_bounds']==card['safe_metadata_bounds']
            and witness['neighbor_bounds']==card['neighbor_bounds'] and witness['thumbnail_bounds'] is not None,
            'CLASSIFIER_CARD_WITNESS')
        ident=fp(card['fingerprint'])
        for key,needle in (('title_ocr',card['title']),('count_ocr',str(ident['expected_images']))):
            item=witness[key]
            require(isinstance(item,dict) and set(item)=={'text','bounds'} and isinstance(item['text'],str)
                and isinstance(item['bounds'],list),'CLASSIFIER_OCR_WITNESS')
            if key=='count_ocr':
                matched=re.search(r'(?<![0-9])'+re.escape(needle)+r'(?![0-9])',item['text']) is not None
            else:matched=item['text']==needle
            require(matched,'CLASSIFIER_OCR_WITNESS')
            found=[candidate for candidate in ocr_items if candidate.get('text')==item['text']
                and candidate.get('bounds')==item['bounds'] and candidate.get('candidate_count')==1
                and candidate.get('confidence',0)>=0.5]
            require(len(found)==1 and inside(item['bounds'],card['metadata_bounds']),'CLASSIFIER_OCR_WITNESS')
        card_node=elements.get(witness['card_ax_index']);thumbnail_node=elements.get(witness['thumbnail_ax_index'])
        require(card_node is not None and card_node['role'] in ('row','group','cell')
            and card_node['bounds_px']==card['card_bounds'] and thumbnail_node is not None
            and thumbnail_node['role']=='image' and thumbnail_node['bounds_px']==witness['thumbnail_bounds']
            and inside(witness['thumbnail_bounds'],card['card_bounds']),'CLASSIFIER_AX_CARD_WITNESS')
    return dict(geometry=evidence,manifest=manifest,classifier=classifier,ax=ax,ocr=ocr)

def _validate_frame(reader,record,cfg,*,session,now=None,max_age=5,allow_high_editable=False):
    required={'frame','frame_id','session_id','group_key','surface','captured_at','provider','layout_key',
        'window_id','pid','width','height','mapping','cards','boundary','editable_focus','occlusion'}
    require(isinstance(record,dict) and set(record)==required,'INVALID_OBSERVATION')
    require(record['session_id']==session and record['group_key']==cfg['group_key'],'CONTEXT_MISMATCH')
    require(record['provider']=='HOSTED_CUA' and record['surface'] in ('ALBUMS','ALBUM_DETAIL','FOLDER_CHOOSER'),'SURFACE_MISMATCH')
    focus_ok=record['editable_focus']=='NONE' or (allow_high_editable and record['editable_focus']=='HIGH_EDITABLE')
    require(record['occlusion']=='CLEAR' and focus_ok,'INPUT_SAFETY_UNKNOWN')
    require(integer(record['pid'],1) and integer(record['window_id'],1) and isinstance(record['layout_key'],str) and record['layout_key'],'WINDOW_IDENTITY')
    instant=dt.datetime.fromisoformat(record['captured_at'].replace('Z','+00:00'))
    require(instant.tzinfo is not None,'INVALID_CAPTURE_TIME')
    age=(dt.datetime.now(dt.timezone.utc) if now is None else now)-instant
    require(age.total_seconds()>=0 and (max_age is None or age.total_seconds()<=max_age),'STALE_OBSERVATION')
    raw=artifact(reader,record['frame']);require(record['frame_id']==sha(raw),'FRAME_ID_MISMATCH')
    size=image_size(raw);require(size==(record['width'],record['height']),'FRAME_DIMENSIONS_MISMATCH')
    mapping=record['mapping']
    require(isinstance(mapping,dict) and set(mapping)=={'space','uncertainty','evidence','frame_id','layout_key','sck_support'},'MAPPING_UNKNOWN')
    require(mapping['space']=='CUA_CAPTURE_PIXELS' and mapping['frame_id']==record['frame_id'] and mapping['layout_key']==record['layout_key'],'MAPPING_MISMATCH')
    require(type(mapping['uncertainty']) in (int,float) and math.isfinite(mapping['uncertainty']) and mapping['uncertainty']>=2,'MAPPING_UNKNOWN')
    artifact(reader,mapping['evidence'])
    support=_support(reader,mapping['sck_support'],record,cfg,now=(dt.datetime.now(dt.timezone.utc) if now is None else now),max_age=max_age)
    require(mapping['uncertainty']>=support['sidecar']['uncertainty_px'],'MAPPING_UNCERTAINTY_UNDERSTATED')
    fixture_root=Path(reader.root).is_relative_to(Path(__file__).resolve().parents[2]/'harness-development') and '/fixtures/' in reader.root
    if not fixture_root:_grounding_evidence(reader,mapping['evidence'],record,support)
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

def frame(reader,record,cfg,*,session,now=None,max_age=5):
    """Validate the unchanged strict 17-key frame; HIGH_EDITABLE always refuses here."""
    return _validate_frame(reader,record,cfg,session=session,now=now,max_age=max_age)

CHOOSER_PHASES=('APPEARED','GO_TO_FOLDER','PATH_FILLED','DESTINATION_SELECTED','CONFIRM_ATTEMPTED')

def chooser_observation(reader,envelope,cfg,*,session,owner,run_id,action_id,destination,
                        previous=None,now=None):
    """Validate one fresh typed chooser phase, with the sole HIGH-focus exception bound to Go to Folder."""
    keys={'version','phase','frame','ax_state','sck_support','dispatch','control'}
    require(isinstance(envelope,dict) and set(envelope)==keys and envelope.get('version')==1
        and envelope.get('phase') in CHOOSER_PHASES,'CHOOSER_ENVELOPE')
    phase=envelope['phase'];index=CHOOSER_PHASES.index(phase)
    if previous is None:require(phase=='APPEARED','CHOOSER_PHASE_ORDER')
    else:
        require(isinstance(previous,dict) and previous.get('phase') in CHOOSER_PHASES
            and index==CHOOSER_PHASES.index(previous['phase'])+1,'CHOOSER_PHASE_ORDER')
    record=envelope['frame'];dispatch=envelope['dispatch'];control=envelope['control']
    require(isinstance(dispatch,dict) and set(dispatch)=={'run_id','action_id','session_id','owner','destination',
        'original_frame_id','original_context'}
        and dispatch==dict(run_id=run_id,action_id=action_id,session_id=session,owner=owner,destination=destination,
            original_frame_id=dispatch.get('original_frame_id'),original_context=dispatch.get('original_context'))
        and isinstance(dispatch.get('original_frame_id'),str) and len(dispatch['original_frame_id'])==64
        and isinstance(dispatch.get('original_context'),dict)
        and set(dispatch['original_context'])=={'frame_id','pid','window_id','layout_key'}
        and dispatch['original_context']['frame_id']==dispatch['original_frame_id']
        and integer(dispatch['original_context']['pid'],1) and integer(dispatch['original_context']['window_id'],1)
        and isinstance(dispatch['original_context']['layout_key'],str) and dispatch['original_context']['layout_key']
        and dispatch['original_context']['pid']==record.get('pid'),
        'CHOOSER_DISPATCH_BINDING')
    require(record.get('session_id')==session,'CHOOSER_SESSION_MISMATCH')
    if phase=='CONFIRM_ATTEMPTED':
        require(record.get('surface') in ('ALBUM_DETAIL','FOLDER_CHOOSER'),'CHOOSER_CONFIRM_FRAME')
    else:require(record.get('surface')=='FOLDER_CHOOSER','CHOOSER_SURFACE')
    expected_support=record.get('mapping',{}).get('sck_support')
    expected_ax=None
    if isinstance(record.get('mapping',{}).get('evidence'),dict):
        grounding=strict_json(artifact(reader,record['mapping']['evidence']),'INVALID_GROUNDING_EVIDENCE')
        if isinstance(grounding,dict) and isinstance(grounding.get('geometry'),dict):
            geometry=strict_json(artifact(reader,grounding['geometry']),'INVALID_GROUNDING_EVIDENCE')
            if isinstance(geometry,dict):expected_ax=geometry.get('ax_state')
    fixture_root=Path(reader.root).is_relative_to(Path(__file__).resolve().parents[2]/'harness-development') and '/fixtures/' in reader.root
    ax_matches=(envelope['ax_state']==expected_ax if expected_ax is not None else fixture_root)
    require(envelope['sck_support']==expected_support and ax_matches,
        'CHOOSER_EVIDENCE_CROSS_PAIR')
    require(isinstance(control,dict),'CHOOSER_CONTROL_BINDING')
    high_phase=phase in ('GO_TO_FOLDER','PATH_FILLED')
    if record.get('editable_focus')=='HIGH_EDITABLE':
        require(high_phase,'CHOOSER_HIGH_FOCUS_SCOPE')
    _validate_frame(reader,record,cfg,session=session,now=now,max_age=5,allow_high_editable=high_phase)
    ax_raw=artifact(reader,envelope['ax_state']);ax=strict_json(ax_raw,'INVALID_CHOOSER_AX_STATE')
    require(isinstance(ax,dict) and set(ax)=={'version','frame_id','session_id','pid','window_id','surface','focused_index','elements'}
        and ax.get('version')==1 and ax.get('frame_id')==record['frame_id'] and ax.get('session_id')==session
        and ax.get('pid')==record['pid'] and ax.get('window_id')==record['window_id'] and ax.get('surface')==record['surface']
        and isinstance(ax.get('elements'),list),'CHOOSER_AX_BINDING')
    for element in ax['elements']:
        require(isinstance(element,dict) and set(element)=={'index','role','subrole','identifier','label','value','enabled','bounds_px','parent_index'}
            and type(element.get('index')) is int and element['index']>=0 and isinstance(element.get('role'),str)
            and isinstance(element.get('subrole'),str) and isinstance(element.get('identifier'),str)
            and isinstance(element.get('enabled'),bool)
            and (element.get('parent_index') is None or type(element.get('parent_index')) is int),'CHOOSER_AX_ELEMENT')
        rect(element.get('bounds_px'),record['width'],record['height'])
    def element_at(i):
        matches=[e for e in ax['elements'] if e['index']==i]
        require(len(matches)==1,'CHOOSER_CONTROL_AMBIGUOUS')
        return matches[0]
    if phase=='APPEARED':
        require(set(control)=={'chooser_index','chooser_identifier'} and type(control['chooser_index']) is int
            and element_at(control['chooser_index'])['role'] in ('window','sheet','dialog')
            and element_at(control['chooser_index'])['identifier']==control['chooser_identifier'],
            'CHOOSER_APPEARED_BINDING')
    elif phase=='GO_TO_FOLDER':
        require(set(control)=={'path_field_index','path_field_role','path_field_subrole','path_field_identifier',
            'path_field_bounds_px','path_field_enabled','focused'}
            and type(control['path_field_index']) is int,'CHOOSER_PATH_FIELD')
        field=element_at(control['path_field_index'])
        require(field['role']=='text field' and field['subrole']=='PathTextField'
            and field['identifier']==control['path_field_identifier'] and field['bounds_px']==control['path_field_bounds_px']
            and control['path_field_role']=='text field' and control['path_field_subrole']=='PathTextField'
            and field['enabled'] is True and control['path_field_enabled'] is True
            and control['focused'] is True and ax['focused_index']==field['index']
            and record['editable_focus']=='HIGH_EDITABLE','CHOOSER_PATH_FIELD')
    elif phase=='PATH_FILLED':
        require(set(control)=={'path_field_index','path_field_role','path_field_subrole','path_field_identifier',
            'path_field_bounds_px','path_field_enabled','value','focused'}
            and type(control['path_field_index']) is int,'CHOOSER_PATH_VALUE')
        field=element_at(control['path_field_index'])
        require(field['role']=='text field' and field['subrole']=='PathTextField'
            and field['identifier']==control['path_field_identifier'] and field['bounds_px']==control['path_field_bounds_px']
            and field['enabled'] is True and control['path_field_enabled'] is True
            and field['value']==destination and control['value']==destination and control['focused'] is True
            and ax['focused_index']==field['index']
            and record['editable_focus']=='HIGH_EDITABLE','CHOOSER_PATH_VALUE')
    elif phase=='DESTINATION_SELECTED':
        require(set(control)=={'path_field_index','path_field_identifier','path_field_role','path_field_subrole',
            'value','selected_leaf','selected_leaf_index','selected_leaf_identifier','selected_leaf_bounds_px',
            'selected_leaf_ocr','confirm_index','confirm_role','confirm_identifier','confirm_bounds_px','confirm_enabled',
            'confirm_point'}
            and type(control['path_field_index']) is int and type(control['confirm_index']) is int
            and type(control['selected_leaf_index']) is int and control['value']==destination
            and control['selected_leaf']==Path(destination).name,
            'CHOOSER_DESTINATION_BINDING')
        field=element_at(control['path_field_index']);confirm=element_at(control['confirm_index'])
        leaf=element_at(control['selected_leaf_index']);leaf_text=Path(destination).name
        leaf_ocr=control['selected_leaf_ocr']
        require(leaf['role'] in ('text','static text','button') and leaf['identifier']==control['selected_leaf_identifier']
            and leaf['bounds_px']==control['selected_leaf_bounds_px'] and leaf_text in (leaf['label'],leaf['value'])
            and isinstance(leaf_ocr,dict) and set(leaf_ocr)=={'text','bounds'} and leaf_ocr['text']==leaf_text
            and isinstance(leaf_ocr['bounds'],list),'CHOOSER_LEAF_NOT_OBSERVED')
        sidecar=strict_json(artifact(reader,record['mapping']['sck_support']),'INVALID_SCK_SUPPORT')
        ocr=strict_json(artifact(reader,sidecar['ocr']),'INVALID_FRAME_SUPPORT_OCR')
        matches=[item for item in ocr['cua'] if item.get('text')==leaf_text and item.get('candidate_count')==1
            and item.get('confidence',0)>=0.5 and item.get('bounds')==leaf_ocr['bounds']
            and inside(item['bounds'],leaf['bounds_px'])]
        leaf_nodes=[e for e in ax['elements'] if e['role'] in ('text','static text','button')
            and leaf_text in (e.get('label'),e.get('value'))]
        require(len(matches)==1 and len(leaf_nodes)==1 and leaf_nodes[0]['index']==leaf['index'],
            'CHOOSER_LEAF_NOT_OBSERVED')
        require(inside(confirm['bounds_px'],sidecar['interactive_intersection_px'],
            record['mapping']['uncertainty']),'CHOOSER_CONFIRM_UNSAFE')
        require(field['role']=='text field' and field['subrole']=='PathTextField'
            and field['identifier']==control['path_field_identifier'] and field['value']==destination
            and control['path_field_role']==field['role'] and control['path_field_subrole']==field['subrole']
            and confirm['role']=='button' and confirm['enabled'] is True and control['confirm_role']==confirm['role']
            and control['confirm_identifier']==confirm['identifier'] and control['confirm_enabled'] is True
            and control['confirm_bounds_px']==confirm['bounds_px'],'CHOOSER_CONFIRM_CONTROL')
        b=confirm['bounds_px'];expected_point=[math.trunc(b[0]+b[2]/2),math.trunc(b[1]+b[3]/2)]
        require(control['confirm_point']==expected_point,'CHOOSER_CONFIRM_CONTROL')
    else:
        require(set(control)=={'confirmation_frame_id','attempted','invocation_count'}
            and control['confirmation_frame_id']==previous['frame']['frame_id'] and control['attempted'] is True
            and control['invocation_count']==1,'CHOOSER_CONFIRM_ATTEMPT')
    return envelope

def validate_download_start(reader,ref,*,run_id,action_id,owner,session,destination,confirmation_frame_id,
                            confirmation_invoked_at,now=None):
    """Require an independent, hash-backed empty-to-new-image observation at the leased destination."""
    evidence=strict_json(artifact(reader,ref),'INVALID_DOWNLOAD_EVIDENCE')
    keys={'version','source_kind','run_id','action_id','execution_id','session_id','destination','baseline',
        'confirmation_frame_id','confirmation_invoked_at','observed_at','destination_identity','before_inventory',
        'after_inventory','sampling'}
    require(isinstance(evidence,dict) and set(evidence)==keys and evidence.get('version')==1
        and evidence.get('source_kind')=='FILESYSTEM_DELTA','INVALID_DOWNLOAD_EVIDENCE')
    require(evidence['run_id']==run_id and evidence['action_id']==action_id and evidence['execution_id']==owner
        and evidence['session_id']==session and evidence['destination']==destination
        and evidence['confirmation_frame_id']==confirmation_frame_id
        and evidence['confirmation_invoked_at']==confirmation_invoked_at,'DOWNLOAD_EVIDENCE_BINDING')
    observed=dt.datetime.fromisoformat(evidence['observed_at'].replace('Z','+00:00'))
    confirmed=dt.datetime.fromisoformat(confirmation_invoked_at.replace('Z','+00:00'))
    require(observed.tzinfo is not None and confirmed.tzinfo is not None,'DOWNLOAD_EVIDENCE_TIME')
    current=dt.datetime.now(dt.timezone.utc) if now is None else now
    require(observed<=current and observed>=confirmed,'DOWNLOAD_EVIDENCE_TIME')
    baseline=strict_json(artifact(reader,evidence['baseline']),'INVALID_DOWNLOAD_BASELINE')
    baseline_keys={'version','run_id','execution_id','destination','captured_at','destination_identity','inventory'}
    require(isinstance(baseline,dict) and set(baseline)==baseline_keys and baseline.get('version')==1
        and baseline.get('run_id')==run_id and baseline.get('execution_id')==owner
        and baseline.get('destination')==destination and baseline.get('inventory')==[]
        and isinstance(baseline.get('captured_at'),str),'DOWNLOAD_BASELINE_BINDING')
    baseline_time=dt.datetime.fromisoformat(baseline['captured_at'].replace('Z','+00:00'))
    require(baseline_time.tzinfo is not None and baseline_time<=confirmed,'DOWNLOAD_BASELINE_TIME')
    require(evidence['before_inventory']==[] and isinstance(evidence['after_inventory'],list)
        and evidence['after_inventory'],'DOWNLOAD_START_NOT_OBSERVED')
    sampling=evidence['sampling']
    require(isinstance(sampling,dict) and set(sampling)=={'sample_count','interval_ms','elapsed_ms'}
        and type(sampling['sample_count']) is int and sampling['sample_count']>=1
        and type(sampling['interval_ms']) is int and sampling['interval_ms']>=0
        and type(sampling['elapsed_ms']) is int and 0<=sampling['elapsed_ms']<=30000
        and (sampling['interval_ms']==0 or sampling['interval_ms']==1000),'DOWNLOAD_SAMPLING_POLICY')
    identity=evidence['destination_identity']
    require(identity==baseline['destination_identity'],'DOWNLOAD_DESTINATION_IDENTITY')
    require(isinstance(identity,dict) and set(identity)=={'device','inode','mode','realpath'}
        and type(identity['device']) is int and type(identity['inode']) is int and type(identity['mode']) is int
        and identity['realpath']==destination,'DOWNLOAD_DESTINATION_IDENTITY')
    backup_root=reader.root+'/backups/'
    require(isinstance(destination,str) and destination.startswith(backup_root),'DOWNLOAD_DESTINATION_SCOPE')
    destination_path=Path(destination)
    require(str(destination_path)==destination and destination_path.resolve(strict=True)==destination_path,
        'DOWNLOAD_DESTINATION_IDENTITY')
    root_stat=os.lstat(destination_path)
    require(stat.S_ISDIR(root_stat.st_mode) and not stat.S_ISLNK(root_stat.st_mode)
        and (root_stat.st_dev,root_stat.st_ino,root_stat.st_mode)==
            (identity['device'],identity['inode'],identity['mode']),'DOWNLOAD_DESTINATION_REPLACED')
    inventory=evidence['after_inventory'];names=[]
    for item in inventory:
        require(isinstance(item,dict) and set(item)=={'name','bytes','mtime_ns','inode','sha256','recognized_image'}
            and isinstance(item['name'],str) and item['name'] not in ('','.','..') and '/' not in item['name']
            and type(item['bytes']) is int and item['bytes']>0 and type(item['mtime_ns']) is int
            and type(item['inode']) is int and isinstance(item['sha256'],str) and len(item['sha256'])==64
            and item['recognized_image'] is True,'DOWNLOAD_INVENTORY_ENTRY')
        names.append(item['name']);path=destination_path/item['name'];st=os.lstat(path)
        require(stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode) and st.st_size==item['bytes']
            and st.st_mtime_ns==item['mtime_ns'] and st.st_ino==item['inode'],'DOWNLOAD_FILE_CHANGED')
        raw=path.read_bytes();require(sha(raw)==item['sha256'],'DOWNLOAD_FILE_CHANGED')
        require(path.suffix.lower() in {'.jpg','.jpeg','.png'} and image_size(raw),'DOWNLOAD_IMAGE_UNRECOGNIZED')
        file_time=dt.datetime.fromtimestamp(item['mtime_ns']/1_000_000_000,dt.timezone.utc)
        require(file_time>=confirmed,'DOWNLOAD_FILE_PREEXISTED_CONFIRMATION')
    require(len(names)==len(set(names)) and sorted(os.listdir(destination_path))==sorted(names),'DOWNLOAD_INVENTORY_DRIFT')
    return evidence

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
