import {ReactNode,useMemo,useState} from 'react';
const ROW_HEIGHT=44; const OVERSCAN=6;
export function VirtualizedRows<T>({items,height=440,render}:{items:T[];height?:number;render:(item:T,index:number)=>ReactNode}){
 const [scrollTop,setScrollTop]=useState(0);
 const range=useMemo(()=>{const start=Math.max(0,Math.floor(scrollTop/ROW_HEIGHT)-OVERSCAN);const count=Math.ceil(height/ROW_HEIGHT)+OVERSCAN*2;return {start,end:Math.min(items.length,start+count)}},[scrollTop,height,items.length]);
 return <div data-virtualized="true" style={{height,overflowY:'auto'}} onScroll={e=>setScrollTop(e.currentTarget.scrollTop)}><div style={{height:items.length*ROW_HEIGHT,position:'relative'}}>{items.slice(range.start,range.end).map((item,j)=><div key={range.start+j} style={{position:'absolute',top:(range.start+j)*ROW_HEIGHT,height:ROW_HEIGHT,left:0,right:0}}>{render(item,range.start+j)}</div>)}</div></div>
}
