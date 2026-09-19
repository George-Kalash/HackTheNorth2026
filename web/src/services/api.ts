import type { components } from './generated/api';
export type Market=components['schemas']['VenueMarket'];
export type Match=components['schemas']['MatchGroup'];
export type Book=components['schemas']['BookSnapshot'];
export type History=components['schemas']['PriceHistory'];
export type Opportunity=components['schemas']['Opportunity'];
export type SearchResult=components['schemas']['SearchResponse'];
export type Comparison=components['schemas']['ComparisonResponse'];
export type ScannerRow=components['schemas']['ScannerRowResponse'];
export interface Watchlist {id:string;name:string;match_ids:string[]}
export interface AlertRule {id:string;name:string;match_id:string|null;min_net_floor:string;cooldown_seconds:number;enabled:boolean}
export interface Health {status:string;venues:{venue:string;books:string;websocket:string;fees:string}[];worker:{heartbeat:string;mode:string;errors:string[]}|null;thresholds:{max_age_seconds:number;poll_seconds:number;max_skew_seconds:number}}
export async function api<T>(path:string,body?:unknown,method?:string):Promise<T>{
 const r=await fetch('/api/v1'+path,{method:method??(body?'POST':'GET'),headers:body?{'Content-Type':'application/json'}:undefined,body:body?JSON.stringify(body):undefined});
 const data=await r.json();if(!r.ok)throw new Error(data.error?.message??JSON.stringify(data.detail??'Request failed'));return data as T;
}
export const money=(v:string|number|null|undefined)=>v==null?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:4}).format(Number(v));
export const percent=(v:string|number|null|undefined)=>v==null?'—':(Number(v)*100).toFixed(2)+'%';
