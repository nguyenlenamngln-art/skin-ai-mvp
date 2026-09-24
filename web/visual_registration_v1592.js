// V1.5.9.2 compatibility loader.
// V1.5.9.3 is now the single authority for visual comparison registration.
(function(){
  if(document.querySelector('script[src*="mobile_comparison_registration_v1593.js"]')) return
  if(!document.querySelector('link[data-v1593-fallback]')){
    const link=document.createElement('link')
    link.rel='stylesheet'
    link.href='/app/mobile_comparison_registration_v1593.css?v=1593'
    link.dataset.v1593Fallback='1'
    document.head.appendChild(link)
  }
  if(!document.querySelector('script[data-v1593-fallback]')){
    const script=document.createElement('script')
    script.src='/app/mobile_comparison_registration_v1593.js?v=1593'
    script.dataset.v1593Fallback='1'
    document.body.appendChild(script)
  }
})()
