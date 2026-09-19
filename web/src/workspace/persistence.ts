export type Group='A'|'B'|'C';
export type Preset='Research'|'Compare'|'Scan'|'Rules Review';
export interface WorkspaceState {scannerFilters:{q:string;review:string;classification:string;quantity:string;minCapacity:string;minNet:string;maxAge:string;expiry:string;verified:boolean};schema_version:1;preset:Preset;group:Group;selected:Record<Group,string|null>;ranges:Record<Group,1|7|30>;tabs:string[];leftWidth:number;rightWidth:number;collapsed:string[];maximized:string|null;rightTab:'RULES'|'TRADE'|'DETAILS';mobileTab:'chart'|'books'|'rules'|'trade';priceType:'provider'|'midpoint'|'bid'|'ask';query:string}
export const defaults:WorkspaceState={scannerFilters:{q:"",review:"",classification:"",quantity:"10",minCapacity:"0",minNet:"",maxAge:"45",expiry:"",verified:false},schema_version:1,preset:'Research',group:'A',selected:{A:null,B:null,C:null},ranges:{A:7,B:7,C:7},tabs:[],leftWidth:270,rightWidth:360,collapsed:[],maximized:null,rightTab:'RULES',mobileTab:'chart',priceType:'provider',query:''};
const record=(v:unknown):v is Record<string,unknown>=>!!v&&typeof v==='object'&&!Array.isArray(v);
const text=(v:unknown):v is string=>typeof v==='string'&&v.length<=2000;
export function restore(value:unknown):WorkspaceState {
 const out=structuredClone(defaults);
 if(!record(value)||value.schema_version!==1)return out;
 const enums={preset:['Research','Compare','Scan','Rules Review'],group:['A','B','C'],rightTab:['RULES','TRADE','DETAILS'],mobileTab:['chart','books','rules','trade'],priceType:['provider','midpoint','bid','ask']} as const;
 for(const key of Object.keys(enums) as (keyof typeof enums)[]) {
  const v=value[key];if(typeof v==='string'&&(enums[key] as readonly string[]).includes(v))Object.assign(out,{[key]:v});
 }
 for(const key of ['leftWidth','rightWidth'] as const){const v=value[key];if(typeof v==='number'&&Number.isFinite(v))out[key]=Math.max(180,Math.min(700,v));}
 for(const key of ['tabs','collapsed'] as const){const v=value[key];if(Array.isArray(v))out[key]=[...new Set(v.filter(text))].slice(0,100);}
 if(value.maximized===null||text(value.maximized))out.maximized=value.maximized;
 if(text(value.query))out.query=value.query;
 for(const g of ['A','B','C'] as const){
  if(record(value.selected)){const v=value.selected[g];if(v===null||text(v))out.selected[g]=v;}
  if(record(value.ranges)){const v=value.ranges[g];if(v===1||v===7||v===30)out.ranges[g]=v;}
 }
 if(record(value.scannerFilters))for(const key of Object.keys(out.scannerFilters) as (keyof typeof out.scannerFilters)[]){
  const v=value.scannerFilters[key];
  if(key==='verified'){if(typeof v==='boolean')out.scannerFilters.verified=v;}
  else if(text(v))out.scannerFilters[key]=v;
 }
 return out;
}
