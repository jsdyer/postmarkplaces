import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {historyLines,matches} from '../web/model.mjs';
const {offices}=JSON.parse(readFileSync(new URL('../web/data/edition.json',import.meta.url)));
const lookup=(name,date)=>matches(offices,name,date,'All areas');
test('Langley Prairie transfers from one office to another on the rename day',()=>{
  const old=lookup('Langley Prairie','1911-05-15')[0].office;
  const next=lookup('Langley Prairie','1911-05-16');
  assert.equal(old.names.at(-1).name,'Murrayville'); assert.equal(next.length,1);
  assert.notEqual(next[0].office.id,old.id);
});
test('Closures and uncertain openings keep their boundaries',()=>{
  assert.equal(lookup('Otter','1917-10-31').length,0);
  assert.equal(lookup('Langley','1871-05-01')[0].state.uncertain,true);
  assert.equal(lookup('Dartmouth','1870-06-01')[0].state.uncertain,true);
  assert.equal(lookup('Dartmouth','1869-12-31').length,0);
  assert.equal(historyLines(lookup('Dartmouth','1894-06-01')[0].office).length,4);
});
