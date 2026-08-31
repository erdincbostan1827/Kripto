import {useEffect,useRef} from 'react';
import {createChart,CandlestickSeries,HistogramSeries,LineSeries,CandlestickData,HistogramData,LineData,Time} from 'lightweight-charts';

const MAX_VISIBLE_POINTS=2000;
export type MarketChartProps={candles:CandlestickData<Time>[];volume:HistogramData<Time>[];indicator?:LineData<Time>[];entry?:number;stop?:number;targets?:number[]};

export function MarketChart({candles,volume,indicator=[],entry,stop,targets=[]}:MarketChartProps){
 const host=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  if(!host.current)return;
  const chart=createChart(host.current,{height:420,handleScroll:true,handleScale:true,timeScale:{timeVisible:true,secondsVisible:false}});
  const candleSeries=chart.addSeries(CandlestickSeries);
  const volumeSeries=chart.addSeries(HistogramSeries,{priceFormat:{type:'volume'},priceScaleId:''});
  const indicatorSeries=chart.addSeries(LineSeries,{priceScaleId:'right'});
  candleSeries.setData(candles.slice(-MAX_VISIBLE_POINTS));
  volumeSeries.setData(volume.slice(-MAX_VISIBLE_POINTS));
  indicatorSeries.setData(indicator.slice(-MAX_VISIBLE_POINTS));
  const lines=[entry&&candleSeries.createPriceLine({price:entry,title:'ENTRY',lineWidth:1}),stop&&candleSeries.createPriceLine({price:stop,title:'STOP',lineWidth:1}),...targets.map((price,i)=>candleSeries.createPriceLine({price,title:`TP${i+1}`,lineWidth:1}))].filter(Boolean);
  chart.timeScale().fitContent();
  const resize=new ResizeObserver(()=>chart.applyOptions({width:host.current?.clientWidth||0})); resize.observe(host.current);
  return ()=>{resize.disconnect(); lines.length=0; chart.remove()};
 },[candles,volume,indicator,entry,stop,targets]);
 return <div ref={host} role="img" aria-label="Candlestick, hacim, indikatör ve Entry/Stop/TP seviyeleri grafiği" style={{width:'100%',minHeight:420,touchAction:'pan-y'}}/>;
}
