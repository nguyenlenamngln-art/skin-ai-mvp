// Scan History layout polish V2.
// Reflow the existing filters, mode switch and session list without changing history/comparison logic.
function applyHistoryLayoutV2(){
  const card=$('#history .card')
  const head=card?.querySelector('.section-head')
  const shell=$('#sessionHistoryShell')
  const filters=$('#historyTrackingFilters')
  if(!card||!head||!shell||!filters) return

  card.classList.add('historyCardV2')
  head.classList.add('historySectionHeadV2')
  shell.classList.add('historyShellV2')

  // Session History V1 originally mounted the shell beside the filters inside
  // the flex header. Move it below the header so visit cards can use full width.
  if(shell.parentElement!==card) head.insertAdjacentElement('afterend',shell)

  if(!$('#historyControlsV2')){
    const controls=document.createElement('div')
    controls.id='historyControlsV2'
    controls.className='historyControlsV2'

    const filterGroup=document.createElement('div')
    filterGroup.className='historyFilterGroupV2'
    filterGroup.innerHTML='<span class="eyebrow">FILTER HISTORY</span>'
    filters.classList.add('historyFiltersV2')
    filterGroup.appendChild(filters)

    const viewGroup=document.createElement('div')
    viewGroup.className='historyViewGroupV2'
    viewGroup.innerHTML='<span class="eyebrow">VIEW</span>'
    const tabs=shell.querySelector('.historyModeTabs')
    if(tabs){
      tabs.classList.add('historyModeTabsV2')
      viewGroup.appendChild(tabs)
    }

    controls.append(filterGroup,viewGroup)
    shell.insertAdjacentElement('afterbegin',controls)
  }
}

applyHistoryLayoutV2()
// Tracking data populates asynchronously, but the structural nodes are created
// synchronously. A short follow-up makes the polish resilient to reload timing.
setTimeout(applyHistoryLayoutV2,0)
setTimeout(applyHistoryLayoutV2,150)
