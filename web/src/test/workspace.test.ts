import {describe,it,expect} from 'vitest';import {parseCommand} from '../terminal/commands';import {restore,defaults} from '../workspace/persistence';import {useWorkspace} from '../workspace/store';
describe('terminal navigation',()=>{it('parses allowlisted commands without evaluation',()=>{expect(parseCommand('SCAN').action).toBe('scanner');expect(parseCommand('SRCH fed october')).toEqual({action:'search',argument:'fed october'});expect(parseCommand('$(touch nope)').action).toBe('search');expect(parseCommand('https://kalshi.com/markets/x/y').action).toBe('search');});it('restores only versioned layout',()=>{expect(restore({schema_version:9})).toEqual(defaults);});it('selection is independent across link groups',()=>{const s=useWorkspace.getState();s.reset();s.select('a','A');s.select('b','B');expect(useWorkspace.getState().selected).toEqual({A:'a',B:'b',C:null});s.close('a');expect(useWorkspace.getState().selected.B).toBe('b');});});

it('recovers malformed nested state without restoring unknown fields',()=>{
 const recovered=restore({schema_version:1,selected:null,ranges:{A:999,B:1},scannerFilters:{verified:'true',q:'fed'},leftWidth:-5,tabs:['a',null,'a',42],set:'malicious',group:'D'});
 expect(recovered.selected).toEqual(defaults.selected);expect(recovered.ranges).toEqual({A:7,B:1,C:7});
 expect(recovered.scannerFilters.verified).toBe(false);expect(recovered.scannerFilters.q).toBe('fed');
 expect(recovered.leftWidth).toBe(180);expect(recovered.tabs).toEqual(['a']);expect(recovered.group).toBe('A');expect(recovered).not.toHaveProperty('set');
});
