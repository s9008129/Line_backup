import assert from 'node:assert/strict';
import {createHash, randomUUID} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {deflateSync,inflateSync} from 'node:zlib';

const here=path.dirname(fileURLToPath(import.meta.url));
const runner=await readFile(path.join(here,'..','live_runner.mjs'),'utf8');
const start=runner.indexOf('export function createRetain({io,repoRoot}) {');
const end=runner.indexOf('\nexport function createProducerHook(',start);
assert.ok(start>=0&&end>start,'production createRetain source markers are present');
const literalFunction=runner.slice(start,end).trim().replace(/^export /,'');
const sourceDigest=createHash('sha256').update(literalFunction).digest('hex');

const fail=code=>{throw Object.assign(new Error(code),{code});};
const need=(ok,code)=>{if(!ok)fail(code);};
const isHash=value=>typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
const factory=new Function('path','CON','need','fail','isHash','encoder','evidenceJSON','randomUUID','sha256','inflateSync',
  `${literalFunction}\nreturn createRetain;`);
const createRetain=factory(path,'task-root',need,fail,isHash,new TextEncoder(),value=>JSON.stringify(value),
  randomUUID,sha256,inflateSync);

function crc32(bytes) {
  let crc=0xffffffff;
  for(const byte of bytes) {
    crc^=byte;
    for(let bit=0;bit<8;bit++)crc=(crc&1)?(0xedb88320^(crc>>>1)):(crc>>>1);
  }
  return (crc^0xffffffff)>>>0;
}

function pngChunk(type,data) {
  const name=Buffer.from(type,'ascii'),length=Buffer.alloc(4),checksum=Buffer.alloc(4);
  length.writeUInt32BE(data.length);checksum.writeUInt32BE(crc32(Buffer.concat([name,data])));
  return Buffer.concat([length,name,data,checksum]);
}

function onePixelPNG(colorType=6) {
  const header=Buffer.alloc(13);
  header.writeUInt32BE(1,0);header.writeUInt32BE(1,4);
  header[8]=8;header[9]=colorType;header[10]=0;header[11]=0;header[12]=0;
  const pixel=colorType===2?Buffer.from([0,255,0,0]):Buffer.from([0,255,0,0,255]);
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),
    pngChunk('IHDR',header),pngChunk('IDAT',deflateSync(pixel)),pngChunk('IEND',Buffer.alloc(0))]);
}

function priorMarkerOnlyJPEGFixture(scanByte=0x3f) {
  const segment=(marker,payload)=>{const length=Buffer.alloc(2);length.writeUInt16BE(payload.length+2);return Buffer.concat([Buffer.from([0xff,marker]),length,payload]);};
  const quant=Buffer.from([0,...Array(64).fill(1)]);
  const huffman=tableClass=>Buffer.from([tableClass<<4|0,1,...Array(15).fill(0),0]);
  const frame=Buffer.from([8,0,1,0,1,1,1,0x11,0]);
  const scan=Buffer.from([1,1,0,0,63,0]);
  return Buffer.concat([Buffer.from([0xff,0xd8]),segment(0xdb,quant),segment(0xc0,frame),
    segment(0xc4,huffman(0)),segment(0xc4,huffman(1)),segment(0xda,scan),Buffer.from([scanByte,0xff,0xd9])]);
}

function memoryStore({corruptReadback=false}={}) {
  const files=new Map();
  return {files,io:{
    async mkdirp() {},
    async writeFile(file,bytes) { files.set(file,Buffer.from(bytes)); },
    async readFile(file) { const value=files.get(file);assert.ok(value);const copy=Buffer.from(value);if(corruptReadback)copy[0]^=1;return copy; },
  }};
}

function assertRetained(bytes,extension) {
  return async()=>{
    const store=memoryStore(),retain=createRetain({io:store.io,repoRoot:'/isolated'});
    const frameId=sha256(bytes),result=await retain({screenshot:bytes,ax:'offline AX fixture',frameId});
    assert.match(result.path,new RegExp(`\\.${extension}$`));
    assert.match(result.ax.path,/\.bin$/);
    assert.equal(result.bytes,bytes.length);
    assert.equal(result.sha256,frameId);
    assert.deepEqual(store.files.get(path.join('/isolated',result.path)),bytes);
    assert.deepEqual(store.files.get(path.join('/isolated',result.ax.path)),Buffer.from('offline AX fixture'));
  };
}

await assertRetained(onePixelPNG(),'png')();
await assertRetained(onePixelPNG(2),'png')();
const jpeg=Buffer.from([0xff,0xd8,0xff,0xd9]);
const malformedEntropyJPEG=priorMarkerOnlyJPEGFixture(0x7f);

for(const malformed of [
  onePixelPNG().subarray(0,onePixelPNG().length-1),
  jpeg,
  malformedEntropyJPEG,
  Buffer.from([...onePixelPNG().subarray(0,12),0,0,0,1,...onePixelPNG().subarray(16)]),
  Buffer.from('not an image'),
  (()=>{const png=onePixelPNG();png[png.length-13]^=0xff;return png;})(),
  (()=>{const png=onePixelPNG(),type=png.indexOf(Buffer.from('IDAT')),length=png.readUInt32BE(type-4),dataStart=type+4;png[dataStart+length-1]^=0xff;png.writeUInt32BE(crc32(png.subarray(type,type+4+length)),dataStart+length);return png;})(),
  (()=>{const png=onePixelPNG(),type=png.indexOf(Buffer.from('IDAT')),length=png.readUInt32BE(type-4),chunkStart=type-4,chunkEnd=type+4+length;return Buffer.concat([png.subarray(0,chunkStart),pngChunk('IDAT',Buffer.concat([png.subarray(type+4,chunkEnd),Buffer.from([0])])),png.subarray(chunkEnd+4)]);})(),
  (()=>{const png=onePixelPNG();png[25]=2;const ihdrEnd=png.indexOf(Buffer.from('IHDR'))+4+13;png.writeUInt32BE(crc32(png.subarray(png.indexOf(Buffer.from('IHDR')),ihdrEnd)),ihdrEnd);return png;})(),
]) {
  const store=memoryStore(),retain=createRetain({io:store.io,repoRoot:'/isolated'});
  const frameId=sha256(malformed);
  await assert.rejects(retain({screenshot:malformed,ax:'offline AX fixture',frameId}));
  assert.equal(store.files.size,0,'malformed image is rejected before any retained write');
}

{
  const store=memoryStore(),retain=createRetain({io:store.io,repoRoot:'/isolated'});
  await assert.rejects(retain({screenshot:onePixelPNG(),ax:'offline AX fixture',frameId:'a'.repeat(64)}));
  assert.equal(store.files.size,0,'a mismatched frame identity is refused before retention');
}

{
  const store=memoryStore({corruptReadback:true}),retain=createRetain({io:store.io,repoRoot:'/isolated'});
  const image=onePixelPNG(),frameId=sha256(image);
  await assert.rejects(retain({screenshot:image,ax:'offline AX fixture',frameId}),/RETAIN_READBACK/);
}

{
  const store=memoryStore(),retain=createRetain({io:store.io,repoRoot:'/isolated'});
  const frameId='a'.repeat(64),result=await retain({artifact:{kind:'offline-proof'},kind:'offline-proof',frameId});
  assert.match(result.path,/\.bin$/,'non-image evidence retains its existing .bin representation');
}

process.stdout.write(`PASS: 14 bounded retained-image cases; production createRetain SHA-256 ${sourceDigest}\n`);
