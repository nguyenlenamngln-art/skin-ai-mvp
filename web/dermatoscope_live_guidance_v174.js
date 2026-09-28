// V1.7.4 — Live previous-position guidance for close-up scan simulator.
(function(){
  const VERSION='1.7.4'
  const SIZE=96
  const SAMPLE_MS=900
  const locale=()=>{try{return window.skinI18n?.getLocale?.()||document.documentElement.dataset.locale||'vi'}catch(_e){return 'vi'}}
  const tr=(en,vi)=>locale()==='vi'?vi:en
  const SUB_LABELS={upper:['Upper','Phía trên'],middle:['Middle','Ở giữa'],lower:['Lower','Phía dưới'],center:['Center','Chính giữa'],left:['Left','Bên trái'],right:['Right','Bên phải'],custom:['