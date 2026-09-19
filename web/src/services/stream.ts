export interface Envelope {schema_version:1;type:'snapshot'|'delta'|'status'|'heartbeat'|'error';topic:string;sequence:number;sent_at:string;data:unknown}
export class TerminalStream {
 private ws?:WebSocket;private timer?:ReturnType<typeof setTimeout>;private closed=false;private sequence=0;private retries=0;private topics=new Set<string>();
 constructor(private receive:(e:Envelope)=>void,private status:(s:string)=>void){}
 connect(){this.closed=false;this.status('CONNECTING');const ws=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/api/v1/stream`);this.ws=ws;
 ws.onopen=()=>{this.sequence=0;this.retries=0;this.status('CONNECTED');this.topics.forEach(topic=>this.send('subscribe',topic));};
 ws.onmessage=event=>{try{const e=JSON.parse(event.data) as Envelope;if(e.schema_version!==1)return;if(e.sequence<=this.sequence)return;if(this.sequence&&e.sequence!==this.sequence+1)this.topics.forEach(t=>this.send('resync',t));this.sequence=e.sequence;this.receive(e);}catch{this.status('INVALID FRAME');}};
 ws.onclose=()=>{this.status('DISCONNECTED');if(!this.closed)this.timer=setTimeout(()=>this.connect(),Math.min(30000,1000*2**this.retries++)+Math.random()*500);};ws.onerror=()=>ws.close();
 }
 private send(action:string,topic:string){if(this.ws?.readyState===WebSocket.OPEN)this.ws.send(JSON.stringify({action,topic}));}
 subscribe(topic:string){this.topics.add(topic);this.send('subscribe',topic);return()=>{this.topics.delete(topic);this.send('unsubscribe',topic);};}
 close(){this.closed=true;clearTimeout(this.timer);this.ws?.close();}
}
